"""Real-data tests for :mod:`the_living_daylights.visibility`."""

from __future__ import annotations

import numpy as np
import pytest

from the_living_daylights import terrain_ops
from the_living_daylights import visibility as v


def _flat_grid(n: int = 7) -> terrain_ops.TerrainGrid:
    elev = np.zeros((n, n))
    lc = np.full((n, n), terrain_ops.open_desert)
    cov = np.zeros((n, n))
    return terrain_ops.TerrainGrid(elev, lc, cov, 500.0, seed=1)


def _ridge_grid(n: int = 7, ridge_row: int = 3) -> terrain_ops.TerrainGrid:
    """Flat grid with a solid 100 m wall across ``ridge_row``."""
    elev = np.zeros((n, n))
    elev[ridge_row, :] = 100.0
    lc = np.full((n, n), terrain_ops.open_desert)
    cov = np.zeros((n, n))
    return terrain_ops.TerrainGrid(elev, lc, cov, 500.0, seed=2)


def test_line_of_sight_flat_visible() -> None:
    grid = _flat_grid()
    assert v.line_of_sight(grid, (0, 0), (6, 6)) == (True, None)
    assert v.line_of_sight(grid, (2, 2), (2, 2)) == (True, None)  # same cell


def test_line_of_sight_ridge_blocks() -> None:
    grid = _ridge_grid(ridge_row=3)
    visible, blocker = v.line_of_sight(grid, (0, 3), (6, 3))
    assert visible is False
    assert blocker is not None
    assert blocker[0] == 3  # the wall row is the first blocker
    # same-side targets remain visible
    assert v.line_of_sight(grid, (0, 3), (2, 3)) == (True, None)


def test_line_of_sight_errors() -> None:
    grid = _flat_grid()
    with pytest.raises(ValueError):
        v.line_of_sight(grid, (-1, 0), (2, 2))
    with pytest.raises(ValueError):
        v.line_of_sight(grid, (0, 0), (9, 9))


def test_viewshed_flat_full_and_deterministic() -> None:
    grid = _flat_grid(n=7)
    visible, count, fraction = v.viewshed(grid, (3, 3), max_range_cells=3)
    assert fraction == 1.0  # flat terrain: every in-range cell visible
    assert count == 7 * 7  # 3-cell radius box covers the whole 7x7 grid
    again, count2, _ = v.viewshed(grid, (3, 3), max_range_cells=3)
    assert again == visible and count2 == count


def test_viewshed_ridge_limits_and_errors() -> None:
    grid = _ridge_grid(n=7, ridge_row=3)
    visible, count, fraction = v.viewshed(grid, (0, 3), max_range_cells=6)
    assert count < 49  # the wall hides everything beyond row 3
    assert fraction < 1.0
    with pytest.raises(ValueError):
        v.viewshed(grid, (9, 9))
    with pytest.raises(ValueError):
        v.viewshed(grid, (0, 0), max_range_cells=0)


def test_elevation_gain() -> None:
    grid = _ridge_grid()  # row 3 is a 100 m wall
    assert v.elevation_gain(grid, (3, 0), (5, 0)) == 100.0
    assert v.elevation_gain(grid, (5, 0), (3, 0)) == -100.0


def test_rank_overwatch_order_and_visibility_weight() -> None:
    grid = _flat_grid()
    target = (2, 2)
    candidates = [(0, 0), (2, 0), (4, 4)]
    ranked = v.rank_overwatch_positions(grid, target, candidates, max_range_cells=4)
    # all flat-terrain candidates see the target
    assert all(r.visible for r in ranked)
    # distance-normalized proximity dominates on a flat grid: nearest first
    assert ranked[0].cell == (2, 0)
    # scores are descending
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_overwatch_range_filter_and_errors() -> None:
    grid = _flat_grid(n=9)
    target = (0, 0)
    far = [(8, 8)]
    assert v.rank_overwatch_positions(grid, target, far, max_range_cells=2) == ()
    with pytest.raises(ValueError):
        v.rank_overwatch_positions(grid, target, far, weights=(0.3, 0.3, 0.3, 0.3))
    with pytest.raises(ValueError):
        v.rank_overwatch_positions(grid, (9, 9), far)
    with pytest.raises(ValueError):
        v.rank_overwatch_positions(grid, target, [(9, 9)])


def test_best_overwatch_skips_a_blind_top_scorer() -> None:
    """The visibility filter is load-bearing, not decorative.

    A close, high, well-covered position can out-score a distant open one on
    the non-visibility terms alone (max 0.60) even though a ridge blinds it,
    beating a visible candidate that scores only the 0.40 visibility weight.
    ``rank_overwatch_positions`` therefore puts the blind cell first, and only
    ``best_overwatch`` returns a position that can actually see the site.
    """
    n = 9
    elev = np.zeros((n, n))
    elev[7, :] = 300.0  # ridge wall between the blind candidate and the site
    elev[6, 4] = 200.0  # blind candidate: high ground behind the wall
    cov = np.zeros((n, n))
    cov[6, 4] = terrain_ops.COVER_THRESHOLD_M  # ...and fully concealed
    lc = np.full((n, n), terrain_ops.open_desert)
    grid = terrain_ops.TerrainGrid(elev, lc, cov, 500.0, seed=3)

    target = (8, 4)
    blind, seeing = (6, 4), (8, 0)
    ranked = v.rank_overwatch_positions(grid, target, [blind, seeing], max_range_cells=6)
    by_cell = {r.cell: r for r in ranked}
    assert by_cell[blind].visible is False
    assert by_cell[seeing].visible is True
    assert ranked[0].cell == blind  # top-SCORED cannot see the site
    best = v.best_overwatch(grid, target, [blind, seeing], max_range_cells=6)
    assert best is not None
    assert best.cell == seeing and best.visible  # top-scored VISIBLE differs
    assert best.cell != ranked[0].cell


def test_best_overwatch_visible_and_none() -> None:
    flat = _flat_grid()
    best = v.best_overwatch(flat, (2, 2), [(0, 0), (4, 4)])
    assert best is not None and best.visible
    # behind a wall, nothing sees the target -> None
    ridge = _ridge_grid(ridge_row=3)
    assert v.best_overwatch(ridge, (6, 3), [(0, 3)]) is None
