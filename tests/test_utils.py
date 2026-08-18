"""Unit tests for utility modules: config, exceptions, and logger."""
import logging
import pytest

from src.utils.config import PipelineConfig, load_config
from src.utils.exceptions import (
    AIRuntimeError,
    OCRExtractionError,
    PipelineError,
    SymbolDetectionError,
    TilingError,
    TopologyError,
    VectorPIDError,
)
from src.utils.logger import get_logger


def test_custom_exceptions():
    err = VectorPIDError("Test error", stage="unit_test", details={"code": 404})
    assert err.message == "Test error"
    assert err.stage == "unit_test"
    d = err.to_dict()
    assert d["error_type"] == "VectorPIDError"
    assert d["details"]["code"] == 404

    pipe_err = PipelineError("Pipeline failed")
    assert pipe_err.stage == "pipeline"

    tile_err = TilingError("Grid error")
    assert tile_err.stage == "tiling"

    ocr_err = OCRExtractionError("OCR failure")
    assert ocr_err.stage == "ocr"

    sym_err = SymbolDetectionError("Symbol missing")
    assert sym_err.stage == "symbol_detection"

    topo_err = TopologyError("Graph disconnected")
    assert topo_err.stage == "topology"

    ai_err = AIRuntimeError("LLM timed out")
    assert ai_err.stage == "ai_reasoning"


def test_pipeline_config_defaults():
    cfg = load_config()
    assert isinstance(cfg, PipelineConfig)
    assert cfg.tiling.tile_size == 1024
    assert cfg.tiling.overlap == 100
    assert cfg.lines.threshold == 50
    assert cfg.symbols.min_area == 100.0
    assert cfg.spatial.proximity_threshold == 80.0
    assert cfg.output_dir == "data/outputs"


def test_logger_creation():
    logger = get_logger("test_channel", level=logging.DEBUG)
    assert logger.name == "test_channel"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
