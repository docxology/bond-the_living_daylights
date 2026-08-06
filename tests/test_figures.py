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


def test_default_output_dir_is_the_package_output_tree() -> None:
    """The no-argument default resolves to the package's git-ignored output/figures."""
    from the_living_daylights.figures import plots

    default = plots._output_dir()
    assert default.name == "figures"
    assert default.parent.name == "output"
    # it must sit inside this package, not the caller's cwd
    assert (default.parent.parent / "src" / "the_living_daylights").is_dir()


def test_render_overwatch_figure_none_best(tmp_path) -> None:
    """Regression (V4): the no-visible-nest arm needs an injection point.

    On the shipped grid at least one candidate sees the site, so without an
    injectable ``solution=`` the ``best is None`` branch of
    :func:`render_overwatch_figure` was unreachable in test (and uncovered).
    """
    from the_living_daylights.compute_mission import mission_solution

    sol = mission_solution()
    sol["overwatch"] = {
        **sol["overwatch"],
        "best_cell": None,
        "best_score": 0.0,
        "best_distance_m": 0.0,
        "best_cover": 0.0,
        "best_elevation_gain_m": 0.0,
        "best_visible": False,
        "top_three": (),
    }
    path = render_overwatch_figure(tmp_path, solution=sol)
    assert path.exists()
    assert path.stat().st_size > 0
