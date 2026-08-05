"""Real-data tests for :mod:`the_living_daylights.compute_mission`."""

from __future__ import annotations

import pytest

from the_living_daylights import settings, terrain_ops, visibility
from the_living_daylights.compute_mission import input_hash, mission_solution


def test_mission_solution_keys() -> None:
    sol = mission_solution()
    for key in (
        "ballistics",
        "rules_of_engagement",
        "optics",
        "countersniper",
        "cello_case",
        "defection",
        "verification",
        "terrain",
        "overwatch",
    ):
        assert key in sol
    assert sol["cello_case"]["fits"] is True
    assert sol["defection"]["plan_verdict"] == "conditional"
    assert sol["defection"]["gate_stage"] == "verify"
    assert sol["verification"]["verdict"] == "conditional"


def test_mission_solution_new_concept_values() -> None:
    sol = mission_solution()
    assert sol["optics"]["mil_dot_range_m"] == pytest.approx(300.0)
    assert sol["optics"]["elevation_clicks"] > 0
    assert 0.0 < float(sol["countersniper"]["glint_detection_probability"]) < 1.0
    assert sol["overwatch"]["best_cell"] is not None
    assert sol["overwatch"]["visible_candidates"] >= 1
    assert sol["countersniper"]["crack_bang_range_m"] == pytest.approx(686.8, abs=1.0)


def test_mission_solution_deterministic() -> None:
    assert mission_solution() == mission_solution()


def test_input_hash_deterministic_and_hex() -> None:
    assert input_hash() == input_hash()
    assert len(input_hash()) == 64


def test_wind_sensitivity() -> None:
    calm = float(mission_solution(wind_mps=0.0)["ballistics"]["wind_drift_m"])
    breezy = float(mission_solution(wind_mps=5.0)["ballistics"]["wind_drift_m"])
    assert abs(breezy) > abs(calm)


def test_reported_overwatch_nest_can_see_the_site() -> None:
    """The nest the mission reports must be visible, not merely top-scored.

    ``rank_overwatch_positions`` scores blind candidates too (they keep the
    proximity, cover, and elevation terms), so ``ranked[0]`` carries no
    visibility guarantee. The solution goes through ``best_overwatch``.

    **This test is currently weaker than it looks, and that is stated rather
    than hidden.** On the shipped seed the 0.40 visibility weight dominates and
    the top-scored candidate happens to *be* the visible one at every candidate
    step from 1 to 8, so reverting ``compute_mission`` to ``ranked[0]`` would
    not turn this red — the code fix removes a latent defect without moving any
    reported number. The falsifiable proof that the two selections can differ
    lives in ``test_visibility.test_best_overwatch_skips_a_blind_top_scorer``,
    which constructs the disagreeing grid directly. What this test does bind is
    the invariant (the reported nest sees the site) and the policy identity
    below, both of which fire if the terrain, seed, or weights ever change.
    """
    sol = mission_solution()
    ow = sol["overwatch"]
    assert ow["best_cell"] is not None
    assert ow["best_visible"] is True
    if not ow["top_scored_is_visible"]:
        assert ow["best_cell"] != ow["top_scored_cell"]

    # policy identity: the reported nest is the first VISIBLE cell in ranking
    # order, recomputed here rather than read back from the solution.
    grid = terrain_ops.generate_terrain(
        settings.TERRAIN_N, settings.TERRAIN_SEED, settings.TERRAIN_CELL_SIZE_M
    )
    target = tuple(int(v) for v in ow["target_cell"])
    candidates = tuple(
        (r, c)
        for r in range(0, grid.n, settings.OVERWATCH_CANDIDATE_STEP)
        for c in range(0, grid.n, settings.OVERWATCH_CANDIDATE_STEP)
        if (r, c) != target
    )
    expected = visibility.best_overwatch(
        grid,
        target,  # type: ignore[arg-type]
        candidates,
        eye_height_m=settings.OVERWATCH_EYE_HEIGHT_M,
        clearance_m=settings.OVERWATCH_CLEARANCE_M,
        max_range_cells=settings.OVERWATCH_MAX_RANGE_CELLS,
    )
    assert expected is not None
    assert ow["best_cell"] == expected.cell
    assert float(ow["best_score"]) == pytest.approx(expected.score)


def test_cover_term_gain_and_field_baseline_are_measured() -> None:
    """Binds the manuscript's honest claim about the cover term.

    Two separate facts, both measured against real baselines:
    1. the exposure term does move the route toward concealment (positive gain
       against the same planner with ``cover_weight=0``); and
    2. the resulting route is nevertheless *below* the grid's own mean
       concealment — it is a mild preference, not a concealment-optimal path.

    If either relation flips, this test goes red and the prose in
    ``manuscript/00_abstract.md`` and ``03_results.md`` must be rewritten.
    """
    ter = mission_solution()["terrain"]
    assert float(ter["cover_term_gain"]) > 0.0
    assert float(ter["mean_cover"]) > float(ter["bare_mean_cover"])
    assert float(ter["cover_vs_field"]) < 0.0
    assert float(ter["mean_cover"]) < float(ter["field_mean_cover"])
    # the gain is small: the blended cost is dominated by traversal and climb
    assert float(ter["cover_term_gain"]) < 0.05
    # and a heavy exposure weight *can* clear the field average, which proves
    # the shortfall above is a weighting choice, not an unreachable ceiling
    heavy = mission_solution(cover_weight=8.0)["terrain"]
    assert float(heavy["mean_cover"]) > float(heavy["field_mean_cover"])


def test_cover_weight_raises_mean_cover() -> None:
    """A heavier exposure penalty must strictly buy concealment.

    Asserted with ``>`` rather than ``>=`` so the check cannot pass if
    ``cover_weight`` stopped reaching the route planner at all.
    """
    base = float(mission_solution(cover_weight=1.0)["terrain"]["mean_cover"])
    covered = float(mission_solution(cover_weight=8.0)["terrain"]["mean_cover"])
    assert covered > base
    assert float(mission_solution(cover_weight=8.0)["terrain"]["route_cost"]) > float(
        mission_solution(cover_weight=1.0)["terrain"]["route_cost"]
    )
