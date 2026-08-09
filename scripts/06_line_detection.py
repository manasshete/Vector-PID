#!/usr/bin/env python3
"""Step 7: Line detection using OpenCV Hough Line Transform."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import matplotlib.pyplot as plt
import numpy as np

from src.geometry.line_detector import LineDetector
from src.preprocessing.image_processor import load_engineering_drawing


def draw_lines_overlay(image: np.ndarray, lines: list, figsize=(24, 16)):
    """Visualize detected lines overlaid on drawing, color-coded by line_type."""
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.imshow(image)

    color_map = {
        "BORDER": "red",
        "DIMENSION": "blue",
        "LIKELY_PIPE": "lime",
        "UNKNOWN": "yellow",
    }

    for line in lines:
        color = color_map.get(line.line_type, "yellow")
        ax.plot(
            [line.start[0], line.end[0]],
            [line.start[1], line.end[1]],
            color=color,
            linewidth=1.5,
            alpha=0.7,
        )

    ax.set_title(f"Detected Lines: {len(lines)} line segments", fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.show(block=True)


def main():
    drawing_path = Path("data/raw/Export Gas Compressor-P&ID.pdf")
    if not drawing_path.exists():
        print(f"[*] Drawing not found: {drawing_path}")
        sys.exit(1)

    print("Loading drawing...")
    img, metadata = load_engineering_drawing(drawing_path, pdf_dpi=300)
    print(f"Loaded image: {metadata.width}x{metadata.height}")

    # Load classified text annotations if available
    text_path = Path("data/outputs/classified_text.json")
    annotations = []
    if text_path.exists():
        annotations = json.loads(text_path.read_text())
        print(f"Loaded {len(annotations)} text annotations for dimension line association")

    print("\n[*] Running OpenCV Hough Line Detector...")
    print("WARNING: Baseline OpenCV detector achieves 40-60% accuracy on dense P&IDs. YOLO/RT-DETR recommended for production.")

    detector = LineDetector(min_length=30.0, max_line_gap=15.0)
    lines = detector.detect(img, annotations=annotations)
    print(f"[+] Detected {len(lines)} lines")

    # Statistics
    type_counts = Counter(l.line_type for l in lines)
    orient_counts = Counter(l.orientation for l in lines)

    print("\n[+] Line type breakdown:")
    for ltype, count in type_counts.items():
        pct = 100 * count / len(lines) if lines else 0
        print(f"   {ltype:<15} {count:>5} ({pct:.1f}%)")

    print("\n[i] Orientation breakdown:")
    for orient, count in orient_counts.items():
        pct = 100 * count / len(lines) if lines else 0
        print(f"   {orient:<15} {count:>5} ({pct:.1f}%)")

    # Save lines to JSON
    output_dir = Path("data/outputs")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "lines.json"

    serialized = [l.model_dump(mode="json") for l in lines]
    output_path.write_text(json.dumps(serialized, indent=2))
    print(f"\n[saved] Detected lines saved: {output_path}")

    # Optional visualization
    # draw_lines_overlay(img, lines)


if __name__ == "__main__":
    main()
