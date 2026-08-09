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
