"""Real-data tests for the SNIPER'S NEST figure generators."""

from __future__ import annotations

from the_living_daylights.figures.plots import (
    render_all_figures,
    render_ballistics_figure,
    render_glint_figure,
    render_overwatch_figure,
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


def test_render_glint_figure(tmp_path) -> None:
    path = render_glint_figure(tmp_path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_render_overwatch_figure(tmp_path) -> None:
    path = render_overwatch_figure(tmp_path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_render_all(tmp_path) -> None:
    paths = render_all_figures(tmp_path)
    assert len(paths) == 4
    assert all(p.exists() for p in paths)
    # byte-determinism: identical renders produce identical bytes
    again = render_all_figures(tmp_path)
    assert [p.read_bytes() for p in paths] == [p.read_bytes() for p in again]
