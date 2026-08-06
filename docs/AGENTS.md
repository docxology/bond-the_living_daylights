# docs/ — SNIPER'S NEST agent documentation

Rulebook for agents and developers working inside `the_living_daylights`. Every
item below is a hard constraint, not a suggestion.

| File | Purpose |
| --- | --- |
| [`agent_instructions.md`](agent_instructions.md) | The behavioral rules. Read first. |
| [`architecture.md`](architecture.md) | Module-by-module architecture, dependency direction, and the frozen `MissionProvider` surface. |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock doctrine, determinism proofs, the coverage gate, and the test inventory. |
| [`README.md`](README.md) | Directory index and reading order. |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | Live test total and achieved coverage. Regenerated, never hand-edited. |

## Key conventions

- **Pure core / thin adapter.** `ballistics`, `optics`, `countersniper`,
  `visibility`, `defection_protocol`, `terrain_ops`, `settings`, and
  `compute_mission` are infrastructure-free (stdlib + numpy). `mission.py` is
  the *only* module that imports `bond_api`, and it holds no business logic.
- **Frozen protocol.** `MissionProvider`'s five methods
  (`brief`/`recon`/`plan`/`execute`/`debrief`) and the module-level `GADGETS`
  registry are consumed across the suite by `bond-cli`, the coordinator, and
  the orchestrator. Their public shape does not change. Deepen inside.
- **One solution.** Every number the package reports comes from
  `compute_mission.mission_solution()`. The mission outcome, the manuscript,
  and the figures are all readers of that one call.
# zero-mock gate is an AST scan of src/, tests/, scripts/ (tests/test_no_mock_frameworks.py)
  `create_autospec` anywhere in `tests/`.
- **Determinism.** Fixed seeds, no global RNG, no wall-clock in persisted
  artifacts — no exception. `MANUSCRIPT_DATE` is the committed `paper.date`
  from `manuscript/config.yaml`. Two runs of
  `scripts/z_generate_manuscript_variables.py` on one interpreter produce a
  byte-identical `output/` tree, and
  `tests/test_regeneration_determinism.py` proves it by running the script
  twice across a second boundary.
- **No hardcoded metrics in prose.** Numbers reach the manuscript only as
  tokens from `manuscript_variables.generate_variables()`. Test counts and
  coverage percentages live in `_generated/COUNTS.md` and are quoted nowhere
  else — documentation describes the *gate*, not a snapshot.
- **Parameters in two places, pinned.** `settings.py` is authoritative;
  `manuscript/config.yaml`'s `mission:` block is a reader-facing echo, and a
  test compares them key for key in both directions.
- **No exemplar lineage.** The tree carries zero `template[_]code_project`
  strings; the fork contract lives in `STANDALONE.md`.
- **Local-only.** No remote, never push. Commit inside this package's own git
  repo with path-scoped commits.

## Verification

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "no mocks"
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo "no lineage"
git status --short   # must be clean after a path-scoped commit
```

Regenerate the live counts after any change to the suite:
[`_generated/COUNTS.md`](_generated/COUNTS.md).
