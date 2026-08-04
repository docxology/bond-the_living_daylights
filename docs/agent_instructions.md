# SNIPER'S NEST — Agent Instructions

Behavioral rules for AI agents working inside this package. These are hard
constraints, not suggestions. Read this file before modifying anything.

## Hard rules

1. **Scope = this package only.** Work inside
   `projects/working/bond/the_living_daylights/` exclusively. Never touch
   sibling packages, bond root files, or the template repo.
2. **Local-only.** There is no remote; never push. Commit inside this package's
   own git repo with path-scoped commits.
3. **Pure domain core.** `ballistics.py`, `defection_protocol.py`,
   `terrain_ops.py`, `compute_mission.py`, `settings.py` are
   infrastructure-free and importable without `bond_api`. Only `mission.py`
   imports `bond_api` (the frozen protocol adapter).
4. **Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch`, or
   `create_autospec` anywhere in `tests/`. Tests use real data and real
   computation, deterministically.
5. **Frozen protocol.** `mission.py` implements the BOND-API `MissionProvider`
   contract exactly. Do not invent or change protocol types.
6. **No hardcoded metrics in prose.** Every number in the manuscript flows
   through `compute_mission.mission_solution()` and
   `manuscript_variables.generate_variables()` as a `{{TOKEN}}`.
7. **Deterministic.** Fixed seeds; no wall-clock in persisted artifacts except
   the regeneration timestamp.
8. **Thin scripts.** Business logic lives in `src/`; `scripts/` are thin
   per-phase CLIs with a `sys.path` bootstrap.

## Verification checklist (run before submitting)

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # expectations: clean after the path-scoped commit
```

Live test count + coverage live in [`_generated/COUNTS.md`](_generated/COUNTS.md).

## Discoverability contract

The orchestrator finds this film as the slug `the_living_daylights`:
`src/the_living_daylights/mission.py` exposes a top-level `MissionProvider`
class whose `film` attribute is `the_living_daylights`. See
`bond_api.discovery.load_provider`.
