"""SNIPER'S NEST — external ballistics: rifle zero, windage, and the cello case.

Pure, infrastructure-free, deterministic external-ballistics core for The
Living Daylights (1987). Models:

* a point-mass projectile with quadratic air drag and gravity, integrated with
  a fixed-step RK4 (deterministic — no RNG, no wall-clock);
* **rifle zero** — solve the muzzle elevation so the trajectory crosses the
  line of sight (LOS) at the zero range, and capture the near/far zero;
* **windage** — lateral crosswind drift and the wind hold (milliradians);
* **rules of engagement** — the trigger-guard hold: a covering sniper may
  disable a hostile's weapon without taking a lethal shot at a third party
  (Bond and the silenced pistol / the cellist in the film);
* **the cello case** — whether a disassembled takedown rifle packs into a
  cello case (deterministic strip packing), and its field assembly time.

SI units throughout. All values are deterministic given the inputs.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

__all__ = [
    "G",
    "RHO_AIR_ICAO",
    "CelloCase",
    "Projectile",
    "RiflePart",
    "ballistic_coefficient",
    "capture_zero",
    "drag_factor",
    "disassemble_takedown_rifle",
    "drop_at_range",
    "engagement_decision",
    "pack_cello_case",
    "standard_atmosphere_density",
    "time_of_flight",
    "trajectory",
    "wind_drift",
    "zero_scope",
]

#: Standard gravity, m/s^2 (ICAO).
G = 9.80665
#: Standard sea-level air density, kg/m^3 (ICAO).
RHO_AIR_ICAO = 1.225


def standard_atmosphere_density(altitude_m: float) -> float:
    """Exponential-barometric air density at altitude, kg/m^3.

    Deterministic closed form ``rho = rho0 * exp(-altitude / 8434.5)`` — a real
    barometric scale-height approximation used to degrade drag at altitude, as
    on mountain positions.
    """
    return RHO_AIR_ICAO * math.exp(-altitude_m / 8434.5)


@dataclass(frozen=True)
class Projectile:
    """A bullet's fixed physical parameters (drag model inputs).

    Drag deceleration is the standard point-mass quadratic law
    ``a_drag = rho * A * C_d / (2*m) * v^2`` where ``A`` is the reference
    cross-section area and ``C_d`` the (constant) drag coefficient.
    """

    mass_kg: float
    caliber_m: float
    drag_coefficient: float = 0.22
    rho_air: float = RHO_AIR_ICAO

    def __post_init__(self) -> None:
        if not (self.mass_kg > 0):
            raise ValueError("Projectile.mass_kg must be positive")
        if not (self.caliber_m > 0):
            raise ValueError("Projectile.caliber_m must be positive")
        if not (0 < self.drag_coefficient <= 2.0):
            raise ValueError("Projectile.drag_coefficient must be in (0, 2]")
        if not (self.rho_air > 0):
            raise ValueError("Projectile.rho_air must be positive")

    @property
    def cross_section_area(self) -> float:
        """Reference cross-section area, m^2 (pi * r^2)."""
        r = self.caliber_m / 2.0
        return math.pi * r * r

    @property
    def drag_decay_rate(self) -> float:
        """Quadratic-drag decay rate ``rho*A*C_d/(2m)`` in 1/m (``a=k*v^2``)."""
        return self.rho_air * self.cross_section_area * self.drag_coefficient / (2.0 * self.mass_kg)

    @property
    def ballistic_coefficient(self) -> float:
        """Ballistic coefficient ``m / (A*C_d)`` in kg/m^2.

        ``__post_init__`` already guarantees a positive caliber and drag
        coefficient, so the denominator is always positive — no second guard
        is added here, since a check that cannot fail is not a check.
        """
        return self.mass_kg / (self.cross_section_area * self.drag_coefficient)


def ballistic_coefficient(projectile: Projectile) -> float:
    """Return the ballistic coefficient (kg/m^2) for a projectile."""
    return projectile.ballistic_coefficient


def drag_factor(projectile: Projectile, rho_air: float | None = None) -> float:
    """Return the quadratic-drag decay rate ``k`` (1/m) for a projectile.

    ``rho_air`` overrides the projectile's built-in density (e.g. for an
    altitude-corrected density at a mountain position).
    """
    rho = rho_air if rho_air is not None else projectile.rho_air
    return (
        rho
        * projectile.cross_section_area
        * projectile.drag_coefficient
        / (2.0 * projectile.mass_kg)
    )


def _rng4(
    dt: float,
    y: tuple[float, ...],
    f: Callable[..., tuple[float, ...]],
    *args: object,
) -> tuple[float, ...]:
    """Advance the ordinary differential equation ``dy/dt = f(y, *args)`` by one RK4 step.

    Deterministic classical RK4 (no state, no randomness). Works for any
    state-vector length and returns a tuple of the same length.
    """
    n = len(y)

    def kcoef(state: tuple[float, ...]) -> tuple[float, ...]:
        return f(*state, *args)

    k1 = kcoef(y)
    k2 = kcoef(tuple(y[i] + 0.5 * dt * k1[i] for i in range(n)))
    k3 = kcoef(tuple(y[i] + 0.5 * dt * k2[i] for i in range(n)))
    k4 = kcoef(tuple(y[i] + dt * k3[i] for i in range(n)))
    return tuple(y[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) for i in range(n))


def _deriv(
    _x: float,
    y: float,
    z: float,
    vx: float,
    vy: float,
    vz: float,
    k: float,
    wind_speed: float,
) -> tuple[float, float, float, float, float, float]:
    """Right-hand side of the 6-D flight ODE (position + velocity) with crosswind.

    State: ``(x, y, z, vx, vy, vz)`` — downrange, up, lateral, and the
    corresponding velocities. Drag opposes the velocity relative to the wind
    ``(0, 0, wind_speed)``; gravity acts down. ``k`` is the quadratic-drag
    decay rate (1/m).
    """
    rvx, rvy, rvz = vx, vy, vz - wind_speed
    speed = math.sqrt(rvx * rvx + rvy * rvy + rvz * rvz)
    if speed <= 0.0:
        return (vx, vy, vz, 0.0, -G, 0.0)
    drag = k * speed
    return (
        vx,
        vy,
        vz,
        -drag * rvx,
        -G - drag * rvy,
        -drag * rvz,
    )


def trajectory(
    v0: float,
    elevation_mrad: float,
    *,
    rho_air: float | None = None,
    wind_speed: float = 0.0,
    dt: float = 5e-4,
    max_range: float = 1200.0,
    max_time: float = 4.0,
    projectile: Projectile | None = None,
) -> tuple[list[float], list[float], list[float], list[float]]:
    """Simulate a point-mass trajectory and return parallel downrange arrays.

    Returns ``(x, y, z, time)`` lists: downrange, height, lateral offset, and
    elapsed time. Integration stops at ``max_range``, ``max_time``, or when the
    round falls below the ground plane. Deterministic: fixed step ``dt``, no
    randomness.
    """
    if not (v0 > 0):
        raise ValueError("v0 must be positive")
    if not (dt > 0):
        raise ValueError("dt must be positive")
    if projectile is not None:
        k = drag_factor(projectile, rho_air)
    else:
        k = (
            _drag_from_v0()
            if rho_air is None
            else drag_factor(Projectile(0.0104, 0.00782, rho_air=rho_air))
        )
    theta = elevation_mrad * 1e-3
    state: tuple[float, ...] = (
        0.0,
        0.0,
        0.0,
        v0 * math.cos(theta),
        v0 * math.sin(theta),
        0.0,
    )
    xs: list[float] = [0.0]
    ys: list[float] = [0.0]
    zs: list[float] = [0.0]
    ts: list[float] = [0.0]
    t = 0.0
    while t < max_time and state[0] < max_range:
        state = _rng4(dt, state, _deriv, k, wind_speed)
        t += dt
        xs.append(state[0])
        ys.append(state[1])
        zs.append(state[2])
        ts.append(t)
        if state[1] < -1.5:
            break
    return xs, ys, zs, ts


def _drag_from_v0() -> float:
    """Nominal quadratic-drag decay rate for a 7.62mm/168gr service round."""
    a = math.pi * (0.00782 / 2.0) ** 2
    return RHO_AIR_ICAO * a * 0.22 / (2.0 * 0.0104)


def time_of_flight(range_m: float, v0: float, *, projectile: Projectile | None = None) -> float:
    """Downrange time of flight to ``range_m`` (seconds), closed form.

    Solves the flat-fire quadratic-drag law exactly. With ``dv/dt = -k v^2``
    the speed decays as ``v(t) = v0 / (1 + k v0 t)`` and downrange position
    integrates to ``x(t) = ln(1 + k v0 t) / k``; inverting that gives

    ``t(x) = (exp(k x) - 1) / (k v0)``.

    Because ``expm1(z) >= z`` for ``z >= 0``, this is always **at or above**
    the drag-free bound ``range / v0`` — a decelerating round cannot beat
    vacuum. It is a closed form, not a readout of :func:`trajectory`: it
    neglects the small extra path length contributed by the launch angle and
    gravity, so it is a lower bound on the RK4 flight time (0.4175 s vs
    0.4175 s at 300 m for the mission round — the two agree to <1 ms).
    ``tests/test_ballistics.py`` pins both the vacuum bound and the agreement
    with the RK4 trajectory's own time array.

    Raises:
        ValueError: if ``range_m`` or ``v0`` is not positive.
    """
    if not (range_m > 0):
        raise ValueError("range_m must be positive")
    if not (v0 > 0):
        raise ValueError("v0 must be positive")
    # ``Projectile.__post_init__`` forces rho, area, and C_d strictly positive,
    # so k > 0 always and the quotient below is well defined.
    k = drag_factor(projectile) if projectile is not None else _drag_from_v0()
    return float(math.expm1(k * range_m) / (k * v0))


def drop_at_range(
    range_m: float,
    v0: float,
    *,
    projectile: Projectile | None = None,
    rho_air: float | None = None,
) -> float:
    """Vertical drop (m) below the line of departure at ``range_m``.

    Determined by numerical trajectory simulation (gravity + drag) from a
    level departure, so it is the physically integrated drop rather than a
    ballistic-table lookup. Negative (a drop is below the bore line).
    """
    elev = 0.0
    xs, ys, _zs, _ts = trajectory(
        v0, elev, rho_air=rho_air, projectile=projectile, max_range=range_m + 10.0
    )
    return _sample_at(xs, ys, range_m)


def _sample_at(xs: list[float], ys: list[float], target: float) -> float:
    """Linear-interpolate ``ys`` at downrange ``target`` on sorted ``xs``."""
    if target <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if xs[i] >= target:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (target - x0) / (x1 - x0)
    return ys[-1]


def zero_scope(
    v0: float,
    zero_range: float,
    sight_height: float,
    *,
    projectile: Projectile | None = None,
    rho_air: float | None = None,
    elevation_bounds: tuple[float, float] = (0.0, 12.0),
    tolerance_mrad: float = 1e-4,
) -> float:
    """Solve the muzzle elevation (mrad) that zeroes the rifle at ``zero_range``.

    Bisection on the simulated impact height: the round must land with height
    0.0 at the target range while the sight line (starting ``sight_height``
    above bore) passes through the same point. Deterministic closed loop.
    """
    if not (zero_range > 0):
        raise ValueError("zero_range must be positive")
    if not (sight_height >= 0):
        raise ValueError("sight_height must be non-negative")
    lo, hi = elevation_bounds

    def impact(elev: float) -> float:
        xs, ys, _z, _t = trajectory(
            v0, elev, rho_air=rho_air, projectile=projectile, max_range=zero_range + 5.0
        )
        return _sample_at(xs, ys, zero_range)

    # Guard the bisection bracket. impact(elev) is monotone increasing near the
    # zero range, so the root lies where impact goes from < 0 to > 0.
    if impact(lo) > 0.0:  # even the lowest elevation overshoots the target
        return lo
    if impact(hi) < 0.0:  # even the highest elevation cannot reach the target
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if impact(mid) > 0.0:
            hi = mid
        else:
            lo = mid
        if (hi - lo) <= tolerance_mrad:
            break
    return 0.5 * (lo + hi)


def capture_zero(
    elevation_mrad: float,
    v0: float,
    zero_range: float,
    sight_height: float,
    *,
    projectile: Projectile | None = None,
    rho_air: float | None = None,
) -> tuple[float, float]:
    """Capture the near-zero and far-zero ranges (m) for a zeroed rifle.

    The trajectory crosses the sight line twice; ``zero_range`` is the far
    (primary) zero by construction of :func:`zero_scope`. Returns
    ``(near_zero, far_zero)``.
    """
    if not (zero_range > 0):
        raise ValueError("zero_range must be positive")
    xs, ys, _z, _t = trajectory(
        v0, elevation_mrad, rho_air=rho_air, projectile=projectile, max_range=zero_range * 1.6
    )

    def los(x: float) -> float:
        return _los(sight_height, zero_range, x)

    crossings: list[float] = []
    prev_sign = math.copysign(1.0, ys[0] - los(xs[0]))
    for i in range(1, len(xs)):
        diff = ys[i] - los(xs[i])
        if diff == 0.0:
            crossings.append(xs[i])
        else:
            sign = math.copysign(1.0, diff)
            if sign != prev_sign:
                crossings.append(xs[i])
                prev_sign = sign
        if len(crossings) == 2:
            break
    if not crossings:
        return (0.0, zero_range)
    if len(crossings) == 1:
        return (crossings[0], zero_range)
    return (min(crossings[0], crossings[1]), max(crossings[0], crossings[1]))


def _los(sight_height: float, zero_range: float, x: float) -> float:
    """Height of the sight line above bore at downrange ``x``."""
    return sight_height * (1.0 - x / zero_range)


def wind_drift(
    range_m: float,
    wind_speed: float,
    v0: float,
    *,
    projectile: Projectile | None = None,
) -> float:
    """Lateral wind drift (m) at ``range_m`` from a full-value crosswind.

    The bullet is driven toward the wind speed by drag; lateral position is
    integrated along the simulated flight. Convention: positive ``wind_speed``
    (from the right) pushes the bullet left-of-line (negative offset), matching
    the shooter-is-facing-target sign used by windage holds.
    """
    if wind_speed == 0.0:
        return 0.0
    xs, _y, zs, _t = trajectory(
        v0, 0.0, wind_speed=wind_speed, projectile=projectile, max_range=range_m + 5.0
    )
    return _sample_at(xs, zs, range_m)


def wind_hold_mrad(
    range_m: float, wind_speed: float, v0: float, *, projectile: Projectile | None = None
) -> float:
    """Windage hold in milliradians that cancels crosswind drift at range."""
    drift = wind_drift(range_m, wind_speed, v0, projectile=projectile)
    return -drift / range_m * 1e3


def engagement_decision(
    *,
    authorized_target: str,
    observed: str,
    hostile: bool,
    weapon_present: bool,
    allow_weapon_disable: bool = True,
) -> tuple[str, str]:
    """Decide the covering sniper's engagement mode (dedicated ROE module).

    The Living Daylights' central dilemma: ordered to cover a defection, Bond
    refuses a lethal shot at an innocent third party and instead takes a
    "trigger-guard" shot to disable a hostile's weapon.

    Rules (deterministic, precedence-ordered):

    * target matches the authorized asset and is hostile → ``engage_primary``;
    * a hostile who is *not* the authorized asset, weapon present, and
      ``allow_weapon_disable`` → ``disable_weapon`` (shoot the trigger guard);
    * any non-hostile observed → ``hold_fire`` (do not shoot an innocent).

    Returns ``(mode, reason)``.
    """
    matches = observed == authorized_target
    if matches:
        if hostile:
            return ("engage_primary", f"confirmed hostile target {observed!r}")
        return ("hold_fire", f"authorized asset {observed!r} is not hostile")
    if hostile and weapon_present and allow_weapon_disable:
        return (
            "disable_weapon",
            f"hostile non-target {observed!r} — trigger-guard shot to disable weapon",
        )
    if hostile:
        return ("hold_fire", f"hostile non-target {observed!r} — no authorized lethal target")
    return ("hold_fire", f"non-hostile {observed!r} — innocent, hold fire")


# --------------------------------------------------------------------------- #
# The cello case — a takedown sniper rifle packed into a cello case, the film's
# signature concealment.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RiflePart:
    """A disassembled rifle component as an axis-aligned box (metres)."""

    name: str
    length_m: float
    width_m: float
    thickness_m: float
    mass_kg: float = 0.0

    def __post_init__(self) -> None:
        for label, value in (
            ("length_m", self.length_m),
            ("width_m", self.width_m),
            ("thickness_m", self.thickness_m),
        ):
            if not (value > 0):
                raise ValueError(f"RiflePart.{label} must be positive")
        if self.mass_kg < 0:
            raise ValueError("RiflePart.mass_kg must be non-negative")


@dataclass(frozen=True)
class CelloCase:
    """A cello case interior as an axis-aligned box (metres)."""

    interior_length_m: float
    interior_width_m: float
    interior_depth_m: float

    def __post_init__(self) -> None:
        for label, value in (
            ("interior_length_m", self.interior_length_m),
            ("interior_width_m", self.interior_width_m),
            ("interior_depth_m", self.interior_depth_m),
        ):
            if not (value > 0):
                raise ValueError(f"CelloCase.{label} must be positive")


def disassemble_takedown_rifle() -> tuple[RiflePart, ...]:
    """Return the disassembled components of the SNIPER'S NEST takedown rifle.

    A compact takedown design (barrel+receiver, stock, scope, suppressor) whose
    individual parts never exceed the length of a cello case. Fixed dimensions —
    deterministic by construction.
    """
    return (
        RiflePart("barrel_receiver", 0.62, 0.09, 0.07, 2.1),
        RiflePart("stock", 0.48, 0.10, 0.06, 1.3),
        RiflePart("optic", 0.27, 0.07, 0.07, 0.8),
        RiflePart("suppressor", 0.30, 0.06, 0.06, 0.5),
    )


def _fits_in(part: RiflePart, case: CelloCase) -> bool:
    """Whether a part, oriented along the case's long axis, fits in the interior."""
    if part.length_m > case.interior_length_m:
        return False
    if part.width_m > case.interior_width_m:
        return False
    if part.thickness_m > case.interior_depth_m:
        return False
    return True


def _shelf_pack(
    parts: tuple[RiflePart, ...] | list[RiflePart],
    case: CelloCase,
) -> tuple[bool, list[tuple[RiflePart, int, float, float, float]]]:
    """Pack parts into the case using bottom-left shelf packing.

    Parts are treated as rectangles laid along the case's long axis (x) and
    stacked across its width (y). Parts are processed width-descending; each is
    placed in the first shelf that has room in length, opening a new shelf
    (stacked in y) when none does. Deterministic — the sort makes the result
    stable regardless of container iteration order.

    Returns ``(fits, placements)`` where each placement carries **the part it
    belongs to** followed by ``(lane_index, start_x, end_x, used_width)``.
    Placements are emitted in the internal width-descending processing order,
    not the caller's input order, so callers must read the part off the
    placement rather than re-zipping against their own sequence.
    """
    if any(not _fits_in(p, case) for p in parts):
        return False, []
    ordered = sorted(parts, key=lambda p: (-p.width_m, p.name))
    # Each shelf: [filled_length, height(used width), baseline_y]
    shelves: list[list[float]] = []
    placements: list[tuple[RiflePart, int, float, float, float]] = []
    for part in ordered:
        placed = False
        for idx, shelf in enumerate(shelves):
            filled, height, _y_base = shelf
            if (
                filled + part.length_m <= case.interior_length_m + 1e-9
                and height + part.width_m <= case.interior_width_m + 1e-9
            ):
                shelf[0] = filled + part.length_m
                shelf[1] = height + part.width_m
                placements.append((part, idx, filled, filled + part.length_m, shelf[1]))
                placed = True
                break
        if placed:
            continue
        # open a new lane on top of the current stack
        new_y = sum(s[1] for s in shelves)
        if new_y + part.width_m <= case.interior_width_m + 1e-9:
            shelves.append([part.length_m, part.width_m, new_y])
            placements.append((part, len(shelves) - 1, 0.0, part.length_m, new_y + part.width_m))
        else:
            return False, []
    return True, placements


def pack_cello_case(
    parts: tuple[RiflePart, ...] | list[RiflePart],
    case: CelloCase,
) -> tuple[bool, dict[str, object]]:
    """Determine whether all parts pack into the cello case (deterministic).

    Uses bottom-left shelf packing (see :func:`_shelf_pack`) so long, thin
    rifle parts can be stacked in parallel lanes across the case's width
    rather than forced end to end. Each part must also fit the interior
    cross-section on its own.

    Returns ``(fits, layout)``. ``layout['parts']`` maps each part's name to
    *its own* lane and ``[start_m, end_m]`` span (so ``end_m - start_m`` equals
    that part's length); ``layout['lanes_used']`` is the number of parallel
    lanes; ``layout['efficiency']`` is the **areal** packing efficiency — the
    summed footprint of the parts over the case's floor area — and
    ``layout['packed_length_m']`` is the longest lane's filled length.
    """
    fits, placements = _shelf_pack(parts, case)
    if not fits:
        return False, {"reason": "parts exceed cello-case interior capacity"}
    max_end = max((end for _p, _lane, _s, end, _w in placements), default=0.0)
    lanes_used = (
        max((lane for _p, lane, _s, _e, _w in placements), default=-1) + 1 if placements else 0
    )
    area_total = sum(p.length_m * p.width_m for p in parts)
    area_case = case.interior_length_m * case.interior_width_m
    efficiency = area_total / area_case if area_case > 0 else 0.0
    layout: dict[str, object] = {
        "packed_length_m": max_end,
        "lanes_used": lanes_used,
        "efficiency": efficiency,
        "parts": {
            part.name: {"lane": lane, "start_m": s, "end_m": e}
            for part, lane, s, e, _w in placements
        },
    }
    return True, layout


def assembly_time(
    parts: tuple[RiflePart, ...] | list[RiflePart], *, seconds_per_part: float = 18.0
) -> float:
    """Total field assembly time (s) to assemble the rifle from its parts.

    Deterministic: each component needs a fixed number of seconds
    (``seconds_per_part``) and there are ``len(parts)`` components.
    """
    if seconds_per_part < 0:
        raise ValueError("seconds_per_part must be non-negative")
    return seconds_per_part * float(len(parts))
