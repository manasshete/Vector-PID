"""Unit test for end-to-end drawing analysis pipeline using synthetic data and mocks."""
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from src.models.schemas import BoundingBox, ImageMetadata
from src.pipeline.drawing_pipeline import analyze_drawing


@patch("src.pipeline.drawing_pipeline.load_engineering_drawing")
@patch("src.pipeline.drawing_pipeline.preprocess_drawing")
@patch("src.pipeline.drawing_pipeline.TileManager")
@patch("src.pipeline.drawing_pipeline.OCREngine")
@patch("src.pipeline.drawing_pipeline.TextClassifier")
@patch("src.pipeline.drawing_pipeline.LineDetector")
@patch("src.pipeline.drawing_pipeline.OpenCVSymbolDetector")
@patch("src.pipeline.drawing_pipeline.RelationshipEngine")
def test_end_to_end_pipeline_orchestration(
    mock_rel_engine,
    mock_symbol_detector,
    mock_line_detector,
    mock_classifier,
    mock_ocr_engine,
    mock_tile_manager,
    mock_preprocess,
    mock_load,
    tmp_path,
):
    # Mock return values
    dummy_img = np.zeros((300, 300, 3), dtype=np.uint8)
    dummy_meta = ImageMetadata(filename="dummy.pdf", width=300, height=300, channels=3, source_format="PDF")
    mock_load.return_value = (dummy_img, dummy_meta)
    mock_preprocess.return_value = {"thresholded": dummy_img}

    mock_tile = MagicMock()
    mock_tile_manager.return_value.generate_tiles.return_value = [mock_tile]

    mock_ocr_result = MagicMock()
    mock_ocr_result.model_dump.return_value = {
        "id": "TXT-001",
        "text": "P-100",
        "confidence": 0.9,
        "bbox": {"x": 10, "y": 10, "width": 20, "height": 10},
        "tile_id": 0,
    }
    mock_ocr_engine.return_value.process_tiles.return_value = [mock_ocr_result]

    mock_classified_text = MagicMock()
    mock_classified_text.classification.value = "PIPE_TAG"
    mock_classified_text.model_dump.return_value = {
        "id": "TXT-001",
        "text": "P-100",
        "classification": "PIPE_TAG",
        "confidence": 0.9,
        "method": "rule",
        "bbox": {"x": 10, "y": 10, "width": 20, "height": 10},
        "tile_id": 0,
    }
    mock_classifier.return_value.classify_batch.return_value = [mock_classified_text]

    mock_line = MagicMock()
    mock_line.line_type = "LIKELY_PIPE"
    mock_line.model_dump.return_value = {
        "id": "LINE-001",
        "start": [0, 0],
        "end": [100, 0],
        "length": 100,
        "orientation": "horizontal",
        "line_type": "LIKELY_PIPE",
        "confidence": 0.8,
    }
    mock_line_detector.return_value.detect.return_value = [mock_line]

    mock_obj = MagicMock()
    mock_obj.type = "VALVE"
    mock_obj.model_dump.return_value = {
        "id": "OBJ-001",
        "type": "VALVE",
        "bbox": {"x": 10, "y": 10, "width": 20, "height": 20},
        "confidence": 0.8,
    }
    mock_symbol_detector.return_value.detect.return_value = [mock_obj]

    mock_rel = MagicMock()
    mock_rel.model_dump.return_value = {
        "from_id": "LINE-001",
        "to_id": "OBJ-001",
        "relationship": "connected_to",
        "distance": 5.0,
        "confidence": 0.85,
    }
    mock_rel_engine.return_value.build_relationships.return_value = (
        [mock_rel],
        [mock_obj.model_dump.return_value],
    )

    # Run analyze_drawing
    result = analyze_drawing("dummy.pdf", output_dir=tmp_path)

    # Assertions
    assert result["drawing"]["filename"] == "dummy.pdf"
    assert "statistics" in result
    assert result["statistics"]["total_texts"] == 1
    assert result["statistics"]["total_symbols"] == 1

    # Verify intermediate files created
    assert (tmp_path / "ocr_results.json").exists()
    assert (tmp_path / "classified_text.json").exists()
    assert (tmp_path / "lines.json").exists()
    assert (tmp_path / "objects.json").exists()
    assert (tmp_path / "relationships.json").exists()
    assert (tmp_path / "graph.json").exists()
    assert (tmp_path / "final_analysis.json").exists()
