"""SNIPER'S NEST — manuscript variable hydration.

Every ``{{TOKEN}}`` in ``manuscript/NN_*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
deterministic mission solution (:func:`~the_living_daylights.compute_mission.mission_solution`).
Metrics flow through this module so the manuscript cannot drift from execution
and is never hand-authored in prose.
"""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from the_living_daylights import settings
from the_living_daylights.compute_mission import mission_solution

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

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


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    now: datetime | None = None,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), require the deterministic mission
            solution to be non-empty so no result token falls back to prose.
        now: Timestamp override for deterministic generation (UTC default).
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    keywords = config.get("keywords", [])
    if not isinstance(keywords, list):
        raise ValueError("manuscript config 'keywords' must be a list")

    sol = mission_solution()
    if require_outputs and not sol:
        raise ValueError("mission solution is empty — cannot hydrate result tokens")

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
        # cello case
        "CELL_NUM_PARTS": str(cell["num_parts"]),
        "CELL_FITS": str(cell["fits"]).lower(),
        "CELL_LANES": str(cell["lanes_used"]),
        "CELL_EFFICIENCY": _fmt(float(cell["packing_efficiency"]), 3),
        "CELL_ASSEMBLY_S": _fmt(float(cell["assembly_time_s"]), 0),
        # defection protocol
        "DEF_NUM_STAGES": str(defe["num_stages"]),
        "DEF_PLAN_SCORE": _fmt(float(defe["plan_score"]), 3),
        "DEF_PLAN_VERDICT": str(defe["plan_verdict"]),
        "DEF_GATE": str(defe["gate_stage"]),
        "DEF_GO_THRESHOLD": _fmt(float(settings.DEFECTION_GO_THRESHOLD), 2),
        "DEF_CONDITIONAL_THRESHOLD": _fmt(float(settings.DEFECTION_CONDITIONAL_THRESHOLD), 2),
        # terrain ops
        "TER_SEED": str(ter["seed"]),
        "TER_N": str(ter["grid_n"]),
        "TER_CELL_M": _fmt(float(ter["cell_size_m"]), 0),
        "TER_DIST_KM": _fmt(float(ter["route_distance_m"]) / 1000.0, 2),
        "TER_STEPS": str(ter["route_steps"]),
        "TER_COST": _fmt(float(ter["route_cost"]), 1),
        "TER_MEAN_COVER": _fmt(float(ter["mean_cover"]), 3),
        "TER_MIN_COVER": _fmt(float(ter["min_cover"]), 3),
        "TER_MIN_COVER_INDEX": str(ter["min_cover_index"]),
        "TER_COVER_POINTS": str(ter["cover_points"]),
        # environment
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
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
