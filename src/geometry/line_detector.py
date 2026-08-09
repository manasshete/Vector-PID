"""Line detector module for engineering drawings using OpenCV Hough line transform.

WARNING: Baseline OpenCV detector achieves 40-60% accuracy on dense P&IDs.
YOLO/RT-DETR recommended for production.
"""
from __future__ import annotations

import math
import cv2
import numpy as np

from src.geometry.geometry_utils import (
    distance_point_to_line,
    merge_collinear_lines,
    orientation,
)
from src.models.schemas import DetectedLine


class LineDetector:
    """Detects vector line segments in engineering drawings using OpenCV.

    WARNING: Baseline OpenCV detector achieves 40-60% accuracy on dense P&IDs.
    YOLO/RT-DETR recommended for production.
    """

    def __init__(
        self,
        min_length: float = 30.0,
        max_line_gap: float = 15.0,
        canny_thresh1: float = 50.0,
        canny_thresh2: float = 150.0,
    ):
        self.min_length = min_length
        self.max_line_gap = max_line_gap
        self.canny_thresh1 = canny_thresh1
        self.canny_thresh2 = canny_thresh2

    def detect(
        self,
        image: np.ndarray,
        annotations: list = None,
        tile_offset: tuple[float, float] = (0.0, 0.0),
    ) -> list[DetectedLine]:
        """Detect lines in image array and classify orientation & line_type.

        Parameters
        ----------
        image : np.ndarray
            RGB or Grayscale image array.
        annotations : list, optional
            List of ClassifiedText objects or dicts for identifying DIMENSION lines.
        tile_offset : tuple[float, float], optional
            (x_offset, y_offset) to map local coords to global space.

        Returns
        -------
        list[DetectedLine]
            Detected line segments in global coordinates.
        """
        if image is None or image.size == 0:
            return []

        # Convert to grayscale if RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        else:
            gray = image.copy()

        img_h, img_w = gray.shape[:2]
        ox, oy = tile_offset

        # Edge detection + Probabilistic Hough Lines
        edges = cv2.Canny(gray, int(self.canny_thresh1), int(self.canny_thresh2))
        raw_lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180.0,
            threshold=50,
            minLineLength=int(self.min_length),
            maxLineGap=int(self.max_line_gap),
        )

        if raw_lines is None:
            return []

        line_tuples: list[tuple[tuple[float, float], tuple[float, float]]] = []
        for line in raw_lines:
            x1, y1, x2, y2 = line[0]
            line_tuples.append(((float(x1), float(y1)), (float(x2), float(y2))))

        # Merge collinear line segments
        merged_tuples = merge_collinear_lines(line_tuples, max_gap=self.max_line_gap, max_angle_diff=5.0)

        annotation_centers = []
        if annotations:
            for item in annotations:
                # Get bbox center
                if hasattr(item, "bbox"):
                    bbox = item.bbox
                    if hasattr(bbox, "center"):
                        annotation_centers.append(bbox.center)
                    elif isinstance(bbox, dict):
                        cx = bbox.get("x", 0) + bbox.get("width", 0) / 2
                        cy = bbox.get("y", 0) + bbox.get("height", 0) / 2
                        annotation_centers.append((cx, cy))

        detected_lines: list[DetectedLine] = []
        for idx, (s_local, e_local) in enumerate(merged_tuples):
            length = math.hypot(e_local[0] - s_local[0], e_local[1] - s_local[1])
            if length < self.min_length:
                continue

            # Convert to global coordinates
            s_global = (s_local[0] + ox, s_local[1] + oy)
            e_global = (e_local[0] + ox, e_local[1] + oy)

            orient = orientation(s_global, e_global)

            # Classify line_type
            # 1. Border: within 50px of image boundary
            is_border = (
                s_local[0] < 50 or s_local[0] > (img_w - 50) or
                s_local[1] < 50 or s_local[1] > (img_h - 50) or
                e_local[0] < 50 or e_local[0] > (img_w - 50) or
                e_local[1] < 50 or e_local[1] > (img_h - 50)
            )

            # 2. Near annotation text: within 50px
            is_dimension = False
            if annotation_centers:
                for ac in annotation_centers:
                    dist = distance_point_to_line(ac, s_global, e_global)
                    if dist <= 50.0:
                        is_dimension = True
                        break

            if is_border and length > min(img_w, img_h) * 0.5:
                line_type = "BORDER"
                confidence = 0.85
            elif is_dimension:
                line_type = "DIMENSION"
                confidence = 0.65
            else:
                line_type = "LIKELY_PIPE"
                confidence = 0.75

            detected_lines.append(
                DetectedLine(
                    id=f"LINE-{idx:04d}",
                    start=s_global,
                    end=e_global,
                    length=round(length, 2),
                    orientation=orient,
                    line_type=line_type,
                    confidence=confidence,
                    source_method="opencv_hough",
                )
            )

        return detected_lines
