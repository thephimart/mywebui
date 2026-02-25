"""PDF text and image extraction for RAG.

NOTE: Phase 3.1-3.2 scope only.
PDF text extraction -> chunk -> embed -> retrieve.
Image extraction (no vision embeddings yet).
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)


class PDFImageExtractionError(Exception):
    """Raised when PDF image extraction fails due to structural issues."""

    pass


@dataclass(frozen=True)
class PDFImageBytes:
    """Raw image bytes extracted from a PDF.

    Immutable and short-lived by design. Callers must not cache
    or hold references across async boundaries.
    """

    page_number: int
    bbox: tuple[float, float, float, float]
    width: int
    height: int
    color_space: str | None
    bits_per_component: int | None
    format: str | None
    byte_length: int
    data: bytes


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


def _extract_page_images(page: Any, page_number: int) -> list[PDFImage]:
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


def extract_image_bytes_from_file(file: BinaryIO) -> list[PDFImageBytes]:
    """Extract raw image bytes from a PDF file.

    Returns raw, unmodified image data as embedded in the PDF.
    No decoding, resizing, or normalization is performed.

    Args:
        file: File-like object containing PDF data

    Returns:
        List of PDFImageBytes in page order, then object order

    Raises:
        PDFImageExtractionError: On structural PDF failures
    """
    try:
        reader = PdfReader(file)
    except PdfReadError as e:
        raise PDFImageExtractionError(f"Failed to read PDF: {e}") from e
    except Exception as e:
        raise PDFImageExtractionError(f"Unexpected error reading PDF: {e}") from e

    images: list[PDFImageBytes] = []

    try:
        for page_num, page in enumerate(reader.pages):
            page_images = _extract_page_image_bytes(page, page_num)
            images.extend(page_images)
    except PDFImageExtractionError:
        raise
    except Exception as e:
        raise PDFImageExtractionError(f"Failed to extract images: {e}") from e

    return images


def extract_image_bytes_from_path(path: Path) -> list[PDFImageBytes]:
    """Extract raw image bytes from a PDF file path.

    Args:
        path: Path to PDF file

    Returns:
        List of PDFImageBytes

    Raises:
        PDFImageExtractionError: On structural PDF failures
    """
    with open(path, "rb") as f:
        return extract_image_bytes_from_file(f)


def iter_image_bytes(file: BinaryIO) -> Iterator[PDFImageBytes]:
    """Iterate over image bytes from a PDF file lazily.

    Useful for memory-constrained processing of large PDFs.

    Args:
        file: File-like object containing PDF data

    Yields:
        PDFImageBytes objects

    Raises:
        PDFImageExtractionError: On structural PDF failures
    """
    try:
        reader = PdfReader(file)
    except PdfReadError as e:
        raise PDFImageExtractionError(f"Failed to read PDF: {e}") from e
    except Exception as e:
        raise PDFImageExtractionError(f"Unexpected error reading PDF: {e}") from e

    for page_num, page in enumerate(reader.pages):
        yield from _extract_page_image_bytes(page, page_num)


def estimate_total_image_bytes(file: BinaryIO) -> int:
    """Estimate total image bytes without full extraction.

    Reads the PDF to count images and estimate total size.

    Args:
        file: File-like object containing PDF data

    Returns:
        Estimated total byte length of all images
    """
    images = extract_image_bytes_from_file(file)
    return sum(img.byte_length for img in images)


def _extract_page_image_bytes(page: Any, page_number: int) -> list[PDFImageBytes]:
    """Extract image bytes from a single PDF page."""
    images: list[PDFImageBytes] = []
    seen_objs: set[int] = set()

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

            obj_id = id(obj)
            if obj_id in seen_objs:
                continue
            seen_objs.add(obj_id)

            img = _extract_image_data(obj, page_number)
            if img is not None:
                images.append(img)

    except Exception as e:
        logger.debug(f"Error extracting bytes from page {page_number}: {e}")

    return images


def _extract_image_data(obj: dict, page_number: int) -> PDFImageBytes | None:
    """Extract raw image data from a PDF image object."""
    try:
        width = obj.get("/Width")
        height = obj.get("/Height")

        if width is None or height is None:
            return None

        width = int(width)
        height = int(height)

        color_space = _get_color_space(obj)
        bits_per_component = _get_bits_per_component(obj)
        img_format = _get_image_format(obj)

        try:
            data = obj.get_data()  # type: ignore[attr-defined]
        except Exception:
            data = b""

        byte_length = len(data)

        bbox = _get_image_bbox(obj)

        return PDFImageBytes(
            page_number=page_number,
            bbox=bbox,
            width=width,
            height=height,
            color_space=color_space,
            bits_per_component=bits_per_component,
            format=img_format,
            byte_length=byte_length,
            data=data,
        )

    except Exception as e:
        logger.debug(f"Failed to extract image data: {e}")
        return None


def _get_color_space(obj: dict) -> str | None:
    """Extract color space from PDF image object."""
    cs = obj.get("/ColorSpace")
    if cs is None:
        return None

    cs_str = str(cs)
    if cs_str.startswith("/DeviceRGB"):
        return "RGB"
    elif cs_str.startswith("/DeviceGray"):
        return "Gray"
    elif cs_str.startswith("/DeviceCMYK"):
        return "CMYK"
    elif cs_str.startswith("/CalRGB"):
        return "CalRGB"
    elif cs_str.startswith("/CalGray"):
        return "CalGray"
    elif cs_str.startswith("/Lab"):
        return "Lab"
    elif cs_str.startswith("/ICCBased"):
        return "ICCBased"
    elif cs_str.startswith("/Indexed"):
        return "Indexed"
    return None


def _get_bits_per_component(obj: dict) -> int | None:
    """Extract bits per component from PDF image object."""
    bpc = obj.get("/BitsPerComponent")
    return int(bpc) if bpc is not None else None


def _get_image_bbox(obj: dict) -> tuple[float, float, float, float]:
    """Extract bounding box from PDF image object."""
    bbox = obj.get("/BBox")
    if bbox and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
    return (0.0, 0.0, float(obj.get("/Width", 0)), float(obj.get("/Height", 0)))
