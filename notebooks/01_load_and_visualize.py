#!/usr/bin/env python3
"""Step 1-2: Load engineering drawing and visualize density."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.preprocessing.image_processor import load_engineering_drawing
from src.utils.viz import show_image
import matplotlib.pyplot as plt
import numpy as np


def main():
    # === INPUT ===
    drawing_path = Path("data/raw/Export Gas Compressor-P&ID.pdf")
    if not drawing_path.exists():
        print(f"❌ Drawing not found: {drawing_path}")
        print("Place an engineering drawing in data/raw/ and update DRAWING_PATH")
        sys.exit(1)

    img, metadata = load_engineering_drawing(drawing_path)

    print(f"Filename: {metadata.filename}")
    print(f"Dimensions: {metadata.width} x {metadata.height}")
    print(f"Channels: {metadata.channels}")
    print(f"DPI: {metadata.dpi}")
    print(f"Format: {metadata.source_format}")

    # === VISUALIZATION: Full Drawing ===
    show_image(img, title=f"Full Drawing ({metadata.width}x{metadata.height})")

    # === VISUALIZATION: Zoomed Regions ===
    h, w = img.shape[:2]
    zoom_size = min(w, h) // 4
    regions = {
        "Top-Left": img[0:zoom_size, 0:zoom_size],
        "Top-Right": img[0:zoom_size, w - zoom_size:w],
        "Center": img[h // 2 - zoom_size // 2:h // 2 + zoom_size // 2,
                      w // 2 - zoom_size // 2:w // 2 + zoom_size // 2],
        "Bottom-Right": img[h - zoom_size:h, w - zoom_size:w],
    }

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    for ax, (name, region) in zip(axes.flat, regions.items()):
        ax.imshow(region)
        ax.set_title(f"{name} ({zoom_size}x{zoom_size})", fontsize=12)
        ax.axis("off")
    plt.suptitle("Zoomed Regions — Text Too Small for Whole-Image OCR", fontsize=14)
    plt.tight_layout()
    plt.show(block=True)

    # === SAVE RESULTS ===
    output_dir = Path("data/processed")
    output_dir.mkdir(exist_ok=True)
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(metadata.model_dump_json(indent=2))
    print(f"✅ Metadata saved to {metadata_path}")


if __name__ == "__main__":
    main()