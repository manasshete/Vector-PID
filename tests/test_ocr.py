"""Unit tests for OCR engine structure and coordinate mapping using EasyOCR."""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.models.schemas import BoundingBox
from src.ocr.ocr_engine import OCREngine, OCRResult
from src.preprocessing.tiling import TileMetadata


@pytest.fixture
def mock_tile_metadata():
    return TileMetadata(
        tile_id=5, x_offset=1024, y_offset=512,
        width=1024, height=1024, row=0, col=1
    )


@pytest.fixture
def sample_tile_image():
    return np.zeros((1024, 1024, 3), dtype=np.uint8)


# --- Structure Tests ---

def test_ocr_result_model_creation():
    result = OCRResult(
        id="TXT-000-0001",
        text="INSTR. AIR",
        confidence=0.96,
        bbox=BoundingBox(x=100, y=200, width=150, height=30),
        tile_id=0,
    )
    assert result.text == "INSTR. AIR"
    assert result.confidence == 0.96
    assert result.method == "easyocr"


def test_process_tile_empty_returns_empty():
    """Empty image should return empty list, not raise."""
    engine = OCREngine.__new__(OCREngine)
    engine._reader = MagicMock()
    meta = TileMetadata(tile_id=0, x_offset=0, y_offset=0, width=100, height=100, row=0, col=0)
    result = engine.process_tile(np.array([]), meta)
    assert result == []


def test_ocr_result_confidence_validation():
    with pytest.raises(ValueError):
        OCRResult(
            id="test", text="x", confidence=1.5,
            bbox=BoundingBox(x=0, y=0, width=10, height=10), tile_id=0
        )


# --- Coordinate Mapping Tests (Mocked EasyOCR) ---

@patch("src.ocr.ocr_engine.easyocr.Reader")
def test_process_tile_maps_coordinates_correctly(mock_reader_cls, mock_tile_metadata, sample_tile_image):
    """Verify local->global coordinate conversion in OCR results."""
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = [
        (
            [[100, 200], [250, 200], [250, 230], [100, 230]],
            "PIPE-1234",
            0.95,
        )
    ]

    engine = OCREngine.__new__(OCREngine)
    engine._reader = mock_reader

    results = engine.process_tile(sample_tile_image, mock_tile_metadata)

    assert len(results) == 1
    r = results[0]
    assert r.text == "PIPE-1234"
    assert r.confidence == 0.95
    assert r.tile_id == 5
    # Global coords = local + offset
    assert abs(r.bbox.x - (100 + 1024)) < 1e-9
    assert abs(r.bbox.y - (200 + 512)) < 1e-9
    assert abs(r.bbox.width - 150) < 1e-9
    assert abs(r.bbox.height - 30) < 1e-9


@patch("src.ocr.ocr_engine.easyocr.Reader")
def test_process_tile_filters_low_confidence(mock_reader_cls, mock_tile_metadata, sample_tile_image):
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = [
        ([[0, 0], [10, 0], [10, 10], [0, 10]], "LOW", 0.3),
        ([[20, 20], [30, 20], [30, 30], [20, 30]], "HIGH", 0.92),
    ]

    engine = OCREngine.__new__(OCREngine)
    engine._reader = mock_reader

    results = engine.process_tile(sample_tile_image, mock_tile_metadata, min_confidence=0.5)
    assert len(results) == 1
    assert results[0].text == "HIGH"


@patch("src.ocr.ocr_engine.easyocr.Reader")
def test_process_empty_tile_returns_empty_list(mock_reader_cls, mock_tile_metadata):
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = []

    engine = OCREngine.__new__(OCREngine)
    engine._reader = mock_reader

    empty_img = np.array([])
    results = engine.process_tile(empty_img, mock_tile_metadata)
    assert results == []


@patch("src.ocr.ocr_engine.easyocr.Reader")
def test_process_tiles_aggregates_results(mock_reader_cls, sample_tile_image):
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = [
        ([[0, 0], [10, 0], [10, 10], [0, 10]], "TEXT", 0.9)
    ]

    engine = OCREngine.__new__(OCREngine)
    engine._reader = mock_reader

    # Create 3 mock tiles
    from src.preprocessing.tiling import TileResult
    tiles = []
    for i in range(3):
        meta = TileMetadata(
            tile_id=i, x_offset=i * 100, y_offset=0,
            width=100, height=100, row=0, col=i
        )
        tiles.append(TileResult(metadata=meta, image=sample_tile_image))

    results = engine.process_tiles(tiles)
    assert len(results) == 3
    assert results[0].tile_id == 0
    assert results[1].tile_id == 1
    assert results[2].tile_id == 2