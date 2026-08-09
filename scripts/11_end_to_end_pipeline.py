#!/usr/bin/env python3
"""Step 12: End-to-End Drawing Intelligence Pipeline Execution."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.drawing_pipeline import analyze_drawing


def main():
    drawing_path = Path("data/raw/Export Gas Compressor-P&ID.pdf")
    if not drawing_path.exists():
        print(f"[*] Drawing not found: {drawing_path}")
        sys.exit(1)

    print("================================================================================")
    print("  ENGINEERING DRAWING INTELLIGENCE PLATFORM — END-TO-END PIPELINE")
    print("================================================================================\n")

    print(f"[*] Analyzing drawing: {drawing_path}")
    result = analyze_drawing(drawing_path, output_dir="data/outputs")

    meta = result["drawing"]
    stats = result["statistics"]

    print("\n[+] PIPELINE EXECUTION SUMMARY")
    print("--------------------------------------------------------------------------------")
    print(f"Drawing Filename    : {meta.get('filename')}")
    print(f"Image Resolution    : {meta.get('width')} x {meta.get('height')}")
    print(f"Total Texts Extracted: {stats.get('total_texts')}")
    print(f"Total Symbols        : {stats.get('total_symbols')}")
    print(f"Total Lines          : {stats.get('total_lines')}")
    print(f"Total Relationships  : {stats.get('total_relationships')}")
    print(f"Graph Nodes / Edges  : {result['graph']['num_nodes']} nodes / {result['graph']['num_edges']} edges")
    print("--------------------------------------------------------------------------------\n")

    print("[saved] Saved all 7 intermediate & final JSON artifacts to data/outputs/:")
    print("   1. ocr_results.json")
    print("   2. classified_text.json")
    print("   3. lines.json")
    print("   4. objects.json")
    print("   5. relationships.json")
    print("   6. graph.json")
    print("   7. final_analysis.json\n")


if __name__ == "__main__":
    main()
