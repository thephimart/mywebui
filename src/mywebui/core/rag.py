"""RAG (Retrieval-Augmented Generation) service."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.db.models import Document, Chunk, Embedding
from mywebui.core.models import get_embedding_model


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
        self.embedding_model = get_embedding_model(embedding_model_name)

    async def search(
        self,
        db: AsyncSession,
        query: str,
        user_id: uuid.UUID,
        limit: int = 5,
        category: str | None = None,
    ) -> list[RetrievedChunk]:
        """Search for relevant chunks."""
        query_embedding = await self.embedding_model.embed([query])
        query_vector = query_embedding.embeddings[0]
        
        base_query = (
            select(Chunk, Document, Embedding)
            .join(Document, Chunk.document_id == Document.id)
            .join(Embedding, Chunk.id == Embedding.chunk_id)
        )
        
        query_conditions = []
        query_conditions.append(
            (Document.visibility == "public") |
            (Document.owner_id == user_id)
        )
        
        if category:
            query_conditions.append(Document.categories.contains([category]))
        
        filtered_query = base_query.where(*query_conditions)
        
        result = await db.execute(filtered_query.limit(limit * 2))
        rows = result.all()
        
        chunks_with_scores = []
        for chunk, doc, embedding in rows:
            if embedding and embedding.vector:
                stored_vector = self._bytes_to_vector(embedding.vector)
                score = self._cosine_similarity(query_vector, stored_vector)
                
                chunks_with_scores.append(RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    text=chunk.text or "",
                    score=score,
                    modality=chunk.modality,
                ))
        
        chunks_with_scores.sort(key=lambda x: x.score, reverse=True)
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
                token_count=len(chunk_text.split()),
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

    def _chunk_text(self, text: str, target_tokens: int = 500) -> list[str]:
        """Split text into chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), target_tokens):
            chunk = " ".join(words[i:i + target_tokens])
            chunks.append(chunk)
        
        return chunks

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
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Get the global RAG service."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
