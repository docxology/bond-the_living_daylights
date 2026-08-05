"""Real-data tests for :mod:`the_living_daylights.terrain_ops`."""

from __future__ import annotations

import numpy as np
import pytest

from the_living_daylights import terrain_ops as t


def test_landcover_name() -> None:
    assert t.landcover_name(t.open_desert) == "open_desert"
    assert t.landcover_name(t.ridgeline) == "ridgeline"
    with pytest.raises(ValueError):
        t.landcover_name(999)


def test_generate_terrain_deterministic() -> None:
    a = t.generate_terrain(seed=7)
    b = t.generate_terrain(seed=7)
    assert np.array_equal(a.elevation, b.elevation)
    assert np.array_equal(a.landcover, b.landcover)
    assert np.array_equal(a.cover_height, b.cover_height)
    assert a.seed == 7 and a.n == 32
    assert set(np.unique(a.landcover).tolist()).issubset(t.LANDCOVER.keys())
    with pytest.raises(ValueError):
        t.generate_terrain(n=1)


def test_terrain_grid_validation() -> None:
    elev = np.zeros((3, 3))
    lc = np.full((3, 3), 0)
    cov = np.zeros((3, 3))
    t.TerrainGrid(elev, lc, cov, 500.0, 1)
    with pytest.raises(ValueError):
        t.TerrainGrid(np.zeros((2, 3)), lc, cov, 500.0, 1)
    with pytest.raises(ValueError):
        t.TerrainGrid(np.zeros((3, 3, 3)), lc, cov, 500.0, 1)
    with pytest.raises(ValueError):
        t.TerrainGrid(elev, np.full((3, 3), 99), cov, 500.0, 1)
    with pytest.raises(ValueError):
        t.TerrainGrid(elev, lc, cov, -1.0, 1)


def test_step_cost_and_errors() -> None:
    grid = t.generate_terrain(seed=7)
    assert t.step_cost(grid, 0, 0, 0, 1) > 0
    with pytest.raises(ValueError):
        t.step_cost(grid, 0, 0, 5, 5)
    with pytest.raises(ValueError):
        t.step_cost(grid, -1, 0, 0, 0)


def test_plan_route_deterministic_and_cover_tradeoff() -> None:
    grid = t.generate_terrain(seed=7)
    start, goal = (0, 0), (grid.n - 1, grid.n - 1)
    route = t.plan_route(grid, start, goal)
    assert route.path[0] == start and route.path[-1] == goal
    assert route.distance_m > 0 and route.total_cost > 0
    assert 0.0 <= route.mean_cover <= 1.0
    # determinism: identical route and cost on re-run
    again = t.plan_route(grid, start, goal)
    assert again.path == route.path and again.total_cost == route.total_cost
    # a heavy cover weight must actually buy concealment (strict, not >=:
    # a >= assertion would pass even if cover_weight were ignored entirely)
    covered = t.plan_route(grid, start, goal, cover_weight=8.0)
    assert covered.mean_cover > route.mean_cover
    assert covered.path != route.path
    # and it pays for that concealment in blended cost
    assert covered.total_cost > route.total_cost


def test_plan_route_errors() -> None:
    grid = t.generate_terrain(seed=7)
    with pytest.raises(ValueError):
        t.plan_route(grid, (999, 0), (0, 0))
    with pytest.raises(ValueError):
        t.plan_route(grid, (0, 0), (0, 999))


def test_assess_cover() -> None:
    grid = t.generate_terrain(seed=7)
    route = t.plan_route(grid, (0, 0), (grid.n - 1, grid.n - 1))
    audit = t.assess_cover(grid, route.path)
    assert "mean_cover" in audit and "cover_points" in audit and "waypoint_cover" in audit
    assert 0.0 <= float(audit["mean_cover"]) <= 1.0
    # the independent audit must reproduce the planner's own numbers exactly
    assert float(audit["mean_cover"]) == pytest.approx(route.mean_cover)
    assert float(audit["min_cover"]) == pytest.approx(route.min_cover)
    assert audit["cover_points"] == route.cover_points
    # and the per-waypoint map must cover every step with the grid's own values
    waypoints = audit["waypoint_cover"]
    assert isinstance(waypoints, dict)
    assert len(waypoints) == len({cell for cell in route.path})
    cover = grid.cover_array()
    for (r, c), value in ((tuple(int(v) for v in k.split(",")), v) for k, v in waypoints.items()):
        assert value == pytest.approx(float(cover[r, c]))
    with pytest.raises(ValueError):
        t.assess_cover(grid, ())
    with pytest.raises(ValueError):
        t.assess_cover(grid, ((0, 999),))


def test_cover_array_tracks_cover_height_not_landcover_code() -> None:
    """Concealment is a function of the cover-height field, honoured verbatim."""
    grid = t.generate_terrain(seed=7)
    # An open-desert cell (low base cover) hand-raised to full standing cover
    # must read as fully concealed — the landcover code is not re-consulted.
    grid.cover_height[0, 0] = t.COVER_THRESHOLD_M
    assert float(grid.cover_array()[0, 0]) == pytest.approx(1.0)
    grid.cover_height[0, 0] = 0.0
    assert float(grid.cover_array()[0, 0]) == pytest.approx(0.0)


def test_step_cost_exposure_term_is_consumed() -> None:
    """cover_weight must change the cost of entering an exposed cell."""
    grid = t.generate_terrain(seed=7)
    grid.cover_height[0, 1] = 0.0  # fully exposed destination cell
    cheap = t.step_cost(grid, 0, 0, 0, 1, cover_weight=0.0)
    dear = t.step_cost(grid, 0, 0, 0, 1, cover_weight=4.0)
    # exposure == 1.0, so the delta is exactly cover_weight * cell_size_m
    assert dear - cheap == pytest.approx(4.0 * grid.cell_size_m)


def test_terrain_grid_rejects_non_square_arrays() -> None:
    """Matching but non-square shapes are rejected by the squareness check."""
    rect = np.zeros((2, 3))
    with pytest.raises(ValueError, match="square"):
        t.TerrainGrid(rect, np.zeros((2, 3), dtype=np.int64), rect.copy(), 500.0, 1)
