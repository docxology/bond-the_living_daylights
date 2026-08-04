"""SNIPER'S NEST — countersniper scope optics.

Rifle-scope geometry and ranging math for the covering sniper:

* **click-value conversions** between minute-of-angle (MOA) and milliradian
  (mrad) turret units, and the click count to apply a given angular
  correction (`clicks_for_angle` / `angle_from_clicks`);
* **mil-dot reticle ranging** — the milliradian relation
  ``range = size_m * 1000 / mils`` and its inverse, plus reticle holdover in
  mils from the ballistic drop;
* **first-order parallax** — the sight-line shift when the target range
  differs from the scope's parallax-focus range;
* **field of view** — true FOV from magnification and apparent FOV.

Pure, infrastructure-free, deterministic (stdlib math only).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "APPARENT_FOV_DEG",
    "MOA_TO_MRAD",
    "MRAD_TO_MOA",
    "ScopeSpec",
    "angle_from_clicks",
    "click_value_mrad",
    "clicks_for_angle",
    "field_of_view_m",
    "holdover_mils",
    "mil_dot_range",
    "mils_for_size",
    "moa_to_mrad",
    "mrad_to_moa",
    "parallax_shift_m",
    "zero_click_schedule",
]

#: One minute of angle expressed in milliradians: 1/60 degree * 1000 mrad/rad.
MOA_TO_MRAD = (1.0 / 60.0) * math.pi / 180.0 * 1000.0
#: Inverse conversion: milliradians to MOA.
MRAD_TO_MOA = 1.0 / MOA_TO_MRAD

#: Default apparent field of view (degrees) for a riflescope eyepiece.
APPARENT_FOV_DEG = 60.0


@dataclass(frozen=True)
class ScopeSpec:
    """A riflescope's fixed optical and turret parameters."""

    magnification: float
    objective_diameter_mm: float
    click_unit: str = "mrad"  # "moa" | "mrad"
    click_size: float = 0.1  # value of one click in ``click_unit``
    clicks_per_rev: int = 120  # clicks per full turret revolution
    reticle: str = "mil-dot"

    def __post_init__(self) -> None:
        if not (self.magnification >= 1.0):
            raise ValueError("ScopeSpec.magnification must be >= 1")
        if not (self.objective_diameter_mm > 0):
            raise ValueError("ScopeSpec.objective_diameter_mm must be positive")
        if self.click_unit not in ("moa", "mrad"):
            raise ValueError("ScopeSpec.click_unit must be 'moa' or 'mrad'")
        if not (self.click_size > 0):
            raise ValueError("ScopeSpec.click_size must be positive")
        if self.clicks_per_rev <= 0:
            raise ValueError("ScopeSpec.clicks_per_rev must be positive")
        if not self.reticle.strip():
            raise ValueError("ScopeSpec.reticle must be a non-empty string")


def moa_to_mrad(moa: float) -> float:
    """Convert minutes of angle to milliradians."""
    return moa * MOA_TO_MRAD


def mrad_to_moa(mrad: float) -> float:
    """Convert milliradians to minutes of angle."""
    return mrad * MRAD_TO_MOA


def click_value_mrad(spec: ScopeSpec) -> float:
    """The angular size of one turret click, expressed in milliradians."""
    if spec.click_unit == "mrad":
        return spec.click_size
    return moa_to_mrad(spec.click_size)


def clicks_for_angle(spec: ScopeSpec, angle_mrad: float) -> int:
    """Turret clicks needed to apply an angular correction in milliradians.

    Rounded to the nearest whole click — a turret cannot dial fractional
    clicks. Deterministic given the spec and correction.
    """
    value = click_value_mrad(spec)
    return int(round(angle_mrad / value))


def angle_from_clicks(spec: ScopeSpec, clicks: int) -> float:
    """The angular correction (milliradians) dialed by ``clicks`` clicks."""
    return clicks * click_value_mrad(spec)


def mil_dot_range(target_size_m: float, mils: float) -> float:
    """Range (m) from a mil-dot reading: ``size_m * 1000 / mils``.

    The milliradian relation: one mil subtends 1 m at 1000 m, so a target of
    height ``target_size_m`` spanning ``mils`` on the reticle sits at that
    range. Raises on non-positive mils.
    """
    if not (mils > 0):
        raise ValueError("mil reading must be positive")
    return target_size_m * 1000.0 / mils


def mils_for_size(target_size_m: float, range_m: float) -> float:
    """Reticle span (mils) of a target of size ``target_size_m`` at range."""
    if not (range_m > 0):
        raise ValueError("range must be positive")
    return target_size_m * 1000.0 / range_m


def holdover_mils(drop_m: float, range_m: float) -> float:
    """Reticle holdover in mils that cancels a ballistic drop at range.

    ``holdover = drop / range * 1000`` — the angular equivalent of the drop.
    """
    if not (range_m > 0):
        raise ValueError("range must be positive")
    return drop_m / range_m * 1000.0


def parallax_shift_m(eye_offset_m: float, range_m: float, focus_range_m: float) -> float:
    """First-order parallax sight shift (m) at target range.

    A scope focused at ``focus_range_m`` forms the reticle image conjugate to
    that object plane; at any other range the sight line through the reticle
    center shifts by ``eye_offset * (range/focus - 1)``. Zero at the focus
    range, monotone away from it.
    """
    if not (range_m > 0):
        raise ValueError("range must be positive")
    if not (focus_range_m > 0):
        raise ValueError("focus_range_m must be positive")
    return eye_offset_m * (range_m / focus_range_m - 1.0)


def field_of_view_m(
    spec: ScopeSpec, range_m: float, apparent_fov_deg: float = APPARENT_FOV_DEG
) -> float:
    """True field-of-view width (m) at range for a scope's apparent FOV.

    ``true_fov = apparent_fov / magnification``; the width is the chord
    ``2 * range * tan(true_fov / 2)``.
    """
    if not (range_m > 0):
        raise ValueError("range must be positive")
    if not (0 < apparent_fov_deg < 180):
        raise ValueError("apparent_fov_deg must be in (0, 180)")
    true_fov_rad = math.radians(apparent_fov_deg) / spec.magnification
    return float(2.0 * range_m * math.tan(true_fov_rad / 2.0))


def zero_click_schedule(
    spec: ScopeSpec, elevation_mrad: float, wind_hold_mrad: float
) -> dict[str, int]:
    """Turret clicks to dial a ballistic solution onto the scope.

    Combines the zero elevation and the wind hold (see
    :mod:`the_living_daylights.ballistics`) into elevation/wind click counts.
    """
    return {
        "elevation_clicks": clicks_for_angle(spec, elevation_mrad),
        "wind_clicks": clicks_for_angle(spec, wind_hold_mrad),
    }
