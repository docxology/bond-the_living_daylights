# Reproducibility

## Determinism

Every number in this manuscript is a pure function of fixed, documented inputs
([`src/the_living_daylights/settings.py`](../src/the_living_daylights/settings.py)).
The mission solution uses a fixed seed ({{TER_SEED}}); the only randomness in
the whole stack is the seeded terrain generator in
[`terrain_ops.generate_terrain`](../src/the_living_daylights/terrain_ops.py),
which is itself deterministic for a fixed seed. No wall-clock value enters any
persisted artifact — there is no exception. The manuscript carries a date
({{MANUSCRIPT_DATE}}), but it is the committed `paper.date` from
[`manuscript/config.yaml`](config.yaml), read like any other parameter, not the
moment of hydration. An earlier version of this package stamped
`datetime.now()` into this page and into
`output/data/manuscript_variables.json`, which made the byte-identical claim
below false on every rerun; the clock has been removed rather than the claim
weakened.

The BOND-API `MissionOutcome` carries a Provenance record with a stable
`input_hash` (a sha256 of the canonical mission solution), so any report can be
audited against the code without re-running the film's I/O.

## Artifacts and regeneration

| Artifact | Producer | Location |
|---|---|---|
| Mission report / figures | [`scripts/execute.py`](../scripts/execute.py), [`scripts/z_generate_manuscript_variables.py`](../scripts/z_generate_manuscript_variables.py) | `output/` (regenerable, git-ignored) |
| Resolved manuscript sections | `z_generate_manuscript_variables.py` | `output/manuscript/` |
| Ballistics + terrain figures | [`src/the_living_daylights/figures/plots.py`](../src/the_living_daylights/figures/plots.py) | `output/figures/ballistics_trajectory.png`, `output/figures/terrain_exfil_route.png` |
| Countersniper + overwatch figures | [`src/the_living_daylights/figures/plots.py`](../src/the_living_daylights/figures/plots.py) | `output/figures/glint_detection.png`, `output/figures/overwatch_nests.png` |
| Hydrated token map | `z_generate_manuscript_variables.py` | `output/data/manuscript_variables.json` |

## Verification gate

The package is verified with three separate commands, and it is worth stating
precisely what each one does and does not enforce:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90   # tests + coverage + no-mock scan
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

The pytest command enforces two things: ≥90% line+**branch** coverage of `src/`
measured over real computation, and — since
[`tests/test_no_mock_frameworks.py`](../tests/test_no_mock_frameworks.py) — the
absence of any mocking framework, parsed from the AST of every `.py` file under
`src/`, `tests/`, and `scripts/`. That second gate carries its own positive
control: a planted `MagicMock`, aliased import, and `mocker` fixture must all
be reported, so the scan cannot pass by being blind. An earlier version of this
section claimed the single pytest command also enforced lint and type
cleanliness. It does not; `ruff` and `mypy` are the second and third commands
above and nothing in `tests/` invokes them.

The achieved figures are recorded in
[`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md) rather than quoted
here, so no prose number can go stale against the gate.

Three tests carry the anti-drift load specifically:

* [`test_all_manuscript_tokens_are_generated`](../tests/test_manuscript_variables.py)
  cross-references every brace-delimited placeholder in these sections against
  the live token map, so none can survive un-generated.
* `test_require_outputs_rejects_an_incomplete_solution` gutted-section by
  gutted-section proves the hydration gate actually fires — it is checked
  against a solution missing each required section in turn, not merely against
  the healthy one.
* `test_config_mission_block_mirrors_settings` pins the reader-facing
  `mission:` echo in `config.yaml` to `settings.py`, key for key.

Re-running `z_generate_manuscript_variables.py` on one interpreter regenerates
a byte-identical `output/` tree — every resolved manuscript section, the token
JSON, and all four figure PNGs. The interpreter is the stated scope because
`PYTHON_VERSION` is itself a token; nothing else in the tree varies between
runs.

That is a claim, so it is bound by a test rather than by assertion.
[`test_regeneration_determinism.py`](../tests/test_regeneration_determinism.py)
runs the generator twice as a real subprocess, deliberately straddling a
wall-clock second boundary, and compares a SHA-256 of every produced file. A
second test in that file AST-scans `src/` for any clock call
(`datetime.now`/`utcnow`, `date.today`, `time.time`, `time.time_ns`,
`time.monotonic`) reachable from the persisted-artifact path, and carries a
positive control: a planted clock call in a temporary module must be reported,
so the scan cannot pass by being blind. Note what the older
`git status --short` check does *not* prove — `output/` is git-ignored, so that
tree stays clean whatever the bytes say.
