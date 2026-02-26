"""Tests for VL embedding models."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mywebui.core.models import (
    BaseVLEmbeddingModel,
    EmbeddingInput,
    EmbeddingResult,
    ImageInput,
    OpenAICompatibleVLEmbeddingModel,
    get_vl_embedding_model,
)


class TestImageInput:
    """Tests for ImageInput dataclass."""

    def test_image_input_creation(self):
        """ImageInput can be created with required fields."""
        img = ImageInput(bytes=b"fake image data", format="jpeg")
        assert img.bytes == b"fake image data"
        assert img.format == "jpeg"

    def test_image_input_optional_format(self):
        """ImageInput handles optional format."""
        img = ImageInput(bytes=b"data")
        assert img.format is None


class TestEmbeddingInput:
    """Tests for EmbeddingInput type."""

    def test_accepts_string(self):
        """EmbeddingInput accepts str."""
        inp: EmbeddingInput = "text string"
        assert isinstance(inp, str)

    def test_accepts_image_input(self):
        """EmbeddingInput accepts ImageInput."""
        inp: EmbeddingInput = ImageInput(bytes=b"data", format="png")
        assert isinstance(inp, ImageInput)


class TestOpenAICompatibleVLEmbeddingModel:
    """Tests for OpenAICompatibleVLEmbeddingModel."""

    def test_initialization(self):
        """Can initialize with url and model."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
        )
        assert model.url == "http://localhost:11433"
        assert model.model == "qwen2-vl-2b"
        assert model.dimension is None

    def test_initialization_with_dimension(self):
        """Can initialize with dimension."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
            dimension=2048,
        )
        assert model.dimension == 2048

    def test_initialization_strips_trailing_slash(self):
        """URL trailing slash is stripped."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433/",
            model="qwen2-vl-2b",
        )
        assert model.url == "http://localhost:11433"

    def test_initialization_with_api_key(self):
        """Can initialize with API key."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
            api_key="secret-key",
        )
        assert model.api_key == "secret-key"


class TestVLEmbeddingClientProperty:
    """Tests for client property."""

    def test_client_created_on_demand(self):
        """Client is created on first access."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
        )
        client = model.client
        assert client is not None

    def test_client_reused(self):
        """Client is reused on subsequent access."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
        )
        client1 = model.client
        client2 = model.client
        assert client1 is client2


class TestEmbedImages:
    """Tests for embed_images method."""

    @pytest.mark.asyncio
    async def test_embed_images_basic(self):
        """Can embed a single image."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "qwen2-vl-2b",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        model._client = mock_client

        result = await model.embed_images([b"fake image bytes"])

        assert isinstance(result, EmbeddingResult)
        assert len(result.embeddings) == 1
        assert result.embeddings[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_images_multiple(self):
        """Can embed multiple images."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2]},
                {"embedding": [0.3, 0.4]},
            ],
            "model": "qwen2-vl-2b",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        model._client = mock_client

        result = await model.embed_images([b"img1", b"img2"])

        assert len(result.embeddings) == 2

    @pytest.mark.asyncio
    async def test_embed_images_with_api_key(self):
        """Includes API key in headers when set."""
        model = OpenAICompatibleVLEmbeddingModel(
            url="http://localhost:11433",
            model="qwen2-vl-2b",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1]}],
            "model": "qwen2-vl-2b",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        model._client = mock_client

        await model.embed_images([b"data"])

        call_args = mock_client.post.call_args
        headers = call_args.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer test-key"


class TestGetVLEmbeddingModel:
    """Tests for get_vl_embedding_model factory."""

    def test_returns_vl_embedding_model(self):
        """Returns BaseVLEmbeddingModel instance."""
        from mywebui.config import ModelConfig

        with patch("mywebui.core.models.get_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.models.image_embedding = ModelConfig(
                url="http://localhost:11433",
                model="qwen2-vl-2b",
            )
            mock_cfg.rag.embedding_dimension = 2048
            mock_config.return_value = mock_cfg

            model = get_vl_embedding_model()

            assert isinstance(model, OpenAICompatibleVLEmbeddingModel)

    def test_caching(self):
        """Model is cached after first call."""
        from mywebui.config import ModelConfig

        with patch("mywebui.core.models.get_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.models.image_embedding = ModelConfig(
                url="http://localhost:11433",
                model="qwen2-vl-2b",
            )
            mock_cfg.rag.embedding_dimension = 2048
            mock_config.return_value = mock_cfg

            model1 = get_vl_embedding_model()
            model2 = get_vl_embedding_model()

            assert model1 is model2


class TestBaseVLEmbeddingModel:
    """Tests for BaseVLEmbeddingModel abstract class."""

    def test_cannot_instantiate_directly(self):
        """BaseVLEmbeddingModel cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseVLEmbeddingModel()
