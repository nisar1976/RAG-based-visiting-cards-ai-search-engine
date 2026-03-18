import logging
import easyocr

logger = logging.getLogger(__name__)

_reader = None


def get_reader():
    """Initialize and cache EasyOCR reader."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def extract(image_path: str) -> list[str]:
    """
    Extract text from image using EasyOCR.
    Returns a list of text lines.
    """
    try:
        reader = get_reader()
        result = reader.readtext(image_path, detail=0)
        return list(result) if result else []
    except Exception as e:
        logger.warning(f"EasyOCR extraction failed for {image_path}: {e}")
        return []
