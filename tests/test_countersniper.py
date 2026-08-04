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
