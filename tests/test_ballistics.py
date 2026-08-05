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


def test_cello_layout_binds_each_part_to_its_own_slot() -> None:
    """Each named slot must be exactly as long as the part it is named for.

    Regression guard: the packer processes parts width-descending, so a layout
    built by re-zipping placements against the caller's input order silently
    swaps slots between parts of different lengths.
    """
    parts = b.disassemble_takedown_rifle()
    case = b.CelloCase(1.30, 0.45, 0.24)
    fits, layout = b.pack_cello_case(parts, case)
    assert fits
    placements = layout["parts"]
    assert isinstance(placements, dict)
    assert set(placements) == {p.name for p in parts}
    by_name = {p.name: p for p in parts}
    for name, slot in placements.items():
        assert isinstance(slot, dict)
        span = float(slot["end_m"]) - float(slot["start_m"])
        assert span == pytest.approx(by_name[name].length_m)
        assert float(slot["end_m"]) <= case.interior_length_m + 1e-9
    # slots sharing a lane must not overlap
    lanes: dict[int, list[tuple[float, float]]] = {}
    for slot in placements.values():
        assert isinstance(slot, dict)
        lanes.setdefault(int(slot["lane"]), []).append(
            (float(slot["start_m"]), float(slot["end_m"]))
        )
    for spans in lanes.values():
        spans.sort()
        for (_s0, e0), (s1, _e1) in zip(spans, spans[1:], strict=False):
            assert e0 <= s1 + 1e-9
    # the packed length is the longest lane's filled length
    assert float(layout["packed_length_m"]) == pytest.approx(
        max(end for spans in lanes.values() for _start, end in spans)
    )


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


def test_sample_at_boundaries() -> None:
    """Interpolation clamps below the first sample and on a zero-width span."""
    xs = [0.0, 10.0, 10.0, 20.0]
    ys = [1.0, 2.0, 3.0, 4.0]
    # a target at or before the first sample returns the first value
    assert b._sample_at(xs, ys, -5.0) == 1.0
    assert b._sample_at(xs, ys, 0.0) == 1.0
    # a degenerate (x1 == x0) span returns the later value rather than dividing by zero
    assert b._sample_at([0.0, 10.0, 10.0], [1.0, 2.0, 3.0], 10.0) == 2.0
    assert b._sample_at([0.0, 10.0, 10.0], [1.0, 2.0, 3.0], 10.000001) == 3.0
    # past the last sample returns the last value
    assert b._sample_at(xs, ys, 99.0) == 4.0


def test_deriv_at_rest_is_free_fall() -> None:
    """With zero relative airspeed the drag term vanishes and gravity remains."""
    out = b._deriv(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1e-4, 0.0)
    assert out == (0.0, 0.0, 0.0, 0.0, -b.G, 0.0)


def test_time_of_flight_validation() -> None:
    with pytest.raises(ValueError):
        b.time_of_flight(300.0, 0.0)
    with pytest.raises(ValueError):
        b.time_of_flight(300.0, -790.0)


def test_zero_scope_lower_bound_already_overshoots() -> None:
    """When even the lowest allowed elevation lands high, the bracket clamps low."""
    elev = b.zero_scope(V0, 100.0, 0.07, projectile=PROJ, elevation_bounds=(5.0, 12.0))
    assert elev == pytest.approx(5.0)


def test_zero_scope_exhausts_bisection_budget() -> None:
    """A zero tolerance runs the full fixed iteration budget and still converges."""
    tight = b.zero_scope(V0, 300.0, 0.07, projectile=PROJ, tolerance_mrad=0.0)
    normal = b.zero_scope(V0, 300.0, 0.07, projectile=PROJ)
    assert tight == pytest.approx(normal, abs=1e-3)


def test_capture_zero_validation_and_degenerate_crossings() -> None:
    with pytest.raises(ValueError):
        b.capture_zero(1.0, V0, 0.0, 0.07, projectile=PROJ)
    # a level shot against a far-away sight line never crosses it: no crossings
    near, far = b.capture_zero(0.0, V0, 10000.0, 0.07, projectile=PROJ)
    assert (near, far) == (0.0, 10000.0)
    # a bore-height sight line is crossed exactly once, on the way down
    single_near, single_far = b.capture_zero(1.5, V0, 400.0, 0.0, projectile=PROJ)
    assert single_near > 0.0
    assert single_far == 400.0


def test_fits_in_rejects_oversize_cross_section() -> None:
    case = b.CelloCase(1.30, 0.45, 0.24)
    assert b._fits_in(b.RiflePart("ok", 0.5, 0.1, 0.1), case)
    assert not b._fits_in(b.RiflePart("too_long", 2.0, 0.1, 0.1), case)
    assert not b._fits_in(b.RiflePart("too_wide", 0.5, 0.9, 0.1), case)
    assert not b._fits_in(b.RiflePart("too_thick", 0.5, 0.1, 0.9), case)


def test_shelf_pack_runs_out_of_width() -> None:
    """Parts that individually fit can still overflow the case across lanes."""
    case = b.CelloCase(0.60, 0.30, 0.20)
    # each 0.5 m x 0.11 m part needs its own lane; three lanes exceed 0.30 m
    parts = tuple(b.RiflePart(f"rod_{i}", 0.50, 0.11, 0.05) for i in range(3))
    fits, layout = b.pack_cello_case(parts, case)
    assert fits is False
    assert layout["reason"]
