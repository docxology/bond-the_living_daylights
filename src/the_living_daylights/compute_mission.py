"""SNIPER'S NEST — the deterministic mission solution.

Single, shared computation of every number the mission reports: ballistics
(zero, windage, ROE), scope optics, countersniper detection/localization,
overwatch selection, the cello-case rig, the defection plan and its evidence
verification, and the terrain route. Both the mission adapter
(:mod:`the_living_daylights.mission`) and the manuscript token generator read
from here, so the manuscript can never drift from execution. Pure,
infrastructure-free, fully deterministic.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast

import numpy as np

from the_living_daylights import (
    ballistics,
    countersniper,
    defection_protocol,
    optics,
    settings,
    terrain_ops,
    visibility,
)

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

    # --- countersniper scope optics ---
    scope = settings.SCOPE
    mil_range_m = optics.mil_dot_range(settings.TARGET_SIZE_M, settings.MIL_READING_MILS)
    holdover_mils = optics.holdover_mils(drop_m, target)
    parallax_shift_m = optics.parallax_shift_m(
        settings.PARALLAX_EYE_OFFSET_M, target, settings.PARALLAX_FOCUS_M
    )
    click_schedule = optics.zero_click_schedule(scope, elevation_mrad, wind_hold_mrad)

    # --- countersniper detection + localization ---
    azimuth_delta = (
        (settings.OBSERVER_AZIMUTH_DEG - settings.SUN_AZIMUTH_DEG + 180.0) % 360.0
    ) - 180.0
    glint_geo = countersniper.glint_geometry_factor(
        settings.SUN_ELEVATION_DEG, azimuth_delta, settings.SPECULAR_HALF_WIDTH_DEG
    )
    glint_snr = countersniper.glint_snr(
        settings.GLINT_RANGE_M,
        scope.objective_diameter_mm,
        glint_geo,
        resolution_mrad=settings.RESOLUTION_MRAD,
        reflectivity=settings.LENS_REFLECTIVITY,
    )
    glint_pdet = countersniper.glint_detection_probability(glint_snr)
    sound_speed_mps = countersniper.speed_of_sound(settings.AIR_TEMP_C)
    crack_bang_range_m = countersniper.crack_bang_range(
        settings.CRACK_BANG_DELAY_S, settings.AIR_TEMP_C
    )
    tri_x, tri_y, tri_residual = countersniper.triangulate_position(
        settings.TRIANGULATION_OBSERVERS, settings.TRIANGULATION_BEARINGS
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

    # --- evidence verification (the verify stage's backstop model) ---
    checks = defection_protocol.koskov_verification()
    certainty = defection_protocol.verification_certainty(checks)
    verdict = defection_protocol.backstop_verdict(certainty)

    # --- mountain/desert terrain route & cover ---
    grid = terrain_ops.generate_terrain(
        settings.TERRAIN_N, settings.TERRAIN_SEED, settings.TERRAIN_CELL_SIZE_M
    )
    route = terrain_ops.plan_route(
        grid, settings.ROUTE_START, settings.ROUTE_GOAL, cover_weight=cover_weight
    )
    cover = terrain_ops.assess_cover(grid, route.path)

    # --- overwatch selection (sniper's nest) ---
    # The extraction site is the grid's low point (a wadi-like cell).
    flat_min = int(np.argmin(grid.elevation))
    target_cell = (flat_min // grid.n, flat_min % grid.n)
    candidates = tuple(
        (r, c)
        for r in range(0, grid.n, settings.OVERWATCH_CANDIDATE_STEP)
        for c in range(0, grid.n, settings.OVERWATCH_CANDIDATE_STEP)
        if (r, c) != target_cell  # a nest is a position that SEES the site
    )
    ranked = visibility.rank_overwatch_positions(
        grid,
        target_cell,
        candidates,
        eye_height_m=settings.OVERWATCH_EYE_HEIGHT_M,
        clearance_m=settings.OVERWATCH_CLEARANCE_M,
        max_range_cells=settings.OVERWATCH_MAX_RANGE_CELLS,
    )
    best = ranked[0] if ranked else None
    visible_count = sum(1 for r in ranked if r.visible)
    top_three = tuple((r.cell, float(r.score)) for r in ranked[:3])

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
        "optics": {
            "magnification": scope.magnification,
            "objective_diameter_mm": scope.objective_diameter_mm,
            "click_unit": scope.click_unit,
            "click_size_mrad": optics.click_value_mrad(scope),
            "mil_dot_range_m": mil_range_m,
            "holdover_mils": holdover_mils,
            "parallax_shift_m": parallax_shift_m,
            "elevation_clicks": click_schedule["elevation_clicks"],
            "wind_clicks": click_schedule["wind_clicks"],
        },
        "countersniper": {
            "sun_elevation_deg": settings.SUN_ELEVATION_DEG,
            "azimuth_delta_deg": azimuth_delta,
            "glint_geometry_factor": glint_geo,
            "glint_snr": glint_snr,
            "glint_detection_probability": glint_pdet,
            "speed_of_sound_mps": sound_speed_mps,
            "crack_bang_range_m": crack_bang_range_m,
            "triangulated_x_m": tri_x,
            "triangulated_y_m": tri_y,
            "triangulation_residual_m": tri_residual,
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
        "verification": {
            "num_checks": len(checks),
            "check_labels": tuple(c.label for c in checks),
            "certainty": certainty,
            "verdict": verdict,
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
        "overwatch": {
            "target_cell": target_cell,
            "num_candidates": len(ranked),
            "candidate_step": settings.OVERWATCH_CANDIDATE_STEP,
            "visible_candidates": visible_count,
            "visible_fraction": visible_count / len(ranked) if ranked else 0.0,
            "best_cell": best.cell if best is not None else None,
            "best_score": best.score if best is not None else 0.0,
            "best_distance_m": best.distance_m if best is not None else 0.0,
            "best_cover": best.cover if best is not None else 0.0,
            "best_elevation_gain_m": best.elevation_gain_m if best is not None else 0.0,
            "top_three": top_three,
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
