"""Real-data tests for :mod:`the_living_daylights.countersniper`."""

from __future__ import annotations

import math

import pytest

from the_living_daylights import countersniper as cs


def test_normal_cdf_reference_values() -> None:
    assert math.isclose(cs.normal_cdf(0.0), 0.5)
    assert math.isclose(cs.normal_cdf(1.96), 0.975, rel_tol=1e-2)
    assert math.isclose(cs.normal_cdf(-1.96), 0.025, rel_tol=1e-2)


def test_glint_geometry_factor() -> None:
    # peak at specular alignment with a high sun
    assert math.isclose(cs.glint_geometry_factor(90.0, 0.0), 1.0)
    # falloff with azimuth misalignment and with lower sun
    aligned = cs.glint_geometry_factor(35.0, 0.0)
    offset = cs.glint_geometry_factor(35.0, 6.0)
    low_sun = cs.glint_geometry_factor(10.0, 0.0)
    assert offset < aligned
    assert low_sun < aligned
    with pytest.raises(ValueError):
        cs.glint_geometry_factor(35.0, 0.0, specular_half_width_deg=0.0)


def test_glint_angular_fraction() -> None:
    # a large nearby lens fills the resolution cell -> capped at 1
    assert math.isclose(cs.glint_angular_fraction(50.0, 1.0), 1.0)
    near = cs.glint_angular_fraction(50.0, 300.0)
    far = cs.glint_angular_fraction(50.0, 1500.0)
    assert near > far > 0.0
    with pytest.raises(ValueError):
        cs.glint_angular_fraction(0.0, 300.0)
    with pytest.raises(ValueError):
        cs.glint_angular_fraction(50.0, 0.0)
    with pytest.raises(ValueError):
        cs.glint_angular_fraction(50.0, 300.0, resolution_mrad=0.0)


def test_glint_contrast() -> None:
    assert cs.glint_contrast(0.0) == 0.0
    assert cs.glint_contrast(1.0) > cs.glint_contrast(0.5)
    with pytest.raises(ValueError):
        cs.glint_contrast(1.5)
    with pytest.raises(ValueError):
        cs.glint_contrast(0.5, reflectivity=0.0)
    with pytest.raises(ValueError):
        cs.glint_contrast(0.5, spread_half_angle_deg=0.0)
    with pytest.raises(ValueError):
        cs.glint_contrast(0.5, solar_irradiance_w_m2=0.0)


def test_glint_snr_range_gradient() -> None:
    geo = cs.glint_geometry_factor(35.0, 2.0)
    near = cs.glint_snr(300.0, 50.0, geo)
    mid = cs.glint_snr(800.0, 50.0, geo)
    far = cs.glint_snr(1500.0, 50.0, geo)
    assert near > mid > far > 0.0
    # larger aperture brightens the glint
    big = cs.glint_snr(800.0, 60.0, geo)
    assert big > mid


def test_glint_detection_probability() -> None:
    assert cs.glint_detection_probability(100.0) > 0.999
    assert cs.glint_detection_probability(0.0) < 0.001
    assert math.isclose(cs.glint_detection_probability(10.0), 0.5, rel_tol=1e-2)
    with pytest.raises(ValueError):
        cs.glint_detection_probability(5.0, sigma=0.0)


def test_speed_of_sound_and_crack_bang() -> None:
    assert math.isclose(cs.speed_of_sound(0.0), 331.3)
    assert math.isclose(cs.speed_of_sound(20.0), 343.4, rel_tol=1e-3)
    delay = cs.crack_bang_delay(686.8, 20.0)
    assert math.isclose(delay, 2.0, rel_tol=1e-2)
    assert math.isclose(cs.crack_bang_range(2.0, 20.0), 686.8, rel_tol=1e-3)
    with pytest.raises(ValueError):
        cs.crack_bang_delay(0.0, 20.0)
    with pytest.raises(ValueError):
        cs.crack_bang_range(-1.0, 20.0)


def test_triangulate_position_exact_intersection() -> None:
    x, y, residual = cs.triangulate_position([(0.0, 0.0), (100.0, 0.0)], [45.0, 135.0])
    assert math.isclose(x, 50.0, abs_tol=1e-6)
    assert math.isclose(y, 50.0, abs_tol=1e-6)
    assert residual < 1e-6


def test_two_bearing_residual_is_zero_by_construction_not_measured() -> None:
    """Documents a limitation rather than claiming a result.

    Two non-parallel bearings are two equations in two unknowns: the fit passes
    exactly through the intersection, so the residual is identically zero for
    *every* such pair. A near-zero residual from a two-observer fix therefore
    says nothing about localization accuracy — it is arithmetic, not evidence.
    The mission's own configuration
    (``settings.TRIANGULATION_OBSERVERS``) is one of these cases.
    """
    exactly_determined = [
        ([(0.0, 0.0), (100.0, 0.0)], [45.0, 135.0]),
        ([(0.0, 0.0), (500.0, 250.0)], [30.0, 300.0]),
        ([(-40.0, 10.0), (60.0, -80.0)], [5.0, 95.0]),
        ([(12.0, 34.0), (-56.0, 78.0)], [170.0, 20.0]),
    ]
    for observers, bearings in exactly_determined:
        _x, _y, residual = cs.triangulate_position(observers, bearings)
        assert residual < 1e-9, (observers, bearings, residual)


def test_over_determined_bearings_produce_a_real_nonzero_residual() -> None:
    """Positive control: the residual code path can report a large number.

    Three mutually inconsistent bearings — ``y = x`` (from the origin at 45°),
    ``x + y = 100`` (from (100, 0) at 135°), and ``y = 100`` (from (0, 100) due
    east) — meet pairwise but never all at once. Minimising the summed squared
    perpendicular distance gives, by hand:

        f(x, y) = (x-y)^2/2 + (x+y-100)^2/2 + (y-100)^2
        df/dx = 2x - 100 = 0            ->  x = 50
        df/dy = 4y - 300 = 0            ->  y = 75
        perpendicular distances         =  25/sqrt(2), 25/sqrt(2), 25
        RMS residual                    =  sqrt(1250/3) = 20.4124 m

    Both the fitted point and the residual are pinned to that closed form, so
    a wrong normal-equation solve or a wrong residual norm shows up here.
    """
    observers = [(0.0, 0.0), (100.0, 0.0), (0.0, 100.0)]
    bearings = [45.0, 135.0, 90.0]
    x, y, residual = cs.triangulate_position(observers, bearings)
    assert x == pytest.approx(50.0, abs=1e-9)
    assert y == pytest.approx(75.0, abs=1e-9)
    assert residual == pytest.approx(math.sqrt(1250.0 / 3.0), abs=1e-9)
    assert residual > 20.0  # unmistakably not float noise


def test_triangulate_position_three_observers() -> None:
    observers = [(0.0, 0.0), (100.0, 0.0), (0.0, 100.0)]
    bearings = [45.0, 135.0, 135.0]  # all three lines meet exactly at (50,50)
    x, y, residual = cs.triangulate_position(observers, bearings)
    assert math.isclose(x, 50.0, abs_tol=1e-6)
    assert math.isclose(y, 50.0, abs_tol=1e-6)
    assert residual < 1e-6


def test_triangulate_position_errors() -> None:
    with pytest.raises(ValueError):
        cs.triangulate_position([(0.0, 0.0)], [45.0])  # one observer
    with pytest.raises(ValueError):
        cs.triangulate_position([(0.0, 0.0), (1.0, 0.0)], [45.0])  # length mismatch
    with pytest.raises(ValueError):
        cs.triangulate_position([(0.0, 0.0), (100.0, 0.0)], [45.0, 45.0])  # parallel


def test_triangulate_position_rejects_non_finite_inputs() -> None:
    """Regression: NaN/inf propagated silently into a NaN "fix".

    A NaN bearing or an inf observer coordinate previously flowed through the
    normal equations and returned ``(nan, nan, nan)`` with no error — a
    fail-open on a detection/localization path. It must reject loudly.
    """
    with pytest.raises(ValueError):
        cs.triangulate_position(((0.0, 0.0), (100.0, 0.0)), (float("nan"), 135.0))
    with pytest.raises(ValueError):
        cs.triangulate_position(((0.0, 0.0), (float("inf"), 0.0)), (45.0, 135.0))
    with pytest.raises(ValueError):
        cs.triangulate_position(((0.0, 0.0), (100.0, 0.0)), (45.0, float("-inf")))
    # the valid case still yields a finite fix and residual
    x, y, res = cs.triangulate_position(((0.0, 0.0), (100.0, 0.0)), (45.0, 135.0))
    assert math.isfinite(x) and math.isfinite(y) and math.isfinite(res)
