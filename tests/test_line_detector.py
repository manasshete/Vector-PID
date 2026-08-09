"""Unit tests for LineDetector on synthetic images."""
import numpy as np
import pytest

from src.geometry.line_detector import LineDetector


def test_synthetic_line_detection():
    # Create black image with a thick white horizontal line
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    img[150, 50:250] = 255
    img[151, 50:250] = 255  # 2px thick line

    detector = LineDetector(min_length=30.0, max_line_gap=15.0)
    lines = detector.detect(img)

    assert len(lines) >= 1
    l = lines[0]
    assert l.orientation == "horizontal"
    assert l.length >= 30.0
    assert l.source_method == "opencv_hough"


def test_empty_image_line_detection():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    detector = LineDetector()
    lines = detector.detect(img)
    assert lines == []
