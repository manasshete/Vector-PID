"""Comprehensive unit tests for tiling and coordinate conversion."""
import numpy as np
import pytest

from src.models.schemas import BoundingBox
from src.preprocessing.tiling import TileManager, TileMetadata


@pytest.fixture
def small_image():
    return np.zeros((500, 600, 3), dtype=np.uint8)


@pytest.fixture
def exact_tile_image():
    return np.zeros((1024, 1024, 3), dtype=np.uint8)


@pytest.fixture
def large_image():
    return np.zeros((3000, 4000, 3), dtype=np.uint8)


# --- Grid Generation Tests ---

def test_default_config_generates_correct_grid(large_image):
    mgr = TileManager(large_image, tile_width=1024, tile_height=1024, overlap=100)
    tiles = mgr.generate_tiles()
    assert len(tiles) == mgr.num_tiles
    assert mgr.grid_shape[0] >= 3 and mgr.grid_shape[1] >= 4


def test_single_tile_when_image_smaller_than_tile_size(small_image):
    mgr = TileManager(small_image, tile_width=1024, tile_height=1024, overlap=100)
    tiles = mgr.generate_tiles()
    assert len(tiles) == 1
    assert tiles[0].metadata.width == 600
    assert tiles[0].metadata.height == 500


def test_exact_tile_size_produces_one_tile(exact_tile_image):
    mgr = TileManager(exact_tile_image, tile_width=1024, tile_height=1024, overlap=0)
    tiles = mgr.generate_tiles()
    assert len(tiles) == 1
    assert tiles[0].metadata.width == 1024
    assert tiles[0].metadata.height == 1024


def test_edge_tiles_are_smaller_not_padded(large_image):
    mgr = TileManager(large_image, tile_width=1024, tile_height=1024, overlap=100)
    tiles = mgr.generate_tiles()
    right_edge = [t for t in tiles if t.metadata.col == mgr.grid_shape[1] - 1]
    bottom_edge = [t for t in tiles if t.metadata.row == mgr.grid_shape[0] - 1]
    for t in right_edge:
        assert t.metadata.width <= 1024
        assert t.image.shape[1] == t.metadata.width
    for t in bottom_edge:
        assert t.metadata.height <= 1024
        assert t.image.shape[0] == t.metadata.height


def test_tile_id_deterministic_ordering(large_image):
    mgr = TileManager(large_image)
    tiles = mgr.generate_tiles()
    ids = [t.metadata.tile_id for t in tiles]
    assert ids == sorted(ids)
    assert ids == list(range(len(tiles)))


# --- Validation Tests ---

def test_overlap_larger_than_tile_raises():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="must be less than"):
        TileManager(img, tile_width=100, tile_height=100, overlap=100)


def test_zero_tile_dims_raise():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="positive"):
        TileManager(img, tile_width=0, tile_height=100)


def test_negative_overlap_raises():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="non-negative"):
        TileManager(img, overlap=-1)


def test_empty_image_raises():
    with pytest.raises(ValueError, match="empty"):
        TileManager(np.array([]))


# --- Coordinate Conversion Tests ---

def test_local_to_global_round_trip_zero_error(large_image):
    mgr = TileManager(large_image, tile_width=1024, tile_height=1024, overlap=100)
    rng = np.random.default_rng(42)
    for _ in range(200):
        gx = float(rng.integers(0, 3950))
        gy = float(rng.integers(0, 2950))
        gw = float(rng.integers(5, 50))
        gh = float(rng.integers(5, 50))
        gbbox = BoundingBox(x=gx, y=gy, width=gw, height=gh)

        tm = mgr.get_tile_at(int(gx), int(gy))
        assert tm is not None
        lbbox = mgr.global_to_local(tm, gbbox)
        assert lbbox is not None
        recovered = mgr.local_to_global(tm, lbbox)
        assert abs(recovered.x - gx) < 1e-9
        assert abs(recovered.y - gy) < 1e-9


def test_global_to_local_returns_none_for_out_of_bounds(large_image):
    mgr = TileManager(large_image)
    tiles = mgr.generate_tiles()
    far_bbox = BoundingBox(x=99999, y=99999, width=10, height=10)
    result = mgr.global_to_local(tiles[0].metadata, far_bbox)
    assert result is None


def test_overlap_point_maps_to_both_tiles():
    img = np.zeros((1024, 2000, 3), dtype=np.uint8)
    mgr = TileManager(img, tile_width=1024, tile_height=1024, overlap=200)
    tiles = mgr.generate_tiles()
    # Point in overlap zone between tile 0 and tile 1
    overlap_x = 1024 - 100  # Inside overlap
    t0 = tiles[0].metadata
    t1 = tiles[1].metadata
    bbox = BoundingBox(x=float(overlap_x), y=100.0, width=50.0, height=50.0)
    r0 = mgr.global_to_local(t0, bbox)
    r1 = mgr.global_to_local(t1, bbox)
    assert r0 is not None, "Overlap point should map to tile 0"
    assert r1 is not None, "Overlap point should map to tile 1"


def test_coordinates_preserved_after_preprocessing_chain():
    """Verify coords survive preprocess → tile chain."""
    from src.preprocessing.image_processor import preprocess_drawing
    img = np.random.randint(0, 255, (2000, 3000, 3), dtype=np.uint8)
    stages = preprocess_drawing(img)
    thresh = stages["thresholded"]
    mgr = TileManager(thresh, tile_width=1024, tile_height=1024, overlap=100)
    tiles = mgr.generate_tiles()
    # Verify first tile offset matches original coordinate space
    assert tiles[0].metadata.x_offset == 0
    assert tiles[0].metadata.y_offset == 0
    # Round-trip still works on preprocessed image
    bbox = BoundingBox(x=500.0, y=300.0, width=80.0, height=40.0)
    tm = mgr.get_tile_at(500, 300)
    local = mgr.global_to_local(tm, bbox)
    recovered = mgr.local_to_global(tm, local)
    assert abs(recovered.x - 500.0) < 1e-9