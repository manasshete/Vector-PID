#!/usr/bin/env python3
"""Step 3: Configurable preprocessing pipeline evaluation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
from src.preprocessing.image_processor import load_engineering_drawing, preprocess_drawing
from src.utils.viz import show_preprocessing_grid


def main():
    drawing_path = Path("data/raw/Export Gas Compressor-P&ID.pdf")
    if not drawing_path.exists():
        print(f"❌ Drawing not found: {drawing_path}")
        sys.exit(1)

    img, metadata = load_engineering_drawing(drawing_path)

    # === DEFAULT CONFIG ===
    print("Applying default preprocessing config...")
    default_stages = preprocess_drawing(img)
    show_preprocessing_grid(default_stages)

    # === CUSTOM CONFIG ===
    custom_config = {
        "contrast_clip_limit": 4.0,
        "threshold_method": "otsu",
        "denoise_strength": 5,
        "deskew_enabled": True,
    }
    print(f"Applying custom config: {custom_config}")
    custom_stages = preprocess_drawing(img, config=custom_config)
    show_preprocessing_grid(custom_stages)

    # === SAVE OUTPUTS ===
    output_dir = Path("data/processed")
    output_dir.mkdir(exist_ok=True)

    thresh_path = output_dir / "preprocessed.png"
    cv2.imwrite(str(thresh_path), custom_stages["thresholded"])
    print(f"✅ Thresholded image saved to {thresh_path}")

    config_output = output_dir / "preprocessing_config.json"
    result = {
        "config_used": custom_config,
        "output_path": str(thresh_path),
        "stages_generated": list(custom_stages.keys()),
    }
    config_output.write_text(json.dumps(result, indent=2))
    print(f"✅ Config saved to {config_output}")


if __name__ == "__main__":
    main()