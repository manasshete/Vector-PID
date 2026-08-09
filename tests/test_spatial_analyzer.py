"""Unit tests for spatial analyzer functions and relationship engine."""
import pytest

from src.models.schemas import BoundingBox, DetectedObject
from src.spatial.relationship_engine import RelationshipEngine
from src.spatial.spatial_analyzer import (
    associate_text_with_object,
    distance_between_objects,
    find_connected_line,
    nearest_object,
    resolve_tile_overlap_duplicates,
)


def test_distance_between_objects():
    o1 = {"bbox": {"x": 0, "y": 0, "width": 10, "height": 10}}  # center (5, 5)
    o2 = {"bbox": {"x": 30, "y": 40, "width": 10, "height": 10}}  # center (35, 45)
    d = distance_between_objects(o1, o2)
    assert abs(d - 50.0) < 1e-6


def test_nearest_object():
    target = {"bbox": {"x": 0, "y": 0, "width": 10, "height": 10}}  # center (5,5)
    c1 = {"id": "c1", "bbox": {"x": 100, "y": 100, "width": 10, "height": 10}}
    c2 = {"id": "c2", "bbox": {"x": 10, "y": 10, "width": 10, "height": 10}}

    best, dist = nearest_object(target, [c1, c2])
    assert best["id"] == "c2"


def test_resolve_tile_overlap_duplicates():
    items = [
        {"id": "t1", "text": "P-1234", "confidence": 0.8, "bbox": {"x": 100, "y": 100, "width": 50, "height": 20}},
        {"id": "t2", "text": "P-1234", "confidence": 0.95, "bbox": {"x": 102, "y": 101, "width": 50, "height": 20}},
        {"id": "t3", "text": "V-100", "confidence": 0.9, "bbox": {"x": 500, "y": 500, "width": 50, "height": 20}},
    ]
    deduped = resolve_tile_overlap_duplicates(items, max_dist=20.0)
    assert len(deduped) == 2
    ids = [it["id"] for it in deduped]
    assert "t2" in ids  # higher confidence item retained
    assert "t3" in ids


def test_relationship_engine():
    objs = [
        DetectedObject(
            id="OBJ-0001", type="VALVE",
            bbox=BoundingBox(x=100, y=100, width=20, height=20),
            confidence=0.8, source_method="opencv"
        )
    ]
    texts = [
        {"id": "TXT-0001", "text": "V-100", "confidence": 0.9, "bbox": {"x": 110, "y": 110, "width": 30, "height": 15}}
    ]
    lines = [
        {"id": "LINE-0001", "start": (100, 100), "end": (200, 100), "length": 100, "orientation": "horizontal", "line_type": "LIKELY_PIPE", "confidence": 0.8}
    ]

    engine = RelationshipEngine()
    rels, enriched = engine.build_relationships(objs, texts, lines)

    assert len(rels) >= 1
    rel_types = [r.relationship for r in rels]
    assert "annotated_by" in rel_types or "connected_to" in rel_types
