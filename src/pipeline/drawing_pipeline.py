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

    # 10. AI Reasoning Layer (Gemini Vision)
    ai_reasoning_data = _run_ai_reasoning(
        img, classified_data, enriched_objects, lines_data, rels_data, output_dir
    )

    # 11. Assemble statistics & final JSON
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

