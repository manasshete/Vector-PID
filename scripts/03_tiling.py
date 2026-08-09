#!/usr/bin/env python3
"""Step 4: Validate tiling and bidirectional coordinate conversion."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from src.models.schemas import BoundingBox
from src.preprocessing.image_processor import load_engineering_drawing
from src.preprocessing.tiling import TileManager


def main():
    drawing_path = Path("data/raw/Export Gas Compressor-P&ID.pdf")
    if not drawing_path.exists():
        print(f"❌ Drawing not found: {drawing_path}")
        print("Place an engineering drawing in data/raw/")
        sys.exit(1)

    img, metadata = load_engineering_drawing(drawing_path)
    print(f"Loaded: {metadata.width}x{metadata.height}")

    # === GENERATE TILES ===
    manager = TileManager(img, tile_width=1024, tile_height=1024, overlap=100)
    tiles = manager.generate_tiles()
    rows, cols = manager.grid_shape

    print(f"\n📐 Tile Grid: {rows} rows × {cols} cols = {len(tiles)} tiles")
    edge_tiles = [t for t in tiles if t.metadata.width < 1024 or t.metadata.height < 1024]
    print(f"   Edge tiles (smaller): {len(edge_tiles)}")
    for et in edge_tiles[:4]:
        m = et.metadata
        print(f"   Tile {m.tile_id}: {m.width}x{m.height} at ({m.x_offset},{m.y_offset})")

    # === VISUALIZE TILE GRID OVERLAY ===
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    ax.imshow(img)
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    for tile in tiles:
        m = tile.metadata
        color = colors[m.tile_id % 10]
        rect = patches.Rectangle(
            (m.x_offset, m.y_offset), m.width, m.height,
            linewidth=1.5, edgecolor=color, facecolor="none", linestyle="--"
        )
        ax.add_patch(rect)
        ax.text(m.x_offset + 5, m.y_offset + 18, f"T{m.tile_id}",
                fontsize=7, color=color, fontweight="bold")
    ax.set_title(f"Tile Grid Overlay ({len(tiles)} tiles, overlap=100)", fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.show(block=True)

    # === COORDINATE CONVERSION ROUND-TRIP TEST ===
    print("\n🔄 Round-trip coordinate conversion test:")
    rng = np.random.default_rng(42)
    max_error = 0.0
    for _ in range(100):
        gx = float(rng.integers(0, metadata.width - 50))
        gy = float(rng.integers(0, metadata.height - 50))
        gw = float(rng.integers(10, 50))
        gh = float(rng.integers(10, 50))
        global_bbox = BoundingBox(x=gx, y=gy, width=gw, height=gh)

        tile_meta = manager.get_tile_at(int(gx), int(gy))
        if tile_meta is None:
            continue
        local_bbox = manager.global_to_local(tile_meta, global_bbox)
        if local_bbox is None:
            continue
        recovered = manager.local_to_global(tile_meta, local_bbox)
        error = abs(recovered.x - gx) + abs(recovered.y - gy)
        max_error = max(max_error, error)

    status = "✅ PASS" if max_error == 0.0 else f"❌ FAIL (max error={max_error})"
    print(f"   100 random points round-trip: {status}")

    # === SAVE MANIFEST & SAMPLE TILES ===
    output_dir = Path("data/tiles")
    output_dir.mkdir(exist_ok=True)

    manifest = [t.metadata.model_dump() for t in tiles]
    manifest_path = output_dir / "tile_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n💾 Manifest saved: {manifest_path} ({len(manifest)} tiles)")

    sample_dir = output_dir / "samples"
    sample_dir.mkdir(exist_ok=True)
    for tile in tiles[:9]:
        out_path = sample_dir / f"tile_{tile.metadata.tile_id:04d}.png"
        cv2.imwrite(str(out_path), cv2.cvtColor(tile.image, cv2.COLOR_RGB2BGR))
    print(f"💾 Sample tiles saved: {sample_dir}/ (first 9)")


if __name__ == "__main__":
    main()