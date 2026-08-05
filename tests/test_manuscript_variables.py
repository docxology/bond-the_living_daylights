"""Real-data tests for :mod:`the_living_daylights.manuscript_variables`."""

from __future__ import annotations

import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from the_living_daylights.compute_mission import mission_solution
from the_living_daylights.manuscript_variables import (
    DEFAULT_CONFIG_PATH,
    REQUIRED_SOLUTION_SECTIONS,
    generate_variables,
    load_manuscript_config,
    resolve_manuscript_tree,
)

FIXED_NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


def test_load_config_round_trip() -> None:
    config = load_manuscript_config(DEFAULT_CONFIG_PATH)
    assert "paper" in config and "keywords" in config


def test_load_config_missing() -> None:
    with pytest.raises(FileNotFoundError):
        load_manuscript_config("/nonexistent/path/config.yaml")


def test_generate_variables_content() -> None:
    variables = generate_variables(now=FIXED_NOW)
    assert variables["IDENTITY"] == "the_living_daylights"
    assert variables["CODENAME"] == "SNIPER'S NEST"
    assert variables["BAL_ZERO_RANGE"] == "300"
    assert variables["DEF_PLAN_VERDICT"] == "conditional"
    assert variables["TER_DIST_KM"]
    assert variables["OPT_MIL_RANGE_M"] == "300"
    assert variables["CS_GLINT_PDET"]
    assert variables["OW_BEST_CELL"]
    assert variables["VER_VERDICT"] == "conditional"
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in variables.items())
    assert variables["GENERATION_TIMESTAMP"] == "2026-08-04T12:00:00+00:00"


def test_generate_variables_deterministic_given_now() -> None:
    a = generate_variables(now=FIXED_NOW)
    b = generate_variables(now=FIXED_NOW)
    assert a == b


def test_all_manuscript_tokens_are_generated() -> None:
    """Live cross-reference: every {{TOKEN}} in NN_*.md must be generated."""
    variables = generate_variables()
    known = set(variables)
    project_root = Path(__file__).resolve().parent.parent
    missing: list[tuple[str, str]] = []
    for section in sorted((project_root / "manuscript").glob("[0-9][0-9]_*.md")):
        for token in re.findall(r"\{\{([A-Z0-9_]+)\}\}", section.read_text(encoding="utf-8")):
            if token not in known:
                missing.append((section.name, token))
    assert missing == []


def test_resolve_tree_writes_sections() -> None:
    variables = generate_variables(now=FIXED_NOW)
    out = Path(tempfile.mkdtemp())
    resolved_dir, names = resolve_manuscript_tree(variables, output_dir=out)
    assert names
    for name in names:
        assert (resolved_dir / name).exists()
    # resolved output must contain no raw tokens
    for name in names:
        text = (resolved_dir / name).read_text(encoding="utf-8")
        assert "{{" not in text


def test_resolve_tree_strict_fails_on_unresolved() -> None:
    src = Path(tempfile.mkdtemp())
    (src / "00_zz.md").write_text("sniper {{NOT_A_GENERATED_TOKEN}} hold", encoding="utf-8")
    with pytest.raises(ValueError):
        resolve_manuscript_tree({"A": "1"}, manuscript_dir=src)


def test_load_config_rejects_non_mapping() -> None:
    """A YAML document that is not a top-level mapping is rejected, not coerced."""
    path = Path(tempfile.mkdtemp()) / "config.yaml"
    path.write_text("- sniper\n- nest\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level mapping"):
        load_manuscript_config(path)


def test_generate_variables_rejects_malformed_sections() -> None:
    """`paper` must be a mapping and `keywords` a list, or hydration fails loudly."""
    root = Path(tempfile.mkdtemp())
    bad_paper = root / "bad_paper.yaml"
    bad_paper.write_text("paper: not-a-mapping\nkeywords: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'paper' section must be a mapping"):
        generate_variables(config_path=bad_paper)

    bad_keywords = root / "bad_keywords.yaml"
    bad_keywords.write_text("paper: {version: '1'}\nkeywords: sniper\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'keywords' must be a list"):
        generate_variables(config_path=bad_keywords)


def test_require_outputs_rejects_an_incomplete_solution() -> None:
    """The require_outputs gate must actually fire on a gutted solution."""
    with pytest.raises(ValueError, match="missing result sections"):
        generate_variables(solution={}, now=FIXED_NOW)

    for section in REQUIRED_SOLUTION_SECTIONS:
        gutted = dict(mission_solution())
        gutted[section] = {}
        with pytest.raises(ValueError, match=re.escape(section)):
            generate_variables(solution=gutted, now=FIXED_NOW)


def test_require_outputs_false_actually_disables_the_gate() -> None:
    """The opt-out flag is a real branch, so it is exercised as one.

    With ``require_outputs=False`` a complete solution still hydrates, and an
    incomplete one is no longer caught by the friendly section check — it
    fails later on a raw ``KeyError``. That contrast is what proves the flag
    is consulted rather than ignored.
    """
    healthy = generate_variables(require_outputs=False, now=FIXED_NOW)
    assert healthy == generate_variables(now=FIXED_NOW)

    gutted = dict(mission_solution())
    gutted["terrain"] = {}
    with pytest.raises(KeyError):
        generate_variables(solution=gutted, require_outputs=False, now=FIXED_NOW)
    with pytest.raises(ValueError, match="missing result sections"):
        generate_variables(solution=gutted, require_outputs=True, now=FIXED_NOW)


def test_injected_solution_flows_into_the_tokens() -> None:
    """A supplied solution is what gets hydrated — not a re-read of the live one."""
    altered = dict(mission_solution())
    altered["terrain"] = {**altered["terrain"], "route_steps": 4321}
    variables = generate_variables(solution=altered, now=FIXED_NOW)
    assert variables["TER_STEPS"] == "4321"
    assert generate_variables(now=FIXED_NOW)["TER_STEPS"] != "4321"


def test_config_mission_block_mirrors_settings() -> None:
    """config.yaml's `mission:` echo must equal settings.py, key for key.

    The echo exists for readers of the manuscript; settings.py is the source of
    truth. This test is what keeps the echo from drifting silently.
    """
    from the_living_daylights import settings

    mission = load_manuscript_config(DEFAULT_CONFIG_PATH)["mission"]
    expected = {
        "film": settings.FILM,
        "codename": settings.CODENAME,
        "muzzle_velocity_mps": settings.MUZZLE_VELOCITY_MPS,
        "zero_range_m": settings.ZERO_RANGE_M,
        "target_range_m": settings.TARGET_RANGE_M,
        "sight_height_m": settings.SIGHT_HEIGHT_M,
        "wind_mps": settings.WIND_MPS,
        "scope_magnification": settings.SCOPE.magnification,
        "scope_objective_mm": settings.SCOPE.objective_diameter_mm,
        "mil_reading_mils": settings.MIL_READING_MILS,
        "target_size_m": settings.TARGET_SIZE_M,
        "parallax_focus_m": settings.PARALLAX_FOCUS_M,
        "sun_elevation_deg": settings.SUN_ELEVATION_DEG,
        "lens_reflectivity": settings.LENS_REFLECTIVITY,
        "glint_range_m": settings.GLINT_RANGE_M,
        "air_temp_c": settings.AIR_TEMP_C,
        "crack_bang_delay_s": settings.CRACK_BANG_DELAY_S,
        "overwatch_candidate_step": settings.OVERWATCH_CANDIDATE_STEP,
        "overwatch_max_range_cells": settings.OVERWATCH_MAX_RANGE_CELLS,
        "defection_go_threshold": settings.DEFECTION_GO_THRESHOLD,
        "defection_conditional_threshold": settings.DEFECTION_CONDITIONAL_THRESHOLD,
        "terrain_seed": settings.TERRAIN_SEED,
        "terrain_n": settings.TERRAIN_N,
        "terrain_cell_size_m": settings.TERRAIN_CELL_SIZE_M,
    }
    # every echoed key must be declared here, and every declared key echoed
    assert set(mission) == set(expected)
    for key, want in expected.items():
        got = mission[key]
        if isinstance(want, str):
            assert got == want, key
        else:
            assert float(got) == pytest.approx(float(want)), key
