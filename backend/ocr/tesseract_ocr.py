import logging
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


def extract(image_path: str) -> list[str]:
    """
    Extract text from image using Tesseract OCR.
    Returns a list of text lines.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines
    except FileNotFoundError:
        logger.warning(f"Image file not found: {image_path}")
        return []
    except pytesseract.TesseractNotFoundError:
        logger.warning("Tesseract OCR is not installed or not found in PATH")
        return []
    except Exception as e:
        logger.warning(f"Tesseract extraction failed for {image_path}: {e}")
        return []
