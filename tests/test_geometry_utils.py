"""Unit tests for geometry utility functions."""
import math
import pytest

from src.geometry.geometry_utils import (
    distance_point_to_line,
    lines_intersect,
    merge_collinear_lines,
    orientation,
)


def test_orientation_horizontal():
    assert orientation((0, 0), (100, 5)) == "horizontal"
    assert orientation((0, 0), (-100, -5)) == "horizontal"


def test_orientation_vertical():
    assert orientation((0, 0), (5, 100)) == "vertical"
    assert orientation((0, 0), (-5, -100)) == "vertical"


def test_orientation_diagonal():
    assert orientation((0, 0), (100, 100)) == "diagonal"


def test_distance_point_to_line():
    # Point on line
    assert abs(distance_point_to_line((50, 0), (0, 0), (100, 0))) < 1e-6
    # Point 10 units away
    assert abs(distance_point_to_line((50, 10), (0, 0), (100, 0)) - 10.0) < 1e-6
    # Off endpoint
    assert abs(distance_point_to_line((110, 0), (0, 0), (100, 0)) - 10.0) < 1e-6


def test_lines_intersect():
    l1 = ((0, 0), (10, 10))
    l2 = ((0, 10), (10, 0))
    assert lines_intersect(l1, l2) is True

    l3 = ((0, 0), (5, 5))
    l4 = ((6, 6), (10, 10))
    assert lines_intersect(l3, l4) is False


def test_merge_collinear_lines():
    lines = [
        ((0, 0), (50, 0)),
        ((45, 0), (100, 0)),
    ]
    merged = merge_collinear_lines(lines, max_gap=15.0, max_angle_diff=5.0)
    assert len(merged) == 1
    (s, e) = merged[0]
    assert s == (0, 0) and e == (100, 0) or s == (100, 0) and e == (0, 0)


def test_calculate_midpoint():
    from src.geometry.geometry_utils import calculate_midpoint
    assert calculate_midpoint((0, 0), (10, 10)) == (5.0, 5.0)
    assert calculate_midpoint((-10, 20), (10, -20)) == (0.0, 0.0)


def test_calculate_angle():
    from src.geometry.geometry_utils import calculate_angle
    assert abs(calculate_angle((0, 0), (10, 0)) - 0.0) < 1e-5
    assert abs(calculate_angle((0, 0), (0, 10)) - 90.0) < 1e-5
    assert abs(calculate_angle((0, 0), (10, 10)) - 45.0) < 1e-5


def test_calculate_iou():
    from src.geometry.geometry_utils import calculate_iou
    # Identical boxes
    box1 = (0, 0, 10, 10)
    assert abs(calculate_iou(box1, box1) - 1.0) < 1e-5

    # Non-overlapping boxes
    box2 = (20, 20, 10, 10)
    assert calculate_iou(box1, box2) == 0.0

    # Half overlap
    box3 = (5, 0, 10, 10)
    # intersection: 5*10 = 50, union: 100 + 100 - 50 = 150 -> 1/3
    assert abs(calculate_iou(box1, box3) - (1.0 / 3.0)) < 1e-5


def test_point_in_polygon():
    from src.geometry.geometry_utils import point_in_polygon
    triangle = [(0.0, 0.0), (10.0, 0.0), (5.0, 10.0)]
    assert point_in_polygon((5.0, 2.0), triangle) is True
    assert point_in_polygon((20.0, 20.0), triangle) is False
    assert point_in_polygon((0.0, 0.0), [(0.0, 0.0), (1.0, 1.0)]) is False

