"""SNIPER'S NEST — mountain/desert terrain operations: routes and cover.

Pure, infrastructure-free, deterministic terrain model for The Living
Daylights' Afghan theatre (and the generic mountain/desert corridor).

* :func:`generate_terrain` builds a deterministic elevation + landcover +
  cover grid from a fixed seed (numpy default_rng, no wall-clock);
* :func:`plan_route` runs Dijkstra's shortest-path algorithm over a movement
  cost model that blends distance, climb, and **exposure** (inverse cover), so
  the requested route trades speed against concealment;
* :func:`assess_cover` grades *any* proposed path's cover — mean concealment,
  cover points (high-concealment waypoints), and the least-covered segment (the
  operator's vulnerable stretch) — through a separate vectorised implementation
  of the same concealment definition. Agreement with :func:`plan_route`'s own
  summary is a cross-implementation consistency check, not independent evidence
  about the terrain.

Deterministic by construction: same seed, grid, and costs yield the same route.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Final

import numpy as np

__all__ = [
    "COVER_THRESHOLD_M",
    "LANDCOVER",
    "RouteResult",
    "TerrainGrid",
    "assess_cover",
    "boulder_field",
    "generate_terrain",
    "landcover_name",
    "mountain",
    "open_desert",
    "plan_route",
    "ridgeline",
    "scree",
    "step_cost",
    "trail",
    "wadi",
]

#: Landcover codes.
open_desert: Final[int] = 0
mountain: Final[int] = 1
scree: Final[int] = 2
boulder_field: Final[int] = 3
ridgeline: Final[int] = 4
wadi: Final[int] = 5
trail: Final[int] = 6

#: Landcover table: code -> (name, base cost per metre, base cover in [0,1]).
LANDCOVER: Final[dict[int, tuple[str, float, float]]] = {
    open_desert: ("open_desert", 1.6, 0.05),
    mountain: ("mountain", 3.6, 0.30),
    scree: ("scree", 2.4, 0.10),
    boulder_field: ("boulder_field", 2.0, 0.85),
    ridgeline: ("ridgeline", 3.0, 1.00),
    wadi: ("wadi", 1.3, 0.40),
    trail: ("trail", 1.0, 0.20),
}

#: Cover height (m) beyond which a cell is treated as fully concealed.
COVER_THRESHOLD_M: Final[float] = 2.0
_GRAVITY_CLIMB_M: Final[float] = 3.0  # climb penalty per metre of ascent (cost)


def landcover_name(code: int) -> str:
    """Human-readable name for a landcover code; raises on unknown codes."""
    if code not in LANDCOVER:
        raise ValueError(f"unknown landcover code {code!r}")
    return LANDCOVER[code][0]


def _cover(cover_height: np.ndarray) -> np.ndarray:
    """Effective concealment in [0,1]: cover height normalized to the threshold.

    Concealment is a pure function of standing cover height — the landcover
    code only sets that height at generation time (see :func:`generate_terrain`)
    and is deliberately *not* re-consulted here, so an edited ``cover_height``
    field is honoured verbatim by routing and visibility.
    """
    return np.clip(cover_height / COVER_THRESHOLD_M, 0.0, 1.0)


@dataclass
class TerrainGrid:
    """A deterministic elevation + landcover + cover terrain grid.

    ``elevation`` is metres above datum, ``landcover`` holds integer codes,
    and ``cover_height`` is metres of standing concealment per cell. All arrays
    are ``(n, n)``; ``cell_size_m`` is the side length of one cell.
    """

    elevation: np.ndarray
    landcover: np.ndarray
    cover_height: np.ndarray
    cell_size_m: float
    seed: int

    def __post_init__(self) -> None:
        if (
            self.elevation.shape != self.landcover.shape
            or self.elevation.shape != self.cover_height.shape
        ):
            raise ValueError("terrain arrays must share shape")
        if self.elevation.ndim != 2 or self.elevation.shape[0] != self.elevation.shape[1]:
            raise ValueError("terrain arrays must be square (n, n)")
        uniq = set(np.unique(self.landcover).tolist())
        if not uniq.issubset(LANDCOVER.keys()):
            raise ValueError(f"landcover contains unknown codes: {uniq - set(LANDCOVER.keys())}")
        if not (self.cell_size_m > 0):
            raise ValueError("cell_size_m must be positive")

    @property
    def n(self) -> int:
        return int(self.elevation.shape[0])

    def cover_array(self) -> np.ndarray:
        """Concealment in [0,1] over the whole grid."""
        return _cover(self.cover_height)

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.n and 0 <= c < self.n


def generate_terrain(
    n: int = 32,
    seed: int = 7,
    cell_size_m: float = 500.0,
    base_elevation_m: float = 600.0,
    relief_m: float = 1200.0,
) -> TerrainGrid:
    """Generate a deterministic terrain grid from a seed.

    Elevation is a smooth, seeded random field (a blurred noise mask scaled to
    ``relief_m`` around ``base_elevation_m``); landcover is a seeded draw over
    the table; cover height is derived per cell from its landcover base plus
    jitter. Same arguments -> identical grid (no wall-clock, no global RNG).
    """
    if n < 2:
        raise ValueError("n must be at least 2")
    rng = np.random.default_rng(seed)
    base = rng.normal(size=(n, n))
    # A small blur makes terrain spatially correlated (hills, not speckle).
    kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=float) / 16.0
    padded = np.pad(base, 1, mode="wrap")
    smooth = np.zeros_like(base)
    for dr in range(3):
        for dc in range(3):
            smooth += kernel[dr, dc] * padded[dr : dr + n, dc : dc + n]
    smooth = (smooth - smooth.mean()) / (smooth.std() + 1e-9)
    elevation = base_elevation_m + relief_m * smooth
    elevation = np.clip(elevation, 0.0, None)

    # landcover: weight toward desert + mountain + wadi for a mountain/desert mix.
    codes = np.array([open_desert, mountain, scree, boulder_field, ridgeline, wadi, trail])
    weights = np.array([0.30, 0.25, 0.10, 0.10, 0.05, 0.15, 0.05])
    landcover = rng.choice(codes, size=(n, n), p=weights).astype(np.int64)

    cover_height = np.zeros((n, n), dtype=float)
    for code, (_name, _cost, base_cover) in LANDCOVER.items():
        mask = landcover == code
        jitter = rng.uniform(0.0, 0.75, size=(n, n))
        cover_height[mask] = np.clip(
            COVER_THRESHOLD_M * base_cover + jitter[mask], 0.0, COVER_THRESHOLD_M * 1.6
        )

    return TerrainGrid(
        elevation=elevation,
        landcover=landcover,
        cover_height=cover_height,
        cell_size_m=cell_size_m,
        seed=seed,
    )


def step_cost(
    grid: TerrainGrid,
    r1: int,
    c1: int,
    r2: int,
    c2: int,
    *,
    cover_weight: float = 1.0,
) -> float:
    """Movement cost to enter cell ``(r2, c2)`` from ``(r1, c1)``.

    Cost is per-metre and blends the landcover's base cost, an ascent penalty
    for climbing, and an exposure penalty weighted by ``cover_weight`` (cells
    with low cover cost more, so cover-seeking routes prefer concealment).

    Raises:
        ValueError: if the cells are not adjacent or are out of bounds.
    """
    if not (grid.in_bounds(r1, c1) and grid.in_bounds(r2, c2)):
        raise ValueError("step_cost requires in-bounds cells")
    dr, dc = abs(r2 - r1), abs(c2 - c1)
    if dr + dc != 1:
        raise ValueError("step_cost permits only 4-adjacent moves")
    code = int(grid.landcover[r2, c2])
    _name, base_cost, _base_cover = LANDCOVER[code]
    climb = max(0.0, float(grid.elevation[r2, c2] - grid.elevation[r1, c1]))
    eff_cover = float(_cover(grid.cover_height)[r2, c2])
    exposure = 1.0 - eff_cover
    per_metre = base_cost + _GRAVITY_CLIMB_M * climb / grid.cell_size_m + cover_weight * exposure
    return per_metre * grid.cell_size_m


@dataclass(frozen=True)
class RouteResult:
    """A planned ground route and its cost/concealment profile."""

    path: tuple[tuple[int, int], ...]
    total_cost: float
    distance_m: float
    mean_cover: float
    cover_points: tuple[tuple[int, int], ...]  # high-concealment waypoints
    min_cover: float
    min_cover_index: int  # step (0-based, along path) of least cover


def plan_route(
    grid: TerrainGrid,
    start: tuple[int, int],
    goal: tuple[int, int],
    *,
    cover_weight: float = 1.0,
) -> RouteResult:
    """Find the least-cost route from ``start`` to ``goal`` (Dijkstra).

    Deterministic: a binary heap over 4-adjacent moves with strict
    ``(cost, node)`` tie-breaking keeps the frontier order reproducible. The
    returned route minimizes blended movement + exposure cost.

    Raises:
        ValueError: if either endpoint is out of bounds.
    """
    n = grid.n
    for endpoint in (start, goal):
        if not grid.in_bounds(*endpoint):
            raise ValueError(f"route endpoint {endpoint!r} out of bounds")
    dist = np.full((n, n), math.inf, dtype=float)
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    dist[start] = 0.0
    heap: list[tuple[float, int, int]] = [(0.0, start[0], start[1])]
    while heap:
        cost, r, c = heapq.heappop(heap)
        if (r, c) == goal:
            break
        if cost > dist[r, c]:
            continue
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not grid.in_bounds(nr, nc):
                continue
            ncost = cost + step_cost(grid, r, c, nr, nc, cover_weight=cover_weight)
            if ncost < dist[nr, nc]:
                dist[nr, nc] = ncost
                prev[(nr, nc)] = (r, c)
                heapq.heappush(heap, (ncost, nr, nc))
    if math.isinf(dist[goal[0], goal[1]]):
        raise ValueError("goal is unreachable on this terrain")

    # reconstruct path (reverse)
    node: tuple[int, int] = goal
    rev: list[tuple[int, int]] = [node]
    while node != start:
        node = prev[node]
        rev.append(node)
    path = tuple(reversed(rev))

    return _summarize(grid, path, dist[goal[0], goal[1]])


def _summarize(
    grid: TerrainGrid, path: tuple[tuple[int, int], ...], total_cost: float
) -> RouteResult:
    """Compute a route's distance, mean/min cover, and cover points."""
    cover = grid.cover_array()
    distance = (len(path) - 1) * grid.cell_size_m
    covers = [float(cover[r, c]) for (r, c) in path]
    mean_cover = sum(covers) / len(covers) if covers else 0.0
    cover_points = tuple((r, c) for (r, c), cv in zip(path, covers, strict=True) if cv >= 0.6)
    min_cover = min(covers) if covers else 0.0
    min_cover_index = int(covers.index(min_cover)) if covers else 0
    return RouteResult(
        path=path,
        total_cost=total_cost,
        distance_m=distance,
        mean_cover=mean_cover,
        cover_points=cover_points,
        min_cover=min_cover,
        min_cover_index=min_cover_index,
    )


def assess_cover(grid: TerrainGrid, path: tuple[tuple[int, int], ...]) -> dict[str, object]:
    """Second, separately implemented cover audit for any proposed path.

    Grades an arbitrary sequence of waypoints — connected or not, Dijkstra's or
    a hand-drawn alternative — reporting ``mean_cover``, ``cover_points``,
    ``min_cover``, ``min_cover_index``, and per-waypoint concealment.

    **What the agreement with** :func:`plan_route` **does and does not show.**
    This function deliberately does *not* call :func:`_summarize`: it is a
    vectorised numpy path over the same concealment definition, where the
    planner's summary is a scalar Python loop. Agreement between the two
    therefore rules out *implementation* drift between the planner's
    self-reported summary and an audit of the same waypoints. It is **not**
    independent evidence about the terrain or the model — both implement one
    definition of concealment, written by one author, so a wrong definition
    would be reproduced identically by both.
    """
    if not path:
        raise ValueError("assess_cover requires a non-empty path")
    for node in path:
        if not grid.in_bounds(*node):
            raise ValueError(f"cover waypoint {node!r} out of bounds")
    cover = grid.cover_array()
    rows = np.array([r for (r, _c) in path], dtype=np.int64)
    cols = np.array([c for (_r, c) in path], dtype=np.int64)
    values = cover[rows, cols]
    min_index = int(np.argmin(values))
    return {
        "mean_cover": float(np.mean(values)),
        "cover_points": tuple(
            node for node, keep in zip(path, values >= 0.6, strict=True) if bool(keep)
        ),
        "min_cover": float(values[min_index]),
        "min_cover_index": min_index,
        "waypoint_cover": {f"{r},{c}": float(cover[r, c]) for (r, c) in path},
    }
