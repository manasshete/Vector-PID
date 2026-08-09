#!/usr/bin/env python3
"""Step 9: Spatial Reasoning & Relationship Extraction."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.spatial.relationship_engine import RelationshipEngine


def main():
    out_dir = Path("data/outputs")
    text_path = out_dir / "classified_text.json"
    obj_path = out_dir / "objects.json"
    line_path = out_dir / "lines.json"

    if not (text_path.exists() and obj_path.exists() and line_path.exists()):
        print("[*] Missing required input JSON files in data/outputs/. Run previous steps first.")
        sys.exit(1)

    texts = json.loads(text_path.read_text())
    objects = json.loads(obj_path.read_text())
    lines = json.loads(line_path.read_text())

    print(f"Loaded {len(texts)} texts, {len(objects)} objects, {len(lines)} lines")

    print("\n[*] Building spatial relationships...")
    engine = RelationshipEngine(max_connection_distance=50.0, max_annotation_distance=150.0)
    relationships, enriched_objects = engine.build_relationships(objects, texts, lines)

    print(f"[+] Extracted {len(relationships)} spatial relationships")

    rel_counts = Counter(r.relationship for r in relationships)
    print("\n[+] Relationship breakdown:")
    for rtype, count in rel_counts.items():
        pct = 100 * count / len(relationships) if relationships else 0
        print(f"   {rtype:<15} {count:>5} ({pct:.1f}%)")

    # Sample relationships
    print("\n[?] Sample relationships:")
    for r in relationships[:8]:
        print(f"   {r.from_id} --[{r.relationship}]--> {r.to_id} (dist={r.distance:.1f}px, conf={r.confidence:.2f})")

    # Save relationships to JSON
    output_path = out_dir / "relationships.json"
    serialized = [r.model_dump(mode="json") for r in relationships]
    output_path.write_text(json.dumps(serialized, indent=2))
    print(f"\n[saved] Spatial relationships saved: {output_path}")

    # Update objects.json with enriched associated_text
    obj_output_path = out_dir / "objects.json"
    obj_output_path.write_text(json.dumps(enriched_objects, indent=2))
    print(f"[saved] Enriched objects saved: {obj_output_path}")


if __name__ == "__main__":
    main()
