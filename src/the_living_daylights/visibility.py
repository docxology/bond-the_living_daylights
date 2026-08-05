"""SNIPER'S NEST — terrain line-of-sight, viewsheds, and overwatch ranking.

Deterministic terrain visibility for the mountain/desert theatre:

* :func:`line_of_sight` — Bresenham cell-walk between two cells, comparing the
  linearly interpolated sight ray against each cell's terrain + cover height;
* :func:`viewshed` — every cell visible from an observer (deterministic
  row-major scan), with count and fraction;
* :func:`rank_overwatch_positions` — scores candidate cells as sniper
  positions: visibility of the target, distance, cover, and elevation
  advantage, and returns them ranked (the sniper's nest selection problem);
* :func:`best_overwatch` — the top-ranked visible candidate.

Same grid model as :mod:`the_living_daylights.terrain_ops`; pure,
infrastructure-free, deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from the_living_daylights.terrain_ops import TerrainGrid

__all__ = [
    "CLEARANCE_M",
    "EYE_HEIGHT_M",
    "OverwatchRanking",
    "best_overwatch",
    "elevation_gain",
    "line_of_sight",
    "rank_overwatch_positions",
    "viewshed",
]

#: Default observer eye height above the ground, metres.
EYE_HEIGHT_M = 1.7
#: Default clearance the sight ray must keep above terrain+cover, metres.
CLEARANCE_M = 0.3


def _bresenham_cells(r0: int, c0: int, r1: int, c1: int) -> tuple[tuple[int, int], ...]:
    """All grid cells on the Bresenham line between two cells, inclusive.

    Deterministic integer line walk (no floats, no RNG) so visibility results
    are byte-reproducible across runs and platforms.
    """
    dr = abs(r1 - r0)
    dc = abs(c1 - c0)
    sr = 1 if r0 < r1 else -1
    sc = 1 if c0 < c1 else -1
    err = dr - dc
    cells: list[tuple[int, int]] = [(r0, c0)]
    r, c = r0, c0
    while (r, c) != (r1, c1):
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
        cells.append((r, c))
    return tuple(cells)


def line_of_sight(
    grid: TerrainGrid,
    observer: tuple[int, int],
    target: tuple[int, int],
    *,
    eye_height_m: float = EYE_HEIGHT_M,
    clearance_m: float = CLEARANCE_M,
    target_height_m: float = EYE_HEIGHT_M,
) -> tuple[bool, tuple[int, int] | None]:
    """Whether the target cell is visible from the observer cell.

    The sight ray starts at ``elevation[observer] + eye_height`` and ends at
    ``elevation[target] + target_height`` (a standing target — a person or the
    asset at a site). An intermediate cell blocks the line when its
    terrain+cover top exceeds the interpolated ray height minus the clearance.
    Returns ``(visible, first_blocker)``.

    Raises:
        ValueError: if either cell is out of bounds.
    """
    for cell in (observer, target):
        if not grid.in_bounds(*cell):
            raise ValueError(f"visibility cell {cell!r} out of bounds")
    if observer == target:
        return True, None
    obs_h = float(grid.elevation[observer[0], observer[1]]) + eye_height_m
    tgt_h = float(grid.elevation[target[0], target[1]]) + target_height_m
    cells = _bresenham_cells(observer[0], observer[1], target[0], target[1])
    total = len(cells) - 1
    for step, (r, c) in enumerate(cells[1:-1], start=1):
        frac = step / total
        ray_h = obs_h + (tgt_h - obs_h) * frac
        cell_top = float(grid.elevation[r, c]) + float(grid.cover_height[r, c])
        if cell_top + clearance_m > ray_h:
            return False, (r, c)
    return True, None


def viewshed(
    grid: TerrainGrid,
    observer: tuple[int, int],
    *,
    max_range_cells: int | None = None,
    eye_height_m: float = EYE_HEIGHT_M,
    clearance_m: float = CLEARANCE_M,
) -> tuple[tuple[tuple[int, int], ...], int, float]:
    """All cells visible from ``observer`` within ``max_range_cells``.

    Deterministic row-major scan. Returns ``(visible_cells, count, fraction)``
    where the fraction is visible cells over the scanned (in-range) cells.
    """
    if not grid.in_bounds(*observer):
        raise ValueError(f"observer {observer!r} out of bounds")
    if max_range_cells is not None and max_range_cells < 1:
        raise ValueError("max_range_cells must be positive")
    visible: list[tuple[int, int]] = []
    scanned = 0
    r_min = max(0, observer[0] - max_range_cells) if max_range_cells is not None else 0
    r_max = (
        min(grid.n, observer[0] + max_range_cells + 1) if max_range_cells is not None else grid.n
    )
    c_min = max(0, observer[1] - max_range_cells) if max_range_cells is not None else 0
    c_max = (
        min(grid.n, observer[1] + max_range_cells + 1) if max_range_cells is not None else grid.n
    )
    for r in range(r_min, r_max):
        for c in range(c_min, c_max):
            scanned += 1
            visible_flag, _blocker = line_of_sight(
                grid, observer, (r, c), eye_height_m=eye_height_m, clearance_m=clearance_m
            )
            if visible_flag:
                visible.append((r, c))
    fraction = len(visible) / scanned if scanned else 0.0
    return tuple(visible), len(visible), float(fraction)


def elevation_gain(grid: TerrainGrid, observer: tuple[int, int], target: tuple[int, int]) -> float:
    """Observer elevation minus target elevation (m); positive = looking down."""
    return float(grid.elevation[observer[0], observer[1]]) - float(
        grid.elevation[target[0], target[1]]
    )


@dataclass(frozen=True)
class OverwatchRanking:
    """A candidate sniper position and its overwatch score."""

    cell: tuple[int, int]
    visible: bool
    distance_m: float
    cover: float
    elevation_gain_m: float
    score: float


def rank_overwatch_positions(
    grid: TerrainGrid,
    target: tuple[int, int],
    candidates: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    *,
    weights: tuple[float, float, float, float] = (0.40, 0.25, 0.20, 0.15),
    eye_height_m: float = EYE_HEIGHT_M,
    clearance_m: float = CLEARANCE_M,
    max_range_cells: int | None = None,
) -> tuple[OverwatchRanking, ...]:
    """Rank candidate cells as overwatch positions for a target.

    Score = ``w_vis * visible + w_dist * (1 - d/d_max) + w_cover * cover +
    w_elev * gain/gain_max`` — visibility (binary), proximity, concealment,
    and looking-down advantage, each normalized over the candidate set.
    Positions that cannot see the target score 0 for the visibility term but
    keep their other terms, so the ranking is total and deterministic (ties
    broken by cell order).

    Raises:
        ValueError: if the target is out of bounds or weights do not sum to 1.
    """
    if not grid.in_bounds(*target):
        raise ValueError(f"target {target!r} out of bounds")
    if not math.isclose(sum(weights), 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("overwatch weights must sum to 1")

    distances: list[tuple[tuple[int, int], float, bool, float, float]] = []
    for cell in candidates:
        if not grid.in_bounds(*cell):
            raise ValueError(f"candidate {cell!r} out of bounds")
        distance = math.dist(cell, target) * grid.cell_size_m
        if max_range_cells is not None and distance > max_range_cells * grid.cell_size_m:
            continue  # beyond practical engagement range — not an overwatch option
        visible, _blocker = line_of_sight(
            grid, cell, target, eye_height_m=eye_height_m, clearance_m=clearance_m
        )
        cover = float(grid.cover_array()[cell[0], cell[1]])
        gain = elevation_gain(grid, cell, target)
        distances.append((cell, distance, visible, cover, gain))

    d_max = max((d for _c, d, _v, _cv, _g in distances), default=0.0) or 1.0
    gain_max = max((g for _c, _d, _v, _cv, g in distances), default=0.0)
    gain_norm = gain_max if gain_max > 0 else 1.0

    rankings: list[OverwatchRanking] = []
    for cell, distance, visible, cover, gain in distances:
        w_vis, w_dist, w_cover, w_elev = weights
        score = (
            w_vis * (1.0 if visible else 0.0)
            + w_dist * (1.0 - distance / d_max)
            + w_cover * cover
            + w_elev * max(0.0, gain / gain_norm)
        )
        rankings.append(
            OverwatchRanking(
                cell=cell,
                visible=visible,
                distance_m=distance,
                cover=cover,
                elevation_gain_m=gain,
                score=score,
            )
        )
    rankings.sort(key=lambda r: (-r.score, r.cell))
    return tuple(rankings)


def best_overwatch(
    grid: TerrainGrid,
    target: tuple[int, int],
    candidates: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    *,
    weights: tuple[float, float, float, float] = (0.40, 0.25, 0.20, 0.15),
    eye_height_m: float = EYE_HEIGHT_M,
    clearance_m: float = CLEARANCE_M,
    max_range_cells: int | None = None,
) -> OverwatchRanking | None:
    """The top-ranked overwatch position, or ``None`` if none sees the target."""
    ranked = rank_overwatch_positions(
        grid,
        target,
        candidates,
        weights=weights,
        eye_height_m=eye_height_m,
        clearance_m=clearance_m,
        max_range_cells=max_range_cells,
    )
    for ranking in ranked:
        if ranking.visible:
            return ranking
    return None
