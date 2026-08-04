"""Real-data tests for the SNIPER'S NEST figure generators."""

from __future__ import annotations

from the_living_daylights.figures.plots import (
    render_all_figures,
    render_ballistics_figure,
    render_terrain_figure,
)


def test_render_ballistics_figure(tmp_path) -> None:
    path = render_ballistics_figure(tmp_path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_render_terrain_figure(tmp_path) -> None:
    path = render_terrain_figure(tmp_path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_render_all(tmp_path) -> None:
    paths = render_all_figures(tmp_path)
    assert len(paths) == 2
    assert all(p.exists() for p in paths)
