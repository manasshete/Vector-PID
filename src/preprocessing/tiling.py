"""Configurable tiling with bidirectional coordinate conversion for engineering drawings."""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from src.models.schemas import BoundingBox


class TileMetadata(BaseModel):
    """Immutable metadata for a single tile in global coordinates."""
    tile_id: int = Field(..., ge=0)
    x_offset: int = Field(..., ge=0)
    y_offset: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    row: int = Field(..., ge=0)
    col: int = Field(..., ge=0)


class TileResult(BaseModel):
    """A tile image paired with its metadata. Image excluded from serialization."""
    metadata: TileMetadata

    class Config:
        arbitrary_types_allowed = True

    # Image stored as instance attribute, not Pydantic field (not serializable)
    _image: np.ndarray = None

    def __init__(self, metadata: TileMetadata, image: np.ndarray):
        super().__init__(metadata=metadata)
        self._image = image

    @property
    def image(self) -> np.ndarray:
        return self._image


class TileManager:
    """Generates overlapping tiles and converts coordinates between local/global spaces."""

    def __init__(
        self,
        image: np.ndarray,
        tile_width: int = 1024,
        tile_height: int = 1024,
        overlap: int = 100,
    ):
        if image is None or image.size == 0:
            raise ValueError("Input image is empty or None")
        if tile_width <= 0 or tile_height <= 0:
            raise ValueError(f"Tile dimensions must be positive: ({tile_width}, {tile_height})")
        if overlap < 0:
            raise ValueError(f"Overlap must be non-negative: {overlap}")
        if overlap >= min(tile_width, tile_height):
            raise ValueError(
                f"Overlap ({overlap}) must be less than min tile dimension ({min(tile_width, tile_height)})"
            )

        self._image = image
        self._tile_width = tile_width
        self._tile_height = tile_height
        self._overlap = overlap
        self._img_h, self._img_w = image.shape[:2]

        # Precompute grid dimensions
        self._step_x = max(1, tile_width - overlap)
        self._step_y = max(1, tile_height - overlap)
        self._num_cols = max(1, math.ceil((self._img_w - overlap) / self._step_x)) if self._img_w > overlap else 1
        self._num_rows = max(1, math.ceil((self._img_h - overlap) / self._step_y)) if self._img_h > overlap else 1

    @property
    def num_tiles(self) -> int:
        return self._num_rows * self._num_cols

    @property
    def grid_shape(self) -> tuple[int, int]:
        return (self._num_rows, self._num_cols)

    def generate_tiles(self) -> list[TileResult]:
        """Generate all tiles. Edge tiles are smaller, never padded."""
        tiles: list[TileResult] = []
        for row in range(self._num_rows):
            for col in range(self._num_cols):
                x_off = min(col * self._step_x, max(0, self._img_w - self._tile_width))
                y_off = min(row * self._step_y, max(0, self._img_h - self._tile_height))

                actual_w = min(self._tile_width, self._img_w - x_off)
                actual_h = min(self._tile_height, self._img_h - y_off)

                # Clamp to valid region
                x_off = max(0, x_off)
                y_off = max(0, y_off)
                actual_w = max(1, actual_w)
                actual_h = max(1, actual_h)

                tile_img = self._image[y_off:y_off + actual_h, x_off:x_off + actual_w].copy()
                tile_id = row * self._num_cols + col

                meta = TileMetadata(
                    tile_id=tile_id,
                    x_offset=x_off,
                    y_offset=y_off,
                    width=actual_w,
                    height=actual_h,
                    row=row,
                    col=col,
                )
                tiles.append(TileResult(metadata=meta, image=tile_img))
        return tiles

    def local_to_global(self, tile_metadata: TileMetadata, local_bbox: BoundingBox) -> BoundingBox:
        """Convert tile-local bbox to original image global coordinates."""
        return BoundingBox(
            x=local_bbox.x + tile_metadata.x_offset,
            y=local_bbox.y + tile_metadata.y_offset,
            width=local_bbox.width,
            height=local_bbox.height,
        )

    def global_to_local(
        self, tile_metadata: TileMetadata, global_bbox: BoundingBox
    ) -> Optional[BoundingBox]:
        """Convert global bbox to tile-local. Returns None if no intersection."""
        # Check intersection using integer arithmetic
        gx, gy = int(global_bbox.x), int(global_bbox.y)
        gw, gh = int(global_bbox.width), int(global_bbox.height)
        tx, ty = tile_metadata.x_offset, tile_metadata.y_offset
        tw, th = tile_metadata.width, tile_metadata.height

        # No intersection check
        if gx + gw <= tx or gx >= tx + tw or gy + gh <= ty or gy >= ty + th:
            return None

        # Clip to tile bounds
        lx = max(0, gx - tx)
        ly = max(0, gy - ty)
        lx2 = min(tw, gx + gw - tx)
        ly2 = min(th, gy + gh - ty)

        return BoundingBox(x=float(lx), y=float(ly), width=float(lx2 - lx), height=float(ly2 - ly))

    def get_tile_at(self, x: int, y: int) -> Optional[TileMetadata]:
        """Find which tile contains a global coordinate point."""
        if x < 0 or y < 0 or x >= self._img_w or y >= self._img_h:
            return None

        col = min(x // self._step_x, self._num_cols - 1)
        row = min(y // self._step_y, self._num_rows - 1)
        tile_id = row * self._num_cols + col

        # Reconstruct metadata for this tile
        x_off = min(col * self._step_x, max(0, self._img_w - self._tile_width))
        y_off = min(row * self._step_y, max(0, self._img_h - self._tile_height))
        actual_w = min(self._tile_width, self._img_w - max(0, x_off))
        actual_h = min(self._tile_height, self._img_h - max(0, y_off))

        return TileMetadata(
            tile_id=tile_id, x_offset=max(0, x_off), y_offset=max(0, y_off),
            width=max(1, actual_w), height=max(1, actual_h), row=row, col=col,
        )