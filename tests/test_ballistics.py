"""Real-data tests for :mod:`the_living_daylights.ballistics`.

Deterministic physics checks: rifle zero, near/far zero capture, windage, the
rules-of-engagement (trigger-guard) decision, and cello-case packing.
"""

from __future__ import annotations

import math

import pytest

from the_living_daylights import ballistics as b

PROJ = b.Projectile(0.0104, 0.00782)
V0 = 790.0


def test_projectile_geometry_and_coefficients() -> None:
    assert PROJ.cross_section_area > 0
    assert PROJ.drag_decay_rate > 0
    assert PROJ.ballistic_coefficient > 900  # 7.62mm/168gr regime
    assert math.isclose(b.ballistic_coefficient(PROJ), PROJ.ballistic_coefficient)
    assert math.isclose(b.drag_factor(PROJ), PROJ.drag_decay_rate)


def test_projectile_validation() -> None:
    bad_cases = [
        dict(mass_kg=0.0, caliber_m=0.00782),
        dict(mass_kg=0.0104, caliber_m=0.0),
        dict(mass_kg=0.0104, caliber_m=0.00782, drag_coefficient=0.0),
        dict(mass_kg=0.0104, caliber_m=0.00782, drag_coefficient=2.5),
        dict(mass_kg=0.0104, caliber_m=0.00782, rho_air=0.0),
    ]
    for kwargs in bad_cases:
        with pytest.raises(ValueError):
            b.Projectile(**kwargs)


def test_standard_atmosphere_density() -> None:
    low = b.standard_atmosphere_density(0.0)
    high = b.standard_atmosphere_density(5000.0)
    assert low > 0
    assert 0 < high < low


def test_trajectory_deterministic_and_shaped() -> None:
    first = b.trajectory(V0, 0.0)
    again = b.trajectory(V0, 0.0)
    assert first == again
    xs, ys, zs, ts = first
    assert len(xs) == len(ys) == len(zs) == len(ts)
    assert xs[0] == 0.0 and ts[0] == 0.0


def test_trajectory_validation() -> None:
    with pytest.raises(ValueError):
        b.trajectory(-1.0, 0.0)
    with pytest.raises(ValueError):
        b.trajectory(V0, 0.0, dt=0.0)


def test_zero_and_capture_physical() -> None:
    elev = b.zero_scope(V0, 300.0, 0.07, projectile=PROJ)
    assert 0 < elev < 5.0
    near, far = b.capture_zero(elev, V0, 300.0, 0.07, projectile=PROJ)
    assert 20 < near < 60
    assert 290 < far < 310
    # the round should land at height ~0 at the far zero
    xs, ys, _z, _t = b.trajectory(V0, elev, projectile=PROJ, max_range=305.0)
    assert abs(b._sample_at(xs, ys, 300.0)) < 0.05


def test_zero_bounds_clamp() -> None:
    # an impossible long zero clamps to the upper elevation bound
    high = b.zero_scope(V0, 4000.0, 0.07, elevation_bounds=(0.0, 12.0))
    assert high >= 12.0 - 1e-6
    # a very short zero needs only a tiny elevation
    low = b.zero_scope(V0, 10.0, 0.20, elevation_bounds=(0.0, 12.0))
    assert 0.0 <= low < 1.0


def test_zero_validation() -> None:
    with pytest.raises(ValueError):
        b.zero_scope(V0, 0.0, 0.07)
    with pytest.raises(ValueError):
        b.zero_scope(V0, 300.0, -1.0)


def test_drop_and_time_of_flight() -> None:
    drop = b.drop_at_range(300.0, V0, projectile=PROJ)
    assert drop < 0.0  # a drop is below the line of departure
    tof = b.time_of_flight(300.0, V0, projectile=PROJ)
    assert 0.2 < tof < 1.0
    with pytest.raises(ValueError):
        b.time_of_flight(-5.0, V0)


def test_wind_drift_and_hold() -> None:
    assert b.wind_drift(300.0, 0.0, V0, projectile=PROJ) == 0.0
    drift = b.wind_drift(300.0, 5.0, V0, projectile=PROJ)
    assert drift > 0.05
    hold = b.wind_hold_mrad(300.0, 5.0, V0, projectile=PROJ)
    assert math.isclose(hold, -drift / 300.0 * 1e3)


def test_engagement_decision_modes() -> None:
    auth = "general_koskov"
    assert (
        b.engagement_decision(
            authorized_target=auth, observed=auth, hostile=True, weapon_present=True
        )[0]
        == "engage_primary"
    )
    assert (
        b.engagement_decision(
            authorized_target=auth, observed=auth, hostile=False, weapon_present=True
        )[0]
        == "hold_fire"
    )
    assert (
        b.engagement_decision(
            authorized_target=auth, observed="sentinel", hostile=True, weapon_present=True
        )[0]
        == "disable_weapon"
    )
    assert (
        b.engagement_decision(
            authorized_target=auth, observed="sentinel", hostile=True, weapon_present=False
        )[0]
        == "hold_fire"
    )
    assert (
        b.engagement_decision(
            authorized_target=auth, observed="cellist", hostile=False, weapon_present=True
        )[0]
        == "hold_fire"
    )
    assert (
        b.engagement_decision(
            authorized_target=auth,
            observed="sentinel",
            hostile=True,
            weapon_present=True,
            allow_weapon_disable=False,
        )[0]
        == "hold_fire"
    )


def test_cello_packing_default_and_negative() -> None:
    parts = b.disassemble_takedown_rifle()
    case = b.CelloCase(1.30, 0.45, 0.24)
    fits, layout = b.pack_cello_case(parts, case)
    assert fits
    assert int(layout["lanes_used"]) >= 1
    assert "parts" in layout and "efficiency" in layout
    # an undersized case cannot hold the rig
    assert not b.pack_cello_case(parts, b.CelloCase(0.3, 0.1, 0.05))[0]
    # an oversized component violates the cross-section
    assert not b.pack_cello_case(list(parts) + [b.RiflePart("tripod", 2.0, 1.0, 1.0)], case)[0]


def test_part_and_case_validation() -> None:
    with pytest.raises(ValueError):
        b.RiflePart("x", 0.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        b.RiflePart("x", 1.0, -1.0, 1.0)
    with pytest.raises(ValueError):
        b.RiflePart("x", 1.0, 1.0, 1.0, mass_kg=-1.0)
    with pytest.raises(ValueError):
        b.CelloCase(-1.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        b.CelloCase(1.0, 0.0, 1.0)


def test_assembly_time() -> None:
    parts = b.disassemble_takedown_rifle()
    assert math.isclose(b.assembly_time(parts), 18.0 * len(parts))
    assert math.isclose(b.assembly_time(parts, seconds_per_part=5.0), 5.0 * len(parts))
    with pytest.raises(ValueError):
        b.assembly_time(parts, seconds_per_part=-1.0)
