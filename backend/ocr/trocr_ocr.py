import logging
import numpy as np
from PIL import Image
import cv2
import torch

logger = logging.getLogger(__name__)

MODEL_NAME = "microsoft/trocr-base-printed"
MAX_LINES = 30
MIN_CROP_HEIGHT = 10
_processor = None
_model = None


def _load_model():
    global _processor, _model
    if _processor is None:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        logger.info("Loading TrOCR model...")
        _processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        _model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
        _model.eval()
        logger.info("TrOCR model loaded")
    return _processor, _model


def _detect_text_lines(img_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Detect text line bounding boxes using OpenCV morphological operations."""
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    # Otsu binarization — handles both light and dark card backgrounds
    _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Horizontal dilation: connects character blobs into text-line blobs
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 8))
    dilated = cv2.dilate(binarized, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        # Filter: valid text lines are wide, short, non-trivial area
        if bw / max(bh, 1) > 1.5 and bw > 30 and bh < h * 0.3 and bw * bh > 500:
            pad = 8
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(w, x + bw + pad)
            y2 = min(h, y + bh + pad)
            boxes.append((x1, y1, x2, y2))

    # Sort top-to-bottom (reading order)
    boxes.sort(key=lambda b: b[1])

    # Fallback: if too few boxes, use horizontal strip sampling
    if len(boxes) < 3:
        strip_h = h // 8
        boxes = [(0, i * strip_h, w, (i + 1) * strip_h) for i in range(8)]

    return boxes[:MAX_LINES]


def _recognize_line(pil_crop: Image.Image, processor, model) -> str:
    """Run TrOCR inference on a single cropped text-line image."""
    pixel_values = processor(images=pil_crop.convert('RGB'), return_tensors="pt").pixel_values
    with torch.no_grad():
        generated_ids = model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()


def extract(image_path: str) -> list[str]:
    """Extract text lines from a visiting card image using TrOCR."""
    try:
        processor, model = _load_model()
        pil_img = Image.open(image_path).convert('RGB')
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        boxes = _detect_text_lines(img_bgr)
        results = []
        for (x1, y1, x2, y2) in boxes:
            if (y2 - y1) < MIN_CROP_HEIGHT:
                continue
            crop = pil_img.crop((x1, y1, x2, y2))
            text = _recognize_line(crop, processor, model)
            if text:
                results.append(text)
        return results
    except Exception as e:
        logger.warning(f"TrOCR extraction failed for {image_path}: {e}")
        return []
