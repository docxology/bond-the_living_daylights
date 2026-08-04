"""Real-data tests for :mod:`the_living_daylights.optics`."""

from __future__ import annotations

import math

import pytest

from the_living_daylights import optics as o

MRAD_SCOPE = o.ScopeSpec(magnification=10.0, objective_diameter_mm=50.0)
MOA_SCOPE = o.ScopeSpec(
    magnification=10.0, objective_diameter_mm=50.0, click_unit="moa", click_size=0.25
)


def test_scope_spec_validation() -> None:
    with pytest.raises(ValueError):
        o.ScopeSpec(0.5, 50.0)
    with pytest.raises(ValueError):
        o.ScopeSpec(10.0, 0.0)
    with pytest.raises(ValueError):
        o.ScopeSpec(10.0, 50.0, click_unit="mil")
    with pytest.raises(ValueError):
        o.ScopeSpec(10.0, 50.0, click_size=0.0)
    with pytest.raises(ValueError):
        o.ScopeSpec(10.0, 50.0, clicks_per_rev=0)
    with pytest.raises(ValueError):
        o.ScopeSpec(10.0, 50.0, reticle="  ")


def test_moa_mrad_conversions_round_trip() -> None:
    assert math.isclose(o.moa_to_mrad(1.0), 0.290888, rel_tol=1e-4)
    assert math.isclose(o.mrad_to_moa(o.moa_to_mrad(7.5)), 7.5)
    assert math.isclose(o.moa_to_mrad(o.mrad_to_moa(3.0)), 3.0)


def test_click_value_per_unit() -> None:
    assert math.isclose(o.click_value_mrad(MRAD_SCOPE), 0.1)
    assert math.isclose(o.click_value_mrad(MOA_SCOPE), o.moa_to_mrad(0.25))


def test_clicks_for_angle_rounding() -> None:
    assert o.clicks_for_angle(MRAD_SCOPE, 2.68) == 27
    assert o.clicks_for_angle(MRAD_SCOPE, -0.63) == -6
    assert o.clicks_for_angle(MOA_SCOPE, o.moa_to_mrad(1.0)) == 4  # 0.25 MOA clicks
    # 0.1 mrad clicks can only resolve whole clicks
    assert math.isclose(o.angle_from_clicks(MRAD_SCOPE, 27), 2.7)


def test_mil_dot_range_and_inverse() -> None:
    assert math.isclose(o.mil_dot_range(1.8, 6.0), 300.0)
    assert math.isclose(o.mils_for_size(1.8, 300.0), 6.0)
    assert math.isclose(o.mils_for_size(2.0, 1000.0), 2.0)  # one mil = 1 m at 1 km
    with pytest.raises(ValueError):
        o.mil_dot_range(1.8, 0.0)
    with pytest.raises(ValueError):
        o.mils_for_size(1.8, -5.0)


def test_holdover_mils() -> None:
    assert math.isclose(o.holdover_mils(-0.804, 300.0), -2.68, rel_tol=1e-2)
    with pytest.raises(ValueError):
        o.holdover_mils(-1.0, 0.0)


def test_parallax_shift() -> None:
    assert o.parallax_shift_m(0.01, 150.0, 150.0) == 0.0  # at focus: no shift
    assert math.isclose(o.parallax_shift_m(0.01, 300.0, 150.0), 0.01)
    assert math.isclose(o.parallax_shift_m(0.01, 75.0, 150.0), -0.005)
    with pytest.raises(ValueError):
        o.parallax_shift_m(0.01, 0.0, 150.0)
    with pytest.raises(ValueError):
        o.parallax_shift_m(0.01, 300.0, 0.0)


def test_field_of_view() -> None:
    width = o.field_of_view_m(MRAD_SCOPE, 300.0)
    # true FOV = 60/10 = 6 deg -> half-width chord = 2*300*tan(3 deg)
    assert math.isclose(width, 2.0 * 300.0 * math.tan(math.radians(3.0)), rel_tol=1e-3)
    with pytest.raises(ValueError):
        o.field_of_view_m(MRAD_SCOPE, 0.0)
    with pytest.raises(ValueError):
        o.field_of_view_m(MRAD_SCOPE, 300.0, apparent_fov_deg=200.0)


def test_zero_click_schedule() -> None:
    schedule = o.zero_click_schedule(MRAD_SCOPE, 2.68, -0.63)
    assert schedule == {"elevation_clicks": 27, "wind_clicks": -6}
    moa_schedule = o.zero_click_schedule(MOA_SCOPE, 2.68, -0.63)
    assert moa_schedule["elevation_clicks"] == o.clicks_for_angle(MOA_SCOPE, 2.68)
