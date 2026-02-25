"""RAG (Retrieval-Augmented Generation) service.

NOTE: Phase 1 scope only.
No PDF parsing, no vision logic, no storage refactors beyond config wiring.
"""

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.config import get_config
from mywebui.core.models import get_embedding_model
from mywebui.db.models import Chunk, Document, Embedding

logger = logging.getLogger(__name__)

try:
    import tiktoken
    from tiktoken import Encoding

    _TOKENIZER: Encoding | None = tiktoken.get_encoding("cl100k_base")
except ImportError:
    _TOKENIZER = None
    logger.debug("tiktoken not available, using word*1.3 token estimation")


def _count_tokens(text: str) -> int:
    """Count tokens in text.

    Uses tiktoken if available, falls back to word*1.3 estimate.
    """
    if _TOKENIZER:
        return len(_TOKENIZER.encode(text))
    return int(len(text.split()) * 1.3)


def _split_at_boundary(text: str, max_tokens: int) -> list[str]:
    """Split text at natural boundaries within token limit.

    Prefers splitting at:
    1. Double newlines (paragraphs)
    2. Single newlines
    3. Sentence endings (. ! ?)
    4. Clause separators (, ; : )
    5. Word boundaries (fallback)

    Returns list of text segments that each fit within max_tokens.
    """
    if _count_tokens(text) <= max_tokens:
        return [text]

    paragraphs = re.split(r"\n\n+", text)
    if len(paragraphs) == 1:
        paragraphs = re.split(r"\n", text)
    if len(paragraphs) == 1:
        paragraphs = re.split(r"(?<=[.!?])\s+", text)
    if len(paragraphs) == 1:
        paragraphs = re.split(r"(?<=[:;,])\s+", text)

    chunks: list[str] = []
    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _count_tokens(para)

        if para_tokens <= max_tokens:
            if current_tokens + para_tokens <= max_tokens:
                current_chunk = (current_chunk + "\n\n" + para).strip()
                current_tokens += para_tokens
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
                current_tokens = para_tokens
        else:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
                current_tokens = 0

            sub_chunks = _split_by_words(para, max_tokens)
            for j, sub in enumerate(sub_chunks):
                sub_tokens = _count_tokens(sub)
                if current_tokens + sub_tokens <= max_tokens:
                    current_chunk = (current_chunk + " " + sub).strip()
                    current_tokens += sub_tokens
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sub
                    current_tokens = sub_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return [c for c in chunks if c.strip()]


def _split_by_words(text: str, max_tokens: int) -> list[str]:
    """Split text by words when no natural boundaries exist.

    Uses word-based splitting with safety margin.
    """
    words = text.split()
    chunks: list[str] = []
    current = []
    current_tokens = 0

    safety_margin = int(max_tokens * 0.9)

    for word in words:
        word_tokens = _count_tokens(word)
        if current_tokens + word_tokens <= safety_margin:
            current.append(word)
            current_tokens += word_tokens
        else:
            if current:
                chunks.append(" ".join(current))
            current = [word]
            current_tokens = word_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks


@dataclass
class RetrievedChunk:
    """A retrieved chunk with score."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    score: float
    modality: str


class RAGService:
    """Service for retrieval-augmented generation."""

    def __init__(self, embedding_model_name: str = "embedding"):
        config = get_config()
        self.chunk_size = config.rag.chunk_size
        self.chunk_overlap = config.rag.chunk_overlap
        self.embedding_ctx_size = config.rag.embedding_ctx_size
        self.mmr_lambda = config.rag.mmr_lambda
        self.embedding_model = get_embedding_model(embedding_model_name)

    async def search(
        self,
        db: AsyncSession,
        query: str,
        user_id: uuid.UUID,
        limit: int = 5,
        category: str | None = None,
        use_mmr: bool = False,
    ) -> list[RetrievedChunk]:
        """Search for relevant chunks.

        Args:
            db: Database session
            query: Search query
            user_id: User ID for ACL filtering
            limit: Max results to return
            category: Optional category filter
            use_mmr: Whether to use MMR re-ranking
        """
        query_embedding = await self.embedding_model.embed([query])
        query_vector = query_embedding.embeddings[0]

        base_query = (
            select(Chunk, Document, Embedding)
            .join(Document, Chunk.document_id == Document.id)
            .join(Embedding, Chunk.id == Embedding.chunk_id)
        )

        query_conditions: list[Any] = []
        query_conditions.append((Document.visibility == "public") | (Document.owner_id == user_id))

        if category:
            query_conditions.append(Document.categories.contains([category]))

        filtered_query = base_query.where(*query_conditions)

        result = await db.execute(filtered_query.limit(limit * 3))
        rows = result.all()

        chunks_with_scores = []
        for chunk, doc, embedding in rows:
            if embedding and embedding.vector:
                stored_vector = self._bytes_to_vector(embedding.vector)
                score = self._cosine_similarity(query_vector, stored_vector)

                chunks_with_scores.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=doc.id,
                        text=chunk.text or "",
                        score=score,
                        modality=chunk.modality,
                    )
                )

        chunks_with_scores.sort(key=lambda x: x.score, reverse=True)

        if use_mmr and limit > 1 and len(chunks_with_scores) > limit:
            chunks_with_scores = await self._mmr_rerank(
                chunks_with_scores,
                query_vector,
                lambda_mult=self.mmr_lambda,
                k=limit,
            )

        return chunks_with_scores[:limit]

    async def ingest_document(
        self,
        db: AsyncSession,
        owner_id: uuid.UUID,
        title: str,
        text: str,
        modality: str = "text",
        visibility: str = "private",
        categories: list[str] | None = None,
        source: str | None = None,
    ) -> Document:
        """Ingest a document and create chunks."""
        doc = Document(
            id=uuid.uuid4(),
            owner_id=owner_id,
            title=title,
            visibility=visibility,
            categories=categories or [],
            source=source,
            created_at=datetime.utcnow(),
        )
        db.add(doc)

        chunks = self._chunk_text(text)

        for i, chunk_text in enumerate(chunks):
            chunk = Chunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                modality=modality,
                text=chunk_text,
                chunk_index=i,
                token_count=_count_tokens(chunk_text),
                created_at=datetime.utcnow(),
            )
            db.add(chunk)

            if modality == "text" and chunk_text.strip():
                embedding_result = await self.embedding_model.embed([chunk_text])
                embedding = Embedding(
                    id=uuid.uuid4(),
                    chunk_id=chunk.id,
                    model_name="default",
                    modality="text",
                    vector=self._vector_to_bytes(embedding_result.embeddings[0]),
                )
                db.add(embedding)

        await db.commit()
        await db.refresh(doc)
        return doc

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks with overlap.

        Uses tiktoken if available, fallback to word*1.3 estimate.
        Enforces hard cap at chunk_size tokens.
        Applies chunk_overlap for continuity.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks, each within chunk_size tokens
        """
        if not text.strip():
            return []

        if _count_tokens(text) <= self.chunk_size:
            return [text]

        paragraphs = re.split(r"\n\n+", text)
        if len(paragraphs) == 1:
            paragraphs = re.split(r"\n", text)
        if len(paragraphs) == 1:
            paragraphs = re.split(r"(?<=[.!?])\s+", text)
        if len(paragraphs) == 1:
            paragraphs = re.split(r"(?<=[:;,])\s+", text)

        if len(paragraphs) == 1 and _count_tokens(paragraphs[0]) > self.chunk_size:
            paragraphs = self._split_large_segment(text)

        all_chunks: list[str] = []
        current_chunk = ""
        current_tokens = 0

        for para in paragraphs:
            para_tokens = _count_tokens(para)

            if para_tokens <= self.chunk_size:
                if current_tokens + para_tokens <= self.chunk_size:
                    current_chunk = (current_chunk + "\n\n" + para).strip()
                    current_tokens = _count_tokens(current_chunk)
                else:
                    if current_chunk:
                        all_chunks.append(current_chunk)
                    current_chunk = para
                    current_tokens = para_tokens
            else:
                if current_chunk:
                    all_chunks.append(current_chunk)
                    current_chunk = ""
                    current_tokens = 0

                sub_chunks = self._split_large_segment(para)
                for sub in sub_chunks:
                    sub_tokens = _count_tokens(sub)
                    if current_tokens + sub_tokens <= self.chunk_size:
                        current_chunk = (current_chunk + " " + sub).strip()
                        current_tokens = _count_tokens(current_chunk)
                    else:
                        if current_chunk:
                            all_chunks.append(current_chunk)
                        current_chunk = sub
                        current_tokens = sub_tokens

        if current_chunk:
            all_chunks.append(current_chunk)

        if self.chunk_overlap == 0 or len(all_chunks) <= 1:
            return all_chunks

        result_chunks: list[str] = [all_chunks[0]]

        for i in range(1, len(all_chunks)):
            prev_chunk = all_chunks[i - 1]
            curr_chunk = all_chunks[i]

            prev_words = prev_chunk.split()
            overlap_words = prev_words[-self.chunk_overlap * 2 :] if self.chunk_overlap > 0 else []

            if overlap_words:
                overlap_text = " ".join(overlap_words)
                combined = overlap_text + " " + curr_chunk
                if _count_tokens(combined) <= self.chunk_size:
                    result_chunks.append(combined)
                else:
                    result_chunks.append(curr_chunk)
            else:
                result_chunks.append(curr_chunk)

        return result_chunks

    def _split_large_segment(self, text: str) -> list[str]:
        """Split a large segment into smaller chunks.

        Used when a natural boundary still exceeds chunk_size.
        """
        chunks: list[str] = []
        current = ""
        current_tokens = 0

        sentences = re.split(r"(?<=[.!?])\s+", text)

        if len(sentences) == 1 and _count_tokens(sentences[0]) > self.chunk_size:
            sentences = []

        for sent in sentences:
            sent_tokens = _count_tokens(sent)

            if sent_tokens <= self.chunk_size:
                if current_tokens + sent_tokens <= self.chunk_size:
                    current = (current + " " + sent).strip()
                    current_tokens += sent_tokens
                else:
                    if current:
                        chunks.append(current)
                    current = sent
                    current_tokens = sent_tokens
            else:
                if current:
                    chunks.append(current)
                    current = ""
                    current_tokens = 0

                word_chunks = self._split_by_words(sent)
                chunks.extend(word_chunks[:-1])
                current = word_chunks[-1] if word_chunks else ""
                current_tokens = _count_tokens(current)

        if current:
            chunks.append(current)

        if not chunks:
            return self._split_by_words(text)

        return chunks

    def _split_by_words(self, text: str) -> list[str]:
        """Split text by words when no natural boundaries exist."""
        words = text.split()
        chunks: list[str] = []
        current = []
        current_tokens = 0

        safety_margin = int(self.chunk_size * 0.9)

        for word in words:
            word_tokens = _count_tokens(word)
            if current_tokens + word_tokens <= safety_margin:
                current.append(word)
                current_tokens += word_tokens
            else:
                if current:
                    chunks.append(" ".join(current))
                current = [word]
                current_tokens = word_tokens

        if current:
            chunks.append(" ".join(current))

        return chunks

    async def _mmr_rerank(
        self,
        chunks: list[RetrievedChunk],
        query_embedding: list[float],
        lambda_mult: float = 0.5,
        k: int = 5,
    ) -> list[RetrievedChunk]:
        """Max Marginal Relevance re-ranking.

        Balances relevance and diversity in retrieval results.

        Args:
            chunks: Candidate chunks from initial retrieval
            query_embedding: Query vector for relevance scoring
            lambda_mult: 0.0 = max relevance, 1.0 = max diversity
            k: Number of results to return

        Default lambda=0.5 (balanced).
        """
        if not chunks or k >= len(chunks):
            return chunks[:k]

        chunk_embeddings: dict[int, list[float]] = {}
        for i, chunk in enumerate(chunks):
            emb = await self.embedding_model.embed([chunk.text])
            chunk_embeddings[i] = emb.embeddings[0]

        selected: list[RetrievedChunk] = []
        selected_indices: list[int] = []
        remaining_indices = list(range(len(chunks)))

        for _ in range(k):
            if not remaining_indices:
                break

            best_score = float("-inf")
            best_idx = 0

            for idx in remaining_indices:
                chunk = chunks[idx]
                relevance = chunk.score

                max_sim_to_selected = 0.0
                if selected_indices:
                    chunk_emb = chunk_embeddings[idx]
                    for sel_idx in selected_indices:
                        sel_emb = chunk_embeddings[sel_idx]
                        sim = self._cosine_similarity(chunk_emb, sel_emb)
                        max_sim_to_selected = max(max_sim_to_selected, sim)

                mmr_score = lambda_mult * max_sim_to_selected - (1 - lambda_mult) * relevance

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            selected.append(chunks[best_idx])
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)

        return selected

    def _vector_to_bytes(self, vector: list[float]) -> bytes:
        """Convert embedding vector to bytes."""
        import struct

        return struct.pack(f"{len(vector)}f", *vector)

    def _bytes_to_vector(self, data: bytes) -> list[float]:
        """Convert bytes back to embedding vector."""
        import struct

        return list(struct.unpack(f"{len(data) // 4}f", data))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product: float = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        result: float = dot_product / (magnitude_a * magnitude_b)
        return result


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Get the global RAG service."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
