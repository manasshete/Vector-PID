"""End-to-end P&ID drawing intelligence pipeline."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.detection.symbol_detector import OpenCVSymbolDetector
from src.geometry.line_detector import LineDetector
from src.graph.drawing_graph import DrawingGraph
from src.models.schemas import ImageMetadata
from src.ocr.ocr_engine import OCREngine
from src.ocr.text_classifier import TextClassifier
from src.preprocessing.image_processor import load_engineering_drawing, preprocess_drawing
from src.preprocessing.tiling import TileManager
from src.spatial.relationship_engine import RelationshipEngine


def analyze_drawing(image_path: str | Path, output_dir: str | Path = "data/outputs") -> dict[str, Any]:
    """Execute complete drawing analysis pipeline on input PDF or raster drawing.

    Parameters
    ----------
    image_path : str | Path
        Path to input PDF or image drawing.
    output_dir : str | Path
        Directory to save intermediate and final JSON artifacts.

    Returns
    -------
    dict
        Structured analysis output containing metadata, texts, objects, lines, connections,
        graph, ai_reasoning, and statistics.
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load drawing
    img, metadata = load_engineering_drawing(image_path, pdf_dpi=300)

    # 2. Preprocess drawing
    preprocessed_stages = preprocess_drawing(img)
    clean_img = preprocessed_stages.get("thresholded", img)

    # 3. Tile drawing
    tile_manager = TileManager(clean_img, tile_width=1024, tile_height=1024, overlap=100)
    tiles = tile_manager.generate_tiles()

    # 4. OCR
    ocr_engine = OCREngine(lang="en", use_gpu=False)
    ocr_results = ocr_engine.process_tiles(tiles, min_confidence=0.5)

    ocr_data = [r.model_dump(mode="json") for r in ocr_results]
    (output_dir / "ocr_results.json").write_text(json.dumps(ocr_data, indent=2))

    # 5. Classify text
    classifier = TextClassifier(grok_service=None)
    classified_texts = classifier.classify_batch(ocr_data)

    classified_data = [t.model_dump(mode="json") for t in classified_texts]
    (output_dir / "classified_text.json").write_text(json.dumps(classified_data, indent=2))

    # 6. Line detection
    line_detector = LineDetector(min_length=30.0, max_line_gap=15.0)
    lines = line_detector.detect(clean_img, annotations=classified_data)

    lines_data = [l.model_dump(mode="json") for l in lines]
    (output_dir / "lines.json").write_text(json.dumps(lines_data, indent=2))

    # 7. Symbol detection
    symbol_detector = OpenCVSymbolDetector(min_confidence=0.4)
    objects = symbol_detector.detect(clean_img)

    objects_data = [o.model_dump(mode="json") for o in objects]

    # 8. Spatial reasoning
    rel_engine = RelationshipEngine(max_connection_distance=50.0, max_annotation_distance=150.0)
    relationships, enriched_objects = rel_engine.build_relationships(objects, classified_texts, lines)

    (output_dir / "objects.json").write_text(json.dumps(enriched_objects, indent=2))

    rels_data = [r.model_dump(mode="json") for r in relationships]
    (output_dir / "relationships.json").write_text(json.dumps(rels_data, indent=2))

    # 9. Graph construction
    drawing_graph = DrawingGraph()
    drawing_graph.build(enriched_objects, classified_data, lines_data, rels_data)
    graph_dict = drawing_graph.to_dict()
    (output_dir / "graph.json").write_text(json.dumps(graph_dict, indent=2))

    # 10. AI Reasoning Layer (Groq LLM)
    ai_reasoning_data = _run_ai_reasoning(
        img, classified_data, enriched_objects, lines_data, rels_data, output_dir
    )

    # 11. Merge AI reasoning into every entity (per-item reasoning)
    enriched_objects = _merge_reasoning_into_objects(enriched_objects, ai_reasoning_data)
    rels_data = _merge_reasoning_into_connections(rels_data, ai_reasoning_data)
    lines_data = _merge_reasoning_into_lines(lines_data, ai_reasoning_data)
    classified_data = _merge_reasoning_into_texts(classified_data, ai_reasoning_data)

    print(f"[Pipeline] Merged AI reasoning into {len(enriched_objects)} objects, "
          f"{len(rels_data)} connections, {len(lines_data)} lines, {len(classified_data)} texts")

    # 12. Assemble statistics & final JSON
    text_class_counts = dict(Counter(t.classification.value for t in classified_texts))
    symbol_counts = dict(Counter(o.type for o in objects))
    line_counts = dict(Counter(l.line_type for l in lines))

    statistics = {
        "total_texts": len(classified_texts),
        "text_categories": text_class_counts,
        "total_symbols": len(objects),
        "symbol_types": symbol_counts,
        "total_lines": len(lines),
        "line_types": line_counts,
        "total_relationships": len(relationships),
        "ai_reasoning_connections": len(ai_reasoning_data.get("connections", [])),
        "ai_reasoning_flows": len(ai_reasoning_data.get("process_flows", [])),
    }

    final_result = {
        "drawing": {
            "type": "process_engineering",
            "filename": metadata.filename,
            "width": metadata.width,
            "height": metadata.height,
        },
        "texts": classified_data,
        "objects": enriched_objects,
        "lines": lines_data,
        "connections": rels_data,
        "graph": graph_dict,
        "ai_reasoning": ai_reasoning_data,
        "statistics": statistics,
    }

    (output_dir / "final_analysis.json").write_text(json.dumps(final_result, indent=2))

    return final_result


def _run_ai_reasoning(
    image,
    texts: list[dict],
    objects: list[dict],
    lines: list[dict],
    relationships: list[dict],
    output_dir: Path,
) -> dict:
    """Run AI reasoning via Groq LLM. Returns empty structure on failure or missing key."""
    try:
        from src.services.gemini_service import GeminiReasoningService

        print("[Pipeline] Starting AI connection reasoning (Groq LLM)...")
        reasoner = GeminiReasoningService()
        result = reasoner.reason_about_connections(
            image=image,
            texts=texts,
            objects=objects,
            lines=lines,
            relationships=relationships,
        )
        (output_dir / "ai_reasoning.json").write_text(json.dumps(result, indent=2))
        num_conns = len(result.get("connections", []))
        num_flows = len(result.get("process_flows", []))
        print(f"[Pipeline] AI reasoning complete: {num_conns} connections, {num_flows} process flows")
        return result
    except EnvironmentError as exc:
        print(f"[Pipeline] GROK_API_KEY not configured, skipping AI reasoning: {exc}")
        return {"drawing_summary": "AI reasoning skipped — GROK_API_KEY not set", "connections": [], "process_flows": []}
    except Exception as exc:
        print(f"[Pipeline] AI reasoning failed: {exc}")
        return {"drawing_summary": f"AI reasoning error: {exc}", "connections": [], "process_flows": []}


def _merge_reasoning_into_objects(objects: list[dict], ai_data: dict) -> list[dict]:
    """Add per-object AI reasoning — which components it connects to and why."""
    ai_connections = ai_data.get("connections", [])
    ai_flows = ai_data.get("process_flows", [])

    # Build lookup: object_id → list of AI connections involving it
    obj_reasons: dict[str, list[dict]] = {}
    for conn in ai_connections:
        from_id = conn.get("from_component", {}).get("id", "")
        to_id = conn.get("to_component", {}).get("id", "")
        entry = {
            "connects_to": conn.get("to_component", {}),
            "connection_type": conn.get("connection_type", ""),
            "flow_direction": conn.get("flow_direction", ""),
            "reason": conn.get("reason", ""),
            "confidence": conn.get("confidence", 0.5),
            "line_ids": conn.get("line_ids", []),
        }
        if from_id:
            obj_reasons.setdefault(from_id, []).append(entry)
        if to_id:
            reverse_entry = {
                "connects_to": conn.get("from_component", {}),
                "connection_type": conn.get("connection_type", ""),
                "flow_direction": conn.get("flow_direction", ""),
                "reason": conn.get("reason", ""),
                "confidence": conn.get("confidence", 0.5),
                "line_ids": conn.get("line_ids", []),
            }
            obj_reasons.setdefault(to_id, []).append(reverse_entry)

    # Find which process flows each object belongs to
    obj_flows: dict[str, list[str]] = {}
    for flow in ai_flows:
        for path_item in flow.get("path", []):
            for obj in objects:
                obj_id = obj.get("id", "")
                assoc_tag = (obj.get("associated_text") or {}).get("text", "")
                if obj_id in path_item or assoc_tag in path_item:
                    obj_flows.setdefault(obj_id, []).append(flow.get("flow_name", ""))

    # Merge into each object
    for obj in objects:
        obj_id = obj.get("id", "")
        obj["ai_reasoning"] = {
            "connections": obj_reasons.get(obj_id, []),
            "part_of_flows": list(set(obj_flows.get(obj_id, []))),
        }

    return objects


def _merge_reasoning_into_connections(connections: list[dict], ai_data: dict) -> list[dict]:
    """Add AI reasoning to each spatial relationship — why this connection exists."""
    ai_connections = ai_data.get("connections", [])

    # Build lookup from (from_id, to_id) pairs in AI reasoning
    ai_lookup: dict[tuple[str, str], dict] = {}
    for conn in ai_connections:
        from_id = conn.get("from_component", {}).get("id", "")
        to_id = conn.get("to_component", {}).get("id", "")
        if from_id and to_id:
            ai_lookup[(from_id, to_id)] = conn
            ai_lookup[(to_id, from_id)] = conn

    for rel in connections:
        from_id = rel.get("from_id", "")
        to_id = rel.get("to_id", "")
        ai_match = ai_lookup.get((from_id, to_id))
        if ai_match:
            rel["ai_reasoning"] = {
                "reason": ai_match.get("reason", ""),
                "connection_type": ai_match.get("connection_type", ""),
                "flow_direction": ai_match.get("flow_direction", ""),
                "confidence": ai_match.get("confidence", 0.5),
            }
        else:
            rel["ai_reasoning"] = None

    return connections


def _merge_reasoning_into_lines(lines: list[dict], ai_data: dict) -> list[dict]:
    """Add AI reasoning to each line — which components it connects."""
    ai_connections = ai_data.get("connections", [])

    # Build lookup: line_id → list of AI connections referencing it
    line_reasons: dict[str, list[dict]] = {}
    for conn in ai_connections:
        for line_id in conn.get("line_ids", []):
            entry = {
                "from": conn.get("from_component", {}),
                "to": conn.get("to_component", {}),
                "reason": conn.get("reason", ""),
                "connection_type": conn.get("connection_type", ""),
            }
            line_reasons.setdefault(line_id, []).append(entry)

    for line in lines:
        line_id = line.get("id", "")
        reasons = line_reasons.get(line_id, [])
        line["ai_reasoning"] = reasons if reasons else None

    return lines


def _merge_reasoning_into_texts(texts: list[dict], ai_data: dict) -> list[dict]:
    """Add AI reasoning to each text — which components reference this tag."""
    ai_connections = ai_data.get("connections", [])

    # Build lookup: tag text → list of AI connections using that tag
    tag_reasons: dict[str, list[dict]] = {}
    for conn in ai_connections:
        for side in ("from_component", "to_component"):
            tag = conn.get(side, {}).get("tag", "")
            if tag:
                entry = {
                    "component_id": conn.get(side, {}).get("id", ""),
                    "component_type": conn.get(side, {}).get("type", ""),
                    "reason": conn.get("reason", ""),
                }
                tag_reasons.setdefault(tag.upper(), []).append(entry)

    for txt in texts:
        text_val = txt.get("text", "").upper()
        reasons = tag_reasons.get(text_val, [])
        txt["ai_reasoning"] = reasons if reasons else None

    return texts
