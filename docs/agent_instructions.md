# SNIPER'S NEST — Agent Instructions

Operational instructions for anyone — human or agent — modifying
`the_living_daylights`. These are hard constraints. Read this file before
touching anything.

## Hard rules

1. **Scope is this repository only.** This is the standalone checkout of
   `the_living_daylights` (originally `projects/working/bond/the_living_daylights`
   in the suite working tree), published at the private
   `github.com/docxology/bond-the_living_daylights`. Never touch a sibling BOND
   package, the bond suite root files, or the template repository.
2. **Commit scope.** `origin` is that GitHub remote. Commit path-scoped inside
   this repository, push only `main`, and never force-push or rewrite history.
3. **Keep the core pure.** `ballistics.py`, `optics.py`, `countersniper.py`,
   `visibility.py`, `defection_protocol.py`, `terrain_ops.py`, `settings.py`,
   and `compute_mission.py` import stdlib and numpy only. They must remain
   importable with `bond_api` absent from the environment. Only `mission.py`
   imports `bond_api`.
4. **Do not change the frozen protocol.** `mission.MissionProvider` must keep
   exposing exactly `brief`, `recon`, `plan`, `execute`, `debrief` with their
   current signatures, its `film` attribute, and the module-level `GADGETS`
   registry plus `register_gadgets(registry)`. `bond-cli`, the coordinator's
   reconcile pass, and the orchestrator consume these across every package.
   Add depth *inside* the package; never rename or re-signature the surface.
# zero-mock gate is an AST scan of src/, tests/, scripts/ (tests/test_no_mock_frameworks.py)
   `create_autospec`, or `mocker.patch` anywhere in `tests/`. Real data, real
   computation, deterministically.
6. **One source of numbers.** Anything the package reports must come from
   `compute_mission.mission_solution()`. Do not compute a metric in
   `mission.py`, in a script, in a figure, or in the manuscript.
7. **No hand-authored metrics in prose.** Every number in
   `manuscript/NN_*.md` is a token produced by
   `manuscript_variables.generate_variables()`. Do not quote a test count or a
   coverage percentage anywhere except `docs/_generated/COUNTS.md`; describe
   the gate instead.
8. **Deterministic.** Fixed seeds, no global RNG, no wall-clock in a persisted
   artifact. `Provenance.wall_time_s` stays 0.0 so outcomes compare across runs.
9. **Thin scripts.** Business logic lives in `src/`. `scripts/` files are
   per-phase CLIs with a `sys.path` bootstrap, argument parsing, a call into
   `src/`, and printing. Nothing else.
10. **Type hints and docstrings** on every public function, with units stated.
    `mypy` runs on `src/` and `scripts/` and must stay clean.
11. **No exemplar lineage.** The tree currently carries zero
    `template_code_project` strings and must stay that way; the fork contract
    is described in `STANDALONE.md` without naming the exemplar.

## Common tasks

### Add a domain concept

1. Pure logic into the matching `src/the_living_daylights/*.py` (or a new
   module if it is genuinely a new concept).
2. Parameters into `settings.py` **and** the `mission:` echo in
   `manuscript/config.yaml` — the mirror test fails until both are updated.
3. Expose the results through `compute_mission.mission_solution()`. A new
   top-level section must also be added to
   `manuscript_variables.REQUIRED_SOLUTION_SECTIONS`.
4. Add a token in `generate_variables()` and cite the token in the manuscript.
5. Add real-data tests covering happy path, boundaries, and every `raise`.
6. Run the gates; regenerate `docs/_generated/COUNTS.md`.

### Add a gadget

Extend the mapping inside `register_gadgets()` in `mission.py`. Do not change
the function's signature, and do not replace the module-level `GADGETS`
instance — the coordinator inspects it by identity at import time.

### Regenerate the manuscript and figures

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

This resolves all sections into `output/manuscript/`, writes the token map to
`output/data/manuscript_variables.json`, and renders four figures into
`output/figures/`. Strict mode fails on any leftover placeholder. `output/` is
git-ignored, so a rerun must leave `git status` clean — that is a live
determinism check.

Note: prose that needs to *mention* a placeholder must not write literal double
braces, or strict resolution will reject the section. Describe it in words.

### Regenerate the live counts

Run the coverage gate, read the real numbers off the run, and write them into
`docs/_generated/COUNTS.md`. Never estimate them, and never copy them into
other prose.

## Verification checklist (run all of it before claiming done)

`uv sync` / `uv run` resolve `bond-api` from the vendored copy at
`vendor/bond-api/`; `STANDALONE.md` records its provenance and the check that
keeps it byte-identical to upstream.

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py
grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "no mocks"
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo "no lineage"
git status --short   # expect clean after the path-scoped commit
```

Read the output. A command that ran is not the same as a command that passed,
and an exit code of 0 on a pytest run that collected nothing is not a pass.

## Discoverability contract

The orchestrator finds this film by the slug `the_living_daylights`:
`src/the_living_daylights/mission.py` exposes a top-level `MissionProvider`
class whose `film` attribute is `the_living_daylights`.
`bond_api.discovery.load_provider('the_living_daylights', …)` imports that
module, binds `film`, and verifies the runtime-checkable protocol. Anything
that breaks that import breaks fleet-wide discovery.
