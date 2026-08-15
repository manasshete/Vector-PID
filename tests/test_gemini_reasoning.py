"""Unit tests for the AI reasoning layer."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.models.schemas import (
    AIConnection,
    AIConnectionComponent,
    AIReasoning,
    ProcessFlow,
)


# --- Pydantic Model Tests ---


class TestAIReasoningModels:
    """Validate the Pydantic models for AI reasoning output."""

    def test_ai_connection_component_defaults(self):
        comp = AIConnectionComponent()
        assert comp.id == ""
        assert comp.tag == ""
        assert comp.type == ""

    def test_ai_connection_component_with_values(self):
        comp = AIConnectionComponent(id="OBJ-001", tag="V-100", type="VALVE")
        assert comp.id == "OBJ-001"
        assert comp.tag == "V-100"
        assert comp.type == "VALVE"

    def test_ai_connection_full(self):
        conn = AIConnection(
            from_component=AIConnectionComponent(id="OBJ-001", tag="V-100", type="VALVE"),
            to_component=AIConnectionComponent(id="OBJ-002", tag="P-200", type="PUMP"),
            connection_type="pipe",
            flow_direction="P-200 → V-100",
            reason="Valve V-100 is on the discharge line of Pump P-200",
            confidence=0.92,
            line_ids=["LINE-042"],
        )
        assert conn.from_component.tag == "V-100"
        assert conn.to_component.type == "PUMP"
        assert conn.confidence == 0.92
        assert "LINE-042" in conn.line_ids

    def test_ai_connection_confidence_clamped(self):
        """Confidence must be between 0 and 1."""
        with pytest.raises(Exception):
            AIConnection(
                from_component=AIConnectionComponent(),
                to_component=AIConnectionComponent(),
                confidence=1.5,
            )

    def test_process_flow(self):
        flow = ProcessFlow(
            flow_name="Gas Compression",
            path=["Inlet Separator", "Compressor", "Cooler"],
            description="Main gas compression loop",
        )
        assert flow.flow_name == "Gas Compression"
        assert len(flow.path) == 3

    def test_ai_reasoning_full(self):
        reasoning = AIReasoning(
            drawing_summary="Test P&ID",
            connections=[
                AIConnection(
                    from_component=AIConnectionComponent(id="OBJ-001", tag="V-100", type="VALVE"),
                    to_component=AIConnectionComponent(id="OBJ-002", tag="P-200", type="PUMP"),
                    reason="Connected via discharge pipe",
                )
            ],
            process_flows=[
                ProcessFlow(flow_name="Main Flow", path=["A", "B", "C"], description="Test flow")
            ],
            ai_model="llama-3.3-70b-versatile",
            timestamp="2026-08-14T00:00:00Z",
        )
        assert len(reasoning.connections) == 1
        assert len(reasoning.process_flows) == 1
        assert reasoning.ai_model == "llama-3.3-70b-versatile"

    def test_ai_reasoning_serialization(self):
        """Test JSON round-trip serialization."""
        reasoning = AIReasoning(
            drawing_summary="Serialization test",
            connections=[
                AIConnection(
                    from_component=AIConnectionComponent(id="OBJ-001", tag="V-100", type="VALVE"),
                    to_component=AIConnectionComponent(id="OBJ-002", tag="P-200", type="PUMP"),
                    connection_type="pipe",
                    reason="Test connection",
                    confidence=0.85,
                )
            ],
        )
        dumped = reasoning.model_dump(mode="json")
        assert isinstance(dumped, dict)
        assert dumped["connections"][0]["from_component"]["tag"] == "V-100"
        assert dumped["connections"][0]["confidence"] == 0.85

        # Round-trip
        restored = AIReasoning(**dumped)
        assert restored.connections[0].reason == "Test connection"

    def test_ai_reasoning_empty_defaults(self):
        reasoning = AIReasoning()
        assert reasoning.drawing_summary == ""
        assert reasoning.connections == []
        assert reasoning.process_flows == []


# --- AI Reasoning Service Tests ---


class TestAIReasoningServiceHelpers:
    """Test helper functions from the reasoning service without API calls."""

    def test_build_context_text_with_data(self):
        from src.services.gemini_service import _build_context_text

        texts = [{"id": "TXT-001", "text": "V-100", "classification": "EQUIPMENT_TAG"}]
        objects = [
            {"id": "OBJ-001", "type": "VALVE", "bbox": {"x": 100, "y": 200, "width": 50, "height": 50},
             "associated_text": {"text": "V-100"}}
        ]
        lines = [{"id": "LINE-001", "line_type": "LIKELY_PIPE", "orientation": "horizontal",
                  "start": [100, 200], "end": [300, 200], "length": 200}]
        relationships = [{"from_id": "LINE-001", "to_id": "OBJ-001", "relationship": "connected_to", "distance": 10.0}]

        context = _build_context_text(texts, objects, lines, relationships)
        assert "V-100" in context
        assert "OBJ-001" in context
        assert "likely pipes" in context

    def test_build_context_text_empty(self):
        from src.services.gemini_service import _build_context_text

        context = _build_context_text([], [], [], [])
        assert context == ""


class TestAIReasoningServiceInit:
    """Test GeminiReasoningService initialization."""

    def test_missing_api_key_raises(self):
        from src.services.gemini_service import GeminiReasoningService

        with patch.dict("os.environ", {"GROK_API_KEY": ""}, clear=False):
            with pytest.raises(EnvironmentError, match="GROK_API_KEY"):
                GeminiReasoningService()


class TestPipelineIntegration:
    """Test that _run_ai_reasoning gracefully handles missing key."""

    def test_run_ai_reasoning_skips_without_key(self):
        from src.pipeline.drawing_pipeline import _run_ai_reasoning
        from pathlib import Path
        import tempfile

        with patch.dict("os.environ", {"GROK_API_KEY": ""}, clear=False):
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            result = _run_ai_reasoning(img, [], [], [], [], Path(tempfile.mkdtemp()))

        assert "connections" in result
        assert result["connections"] == []
        assert "skipped" in result.get("drawing_summary", "").lower() or "error" in result.get("drawing_summary", "").lower()
