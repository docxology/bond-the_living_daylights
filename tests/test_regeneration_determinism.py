"""The package's byte-identical-regeneration claim, bound to a probe that can fail.

`manuscript/06_reproducibility.md` claims that re-running
`scripts/z_generate_manuscript_variables.py` regenerates a byte-identical
`output/` tree. That claim was false for a long time: `generate_variables()`
stamped `datetime.now()` into `GENERATION_TIMESTAMP`, which was rendered into
`manuscript/05_experimental_setup.md`, into `06_reproducibility.md` itself, and
into `output/data/manuscript_variables.json`. Every rerun differed in bytes.

The breach survived because the tests that looked like determinism tests all
passed a fixed `now=` into the generator. A probe that injects the very value
it is meant to be checking cannot fail on it. So these tests inject nothing:

* `test_two_full_regenerations_are_byte_identical` runs the real script twice
  as a subprocess, *deliberately straddling a wall-clock second boundary*, and
  compares a SHA-256 of every file produced. Reintroduce any clock into the
  persisted path and it goes red.
* `test_no_wall_clock_call_in_src` AST-scans `src/` for clock calls, and
  carries a positive control so it cannot pass by being blind.

No mocks: real subprocesses, real files, real bytes.
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"

#: Every way this package could read a clock. `datetime.now`/`utcnow` is the
#: call that actually broke the claim; the rest close the class.
CLOCK_ATTRS: frozenset[str] = frozenset(
    {
        "now",
        "utcnow",
        "today",
        "time",
        "time_ns",
        "monotonic",
        "monotonic_ns",
        "perf_counter",
        "perf_counter_ns",
        "process_time",
    }
)
CLOCK_ROOTS: frozenset[str] = frozenset({"datetime", "date", "time"})


def _regenerate(destination: Path) -> None:
    """Run the real generator script, writing every artifact under `destination`."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--output-root", str(destination)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stderr


def _tree_digest(root: Path) -> dict[str, str]:
    """SHA-256 every file under `root`, keyed by its path relative to `root`."""
    digests = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    assert digests, f"no artifacts written under {root} — the probe would be vacuous"
    return digests


def test_two_full_regenerations_are_byte_identical(tmp_path) -> None:
    """The claim itself: two real regenerations produce identical bytes.

    The `sleep` is load-bearing, not padding. `GENERATION_TIMESTAMP` used
    second granularity, so two back-to-back runs could land in the same second
    and a gapless probe would report determinism that was not there. Crossing a
    full second boundary is what makes this test able to fail.
    """
    first = tmp_path / "run1"
    second = tmp_path / "run2"

    _regenerate(first)
    time.sleep(1.1)
    _regenerate(second)

    digest_first = _tree_digest(first)
    digest_second = _tree_digest(second)

    assert sorted(digest_first) == sorted(digest_second), "regeneration changed the file set"
    differing = sorted(name for name, h in digest_first.items() if digest_second[name] != h)
    assert differing == [], f"regeneration is not byte-identical; artifacts differ: {differing}"

    # Non-vacuity: the probe must actually be covering the artifacts the claim
    # names — the resolved sections, the token JSON, and all four plates.
    names = set(digest_first)
    assert "data/manuscript_variables.json" in names
    assert any(n.startswith("manuscript/") and n.endswith(".md") for n in names)
    assert sum(1 for n in names if n.endswith(".png")) == 4


def _clock_calls(tree: ast.AST) -> list[str]:
    """Return dotted names of every clock call in an AST (`a.b.now()` → `a.b.now`)."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in CLOCK_ATTRS:
            parts: list[str] = [func.attr]
            value: ast.expr = func.value
            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value
            if isinstance(value, ast.Name):
                parts.append(value.id)
            dotted = ".".join(reversed(parts))
            if parts[-1] in CLOCK_ROOTS:
                found.append(dotted)
        elif isinstance(func, ast.Name) and func.id in {"time", "monotonic", "perf_counter"}:
            found.append(func.id)
    return found


def test_clock_scanner_reports_a_planted_call(tmp_path) -> None:
    """Positive control: the scanner must see a clock it is pointed at.

    Without this, `test_no_wall_clock_call_in_src` could pass by being blind —
    exactly the failure mode that let the original defect ship.
    """
    planted = tmp_path / "planted.py"
    planted.write_text(
        "import time\n"
        "from datetime import datetime, date\n"
        "a = datetime.now()\n"
        "b = datetime.utcnow()\n"
        "c = date.today()\n"
        "d = time.time()\n"
        "e = time.monotonic()\n",
        encoding="utf-8",
    )
    found = _clock_calls(ast.parse(planted.read_text(encoding="utf-8")))
    assert sorted(found) == [
        "date.today",
        "datetime.now",
        "datetime.utcnow",
        "time.monotonic",
        "time.time",
    ]


def test_no_wall_clock_call_in_src() -> None:
    """No module on the persisted-artifact path may read a clock."""
    sources = sorted((PROJECT_ROOT / "src").rglob("*.py"))
    assert len(sources) >= 8, "source scan set is suspiciously small — check the glob"
    offenders: list[str] = []
    for source in sources:
        for call in _clock_calls(ast.parse(source.read_text(encoding="utf-8"))):
            offenders.append(f"{source.relative_to(PROJECT_ROOT)}: {call}()")
    assert offenders == [], f"wall-clock call(s) reachable from persisted artifacts: {offenders}"
