"""OpenCV baseline contour-based symbol detector for P&ID drawings.

WARNING: This OpenCV baseline is unreliable on complex P&IDs (<40% mAP expected).
It exists only as an interface placeholder. Replace with YOLO/RT-DETR before any production use.
"""
from __future__ import annotations

import logging
import cv2
import numpy as np

from src.detection.detector import Detector
from src.models.schemas import BoundingBox, DetectedObject

logger = logging.getLogger(__name__)


class OpenCVSymbolDetector(Detector):
    """Contour analysis symbol detector using shape heuristics.

    WARNING: This OpenCV baseline is unreliable on complex P&IDs (<40% mAP expected).
    It exists only as an interface placeholder. Replace with YOLO/RT-DETR before any production use.
    """

    def __init__(self, min_confidence: float = 0.4):
        self.min_confidence = min_confidence

    def detect(self, image: np.ndarray, tile_offset: tuple[float, float] = (0.0, 0.0)) -> list[DetectedObject]:
        """Detect symbols (VALVE, PUMP, TANK, INSTRUMENT, FLANGE, EQUIPMENT) via contour analysis."""
        if image is None or image.size == 0:
            return []

        ox, oy = tile_offset

        # Convert to grayscale
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        else:
            gray = image.copy()

        # Binarize with Otsu
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find external and child contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        objects: list[DetectedObject] = []
        obj_counter = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter extremely small noise (<100px) or whole-page background (>80% image area)
            img_area = gray.shape[0] * gray.shape[1]
            if area < 100 or area > (0.8 * img_area):
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            if w <= 5 or h <= 5:
                continue

            aspect_ratio = float(w) / float(h)
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0.0

            # Circularity check for instrument bubbles / tanks
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * (area / (perimeter * perimeter)) if perimeter > 0 else 0.0

            # Heuristic classification
            symbol_type = None
            conf = 0.50

            # 1. Circle / Bubble -> INSTRUMENT bubble
            if circularity > 0.70 and 15 <= w <= 120 and 15 <= h <= 120:
                symbol_type = "INSTRUMENT"
                conf = 0.65
            # 2. Large vertical rectangle / vessel -> TANK / VESSEL
            elif aspect_ratio < 0.5 and h > 100 and area > 1000:
                symbol_type = "TANK"
                conf = 0.60
            # 3. Hourglass / triangle aspect -> VALVE
            elif (0.6 <= aspect_ratio <= 1.6) and (20 <= w <= 80) and (20 <= h <= 80) and solidity < 0.75:
                symbol_type = "VALVE"
                conf = 0.55
            # 4. Circular/pump shape
            elif circularity > 0.55 and (40 <= w <= 150) and (40 <= h <= 150):
                symbol_type = "PUMP"
                conf = 0.50
            # 5. Small square/flange
            elif 0.8 <= aspect_ratio <= 1.2 and 10 <= w <= 30 and 10 <= h <= 30:
                symbol_type = "FLANGE"
                conf = 0.45
            # 6. Larger general equipment box
            elif area > 1500 and (w > 60 and h > 60):
                symbol_type = "EQUIPMENT"
                conf = 0.45

            if symbol_type and conf >= self.min_confidence:
                obj_counter += 1
                bbox = BoundingBox(
                    x=float(x + ox),
                    y=float(y + oy),
                    width=float(w),
                    height=float(h),
                )
                objects.append(
                    DetectedObject(
                        id=f"OBJ-{obj_counter:04d}",
                        type=symbol_type,
                        bbox=bbox,
                        confidence=conf,
                        properties={
                            "area": float(area),
                            "aspect_ratio": round(aspect_ratio, 2),
                            "solidity": round(solidity, 2),
                        },
                        source_method="opencv_contour",
                    )
                )

        if len(objects) > 200:
            logger.warning(
                f"[!] High symbol detection count ({len(objects)}). OpenCV baseline likely produced false positives."
            )
        elif len(objects) < 5 and img_area > 100000:
            logger.warning(
                f"[!] Low symbol detection count ({len(objects)}). OpenCV baseline likely suffered false negatives."
            )

        return objects
