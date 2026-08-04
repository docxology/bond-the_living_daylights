"""Subprocess smoke tests for the thin SNIPER'S NEST mission CLIs.

Runs each script with ``sys.executable`` (the venv python) from the project
root, asserting exit code 0 and expected output. No mocks — real execution.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_brief_smoke() -> None:
    result = _run("brief.py")
    assert result.returncode == 0, result.stderr
    assert "SNIPER'S NEST" in result.stdout


def test_recon_smoke() -> None:
    result = _run("recon.py", "--goal", "recon the site")
    assert result.returncode == 0, result.stderr
    assert "recon" in result.stdout.lower()


def test_plan_smoke() -> None:
    result = _run("plan.py")
    assert result.returncode == 0, result.stderr
    assert "solve_rifle_zero" in result.stdout


def test_execute_smoke() -> None:
    result = _run("execute.py")
    assert result.returncode == 0, result.stderr
    assert "success: True" in result.stdout


def test_debrief_smoke() -> None:
    result = _run("debrief.py")
    assert result.returncode == 0, result.stderr
    assert "lessons learned" in result.stdout


def test_preflight_smoke() -> None:
    result = _run("00_preflight.py")
    assert result.returncode == 0, result.stderr
    assert "preflight OK" in result.stdout


def test_variables_smoke_writes_artifacts() -> None:
    result = _run("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    assert (PROJECT_ROOT / "output" / "data" / "manuscript_variables.json").exists()
    assert (PROJECT_ROOT / "output" / "figures" / "ballistics_trajectory.png").exists()
