"""Detection package exports."""
from src.detection.detector import Detector
from src.detection.symbol_detector import OpenCVSymbolDetector

__all__ = ["Detector", "OpenCVSymbolDetector"]
