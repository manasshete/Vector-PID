"""Spatial relationship extraction engine."""
from __future__ import annotations

import math
from typing import Any

from src.models.schemas import SpatialRelationship
from src.spatial.spatial_analyzer import (
    associate_text_with_object,
    distance_between_objects,
    nearest_object,
    resolve_tile_overlap_duplicates,
)


class RelationshipEngine:
    """Extracts spatial & logical relationships between detected entities."""

    def __init__(self, max_connection_distance: float = 50.0, max_annotation_distance: float = 150.0):
        self.max_connection_distance = max_connection_distance
        self.max_annotation_distance = max_annotation_distance

    def build_relationships(
        self,
        objects: list[Any],
        texts: list[Any],
        lines: list[Any],
    ) -> tuple[list[SpatialRelationship], list[dict]]:
        """Extract spatial relationships and return (relationships, enriched_objects).

        1. Deduplicate tile overlap texts
        2. Associate nearest text with objects -> "annotated_by"
        3. Connect line endpoints to nearby objects -> "connected_to"
        4. Spatial proximity -> "near"
        """
        # Deduplicate tile overlap texts
        clean_texts = resolve_tile_overlap_duplicates(texts, max_dist=20.0)

        relationships: list[SpatialRelationship] = []
        rel_set = set()

        def add_rel(from_id: str, to_id: str, rel_type: str, dist: float, conf: float):
            key = (from_id, to_id, rel_type)
            if key not in rel_set and from_id != to_id:
                rel_set.add(key)
                relationships.append(
                    SpatialRelationship(
                        from_id=from_id,
                        to_id=to_id,
                        relationship=rel_type,
                        distance=round(dist, 2),
                        confidence=round(conf, 2),
                    )
                )

        # 1. Object <-> Text (Annotation)
        for obj in objects:
            obj_id = getattr(obj, "id", None) or obj.get("id")
            near_txt, dist = nearest_object(obj, clean_texts)

            if near_txt and dist <= self.max_annotation_distance:
                txt_id = getattr(near_txt, "id", None) or near_txt.get("id")
                add_rel(obj_id, txt_id, "annotated_by", dist, 0.90)

        # 2. Line <-> Object (Connectivity)
        for line in lines:
            line_id = getattr(line, "id", None) or line.get("id")
            if hasattr(line, "start") and hasattr(line, "end"):
                s, e = line.start, line.end
            elif isinstance(line, dict):
                s, e = line.get("start", (0, 0)), line.get("end", (0, 0))
            else:
                continue

            for obj in objects:
                obj_id = getattr(obj, "id", None) or obj.get("id")
                c = (
                    obj.bbox.center if hasattr(obj, "bbox") and hasattr(obj.bbox, "center")
                    else (obj["bbox"]["x"] + obj["bbox"]["width"] / 2, obj["bbox"]["y"] + obj["bbox"]["height"] / 2)
                )

                d_start = math.hypot(c[0] - s[0], c[1] - s[1])
                d_end = math.hypot(c[0] - e[0], c[1] - e[1])

                if d_start <= self.max_connection_distance:
                    add_rel(line_id, obj_id, "connected_to", d_start, 0.85)

                if d_end <= self.max_connection_distance:
                    add_rel(line_id, obj_id, "connected_to", d_end, 0.85)

        # 3. Object <-> Object Proximity ("near")
        for i in range(len(objects)):
            obj_i = objects[i]
            id_i = getattr(obj_i, "id", None) or obj_i.get("id")

            for j in range(i + 1, len(objects)):
                obj_j = objects[j]
                id_j = getattr(obj_j, "id", None) or obj_j.get("id")

                d = distance_between_objects(obj_i, obj_j)
                if d <= 150.0:
                    add_rel(id_i, id_j, "near", d, 0.70)

        # Enrich objects with associated text
        enriched_objects = associate_text_with_object(objects, clean_texts, max_distance=self.max_annotation_distance)

        return relationships, enriched_objects
