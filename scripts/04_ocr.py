#!/usr/bin/env python3
"""Step 5: Run OCR on tiles and visualize bounding boxes."""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*urllib3.*")
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from src.ocr.ocr_engine import OCREngine
from src.preprocessing.image_processor import load_engineering_drawing
from src.preprocessing.tiling import TileManager


def draw_ocr_boxes(image: np.ndarray, results: list, figsize=(24, 16)):
    """Visualize OCR bounding boxes colored by confidence."""
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.imshow(image)

    for r in results:
        # Color by confidence: green (>0.9), yellow (0.7-0.9), red (<0.7)
        if r.confidence >= 0.9:
            color = "lime"
        elif r.confidence >= 0.7:
            color = "yellow"
        else:
            color = "red"

        rect = patches.Rectangle(
            (r.bbox.x, r.bbox.y), r.bbox.width, r.bbox.height,
            linewidth=1.2, edgecolor=color, facecolor="none"
        )
        ax.add_patch(rect)
        ax.text(
            r.bbox.x, r.bbox.y - 3,
            f"{r.text[:20]} ({r.confidence:.2f})",
            fontsize=6, color=color, fontweight="bold",
            bbox=dict(facecolor="black", alpha=0.5, pad=1, edgecolor="none"),
        )

    ax.set_title(f"OCR Results: {len(results)} detections", fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.show(block=True)


def main():
    drawing_path = Path("data/raw/Export Gas Compressor-P&ID.pdf")
    if not drawing_path.exists():
        print(f"❌ Drawing not found: {drawing_path}")
        sys.exit(1)

    # === LOAD & TILE ===
    print("Loading drawing...")
    img, metadata = load_engineering_drawing(drawing_path, pdf_dpi=300)
    print(f"Image size: {metadata.width}x{metadata.height}")

    print("Generating tiles...")
    manager = TileManager(img, tile_width=1024, tile_height=1024, overlap=100)
    tiles = manager.generate_tiles()
    print(f"Generated {len(tiles)} tiles")

    # === RUN OCR ===
    print("Initializing PaddleOCR (downloads models on first run)...")
    engine = OCREngine(lang="en", use_gpu=False)

    print("Running OCR on all tiles...")
    results = engine.process_tiles(tiles, min_confidence=0.5)
    print(f"✅ Detected {len(results)} text regions")

    # === STATISTICS ===
    high_conf = sum(1 for r in results if r.confidence >= 0.9)
    med_conf = sum(1 for r in results if 0.7 <= r.confidence < 0.9)
    low_conf = sum(1 for r in results if r.confidence < 0.7)
    print(f"\n📊 Confidence breakdown:")
    print(f"   High (≥0.9): {high_conf}")
    print(f"   Medium (0.7-0.9): {med_conf}")
    print(f"   Low (<0.7): {low_conf}")

    # === VISUALIZE ===
    draw_ocr_boxes(img, results)

    # === SAVE RESULTS ===
    output_dir = Path("data/outputs")
    output_dir.mkdir(exist_ok=True)

    # Save JSON (exclude non-serializable fields)
    ocr_data = [r.model_dump() for r in results]
    ocr_path = output_dir / "ocr_results.json"
    ocr_path.write_text(json.dumps(ocr_data, indent=2))
    print(f"\n💾 OCR results saved: {ocr_path}")

    # Save annotated image
    annotated = img.copy()
    for r in results:
        x, y, w, h = int(r.bbox.x), int(r.bbox.y), int(r.bbox.width), int(r.bbox.height)
        color = (0, 255, 0) if r.confidence >= 0.9 else (0, 255, 255) if r.confidence >= 0.7 else (0, 0, 255)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
        cv2.putText(annotated, r.text[:15], (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    annotated_path = output_dir / "ocr_annotated.png"
    cv2.imwrite(str(annotated_path), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
    print(f"💾 Annotated image saved: {annotated_path}")

    # Print sample detections
    print("\n🔍 Sample detections:")
    for r in results[:10]:
        print(f"   [{r.id}] '{r.text}' @ ({r.bbox.x:.0f},{r.bbox.y:.0f}) conf={r.confidence:.2f}")


if __name__ == "__main__":
    main()