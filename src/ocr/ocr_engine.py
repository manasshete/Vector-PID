"""EasyOCR wrapper with coordinate mapping for engineering drawings.

Replaces PaddleOCR (which has known instability on Python 3.13 + Windows)
with EasyOCR — a PyTorch-based OCR library with full Python 3.13 support.
"""
from __future__ import annotations

import numpy as np
import easyocr
from pydantic import BaseModel, Field

from src.models.schemas import BoundingBox
from src.preprocessing.tiling import TileMetadata


class OCRResult(BaseModel):
    """Single OCR detection with global coordinates."""
    id: str
    text: str
    confidence: float = Field(..., ge=0, le=1)
    bbox: BoundingBox
    tile_id: int
    method: str = "easyocr"


class OCREngine:
    """Wrapper around EasyOCR with tile-aware coordinate conversion."""

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        """Initialize EasyOCR reader.

        Parameters
        ----------
        lang : str
            Language code (default ``"en"``). For engineering drawings
            English is sufficient; pass ``["en"]`` list if needed.
        use_gpu : bool
            If True, use CUDA GPU. Default ``False`` (CPU).
        """
        lang_list = [lang] if isinstance(lang, str) else lang
        self._reader = easyocr.Reader(lang_list, gpu=use_gpu, verbose=False)

    def process_tile(
        self,
        tile_image: np.ndarray,
        tile_metadata: TileMetadata,
        min_confidence: float = 0.5,
    ) -> list[OCRResult]:
        """Run OCR on a single tile and convert coords to global space.

        Parameters
        ----------
        tile_image : np.ndarray
            RGB image array for this tile.
        tile_metadata : TileMetadata
            Offset metadata used to map local bbox to global coordinates.
        min_confidence : float
            Discard detections below this score.

        Returns
        -------
        list[OCRResult]
            Detections in global drawing coordinate space.
        """
        if tile_image is None or tile_image.size == 0:
            return []

        # EasyOCR returns: list of (bbox_points, text, confidence)
        # bbox_points: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] (clockwise polygon)
        raw_results = self._reader.readtext(tile_image)

        results: list[OCRResult] = []
        for idx, (bbox_points, text, confidence) in enumerate(raw_results):
            if confidence < min_confidence:
                continue

            xs = [float(p[0]) for p in bbox_points]
            ys = [float(p[1]) for p in bbox_points]

            local_bbox = BoundingBox(
                x=min(xs),
                y=min(ys),
                width=max(xs) - min(xs),
                height=max(ys) - min(ys),
            )

            global_bbox = BoundingBox(
                x=local_bbox.x + tile_metadata.x_offset,
                y=local_bbox.y + tile_metadata.y_offset,
                width=local_bbox.width,
                height=local_bbox.height,
            )

            results.append(OCRResult(
                id=f"TXT-{tile_metadata.tile_id:03d}-{idx:04d}",
                text=str(text).strip(),
                confidence=float(confidence),
                bbox=global_bbox,
                tile_id=tile_metadata.tile_id,
            ))

        return results

    def process_tiles(
        self,
        tiles: list,
        min_confidence: float = 0.5,
    ) -> list[OCRResult]:
        """Process all tiles and return flattened list of global OCR results."""
        all_results: list[OCRResult] = []
        for tile in tiles:
            tile_results = self.process_tile(tile.image, tile.metadata, min_confidence)
            all_results.extend(tile_results)
        return all_results