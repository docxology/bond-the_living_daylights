"""Real-data tests for :mod:`the_living_daylights.compute_mission`."""

from __future__ import annotations

import pytest

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
