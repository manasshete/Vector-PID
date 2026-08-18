"""Unit tests for DrawingGraph NetworkX wrapper."""
import pytest
from src.graph.drawing_graph import DrawingGraph


def test_graph_construction_and_tracing():
    objs = [{"id": "OBJ-001", "type": "VALVE", "bbox": {"x": 0, "y": 0, "width": 10, "height": 10}, "confidence": 0.9}]
    texts = [{"id": "TXT-001", "text": "V-100", "classification": "EQUIPMENT_TAG", "bbox": {"x": 10, "y": 10, "width": 20, "height": 10}, "confidence": 0.9}]
    lines = [{"id": "LINE-001", "start": (0, 0), "end": (100, 0), "line_type": "LIKELY_PIPE", "orientation": "horizontal", "length": 100, "confidence": 0.8}]
    rels = [
        {"from_id": "OBJ-001", "to_id": "TXT-001", "relationship": "annotated_by", "distance": 14.14, "confidence": 0.9},
        {"from_id": "LINE-001", "to_id": "OBJ-001", "relationship": "connected_to", "distance": 5.0, "confidence": 0.85},
    ]

    dgraph = DrawingGraph()
    nx_g = dgraph.build(objs, texts, lines, rels)

    assert nx_g.number_of_nodes() == 3
    assert nx_g.number_of_edges() == 2

    neighbors = dgraph.get_neighbors("OBJ-001")
    assert "TXT-001" in neighbors
    assert "LINE-001" in neighbors

    trace = dgraph.trace_from_object("LINE-001", max_depth=2)
    assert "LINE-001" in trace
    assert "OBJ-001" in trace
    assert "TXT-001" in trace

    gdict = dgraph.to_dict()
    assert gdict["num_nodes"] == 3
    assert gdict["num_edges"] == 2

    # Path finding
    path = dgraph.find_path("LINE-001", "TXT-001")
    assert path == ["LINE-001", "OBJ-001", "TXT-001"]

    no_path = dgraph.find_path("LINE-001", "NON-EXISTENT")
    assert no_path == []

    # Subgraph extraction
    sub = dgraph.get_subgraph(["OBJ-001", "TXT-001"])
    assert sub["num_nodes"] == 2
    assert sub["num_edges"] == 1

    # Connected components
    components = dgraph.get_connected_components()
    assert len(components) == 1
    assert len(components[0]) == 3

