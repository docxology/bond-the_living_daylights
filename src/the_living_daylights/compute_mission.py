"""SNIPER'S NEST — the deterministic mission solution.

Single, shared computation of every number the mission reports: ballistics
(zero, windage, ROE), the cello-case rig, the defection plan, and the terrain
route. Both the mission adapter (:mod:`the_living_daylights.mission`) and the
manuscript token generator read from here, so the manuscript can never drift
from execution. Pure, infrastructure-free, fully deterministic.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast

from the_living_daylights import ballistics, defection_protocol, settings, terrain_ops

__all__ = ["input_hash", "mission_solution"]


def mission_solution(
    *, wind_mps: float = settings.WIND_MPS, cover_weight: float = 1.0
) -> dict[str, Any]:
    """Compute the full deterministic SNIPER'S NEST mission solution.

    All numbers derive from the fixed physics, geometry, and the seeded terrain
    grid in :mod:`the_living_daylights.settings`. No RNG draws beyond the
    seeded terrain, no wall-clock, no I/O — byte-deterministic per inputs.
    """
    proj = settings.PROJECTILE
    v0 = settings.MUZZLE_VELOCITY_MPS
    zero = settings.ZERO_RANGE_M
    sight = settings.SIGHT_HEIGHT_M
    target = settings.TARGET_RANGE_M

    # --- sniper ballistics ---
    elevation_mrad = ballistics.zero_scope(v0, zero, sight, projectile=proj)
    near_zero, far_zero = ballistics.capture_zero(elevation_mrad, v0, zero, sight, projectile=proj)
    drift_m = ballistics.wind_drift(target, wind_mps, v0, projectile=proj)
    wind_hold_mrad = ballistics.wind_hold_mrad(target, wind_mps, v0, projectile=proj)
    tof_s = ballistics.time_of_flight(target, v0, projectile=proj)
    drop_m = ballistics.drop_at_range(target, v0, projectile=proj)

    # rules of engagement: the cellist is innocent (Bond refuses the kill),
    # a hostile non-target gets a trigger-guard weapon-disable shot.
    roe_innocent_mode, roe_innocent_reason = ballistics.engagement_decision(
        authorized_target=settings.SNIPER_ASSET,
        observed="cellist",
        hostile=False,
        weapon_present=True,
    )
    roe_disable_mode, roe_disable_reason = ballistics.engagement_decision(
        authorized_target=settings.SNIPER_ASSET,
        observed="sentinel",
        hostile=True,
        weapon_present=True,
    )

    # --- the cello case rig ---
    parts = ballistics.disassemble_takedown_rifle()
    case_fits, case_layout = ballistics.pack_cello_case(parts, settings.CELLO_CASE)
    assembly_s = ballistics.assembly_time(parts)

    # --- staged, risk-scored defection handling ---
    defection = defection_protocol.assess_defection(
        defection_protocol.koskov_scenario(),
        go_threshold=settings.DEFECTION_GO_THRESHOLD,
        conditional_threshold=settings.DEFECTION_CONDITIONAL_THRESHOLD,
    )

    # --- mountain/desert terrain route & cover ---
    grid = terrain_ops.generate_terrain(
        settings.TERRAIN_N, settings.TERRAIN_SEED, settings.TERRAIN_CELL_SIZE_M
    )
    route = terrain_ops.plan_route(
        grid, settings.ROUTE_START, settings.ROUTE_GOAL, cover_weight=cover_weight
    )
    cover = terrain_ops.assess_cover(grid, route.path)

    return {
        "ballistics": {
            "muzzle_velocity_mps": v0,
            "bullet_mass_kg": proj.mass_kg,
            "caliber_m": proj.caliber_m,
            "ballistic_coefficient_kg_m2": proj.ballistic_coefficient,
            "zero_range_m": zero,
            "sight_height_m": sight,
            "elevation_mrad": elevation_mrad,
            "near_zero_m": near_zero,
            "far_zero_m": far_zero,
            "drop_at_target_m": drop_m,
            "time_of_flight_s": tof_s,
            "wind_mps": wind_mps,
            "wind_drift_m": drift_m,
            "wind_hold_mrad": wind_hold_mrad,
        },
        "rules_of_engagement": {
            "cellist_mode": roe_innocent_mode,
            "cellist_reason": roe_innocent_reason,
            "sentinel_mode": roe_disable_mode,
            "sentinel_reason": roe_disable_reason,
        },
        "cello_case": {
            "parts": tuple(p.name for p in parts),
            "num_parts": len(parts),
            "fits": case_fits,
            "lanes_used": case_layout.get("lanes_used", 0),
            "packing_efficiency": case_layout.get("efficiency", 0.0),
            "assembly_time_s": assembly_s,
        },
        "defection": {
            "num_stages": len(defection.stages),
            "stages": tuple(s.stage for s in defection.stages),
            "stage_scores": {s.stage: s.score for s in defection.stages},
            "stage_verdicts": {s.stage: s.verdict for s in defection.stages},
            "plan_score": defection.plan_score,
            "plan_verdict": defection.plan_verdict,
            "gate_stage": defection.gate_stage,
            "approval": tuple(defection.approval),
        },
        "terrain": {
            "seed": settings.TERRAIN_SEED,
            "grid_n": settings.TERRAIN_N,
            "cell_size_m": settings.TERRAIN_CELL_SIZE_M,
            "route_distance_m": route.distance_m,
            "route_steps": len(route.path) - 1,
            "route_cost": route.total_cost,
            "mean_cover": route.mean_cover,
            "min_cover": route.min_cover,
            "min_cover_index": route.min_cover_index,
            "cover_points": len(route.cover_points),
            "audit_mean_cover": float(cast("float", cover["mean_cover"])),
            "start": settings.ROUTE_START,
            "goal": settings.ROUTE_GOAL,
        },
        "determinism": {
            "cover_weight": cover_weight,
        },
    }


def input_hash() -> str:
    """Stable sha256 fingerprint of the deterministic mission solution.

    Canonical compact JSON (sorted keys) of :func:`mission_solution`, so the
    provenance ``input_hash`` is reproducible and audit-able without re-running
    the film's I/O. No wall-clock involved.
    """
    data = json.dumps(mission_solution(), sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
