"""Unit tests for SymbolDetector implementation."""
import numpy as np
import pytest
import cv2

from src.detection.symbol_detector import OpenCVSymbolDetector


def test_symbol_detector_interface():
    detector = OpenCVSymbolDetector()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    res = detector.detect(img)
    assert isinstance(res, list)
    assert res == []


def test_synthetic_instrument_circle_detection():
    # Create black image with a white circle (instrument bubble)
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 30, (255, 255, 255), 2)

    detector = OpenCVSymbolDetector(min_confidence=0.4)
    objects = detector.detect(img)

    assert len(objects) >= 1
    obj = objects[0]
    assert obj.confidence >= 0.4
    assert obj.source_method == "opencv_contour"
