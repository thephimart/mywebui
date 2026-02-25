"""PDF text and image extraction for RAG.

NOTE: Phase 3.1-3.2 scope only.
PDF text extraction -> chunk -> embed -> retrieve.
Image extraction (no vision embeddings yet).
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

logger = logging.getLogger(__name__)


@dataclass
class PDFPage:
    """Represents a single page from a PDF."""

    page_number: int
    text: str
    has_images: bool = False


@dataclass
class PDFImage:
    """Represents an image extracted from a PDF."""

    page_number: int
    bbox: tuple[float, float, float, float] | None
    width: int | None
    height: int | None
    image_bytes: bytes | None
    image_format: str | None


@dataclass
class PDFDocument:
    """Represents an extracted PDF document."""

    filename: str
    pages: list[PDFPage]
    total_pages: int


def extract_text_from_file(file: BinaryIO) -> PDFDocument:
    """Extract text from a PDF file.

    Args:
        file: File-like object containing PDF data

    Returns:
        PDFDocument with extracted text per page
    """
    try:
        reader = PdfReader(file)
        pages = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            has_images = "/XObject" in page.get("/Resources", {})

            pages.append(
                PDFPage(
                    page_number=i + 1,
                    text=text or "",
                    has_images=has_images,
                )
            )

        return PDFDocument(
            filename=getattr(file, "name", "unknown.pdf"),
            pages=pages,
            total_pages=len(pages),
        )
    except Exception as e:
        logger.error(f"Failed to extract PDF: {e}")
        raise


def extract_text_from_path(path: Path) -> PDFDocument:
    """Extract text from a PDF file path.

    Args:
        path: Path to PDF file

    Returns:
        PDFDocument with extracted text per page
    """
    with open(path, "rb") as f:
        return extract_text_from_file(f)


def get_full_text(doc: PDFDocument) -> str:
    """Get full text from a PDF document.

    Args:
        doc: PDFDocument to extract from

    Returns:
        Full text with page markers
    """
    parts = []
    for page in doc.pages:
        parts.append(f"[Page {page.page_number}]\n{page.text}")

    return "\n\n".join(parts)


def get_page_texts(doc: PDFDocument) -> list[tuple[int, str]]:
    """Get text per page from a PDF document.

    Args:
        doc: PDFDocument to extract from

    Returns:
        List of (page_number, text) tuples
    """
    return [(p.page_number, p.text) for p in doc.pages if p.text.strip()]


def has_images(doc: PDFDocument) -> bool:
    """Check if PDF contains any images.

    Args:
        doc: PDFDocument to check

    Returns:
        True if any page contains images
    """
    return any(p.has_images for p in doc.pages)


def extract_images_from_file(file: BinaryIO) -> list[PDFImage]:
    """Extract images from a PDF file.

    NOTE: This extracts metadata only. Image bytes are not extracted
    to keep memory usage low. Use extract_images_with_bytes() if needed.

    Args:
        file: File-like object containing PDF data

    Returns:
        List of PDFImage objects with page, bbox, and dimensions
    """
    images: list[PDFImage] = []

    try:
        reader = PdfReader(file)

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_images = _extract_page_images(page, page_num)
                images.extend(page_images)
            except Exception as e:
                logger.warning(f"Failed to extract images from page {page_num}: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to extract images from PDF: {e}")
        raise

    return images


def extract_images_from_path(path: Path) -> list[PDFImage]:
    """Extract images from a PDF file path.

    Args:
        path: Path to PDF file

    Returns:
        List of PDFImage objects
    """
    with open(path, "rb") as f:
        return extract_images_from_file(f)


def _extract_page_images(page, page_number: int) -> list[PDFImage]:
    """Extract images from a single PDF page."""
    images: list[PDFImage] = []

    try:
        resources = page.get("/Resources")
        if resources is None:
            return images

        xobj = resources.get("/XObject")
        if xobj is None or not isinstance(xobj, dict):
            return images

        for obj_name in xobj:
            obj = xobj[obj_name]
            if not isinstance(obj, dict):
                continue

            subtype = obj.get("/Subtype")
            if subtype != "/Image":
                continue

            width = obj.get("/Width")
            height = obj.get("/Height")

            bbox: tuple[float, float, float, float] | None = None

            images.append(
                PDFImage(
                    page_number=page_number,
                    bbox=bbox,
                    width=int(width) if width else None,
                    height=int(height) if height else None,
                    image_bytes=None,
                    image_format=_get_image_format(obj),
                )
            )

    except Exception as e:
        logger.debug(f"Error parsing page {page_number}: {e}")

    return images


def _get_image_format(obj: dict) -> str | None:
    """Determine image format from PDF object."""
    filter_type = obj.get("/Filter")
    if filter_type is None:
        return "raw"
    filter_str = str(filter_type)
    if "DCT" in filter_str:
        return "jpeg"
    elif "JPX" in filter_str:
        return "jpeg2000"
    elif "Flate" in filter_str:
        return "png"
    return "unknown"


def get_image_count(doc: PDFDocument) -> int:
    """Count total images in a PDF document.

    Note: This only returns the count from metadata, not actual
    extracted images.

    Args:
        doc: PDFDocument to check

    Returns:
        Number of pages with images (estimated)
    """
    return sum(1 for p in doc.pages if p.has_images)
