"""Spatial helper functions for geometric proximity and entity association."""
from __future__ import annotations

import math
from typing import Any, Optional

from src.models.schemas import BoundingBox


def _get_center(item: Any) -> tuple[float, float]:
    """Extract center (x, y) coordinates from a dict or Pydantic object."""
    if hasattr(item, "bbox"):
        bbox = item.bbox
        if hasattr(bbox, "center"):
            return bbox.center
        elif isinstance(bbox, dict):
            return (bbox.get("x", 0) + bbox.get("width", 0) / 2, bbox.get("y", 0) + bbox.get("height", 0) / 2)
    elif isinstance(item, dict) and "bbox" in item:
        bbox = item["bbox"]
        return (bbox.get("x", 0) + bbox.get("width", 0) / 2, bbox.get("y", 0) + bbox.get("height", 0) / 2)
    elif hasattr(item, "start") and hasattr(item, "end"):
        # DetectedLine
        return ((item.start[0] + item.end[0]) / 2, (item.start[1] + item.end[1]) / 2)
    return (0.0, 0.0)


def distance_between_objects(obj1: Any, obj2: Any) -> float:
    """Calculate Euclidean distance between bounding box centers of two objects."""
    c1 = _get_center(obj1)
    c2 = _get_center(obj2)
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])


def nearest_object(target_obj: Any, candidates: list[Any]) -> tuple[Optional[Any], float]:
    """Find nearest candidate object to target_obj.

    Returns (nearest_candidate, distance).
    """
    if not candidates:
        return None, float("inf")

    best_candidate = None
    min_dist = float("inf")

    for cand in candidates:
        d = distance_between_objects(target_obj, cand)
        if d < min_dist:
            min_dist = d
            best_candidate = cand

    return best_candidate, min_dist


def find_connected_line(obj: Any, lines: list[Any], max_distance: float = 50.0) -> list[Any]:
    """Find all line segments whose start or end endpoint is within max_distance of obj center/bbox."""
    connected = []
    c = _get_center(obj)

    for line in lines:
        if hasattr(line, "start") and hasattr(line, "end"):
            s, e = line.start, line.end
        elif isinstance(line, dict):
            s, e = line.get("start", (0, 0)), line.get("end", (0, 0))
        else:
            continue

        d_start = math.hypot(c[0] - s[0], c[1] - s[1])
        d_end = math.hypot(c[0] - e[0], c[1] - e[1])

        if d_start <= max_distance or d_end <= max_distance:
            connected.append(line)

    return connected


def associate_text_with_object(objects: list[Any], texts: list[Any], max_distance: float = 150.0) -> list[dict]:
    """Enrich object records with nearest associated text within max_distance."""
    enriched = []

    for obj in objects:
        nearest_txt, dist = nearest_object(obj, texts)
        obj_dict = obj.model_dump(mode="json") if hasattr(obj, "model_dump") else dict(obj)

        if nearest_txt and dist <= max_distance:
            txt_val = nearest_txt.text if hasattr(nearest_txt, "text") else nearest_txt.get("text", "")
            txt_id = nearest_txt.id if hasattr(nearest_txt, "id") else nearest_txt.get("id", "")
            obj_dict["associated_text"] = {"id": txt_id, "text": txt_val, "distance": round(dist, 2)}
        else:
            obj_dict["associated_text"] = None

        enriched.append(obj_dict)

    return enriched


def resolve_tile_overlap_duplicates(items: list[Any], max_dist: float = 20.0) -> list[Any]:
    """Deduplicate tile overlap texts/objects with identical content and bbox within max_dist.

    Keeps the item with higher confidence.
    """
    if not items:
        return []

    deduped = []
    used = [False] * len(items)

    for i in range(len(items)):
        if used[i]:
            continue

        item_i = items[i]
        text_i = getattr(item_i, "text", None) or (item_i.get("text") if isinstance(item_i, dict) else None)
        c_i = _get_center(item_i)
        conf_i = getattr(item_i, "confidence", 0.0) or (item_i.get("confidence", 0.0) if isinstance(item_i, dict) else 0.0)

        best_item = item_i
        best_conf = conf_i
        used[i] = True

        for j in range(i + 1, len(items)):
            if used[j]:
                continue

            item_j = items[j]
            text_j = getattr(item_j, "text", None) or (item_j.get("text") if isinstance(item_j, dict) else None)
            c_j = _get_center(item_j)
            conf_j = getattr(item_j, "confidence", 0.0) or (item_j.get("confidence", 0.0) if isinstance(item_j, dict) else 0.0)

            # Match text content (if text exists) or center proximity
            same_text = (text_i is not None and text_j is not None and text_i.strip().upper() == text_j.strip().upper())
            close_dist = math.hypot(c_i[0] - c_j[0], c_i[1] - c_j[1]) <= max_dist

            if same_text and close_dist:
                used[j] = True
                if conf_j > best_conf:
                    best_item = item_j
                    best_conf = conf_j

        deduped.append(best_item)

    return deduped
