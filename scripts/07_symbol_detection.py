#!/usr/bin/env python3
"""Step 8: Symbol detection using OpenCV contour analysis."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.detection.symbol_detector import OpenCVSymbolDetector
from src.preprocessing.image_processor import load_engineering_drawing


def main():
    print("================================================================================")
    print("  ACCURACY DISCLAIMER FOR STEP 8: SYMBOL DETECTION")
    print("  WARNING: This OpenCV baseline is unreliable on complex P&IDs (<40% mAP expected).")
    print("  It exists only as an interface placeholder. Replace with YOLO/RT-DETR before any production use.")
    print("================================================================================\n")

    drawing_path = Path("data/raw/Export Gas Compressor-P&ID.pdf")
    if not drawing_path.exists():
        print(f"[*] Drawing not found: {drawing_path}")
        sys.exit(1)

    print("Loading drawing...")
    img, metadata = load_engineering_drawing(drawing_path, pdf_dpi=300)
    print(f"Loaded image: {metadata.width}x{metadata.height}")

    print("\n[*] Running OpenCV Symbol Detector...")
    detector = OpenCVSymbolDetector(min_confidence=0.4)
    objects = detector.detect(img)
    print(f"[+] Detected {len(objects)} symbols")

    if len(objects) > 200:
        print(f"[!] WARNING: High detection count ({len(objects)} > 200). Likely contains false positives.")
    elif len(objects) < 5:
        print(f"[!] WARNING: Low detection count ({len(objects)} < 5). Likely suffers false negatives.")

    # Statistics
    type_counts = Counter(obj.type for obj in objects)
    print("\n[+] Symbol type breakdown:")
    for stype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(objects) if objects else 0
        print(f"   {stype:<15} {count:>5} ({pct:.1f}%)")

    # Sample output
    print("\n[?] Sample detected objects:")
    for obj in objects[:5]:
        print(f"   [{obj.id}] {obj.type} @ ({obj.bbox.x:.0f},{obj.bbox.y:.0f}) conf={obj.confidence:.2f}")

    # Save to JSON
    output_dir = Path("data/outputs")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "objects.json"

    serialized = [obj.model_dump(mode="json") for obj in objects]
    output_path.write_text(json.dumps(serialized, indent=2))
    print(f"\n[saved] Detected objects saved: {output_path}")


if __name__ == "__main__":
    main()
