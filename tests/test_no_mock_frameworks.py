"""The zero-mock policy as an executable gate, not a promise in a document.

``docs/testing_philosophy.md`` and ``manuscript/06_reproducibility.md`` both
state that no mocking framework appears anywhere in this package. Before this
module that was an unenforced assertion: ``pytest --cov`` checks a coverage
floor and nothing else, so a ``MagicMock`` could have been added without any
gate turning red. This test walks every ``.py`` file under ``src/``, ``tests/``,
and ``scripts/`` with the ``ast`` module and fails on a real import or a real
name reference.

Parsed, not grepped: a substring search would flag the very identifiers this
file has to name, and would miss ``import unittest.mock as m``. Every banned
identifier below lives in a string literal, which the AST walk ignores by
construction.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SCANNED_DIRS = ("src", "tests", "scripts")

#: Modules whose whole purpose is replacing a real dependency with a double.
BANNED_MODULES = frozenset(
    {
        "mock",
        "unittest.mock",
        "pytest_mock",
        "flexmock",
        "mockito",
        "doublex",
        "responses",
        "requests_mock",
        "freezegun",
        "time_machine",
    }
)

#: Names a mock framework exports, in case one is imported under an alias.
BANNED_NAMES = frozenset(
    {
        "MagicMock",
        "AsyncMock",
        "NonCallableMock",
        "NonCallableMagicMock",
        "PropertyMock",
        "create_autospec",
        "mock_open",
        "patch",
    }
)

#: Fixture parameters that inject a mocking framework into a test body.
BANNED_FIXTURES = frozenset({"mocker"})


def _python_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCANNED_DIRS:
        files.extend(sorted((PACKAGE_ROOT / directory).rglob("*.py")))
    return files


def _module_is_banned(dotted: str) -> bool:
    parts = dotted.split(".")
    return any(".".join(parts[: i + 1]) in BANNED_MODULES for i in range(len(parts)))


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _module_is_banned(alias.name):
                    found.append(f"{path.name}:{node.lineno} import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _module_is_banned(module):
                found.append(f"{path.name}:{node.lineno} from {module} import ...")
            for alias in node.names:
                if alias.name in BANNED_NAMES:
                    found.append(f"{path.name}:{node.lineno} from {module} import {alias.name}")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            found.append(f"{path.name}:{node.lineno} name {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_NAMES:
            found.append(f"{path.name}:{node.lineno} attribute .{node.attr}")
        elif isinstance(node, ast.arg) and node.arg in BANNED_FIXTURES:
            found.append(f"{path.name}:{node.lineno} fixture {node.arg}")
    return found


def test_the_scan_actually_sees_the_package() -> None:
    """Guard against a vacuous pass from an empty or mis-rooted file set."""
    files = _python_files()
    assert len(files) >= 20, f"only {len(files)} files scanned — wrong root?"
    names = {p.name for p in files}
    assert {"ballistics.py", "terrain_ops.py", "test_ballistics.py"} <= names


def test_no_mock_framework_anywhere_in_the_package() -> None:
    """Zero mocks: parsed from source, across src/, tests/, and scripts/."""
    offenders = [v for path in _python_files() for v in _violations(path)]
    assert offenders == [], f"mock-framework usage found: {offenders}"


def test_the_scanner_detects_a_planted_mock(tmp_path: Path) -> None:
    """Positive control — a scan that cannot fire is not a gate.

    Each form a mock could enter by is planted in a throwaway file and must be
    reported: a plain import, an aliased import, a from-import of a mock class,
    a bare name reference, and a ``mocker`` fixture parameter.
    """
    planted = tmp_path / "planted.py"
    planted.write_text(
        "\n".join(
            (
                "import unittest.mock",
                "import pytest_mock as pm",
                "from unittest.mock import MagicMock",
                "def test_thing(mocker):",
                "    return MagicMock()",
            )
        ),
        encoding="utf-8",
    )
    reported = _violations(planted)
    assert len(reported) >= 5, reported
    joined = " ".join(reported)
    for expected in ("import unittest.mock", "pytest_mock", "MagicMock", "fixture mocker"):
        assert expected in joined, (expected, reported)

    # ...and a clean file must produce nothing, so the scanner is not simply
    # flagging everything it is handed.
    innocent = tmp_path / "innocent.py"
    innocent.write_text("import math\n\n\ndef f(x: float) -> float:\n    return math.sqrt(x)\n")
    assert _violations(innocent) == []


def test_scanner_rejects_unparseable_source(tmp_path: Path) -> None:
    """A file the scanner cannot parse must raise, never be silently skipped."""
    broken = tmp_path / "broken.py"
    broken.write_text("def f(:\n", encoding="utf-8")
    with pytest.raises(SyntaxError):
        _violations(broken)
