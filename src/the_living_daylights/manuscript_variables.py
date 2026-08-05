"""SNIPER'S NEST — manuscript variable hydration.

Every ``{{TOKEN}}`` in ``manuscript/NN_*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
deterministic mission solution (:func:`~the_living_daylights.compute_mission.mission_solution`).
Metrics flow through this module so the manuscript cannot drift from execution
and is never hand-authored in prose.

No wall clock is read here. Every token is a pure function of committed inputs
(``manuscript/config.yaml``, ``settings.py``, the mission solution) plus the
running interpreter version, so two regenerations on one interpreter produce
byte-identical artifacts. ``MANUSCRIPT_DATE`` is the manuscript's *committed*
date from ``config.yaml``, not the moment of hydration — this module used to
stamp ``datetime.now()`` into the prose, which silently falsified the
package's byte-identical-regeneration claim.
"""

from __future__ import annotations

import platform
import re
from pathlib import Path
from typing import Any

import yaml

from the_living_daylights import settings
from the_living_daylights.compute_mission import mission_solution

__all__ = [
    "REQUIRED_SOLUTION_SECTIONS",
    "generate_variables",
    "load_manuscript_config",
    "resolve_manuscript_tree",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(
            f"manuscript config must be a top-level mapping, got {type(data).__name__}"
        )
    return data


def _fmt(value: float, ndigits: int = 3) -> str:
    return f"{value:.{ndigits}f}"


#: Mission-solution sections every result token reads from. ``require_outputs``
#: checks these by name, so a solution that silently loses a section fails
#: hydration loudly instead of emitting half a manuscript.
REQUIRED_SOLUTION_SECTIONS: tuple[str, ...] = (
    "ballistics",
    "rules_of_engagement",
    "optics",
    "countersniper",
    "cello_case",
    "defection",
    "verification",
    "terrain",
    "overwatch",
)


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    solution: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), require every section of
            :data:`REQUIRED_SOLUTION_SECTIONS` to be present and non-empty in
            the mission solution, so no result token falls back to prose.
        solution: Override for the mission solution (defaults to the live
            :func:`~the_living_daylights.compute_mission.mission_solution`).
            Supplying it is what makes ``require_outputs`` an enforceable gate
            rather than an assertion that can never fire.

    Returns:
        The ``{{TOKEN}}`` → value mapping. It reads no wall clock, so repeated
        calls on one interpreter are equal.

    Raises:
        ValueError: if the config sections are malformed, if ``paper.date`` is
            missing or empty, or if ``require_outputs`` is set and the solution
            is missing or has an empty required section.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    keywords = config.get("keywords", [])
    if not isinstance(keywords, list):
        raise ValueError("manuscript config 'keywords' must be a list")
    # The manuscript's date is a committed value, never the hydration moment:
    # reading a clock here would make every regeneration differ in bytes.
    manuscript_date = str(paper.get("date", "")).strip()
    if not manuscript_date:
        raise ValueError(
            "manuscript config 'paper.date' must be a non-empty string — it is the "
            "committed, deterministic source of MANUSCRIPT_DATE"
        )

    sol = mission_solution() if solution is None else solution
    if require_outputs:
        missing = [name for name in REQUIRED_SOLUTION_SECTIONS if name not in sol or not sol[name]]
        if missing:
            raise ValueError(
                "mission solution is missing result sections "
                f"{missing} — cannot hydrate result tokens"
            )

    bal = sol["ballistics"]
    roe = sol["rules_of_engagement"]
    cell = sol["cello_case"]
    defe = sol["defection"]
    ter = sol["terrain"]

    variables = {
        "IDENTITY": settings.FILM,
        "CODENAME": settings.CODENAME,
        "VERSION": str(paper.get("version", "")),
        "TITLE": str(paper.get("title", "")),
        "SUBTITLE": str(paper.get("subtitle", "")),
        "CONFIG_KEYWORDS": ", ".join(str(k) for k in keywords),
        # ballistics
        "BAL_MUZZLE_VELOCITY": _fmt(float(bal["muzzle_velocity_mps"]), 0),
        "BAL_BULLET_MASS_G": _fmt(float(bal["bullet_mass_kg"]) * 1000.0, 1),
        "BAL_CALIBER_MM": _fmt(float(bal["caliber_m"]) * 1000.0, 1),
        "BAL_BC": _fmt(float(bal["ballistic_coefficient_kg_m2"]), 0),
        "BAL_ZERO_RANGE": _fmt(float(bal["zero_range_m"]), 0),
        "BAL_TARGET_RANGE": _fmt(float(settings.TARGET_RANGE_M), 0),
        "BAL_SIGHT_HEIGHT": _fmt(float(bal["sight_height_m"]), 2),
        "BAL_ELEVATION_MRAD": _fmt(float(bal["elevation_mrad"]), 2),
        "BAL_NEAR_ZERO": _fmt(float(bal["near_zero_m"]), 1),
        "BAL_FAR_ZERO": _fmt(float(bal["far_zero_m"]), 1),
        "BAL_DROP": _fmt(float(bal["drop_at_target_m"]), 3),
        "BAL_TOF": _fmt(float(bal["time_of_flight_s"]), 3),
        "BAL_WIND_MPS": _fmt(float(bal["wind_mps"]), 1),
        "BAL_WIND_DRIFT": _fmt(float(bal["wind_drift_m"]), 3),
        "BAL_WIND_HOLD_MRAD": _fmt(float(bal["wind_hold_mrad"]), 2),
        # rules of engagement
        "ROE_CELLIST_MODE": str(roe["cellist_mode"]),
        "ROE_CELLIST_REASON": str(roe["cellist_reason"]),
        "ROE_SENTINEL_MODE": str(roe["sentinel_mode"]),
        "ROE_SENTINEL_REASON": str(roe["sentinel_reason"]),
        # countersniper optics
        "OPT_MAGNIFICATION": _fmt(float(sol["optics"]["magnification"]), 0),
        "OPT_OBJECTIVE_MM": _fmt(float(sol["optics"]["objective_diameter_mm"]), 0),
        "OPT_CLICK_MRAD": _fmt(float(sol["optics"]["click_size_mrad"]), 2),
        "OPT_ELEVATION_CLICKS": str(sol["optics"]["elevation_clicks"]),
        "OPT_WIND_CLICKS": str(sol["optics"]["wind_clicks"]),
        "OPT_MIL_RANGE_M": _fmt(float(sol["optics"]["mil_dot_range_m"]), 0),
        "MIL_READING_MILS": _fmt(float(settings.MIL_READING_MILS), 1),
        "OPT_HOLDOVER_MILS": _fmt(float(sol["optics"]["holdover_mils"]), 2),
        "OPT_PARALLAX_MM": _fmt(float(sol["optics"]["parallax_shift_m"]) * 1000.0, 1),
        "OPT_PARALLAX_FOCUS_M": _fmt(float(settings.PARALLAX_FOCUS_M), 0),
        "OPT_TARGET_SIZE_M": _fmt(float(settings.TARGET_SIZE_M), 2),
        # countersniper detection + localization
        "CS_SUN_ELEVATION_DEG": _fmt(float(sol["countersniper"]["sun_elevation_deg"]), 0),
        "CS_SPECULAR_HALF_DEG": _fmt(float(settings.SPECULAR_HALF_WIDTH_DEG), 1),
        "CS_LENS_REFLECTIVITY": _fmt(float(settings.LENS_REFLECTIVITY), 2),
        "CS_RESOLUTION_MRAD": _fmt(float(settings.RESOLUTION_MRAD), 1),
        "CS_NUM_OBSERVERS": str(len(settings.TRIANGULATION_OBSERVERS)),
        "CS_AZIMUTH_DELTA_DEG": _fmt(float(sol["countersniper"]["azimuth_delta_deg"]), 1),
        "CS_GLINT_GEOMETRY": _fmt(float(sol["countersniper"]["glint_geometry_factor"]), 3),
        "CS_GLINT_SNR": _fmt(float(sol["countersniper"]["glint_snr"]), 1),
        "CS_GLINT_PDET": _fmt(float(sol["countersniper"]["glint_detection_probability"]), 3),
        "CS_GLINT_RANGE_M": _fmt(float(settings.GLINT_RANGE_M), 0),
        "CS_SOUND_SPEED": _fmt(float(sol["countersniper"]["speed_of_sound_mps"]), 1),
        "CS_CRACK_BANG_M": _fmt(float(sol["countersniper"]["crack_bang_range_m"]), 0),
        "CRACK_BANG_DELAY_S": _fmt(float(settings.CRACK_BANG_DELAY_S), 1),
        "AIR_TEMP_C": _fmt(float(settings.AIR_TEMP_C), 0),
        "CS_TRI_X_M": _fmt(float(sol["countersniper"]["triangulated_x_m"]), 1),
        "CS_TRI_Y_M": _fmt(float(sol["countersniper"]["triangulated_y_m"]), 1),
        "CS_TRI_RESIDUAL_M": _fmt(float(sol["countersniper"]["triangulation_residual_m"]), 2),
        # overwatch selection
        "OW_TARGET_CELL": str(sol["overwatch"]["target_cell"]),
        "OW_NUM_CANDIDATES": str(sol["overwatch"]["num_candidates"]),
        "OW_VISIBLE_CANDIDATES": str(sol["overwatch"]["visible_candidates"]),
        "OW_VISIBLE_FRACTION": _fmt(float(sol["overwatch"]["visible_fraction"]), 3),
        "OW_BEST_CELL": str(sol["overwatch"]["best_cell"]),
        "OW_BEST_SCORE": _fmt(float(sol["overwatch"]["best_score"]), 3),
        "OW_BEST_DISTANCE_M": _fmt(float(sol["overwatch"]["best_distance_m"]), 0),
        "OW_BEST_COVER": _fmt(float(sol["overwatch"]["best_cover"]), 2),
        "OW_BEST_ELEV_GAIN_M": _fmt(float(sol["overwatch"]["best_elevation_gain_m"]), 1),
        "OW_CANDIDATE_STEP": str(sol["overwatch"]["candidate_step"]),
        "OW_MAX_RANGE_CELLS": str(settings.OVERWATCH_MAX_RANGE_CELLS),
        "OW_EYE_HEIGHT_M": _fmt(float(settings.OVERWATCH_EYE_HEIGHT_M), 2),
        "OW_CLEARANCE_M": _fmt(float(settings.OVERWATCH_CLEARANCE_M), 2),
        # evidence verification
        "VER_NUM_CHECKS": str(sol["verification"]["num_checks"]),
        "VER_CHECK_LABELS": ", ".join(str(c) for c in sol["verification"]["check_labels"]),
        "VER_CERTAINTY": _fmt(float(sol["verification"]["certainty"]), 3),
        "VER_VERDICT": str(sol["verification"]["verdict"]),
        # cello case
        "CELL_NUM_PARTS": str(cell["num_parts"]),
        "CELL_PART_NAMES": ", ".join(str(p) for p in cell["parts"]),
        "CELL_FITS": str(cell["fits"]).lower(),
        "CELL_LANES": str(cell["lanes_used"]),
        "CELL_EFFICIENCY": _fmt(float(cell["packing_efficiency"]), 3),
        "CELL_PACKED_LENGTH_M": _fmt(float(cell["packed_length_m"]), 2),
        "CELL_CASE_L_M": _fmt(float(cell["interior_length_m"]), 2),
        "CELL_CASE_W_M": _fmt(float(cell["interior_width_m"]), 2),
        "CELL_CASE_D_M": _fmt(float(cell["interior_depth_m"]), 2),
        "CELL_ASSEMBLY_S": _fmt(float(cell["assembly_time_s"]), 0),
        # defection protocol
        "DEF_NUM_STAGES": str(defe["num_stages"]),
        "DEF_STAGE_NAMES": ", ".join(str(s) for s in defe["stages"]),
        "DEF_PLAN_SCORE": _fmt(float(defe["plan_score"]), 3),
        "DEF_PLAN_VERDICT": str(defe["plan_verdict"]),
        "DEF_GATE": str(defe["gate_stage"]),
        "DEF_GO_THRESHOLD": _fmt(float(settings.DEFECTION_GO_THRESHOLD), 2),
        "DEF_CONDITIONAL_THRESHOLD": _fmt(float(settings.DEFECTION_CONDITIONAL_THRESHOLD), 2),
        # terrain ops
        "TER_SEED": str(ter["seed"]),
        "TER_N": str(ter["grid_n"]),
        "TER_CELL_M": _fmt(float(ter["cell_size_m"]), 0),
        "TER_START": str(ter["start"]),
        "TER_GOAL": str(ter["goal"]),
        "TER_DIST_KM": _fmt(float(ter["route_distance_m"]) / 1000.0, 2),
        "TER_STEPS": str(ter["route_steps"]),
        "TER_COST": _fmt(float(ter["route_cost"]), 1),
        "TER_MEAN_COVER": _fmt(float(ter["mean_cover"]), 3),
        "TER_AUDIT_MEAN_COVER": _fmt(float(ter["audit_mean_cover"]), 3),
        "TER_FIELD_MEAN_COVER": _fmt(float(ter["field_mean_cover"]), 3),
        "TER_BARE_MEAN_COVER": _fmt(float(ter["bare_mean_cover"]), 3),
        "TER_COVER_TERM_GAIN": _fmt(float(ter["cover_term_gain"]), 3),
        "TER_COVER_VS_FIELD": _fmt(float(ter["cover_vs_field"]), 3),
        "TER_MIN_COVER": _fmt(float(ter["min_cover"]), 3),
        "TER_MIN_COVER_INDEX": str(ter["min_cover_index"]),
        "TER_COVER_POINTS": str(ter["cover_points"]),
        # environment / identity
        "PYTHON_VERSION": platform.python_version(),
        "MANUSCRIPT_DATE": manuscript_date,
    }
    return variables


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Copies only ``NN_*.md`` sections (not sidecars such as ``SYNTAX.md``). In
    strict mode any leftover ``{{TOKEN}}`` fails the resolution so the
    manuscript never renders with raw braces.
    """
    manuscript_dir = (
        Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    )
    output_dir = (
        Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    )
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
