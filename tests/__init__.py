"""Test suite for engineering drawing intelligence package."""
import pytest
from src.models.schemas import BoundingBox, ImageMetadata


def test_bounding_box_xyxy():
    bbox = BoundingBox(x=10, y=20, width=100, height=50)
    assert bbox.xyxy == [10, 20, 110, 70]
    assert bbox.center == (60, 45)


def test_bounding_box_validation():
    with pytest.raises(ValueError):
        BoundingBox(x=-1, y=0, width=10, height=10)
    with pytest.raises(ValueError):
        BoundingBox(x=0, y=0, width=0, height=10)


def test_image_metadata_creation():
    meta = ImageMetadata(
        filename="test.png", width=1920, height=1080,
        channels=3, source_format="png"
    )
    assert meta.dpi is None