"""Real-data tests for :mod:`the_living_daylights.compute_mission`."""

from __future__ import annotations

from the_living_daylights.compute_mission import input_hash, mission_solution


def test_mission_solution_keys() -> None:
    sol = mission_solution()
    for key in ("ballistics", "rules_of_engagement", "cello_case", "defection", "terrain"):
        assert key in sol
    assert sol["cello_case"]["fits"] is True
    assert sol["defection"]["plan_verdict"] == "conditional"
    assert sol["defection"]["gate_stage"] == "verify"


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
    base = float(mission_solution(cover_weight=1.0)["terrain"]["mean_cover"])
    covered = float(mission_solution(cover_weight=8.0)["terrain"]["mean_cover"])
    assert covered >= base
