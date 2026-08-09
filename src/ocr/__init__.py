"""OCR module package initialization."""
from .ocr_engine import OCREngine, OCRResult
from .text_classifier import TextClassifier, TextClass, ClassifiedText

__all__ = ["OCREngine", "OCRResult", "TextClassifier", "TextClass", "ClassifiedText"]