"""Geometry utility functions for vector analysis of engineering drawings."""
from __future__ import annotations

import math
from typing import Optional


def orientation(start: tuple[float, float], end: tuple[float, float]) -> str:
    """Classify line orientation based on angle relative to horizontal axis.

    |angle| < 15° -> "horizontal"
    |angle| > 75° -> "vertical"
    else -> "diagonal"
    """
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle_rad = math.atan2(abs(dy), abs(dx))
    angle_deg = math.degrees(angle_rad)

    if angle_deg < 15.0:
        return "horizontal"
    elif angle_deg > 75.0:
        return "vertical"
    else:
        return "diagonal"


def distance_point_to_line(
    point: tuple[float, float],
    line_start: tuple[float, float],
    line_end: tuple[float, float],
) -> float:
    """Calculate shortest distance from a point to a line segment."""
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))

    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return math.hypot(px - proj_x, py - proj_y)


def lines_intersect(
    line1: tuple[tuple[float, float], tuple[float, float]],
    line2: tuple[tuple[float, float], tuple[float, float]],
) -> bool:
    """Determine if two 2D line segments intersect."""
    (p1x, p1y), (q1x, q1y) = line1
    (p2x, p2y), (q2x, q2y) = line2

    def ccw(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    p1, q1, p2, q2 = (p1x, p1y), (q1x, q1y), (p2x, p2y), (q2x, q2y)
    return (ccw(p1, p2, q2) != ccw(q1, p2, q2)) and (ccw(p1, q1, p2) != ccw(p1, q1, q2))


def merge_collinear_lines(
    lines: list[tuple[tuple[float, float], tuple[float, float]]],
    max_gap: float = 15.0,
    max_angle_diff: float = 5.0,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Merge collinear line segments within a distance gap and angle tolerance."""
    if not lines:
        return []

    def get_angle(s: tuple[float, float], e: tuple[float, float]) -> float:
        ang = math.degrees(math.atan2(e[1] - s[1], e[0] - s[0])) % 180.0
        return ang

    merged: list[tuple[tuple[float, float], tuple[float, float]]] = []
    used = [False] * len(lines)

    for i in range(len(lines)):
        if used[i]:
            continue

        s1, e1 = lines[i]
        angle1 = get_angle(s1, e1)
        cluster = [s1, e1]
        used[i] = True

        for j in range(i + 1, len(lines)):
            if used[j]:
                continue

            s2, e2 = lines[j]
            angle2 = get_angle(s2, e2)

            # Check angle difference
            angle_diff = abs(angle1 - angle2)
            if angle_diff > 90.0:
                angle_diff = 180.0 - angle_diff

            if angle_diff <= max_angle_diff:
                # Perpendicular distance to infinite line through s1-e1
                line_len = math.hypot(e1[0] - s1[0], e1[1] - s1[1])
                if line_len > 0:
                    perp_s2 = abs((e1[1] - s1[1]) * s2[0] - (e1[0] - s1[0]) * s2[1] + e1[0] * s1[1] - e1[1] * s1[0]) / line_len
                    perp_e2 = abs((e1[1] - s1[1]) * e2[0] - (e1[0] - s1[0]) * e2[1] + e1[0] * s1[1] - e1[1] * s1[0]) / line_len
                else:
                    perp_s2 = math.hypot(s2[0] - s1[0], s2[1] - s1[1])
                    perp_e2 = math.hypot(e2[0] - s1[0], e2[1] - s1[1])

                # Minimum endpoint-to-endpoint gap
                min_gap = min(
                    math.hypot(s1[0] - s2[0], s1[1] - s2[1]),
                    math.hypot(s1[0] - e2[0], s1[1] - e2[1]),
                    math.hypot(e1[0] - s2[0], e1[1] - s2[1]),
                    math.hypot(e1[0] - e2[0], e1[1] - e2[1]),
                )

                if perp_s2 <= max_gap and perp_e2 <= max_gap and min_gap <= max_gap:
                    cluster.extend([s2, e2])
                    used[j] = True

        # Find maximum extent of cluster along its main axis
        if len(cluster) == 2:
            merged.append((cluster[0], cluster[1]))
        else:
            # Pick pair with maximum distance
            max_dist = -1.0
            best_pair = (cluster[0], cluster[1])
            for pA in range(len(cluster)):
                for pB in range(pA + 1, len(cluster)):
                    d = math.hypot(cluster[pA][0] - cluster[pB][0], cluster[pA][1] - cluster[pB][1])
                    if d > max_dist:
                        max_dist = d
                        best_pair = (cluster[pA], cluster[pB])
            merged.append(best_pair)

    return merged
