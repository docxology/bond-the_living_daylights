"""Real-data tests for :mod:`the_living_daylights.manuscript_variables`."""

from __future__ import annotations

import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from the_living_daylights.manuscript_variables import (
    DEFAULT_CONFIG_PATH,
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
