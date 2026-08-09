#!/usr/bin/env python3
"""Step 10: Graph Construction using NetworkX."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph.drawing_graph import DrawingGraph


def main():
    out_dir = Path("data/outputs")
    text_path = out_dir / "classified_text.json"
    obj_path = out_dir / "objects.json"
    line_path = out_dir / "lines.json"
    rel_path = out_dir / "relationships.json"

    if not (text_path.exists() and obj_path.exists() and line_path.exists() and rel_path.exists()):
        print("[*] Missing required input JSON files in data/outputs/. Run previous steps first.")
        sys.exit(1)

    texts = json.loads(text_path.read_text())
    objects = json.loads(obj_path.read_text())
    lines = json.loads(line_path.read_text())
    relationships = json.loads(rel_path.read_text())

    print(f"Loaded {len(objects)} objects, {len(texts)} texts, {len(lines)} lines, {len(relationships)} relationships")

    print("\n[*] Constructing NetworkX drawing graph...")
    dgraph = DrawingGraph()
    nx_graph = dgraph.build(objects, texts, lines, relationships)

    print(f"[+] Graph built: {nx_graph.number_of_nodes()} nodes, {nx_graph.number_of_edges()} edges")

    # Demonstrate tracing
    sample_node = objects[0]["id"] if objects else (texts[0]["id"] if texts else None)
    if sample_node:
        neighbors = dgraph.get_neighbors(sample_node)
        print(f"\n[?] Direct neighbors for {sample_node}: {neighbors}")

        path = dgraph.trace_from_object(sample_node, max_depth=3)
        print(f"[?] Trace path from {sample_node} (max_depth=3): {path}")

    # Export to JSON
    output_path = out_dir / "graph.json"
    graph_dict = dgraph.to_dict()
    output_path.write_text(json.dumps(graph_dict, indent=2))
    print(f"\n[saved] Drawing graph exported: {output_path}")


if __name__ == "__main__":
    main()
