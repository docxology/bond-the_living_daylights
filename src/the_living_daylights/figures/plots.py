"""SNIPER'S NEST — deterministic matplotlib figures for the manuscript.

Renders two plates from the pure domain modules (Agg backend, no display):
* :func:`render_ballistics_figure` — the zeroed trajectory against the sight
  line, with the near/far zero and a wind-drift panel;
* :func:`render_terrain_figure` — the seeded mountain/desert grid with the
  planned exfil route and its cover points.

Everything derives from the domain modules (no RNG beyond the seeded terrain,
no wall-clock). Output lands under ``output/figures/`` (git-ignored).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from the_living_daylights import ballistics, settings, terrain_ops

matplotlib.use("Agg")

__all__ = [
    "render_all_figures",
    "render_ballistics_figure",
    "render_terrain_figure",
]


def _output_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "output" / "figures"


def render_ballistics_figure(output_dir: Path | None = None) -> Path:
    """Plot the zeroed rifle trajectory, sight line, zeros, and wind drift."""
    out = output_dir if output_dir is not None else _output_dir()
    proj = settings.PROJECTILE
    v0 = settings.MUZZLE_VELOCITY_MPS
    zero = settings.ZERO_RANGE_M
    sight = settings.SIGHT_HEIGHT_M
    elev = ballistics.zero_scope(v0, zero, sight, projectile=proj)
    near_zero, far_zero = ballistics.capture_zero(elev, v0, zero, sight, projectile=proj)

    xs, ys, _zs, _ts = ballistics.trajectory(v0, elev, projectile=proj, max_range=far_zero * 1.15)
    xs_no_wind = xs
    # sight line (bore-relative, so add the sight height at muzzle to match plot)
    los = [sight * (1.0 - x / zero) for x in xs_no_wind]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax.plot(xs_no_wind, ys, color="#1f6feb", label="bullet trajectory")
    ax.plot(xs_no_wind, los, color="#9b9b9b", ls="--", label="sight line")
    ax.axhline(0.0, color="black", lw=0.6)
    for zr, zc in ((near_zero, "near zero"), (far_zero, "far zero")):
        ax.axvline(zr, color="#f2cc60", ls=":", lw=1.2)
        ax.annotate(zc, (zr, 0.05), rotation=90, fontsize=8)
    ax.set_xlabel("range (m)")
    ax.set_ylabel("height above bore (m)")
    ax.set_title(f"Zeroed trajectory at {float(zero):.0f} m  (elev {elev:.2f} mrad)")
    ax.legend(fontsize=8)

    ranges = list(range(50, 901, 50))
    drifts = [ballistics.wind_drift(r, settings.WIND_MPS, v0, projectile=proj) for r in ranges]
    ax2.plot(ranges, drifts, color="#cf222e")
    ax2.set_xlabel("range (m)")
    ax2.set_ylabel(f"wind drift (m) @ {float(settings.WIND_MPS):.0f} m/s")
    ax2.set_title("Full-value crosswind drift")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "ballistics_trajectory.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def render_terrain_figure(output_dir: Path | None = None) -> Path:
    """Plot the seeded terrain with the planned exfil route and cover points."""
    out = output_dir if output_dir is not None else _output_dir()
    grid = terrain_ops.generate_terrain(
        settings.TERRAIN_N, settings.TERRAIN_SEED, settings.TERRAIN_CELL_SIZE_M
    )
    route = terrain_ops.plan_route(grid, settings.ROUTE_START, settings.ROUTE_GOAL)
    cover = grid.cover_array()

    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    im = ax.imshow(cover, origin="lower", cmap="Greens", vmin=0.0, vmax=1.0)
    ax.set_title(f"Planned exfil route (seed {settings.TERRAIN_SEED}) — cover map")
    rs = [p[0] for p in route.path]
    cs = [p[1] for p in route.path]
    ax.plot(cs, rs, color="#1f6feb", lw=2.2, label="route")
    for pr, pc in route.cover_points:
        ax.plot(pc, pr, "o", ms=4, color="#cf222e", zorder=5)
    ax.plot(route.path[0][1], route.path[0][0], "s", color="white", ms=7, zorder=6, label="start")
    ax.plot(
        route.path[-1][1], route.path[-1][0], "*", color="yellow", ms=12, zorder=6, label="goal"
    )
    ax.legend(loc="upper right", fontsize=8)
    fig.colorbar(im, ax=ax, label="concealment cover (0–1)")

    fig.tight_layout()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "terrain_exfil_route.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def render_all_figures(output_dir: Path | None = None) -> list[Path]:
    """Render every manuscript plate and return their paths (deterministic)."""
    return [render_ballistics_figure(output_dir), render_terrain_figure(output_dir)]
