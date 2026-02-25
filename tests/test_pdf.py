"""Tests for PDF text extraction."""

import io
from pathlib import Path

import pytest

from mywebui.core.pdf import (
    PDFDocument,
    PDFPage,
    extract_text_from_file,
    extract_text_from_path,
    get_full_text,
    get_page_texts,
    has_images,
)


class TestPDFPage:
    """Tests for PDFPage dataclass."""

    def test_pdf_page_creation(self):
        """PDFPage can be created with required fields."""
        page = PDFPage(page_number=1, text="Test content", has_images=False)
        assert page.page_number == 1
        assert page.text == "Test content"
        assert page.has_images is False

    def test_pdf_page_with_images(self):
        """PDFPage tracks image presence."""
        page = PDFPage(page_number=1, text="Content", has_images=True)
        assert page.has_images is True


class TestPDFDocument:
    """Tests for PDFDocument dataclass."""

    def test_pdf_document_creation(self):
        """PDFDocument can be created with pages."""
        pages = [
            PDFPage(page_number=1, text="Page 1"),
            PDFPage(page_number=2, text="Page 2"),
        ]
        doc = PDFDocument(filename="test.pdf", pages=pages, total_pages=2)

        assert doc.filename == "test.pdf"
        assert doc.total_pages == 2
        assert len(doc.pages) == 2


class TestGetFullText:
    """Tests for get_full_text function."""

    def test_empty_document(self):
        """Empty document returns empty string."""
        doc = PDFDocument(filename="test.pdf", pages=[], total_pages=0)
        result = get_full_text(doc)
        assert result == ""

    def test_single_page(self):
        """Single page document returns page text."""
        doc = PDFDocument(
            filename="test.pdf",
            pages=[PDFPage(page_number=1, text="Hello World")],
            total_pages=1,
        )
        result = get_full_text(doc)
        assert "Page 1" in result
        assert "Hello World" in result

    def test_multiple_pages(self):
        """Multiple pages include page markers."""
        doc = PDFDocument(
            filename="test.pdf",
            pages=[
                PDFPage(page_number=1, text="First page"),
                PDFPage(page_number=2, text="Second page"),
            ],
            total_pages=2,
        )
        result = get_full_text(doc)
        assert "Page 1" in result
        assert "Page 2" in result
        assert "First page" in result
        assert "Second page" in result


class TestGetPageTexts:
    """Tests for get_page_texts function."""

    def test_filters_empty_pages(self):
        """Empty pages are filtered out."""
        doc = PDFDocument(
            filename="test.pdf",
            pages=[
                PDFPage(page_number=1, text="Content"),
                PDFPage(page_number=2, text=""),
                PDFPage(page_number=3, text="More content"),
            ],
            total_pages=3,
        )
        result = get_page_texts(doc)
        assert len(result) == 2
        assert result[0] == (1, "Content")
        assert result[1] == (3, "More content")

    def test_returns_page_text_tuples(self):
        """Returns correct (page_number, text) tuples."""
        doc = PDFDocument(
            filename="test.pdf",
            pages=[
                PDFPage(page_number=5, text="Page five"),
            ],
            total_pages=1,
        )
        result = get_page_texts(doc)
        assert result == [(5, "Page five")]


class TestHasImages:
    """Tests for has_images function."""

    def test_no_images(self):
        """Returns False when no images."""
        doc = PDFDocument(
            filename="test.pdf",
            pages=[
                PDFPage(page_number=1, text="Text", has_images=False),
                PDFPage(page_number=2, text="More text", has_images=False),
            ],
            total_pages=2,
        )
        assert has_images(doc) is False

    def test_with_images(self):
        """Returns True when any page has images."""
        doc = PDFDocument(
            filename="test.pdf",
            pages=[
                PDFPage(page_number=1, text="Text", has_images=False),
                PDFPage(page_number=2, text="Has image", has_images=True),
            ],
            total_pages=2,
        )
        assert has_images(doc) is True


class TestExtractTextFromFile:
    """Tests for extract_text_from_file function."""

    def test_invalid_pdf(self):
        """Invalid PDF raises exception."""
        with pytest.raises(Exception):
            extract_text_from_file(io.BytesIO(b"not a pdf"))

    def test_extract_from_bytesio(self):
        """Can extract from BytesIO with name attribute."""
        file = io.BytesIO(b"%PDF-1.4 test")
        file.name = "test.pdf"
        with pytest.raises(Exception):
            extract_text_from_file(file)


class TestExtractTextFromPath:
    """Tests for extract_text_from_path function."""

    def test_nonexistent_path(self):
        """Nonexistent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            extract_text_from_path(Path("/nonexistent/file.pdf"))


class TestPDFImage:
    """Tests for PDFImage dataclass."""

    def test_pdf_image_creation(self):
        """PDFImage can be created with required fields."""
        from mywebui.core.pdf import PDFImage

        img = PDFImage(
            page_number=1,
            bbox=(0, 0, 100, 100),
            width=100,
            height=100,
            image_bytes=None,
            image_format="jpeg",
        )
        assert img.page_number == 1
        assert img.bbox == (0, 0, 100, 100)
        assert img.image_format == "jpeg"

    def test_pdf_image_optional_fields(self):
        """PDFImage works with optional fields as None."""
        from mywebui.core.pdf import PDFImage

        img = PDFImage(
            page_number=1,
            bbox=None,
            width=None,
            height=None,
            image_bytes=None,
            image_format=None,
        )
        assert img.bbox is None
        assert img.width is None


class TestExtractImages:
    """Tests for image extraction functions."""

    def test_extract_images_from_invalid_pdf(self):
        """Invalid PDF raises exception."""
        from mywebui.core.pdf import extract_images_from_file

        with pytest.raises(Exception):
            extract_images_from_file(io.BytesIO(b"not a pdf"))

    def test_extract_images_from_bytesio(self):
        """Can extract from BytesIO with name attribute."""
        from mywebui.core.pdf import extract_images_from_file

        file = io.BytesIO(b"%PDF-1.4 test")
        file.name = "test.pdf"
        with pytest.raises(Exception):
            extract_images_from_file(file)

    def test_extract_images_nonexistent_path(self):
        """Nonexistent path raises FileNotFoundError."""
        from mywebui.core.pdf import extract_images_from_path

        with pytest.raises(FileNotFoundError):
            extract_images_from_path(Path("/nonexistent/file.pdf"))


class TestGetImageCount:
    """Tests for get_image_count function."""

    def test_no_images(self):
        """Returns 0 when no pages have images."""
        from mywebui.core.pdf import get_image_count

        doc = PDFDocument(
            filename="test.pdf",
            pages=[
                PDFPage(page_number=1, text="Text", has_images=False),
                PDFPage(page_number=2, text="More text", has_images=False),
            ],
            total_pages=2,
        )
        assert get_image_count(doc) == 0

    def test_with_images(self):
        """Returns count of pages with images."""
        from mywebui.core.pdf import get_image_count

        doc = PDFDocument(
            filename="test.pdf",
            pages=[
                PDFPage(page_number=1, text="Text", has_images=False),
                PDFPage(page_number=2, text="Has image", has_images=True),
                PDFPage(page_number=3, text="Also has image", has_images=True),
            ],
            total_pages=3,
        )
        assert get_image_count(doc) == 2


class TestPDFImageBytes:
    """Tests for PDFImageBytes dataclass."""

    def test_pdf_image_bytes_creation(self):
        """PDFImageBytes can be created with all fields."""
        from mywebui.core.pdf import PDFImageBytes

        img = PDFImageBytes(
            page_number=0,
            bbox=(0.0, 0.0, 100.0, 100.0),
            width=100,
            height=100,
            color_space="RGB",
            bits_per_component=8,
            format="jpeg",
            byte_length=1024,
            data=b"fake image data",
        )
        assert img.page_number == 0
        assert img.bbox == (0.0, 0.0, 100.0, 100.0)
        assert img.width == 100
        assert img.height == 100
        assert img.color_space == "RGB"
        assert img.bits_per_component == 8
        assert img.format == "jpeg"
        assert img.byte_length == 1024
        assert img.data == b"fake image data"

    def test_pdf_image_bytes_frozen(self):
        """PDFImageBytes is immutable."""
        from mywebui.core.pdf import PDFImageBytes

        img = PDFImageBytes(
            page_number=0,
            bbox=(0.0, 0.0, 100.0, 100.0),
            width=100,
            height=100,
            color_space=None,
            bits_per_component=None,
            format=None,
            byte_length=0,
            data=b"",
        )
        with pytest.raises(AttributeError):
            img.page_number = 1  # type: ignore

    def test_pdf_image_bytes_optional_fields(self):
        """PDFImageBytes handles optional fields."""
        from mywebui.core.pdf import PDFImageBytes

        img = PDFImageBytes(
            page_number=0,
            bbox=(0.0, 0.0, 50.0, 50.0),
            width=50,
            height=50,
            color_space=None,
            bits_per_component=None,
            format=None,
            byte_length=0,
            data=b"",
        )
        assert img.color_space is None
        assert img.bits_per_component is None
        assert img.format is None


class TestPDFImageExtractionError:
    """Tests for PDFImageExtractionError exception."""

    def test_exception_can_be_raised(self):
        """PDFImageExtractionError can be raised."""
        from mywebui.core.pdf import PDFImageExtractionError

        with pytest.raises(PDFImageExtractionError):
            raise PDFImageExtractionError("Test error")

    def test_exception_has_message(self):
        """PDFImageExtractionError stores message."""
        from mywebui.core.pdf import PDFImageExtractionError

        err = PDFImageExtractionError("test message")
        assert str(err) == "test message"

    def test_exception_can_chain(self):
        """PDFImageExtractionError supports exception chaining."""
        from mywebui.core.pdf import PDFImageExtractionError

        original = ValueError("original")
        err: PDFImageExtractionError = PDFImageExtractionError("wrapped")
        err.__cause__ = original
        assert err.__cause__ is original


class TestExtractImageBytesFromFile:
    """Tests for extract_image_bytes_from_file function."""

    def test_returns_list(self):
        """Returns a list of PDFImageBytes."""
        from mywebui.core.pdf import extract_image_bytes_from_file

        pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
        if not pdf_path.exists():
            pytest.skip("Sample PDF not found")

        with open(pdf_path, "rb") as f:
            images = extract_image_bytes_from_file(f)

        assert isinstance(images, list)

    def test_images_have_required_fields(self):
        """Each image has all required fields."""
        from mywebui.core.pdf import extract_image_bytes_from_file

        pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
        if not pdf_path.exists():
            pytest.skip("Sample PDF not found")

        with open(pdf_path, "rb") as f:
            images = extract_image_bytes_from_file(f)

        for img in images:
            assert isinstance(img.page_number, int)
            assert isinstance(img.bbox, tuple)
            assert len(img.bbox) == 4
            assert isinstance(img.width, int)
            assert isinstance(img.height, int)
            assert isinstance(img.byte_length, int)
            assert isinstance(img.data, bytes)

    def test_empty_pdf_returns_empty_list(self):
        """Empty PDF returns empty list."""
        from mywebui.core.pdf import extract_image_bytes_from_file

        empty_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj
xref
0 3
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
trailer<</Size 3/Root 1 0 R>>
startxref
111
%%EOF"""
        f = io.BytesIO(empty_pdf)
        images = extract_image_bytes_from_file(f)
        assert images == []

    def test_invalid_pdf_raises_error(self):
        """Invalid PDF raises PDFImageExtractionError."""
        from mywebui.core.pdf import (
            PDFImageExtractionError,
            extract_image_bytes_from_file,
        )

        f = io.BytesIO(b"not a pdf")
        with pytest.raises(PDFImageExtractionError):
            extract_image_bytes_from_file(f)


class TestExtractImageBytesFromPath:
    """Tests for extract_image_bytes_from_path function."""

    def test_extracts_from_path(self):
        """Can extract from valid path."""
        from mywebui.core.pdf import extract_image_bytes_from_path

        pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
        if not pdf_path.exists():
            pytest.skip("Sample PDF not found")

        images = extract_image_bytes_from_path(pdf_path)
        assert isinstance(images, list)

    def test_nonexistent_path_raises_error(self):
        """Nonexistent path raises FileNotFoundError."""
        from mywebui.core.pdf import extract_image_bytes_from_path

        with pytest.raises(FileNotFoundError):
            extract_image_bytes_from_path(Path("/nonexistent/file.pdf"))


class TestIterImageBytes:
    """Tests for iter_image_bytes function."""

    def test_returns_iterator(self):
        """Returns an iterator of PDFImageBytes."""
        from mywebui.core.pdf import iter_image_bytes

        pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
        if not pdf_path.exists():
            pytest.skip("Sample PDF not found")

        with open(pdf_path, "rb") as f:
            images = list(iter_image_bytes(f))

        assert isinstance(images, list)


class TestEstimateTotalImageBytes:
    """Tests for estimate_total_image_bytes function."""

    def test_returns_int(self):
        """Returns integer estimate."""
        from mywebui.core.pdf import estimate_total_image_bytes

        pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
        if not pdf_path.exists():
            pytest.skip("Sample PDF not found")

        with open(pdf_path, "rb") as f:
            total = estimate_total_image_bytes(f)

        assert isinstance(total, int)
        assert total >= 0

    def test_empty_pdf_returns_zero(self):
        """Empty PDF returns 0."""
        from mywebui.core.pdf import estimate_total_image_bytes

        empty_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj
xref
0 3
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
trailer<</Size 3/Root 1 0 R>>
startxref
111
%%EOF"""
        f = io.BytesIO(empty_pdf)
        total = estimate_total_image_bytes(f)
        assert total == 0
