"""SNIPER'S NEST — countersniper operations.

Detection and localization of a hostile sniper, deterministic:

* **optic-glint detection** — a radiometric model of a lens reflecting
  sunlight: a geometric brightness factor (sun elevation + specular azimuth
  alignment), the glint's contrast against sky radiance, its angular size at
  the observer (which shrinks with range^2), and a signal-detection
  probability (normal CDF over SNR);
* **acoustic crack-bang ranging** — the classic flash-to-bang delay scaled by
  the speed of sound (``c(T) = 331.3 + 0.606*T``);
* **bearing triangulation** — least-squares intersection of true-azimuth
  bearings from multiple observer positions to localize the hostile position.

Pure, infrastructure-free, deterministic (stdlib math only).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

__all__ = [
    "SOLAR_IRRADIANCE_W_M2",
    "crack_bang_delay",
    "crack_bang_range",
    "glint_angular_fraction",
    "glint_contrast",
    "glint_detection_probability",
    "glint_geometry_factor",
    "glint_snr",
    "normal_cdf",
    "speed_of_sound",
    "triangulate_position",
]

#: Reference solar irradiance at the lens, W/m^2 (AM1.5-style reference).
SOLAR_IRRADIANCE_W_M2 = 1000.0

#: Sky radiance used as the glint's background, W/(m^2 sr) (daylight sky).
_SKY_RADIANCE_W_M2_SR = 10.0


def normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function (scalar, erf-based)."""
    return float(0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))


def glint_geometry_factor(
    sun_elevation_deg: float,
    azimuth_delta_deg: float,
    specular_half_width_deg: float = 3.0,
) -> float:
    """Geometric brightness of a lens glint in ``[0, 1]``.

    Two deterministic terms: a sine falloff with sun elevation (a higher sun
    illuminates the lens with more direct irradiance ``sin(elevation)``) and a
    specular falloff with the azimuth misalignment between the sun's reflected
    direction and the observer, modeled as ``exp(-(delta/half_width)^2)``.
    """
    if not (specular_half_width_deg > 0):
        raise ValueError("specular_half_width_deg must be positive")
    vertical = max(0.0, math.sin(math.radians(sun_elevation_deg)))
    specular = math.exp(-((azimuth_delta_deg / specular_half_width_deg) ** 2))
    return float(vertical * specular)


def glint_angular_fraction(
    aperture_mm: float,
    range_m: float,
    *,
    resolution_mrad: float = 1.0,
) -> float:
    """The lens's angular size relative to one resolution cell, in ``[0, 1]``.

    A glint at range ``R`` subtends the lens solid angle ``A_lens / R^2``; the
    observer's eye/optics blur it across a resolution cell of
    ``pi * (res_mrad/2)^2``. The fraction caps at 1 (the lens fills the cell —
    SNR saturates at the full contrast).
    """
    if not (aperture_mm > 0):
        raise ValueError("aperture_mm must be positive")
    if not (range_m > 0):
        raise ValueError("range_m must be positive")
    if not (resolution_mrad > 0):
        raise ValueError("resolution_mrad must be positive")
    lens_area = math.pi * (aperture_mm * 1e-3 / 2.0) ** 2
    resolution_sr = math.pi * (resolution_mrad * 1e-3 / 2.0) ** 2
    fraction = lens_area / (range_m * range_m * resolution_sr)
    return float(min(1.0, fraction))


def glint_contrast(
    brightness_factor: float,
    *,
    reflectivity: float = 0.35,
    spread_half_angle_deg: float = 3.0,
    solar_irradiance_w_m2: float = SOLAR_IRRADIANCE_W_M2,
    sky_radiance_w_m2_sr: float = _SKY_RADIANCE_W_M2_SR,
) -> float:
    """Range-independent glint-to-sky contrast (lens irradiance / sky).

    The lens collects ``I_sun * A * rho * g`` and reflects it into a cone of
    solid angle ``Omega = 2*pi*(1 - cos(half_angle))``; the contrast is the
    reflected radiance divided by the sky radiance. Range cancels — glints are
    visible at long range because they are point sources against the sky.
    """
    if not (0.0 <= brightness_factor <= 1.0):
        raise ValueError("brightness_factor must be in [0, 1]")
    if not (0.0 < reflectivity <= 1.0):
        raise ValueError("reflectivity must be in (0, 1]")
    if not (spread_half_angle_deg > 0):
        raise ValueError("spread_half_angle_deg must be positive")
    if solar_irradiance_w_m2 <= 0 or sky_radiance_w_m2_sr <= 0:
        raise ValueError("irradiance and sky radiance must be positive")
    spread_sr = 2.0 * math.pi * (1.0 - math.cos(math.radians(spread_half_angle_deg)))
    reflected_radiance = solar_irradiance_w_m2 * reflectivity * brightness_factor / spread_sr
    return float(reflected_radiance / sky_radiance_w_m2_sr)


def glint_snr(
    range_m: float,
    aperture_mm: float,
    brightness_factor: float,
    *,
    resolution_mrad: float = 1.0,
    reflectivity: float = 0.35,
) -> float:
    """Detection SNR of the optic glint: ``contrast * angular_fraction``.

    The angular-fraction term makes SNR fall as ``1/range^2`` once the lens
    no longer fills a resolution cell, so near-field glints are bright and
    far-field glints fade — the gradient a countersniper search exploits.
    """
    contrast = glint_contrast(brightness_factor, reflectivity=reflectivity)
    fraction = glint_angular_fraction(aperture_mm, range_m, resolution_mrad=resolution_mrad)
    return float(contrast * fraction)


def glint_detection_probability(
    snr: float,
    *,
    detection_threshold: float = 10.0,
    sigma: float = 3.0,
) -> float:
    """Probability of detecting a glint given its SNR (signal-detection CDF).

    ``P_det = Phi((SNR - threshold) / sigma)`` — the classic detection model;
    monotone increasing in SNR, monotone decreasing in range.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    return float(normal_cdf((snr - detection_threshold) / sigma))


def speed_of_sound(temp_c: float) -> float:
    """Speed of sound (m/s) in air at temperature ``temp_c`` (deg C)."""
    return 331.3 + 0.606 * temp_c


def crack_bang_delay(range_m: float, temp_c: float) -> float:
    """Flash-to-bang delay (s) for a shot at ``range_m``.

    The shooter's muzzle flash arrives at light speed; the report arrives at
    the speed of sound, so the delay is ``range / c(T)``.
    """
    if not (range_m > 0):
        raise ValueError("range_m must be positive")
    return float(range_m / speed_of_sound(temp_c))


def crack_bang_range(delay_s: float, temp_c: float) -> float:
    """Range (m) to the shooter from a measured flash-to-bang delay."""
    if delay_s < 0:
        raise ValueError("delay_s must be non-negative")
    return float(delay_s * speed_of_sound(temp_c))


def triangulate_position(
    observers: Sequence[tuple[float, float]],
    bearings_deg: Sequence[float],
) -> tuple[float, float, float]:
    """Least-squares intersection of true-azimuth bearings (x, y, residual).

    Each bearing defines a line through its observer; the hostile position is
    the point minimizing the sum of squared perpendicular distances. Solves
    the 2x2 normal equations in closed form. Bearings are true azimuths in
    degrees clockwise from north; coordinates are in consistent units (m).

    Raises:
        ValueError: if fewer than two observers, the bearings are
            parallel/collinear (singular normal matrix), or any observer
            coordinate or bearing is NaN/inf (a non-finite input would
            otherwise propagate silently into a NaN "fix").
    """
    n = len(observers)
    if n < 2:
        raise ValueError("triangulation requires at least two observers")
    if n != len(bearings_deg):
        raise ValueError("observers and bearings must be same length")
    # A NaN/inf coordinate or bearing must fail loudly: with finite inputs the
    # normal matrix is finite, so this single guard roots out NaN propagation.
    for (x_i, y_i), theta in zip(observers, bearings_deg, strict=True):
        if not (math.isfinite(x_i) and math.isfinite(y_i) and math.isfinite(theta)):
            raise ValueError("triangulation inputs must be finite (reject NaN/inf)")

    a11 = 0.0
    a12 = 0.0
    a22 = 0.0
    b1 = 0.0
    b2 = 0.0
    for (x_i, y_i), theta in zip(observers, bearings_deg, strict=True):
        theta_rad = math.radians(theta)
        ux = math.sin(theta_rad)  # east component of the bearing direction
        uy = math.cos(theta_rad)  # north component
        a_i = (-uy, ux)
        rhs = ux * y_i - uy * x_i
        a11 += a_i[0] * a_i[0]
        a12 += a_i[0] * a_i[1]
        a22 += a_i[1] * a_i[1]
        b1 += a_i[0] * rhs
        b2 += a_i[1] * rhs

    det = a11 * a22 - a12 * a12
    if abs(det) < 1e-12:
        raise ValueError("bearings are parallel or collinear — no unique intersection")

    x = (b1 * a22 - a12 * b2) / det
    y = (a11 * b2 - a12 * b1) / det

    residuals: list[float] = []
    for (x_i, y_i), theta in zip(observers, bearings_deg, strict=True):
        theta_rad = math.radians(theta)
        ux = math.sin(theta_rad)
        uy = math.cos(theta_rad)
        perp = abs(ux * (y - y_i) - uy * (x - x_i))
        residuals.append(perp)
    residual = math.sqrt(sum(r * r for r in residuals) / n)
    return float(x), float(y), float(residual)
