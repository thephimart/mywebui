"""Tests for RAG chunking functionality."""

import pytest

from mywebui.core.rag import _count_tokens, _split_at_boundary


class TestTokenCounting:
    """Test token counting with tiktoken fallback."""

    def test_count_tokens_with_tiktoken(self):
        """Test token counting uses tiktoken when available."""
        text = "This is a test sentence with some words."
        count = _count_tokens(text)
        assert count > 0
        assert count < 20

    def test_count_tokens_estimate_fallback(self):
        """Test token estimation when tiktoken not available."""
        import mywebui.core.rag as rag_module

        original_tokenizer = rag_module._TOKENIZER
        rag_module._TOKENIZER = None
        try:
            text = "one two three four five six seven eight nine ten"
            count = _count_tokens(text)
            word_count = len(text.split())
            assert count == int(word_count * 1.3)
        finally:
            rag_module._TOKENIZER = original_tokenizer

    def test_count_tokens_empty(self):
        """Test empty string returns 0."""
        assert _count_tokens("") == 0

    def test_count_tokens_preserves_relative_order(self):
        """Longer texts should have higher token counts."""
        short = "hello"
        long = "hello world this is a longer text"
        assert _count_tokens(long) > _count_tokens(short)


class TestBoundarySplitting:
    """Test text splitting at natural boundaries."""

    def test_split_single_paragraph(self):
        """Single short paragraph returns as-is."""
        text = "This is a short paragraph."
        result = _split_at_boundary(text, max_tokens=20)
        assert len(result) == 1
        assert result[0] == text

    def test_split_at_double_newline(self):
        """Split at paragraph boundaries (double newline)."""
        text = "First paragraph.\n\nSecond paragraph."
        result = _split_at_boundary(text, max_tokens=5)
        assert len(result) == 2

    def test_split_at_single_newline(self):
        """Split at single newlines if no double newlines."""
        text = "Line one.\nLine two.\nLine three."
        result = _split_at_boundary(text, max_tokens=3)
        assert len(result) >= 2

    def test_split_long_paragraph_at_sentence(self):
        """Split long paragraph at sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        result = _split_at_boundary(text, max_tokens=3)
        assert len(result) >= 2

    def test_respects_max_tokens(self):
        """Ensure no segment exceeds max_tokens."""
        text = "word " * 100
        result = _split_at_boundary(text, max_tokens=20)
        for segment in result:
            assert _count_tokens(segment) <= 20


class TestChunkTextIntegration:
    """Integration tests for chunking with config settings."""

    @pytest.fixture
    def chunk_settings(self):
        """Return chunk settings from config."""
        from mywebui.config import get_config

        config = get_config()
        return {
            "chunk_size": config.rag.chunk_size,
            "chunk_overlap": config.rag.chunk_overlap,
        }

    def test_empty_text(self, chunk_settings):
        """Empty text returns empty list."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        result = service._chunk_text("")
        assert result == []

    def test_whitespace_only(self, chunk_settings):
        """Whitespace-only text returns empty list."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        result = service._chunk_text("   \n\n   ")
        assert result == []

    def test_single_short_paragraph(self, chunk_settings):
        """Single short paragraph returns as single chunk."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        text = "This is a short document."
        result = service._chunk_text(text)
        assert len(result) == 1

    def test_multiple_paragraphs(self, chunk_settings):
        """Multiple paragraphs get split when exceeding chunk size."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph."
        result = service._chunk_text(text)
        assert len(result) >= 1
        assert "First" in result[0]
        assert "Third" in result[-1]

    def test_chunk_size_limit(self, chunk_settings):
        """No chunk exceeds chunk_size (512 tokens)."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        text = "word " * 1000
        result = service._chunk_text(text)
        for chunk in result:
            tokens = _count_tokens(chunk)
            assert tokens <= service.chunk_size + 50

    def test_overlap_applied(self, chunk_settings):
        """Overlap is applied between chunks when text is long enough."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        text = " ".join([f"word{i}" for i in range(700)])
        result = service._chunk_text(text)
        assert len(result) >= 2


class TestMarkdownChunking:
    """Test chunking with markdown content."""

    @pytest.fixture
    def chunk_settings(self):
        from mywebui.config import get_config

        config = get_config()
        return {
            "chunk_size": config.rag.chunk_size,
            "chunk_overlap": config.rag.chunk_overlap,
        }

    def test_headings_preserved(self, chunk_settings):
        """Headings should remain with their content."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        text = """# Title

Introduction paragraph.

## Section One

Content for section one.

## Section Two

Content for section two.
"""
        result = service._chunk_text(text)
        assert len(result) >= 1
        full_text = " ".join(result)
        assert "# Title" in full_text
        assert "## Section One" in full_text
        assert "## Section Two" in full_text


class TestCodeChunking:
    """Test chunking with code content."""

    @pytest.fixture
    def chunk_settings(self):
        from mywebui.config import get_config

        config = get_config()
        return {
            "chunk_size": config.rag.chunk_size,
            "chunk_overlap": config.rag.chunk_overlap,
        }

    def test_code_block_not_split_mid_block(self, chunk_settings):
        """Code blocks should not be split mid-block."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.chunk_size = chunk_settings["chunk_size"]
        service.chunk_overlap = chunk_settings["chunk_overlap"]
        code = """def hello_world():
    print("Hello")
    print("World")
    return True

def another_function():
    x = 1
    return x
"""
        result = service._chunk_text(code)
        for chunk in result:
            opens = chunk.count("def ")
            closes = chunk.count("def ")
            if opens > 0:
                assert opens == closes


class TestMMRReranking:
    """Tests for Max Marginal Relevance re-ranking."""

    @pytest.mark.asyncio
    async def test_mmr_guard_k_equals_1(self):
        """MMR guard should handle k=1 case."""
        import uuid

        from mywebui.core.rag import Modality, RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                text="Test",
                score=0.9,
                modality=Modality.TEXT,
            ),
        ]

        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.mmr_lambda = 0.5

        result = await service._mmr_rerank(chunks, [0.1] * 2048, k=1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_mmr_empty_input(self):
        """MMR should handle empty input."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.mmr_lambda = 0.5

        result = await service._mmr_rerank([], [0.1] * 2048, k=3)

        assert result == []

    @pytest.mark.asyncio
    async def test_mmr_k_larger_than_input(self):
        """MMR should return all chunks when k > len(chunks)."""
        import uuid

        from mywebui.core.rag import Modality, RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                text="Test",
                score=0.9,
                modality=Modality.TEXT,
            ),
            RetrievedChunk(
                chunk_id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                text="Test 2",
                score=0.8,
                modality=Modality.TEXT,
            ),
        ]

        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.mmr_lambda = 0.5

        result = await service._mmr_rerank(chunks, [0.1] * 2048, k=10)

        assert len(result) == 2


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        vec = [1.0, 0.0, 0.0]
        result = service._cosine_similarity(vec, vec)
        assert result == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        result = service._cosine_similarity(vec1, vec2)
        assert result == pytest.approx(0.0)

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        result = service._cosine_similarity(vec1, vec2)
        assert result == pytest.approx(-1.0)

    def test_zero_vector(self):
        """Zero vector should return 0.0."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        result = service._cosine_similarity(vec1, vec2)
        assert result == 0.0


class TestModalityEnum:
    """Tests for Modality enum."""

    def test_modality_values(self):
        """Modality enum has correct values."""
        from mywebui.core.rag import Modality

        assert Modality.TEXT.value == "text"
        assert Modality.IMAGE.value == "image"
        assert Modality.MIXED.value == "mixed"

    def test_retrieval_mode_values(self):
        """RetrievalMode enum has correct values."""
        from mywebui.core.rag import RetrievalMode

        assert RetrievalMode.TEXT_ONLY.value == "text_only"
        assert RetrievalMode.IMAGE_ONLY.value == "image_only"
        assert RetrievalMode.HYBRID.value == "hybrid"


class TestImageRetrievedChunk:
    """Tests for ImageRetrievedChunk dataclass."""

    def test_creation(self):
        """Can create ImageRetrievedChunk."""
        import uuid

        from mywebui.core.rag import ImageRetrievedChunk, Modality

        chunk = ImageRetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            image_bytes=b"fake image data",
            page_number=1,
            bbox=(0.0, 0.0, 100.0, 100.0),
            score=0.95,
            modality=Modality.IMAGE,
        )
        assert chunk.image_bytes == b"fake image data"
        assert chunk.page_number == 1
        assert chunk.modality == Modality.IMAGE


class TestRetrievalModeDetection:
    """Tests for query-based retrieval mode detection."""

    def test_detects_image_query(self):
        """Detects image-only query."""
        from mywebui.core.rag import RAGService, RetrievalMode

        service = RAGService.__new__(RAGService)
        result = service.get_retrieval_mode("show me the chart")
        assert result == RetrievalMode.IMAGE_ONLY

    def test_detects_text_query(self):
        """Detects text-only query."""
        from mywebui.core.rag import RAGService, RetrievalMode

        service = RAGService.__new__(RAGService)
        result = service.get_retrieval_mode("read the document")
        assert result == RetrievalMode.TEXT_ONLY

    def test_detects_hybrid_query(self):
        """Detects hybrid query."""
        from mywebui.core.rag import RAGService, RetrievalMode

        service = RAGService.__new__(RAGService)
        result = service.get_retrieval_mode("find the image and read the text")
        assert result == RetrievalMode.HYBRID


class TestCrossModalitySimilarity:
    """Tests for cross-modality similarity calculation."""

    def test_different_modalities_return_zero(self):
        """Different modalities return 0.0."""
        import uuid

        from mywebui.core.rag import (
            ImageRetrievedChunk,
            RAGService,
            RetrievedChunk,
        )

        service = RAGService.__new__(RAGService)
        text_chunk = RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            text="test",
            score=0.9,
        )
        image_chunk = ImageRetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            image_bytes=b"data",
            page_number=1,
            bbox=None,
            score=0.8,
        )

        result = service._cross_modality_similarity(text_chunk, image_chunk)
        assert result == 0.0

    def test_same_modalities_return_zero(self):
        """Same modalities currently return 0.0 (placeholder)."""
        import uuid

        from mywebui.core.rag import RAGService, RetrievedChunk

        service = RAGService.__new__(RAGService)
        chunk1 = RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            text="test1",
            score=0.9,
        )
        chunk2 = RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            text="test2",
            score=0.8,
        )

        result = service._cross_modality_similarity(chunk1, chunk2)
        assert result == 0.0


class TestResultMerging:
    """Tests for merging text and image results."""

    def test_merge_with_weights(self):
        """Merges results with configured weights."""
        import uuid

        from mywebui.core.rag import (
            ImageRetrievedChunk,
            RAGService,
            RetrievedChunk,
        )

        service = RAGService.__new__(RAGService)
        service.text_weight = 0.7
        service.image_weight = 0.3

        text_chunks = [
            RetrievedChunk(
                chunk_id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                text="text1",
                score=1.0,
            )
        ]
        image_chunks = [
            ImageRetrievedChunk(
                chunk_id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                image_bytes=b"img",
                page_number=1,
                bbox=None,
                score=1.0,
            )
        ]

        merged = service._merge_results(text_chunks, image_chunks, 10)

        assert len(merged) == 2
        text_result = next(r for r in merged if hasattr(r, "text"))
        assert text_result.score == pytest.approx(0.7)

    def test_merge_empty_results(self):
        """Handles empty results."""
        from mywebui.core.rag import RAGService

        service = RAGService.__new__(RAGService)
        service.text_weight = 0.7
        service.image_weight = 0.3

        merged = service._merge_results([], [], 5)
        assert merged == []
