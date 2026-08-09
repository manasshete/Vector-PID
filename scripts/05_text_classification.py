#!/usr/bin/env python3
"""Step 6: Classify OCR text into engineering categories."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ocr.text_classifier import TextClassifier, TextClass


def main():
    # === LOAD OCR RESULTS ===
    ocr_path = Path("data/outputs/ocr_results.json")
    if not ocr_path.exists():
        print(f"[*] OCR results not found: {ocr_path}")
        print("Run scripts/04_ocr.py first.")
        sys.exit(1)

    ocr_data = json.loads(ocr_path.read_text())
    print(f"Loaded {len(ocr_data)} OCR results from {ocr_path}")

    # === CLASSIFY (Rules Only — No Grok for MVP) ===
    print("\n[*] Classifying text using deterministic rules...")
    classifier = TextClassifier(grok_service=None)  # Grok disabled for initial validation
    classified = classifier.classify_batch(ocr_data)

    # === STATISTICS ===
    class_counts = Counter(item.classification.value for item in classified)
    method_counts = Counter(item.method for item in classified)

    print("\n[+] Classification breakdown:")
    for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(classified)
        print(f"   {cls:<20} {count:>4} ({pct:.1f}%)")

    print("\n[i] Method breakdown:")
    print(f"   Rule-based:    {method_counts.get('rule', 0)}")
    print(f"   Grok fallback: {method_counts.get('grok', 0)}")

    # === SAMPLE OUTPUT BY CATEGORY ===
    print("\n[?] Sample classifications:")
    for cls in TextClass:
        samples = [item for item in classified if item.classification == cls][:3]
        if samples:
            print(f"\n   [{cls.value}]")
            for s in samples:
                print(f"      '{s.text}' -> conf={s.confidence:.2f} ({s.method})")

    # === SAVE RESULTS ===
    output_dir = Path("data/outputs")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "classified_text.json"

    serialized = [item.model_dump(mode="json") for item in classified]
    output_path.write_text(json.dumps(serialized, indent=2))
    print(f"\n[saved] Classified text saved: {output_path}")

    # === UNKNOWN ANALYSIS ===
    unknowns = [item for item in classified if item.classification == TextClass.UNKNOWN]
    if unknowns:
        print(f"\n[!] {len(unknowns)} UNKNOWN texts (candidates for Grok or rule refinement):")
        for u in unknowns[:10]:
            print(f"      '{u.text}' @ conf={u.confidence:.2f}")


if __name__ == "__main__":
    main()
