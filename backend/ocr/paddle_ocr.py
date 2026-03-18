import logging

logger = logging.getLogger(__name__)

_ocr = None


def get_ocr():
    """Initialize and cache PaddleOCR instance."""
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(use_angle_cls=True, lang='en')
    return _ocr


def extract(image_path: str) -> list[str]:
    """
    Extract text from image using PaddleOCR.
    Returns a list of text lines.
    """
    # Temporarily disabled due to show_log parameter issue with current PaddleOCR version
    logger.warning(f"PaddleOCR disabled for {image_path}")
    return []
