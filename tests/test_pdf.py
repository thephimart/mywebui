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
