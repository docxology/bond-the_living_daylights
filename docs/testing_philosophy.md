# SNIPER'S NEST — Testing Philosophy

## Zero mocks, real data, real computation

There is no mocking framework anywhere in `tests/` — no `unittest.mock`, no
`MagicMock`, no `@patch`, no `create_autospec`, no `mocker.patch`. This is not a
style preference. A mocked test asserts that the code called the function you
told it to call; a real-data test asserts that the code got the right answer.
Only the second one can fail when the physics is wrong.

Concretely, "real" means:

* **Ballistics are integrated, not looked up.** `test_ballistics.py` solves a
  zero and then re-simulates the trajectory to confirm the round actually
  arrives at height ~0 at the zero range.
* **Terrain is generated, routed, and audited.** The seeded grid is built by
  numpy and Dijkstra walks it. The `assess_cover` audit is a second
  implementation (vectorised numpy against the planner's scalar loop, sharing
  no helper), but the suite does *not* check the two against each other — an
  equality between two callers of one definition holds no matter how wrong that
  definition is. Both are checked against a third calculation performed in the
  test from the raw `cover_height` field.
* **Figures are rendered.** `test_figures.py` writes real PNGs under `tmp_path`,
  reads them back, and renders twice to compare bytes.
* **Scripts are executed**, not imported and called. `test_scripts_smoke.py`
  runs each CLI as a subprocess via `sys.executable`, so a broken CLI produces a
  real non-zero exit code.
* **The manuscript is hydrated** from the live token map and cross-referenced
  against the actual section files on disk.

## Determinism is a tested property, not a claim

Every result is a pure function of documented inputs. The only randomness in the
stack is the seeded terrain generator, and it is seeded. The suite proves this
rather than asserting it:

* identical mission solutions across calls (byte-equal dicts);
* identical provenance `input_hash` across calls;
* identical terrain arrays and identical routes for a fixed seed;
* identical figure **bytes** across two renders;
* identical token maps across repeated calls, with no clock to pin.

No wall-clock value enters a persisted artifact, with no exception.
`Provenance.wall_time_s` is fixed at 0.0 precisely so an outcome is comparable
across runs, and `generate_variables()` reads no clock at all — the manuscript's
date is the committed `paper.date` from `manuscript/config.yaml`.

This is the one place a pinned-input test was actively harmful. The old
`generate_variables(now=…)` override made every determinism test pass while the
unpinned production path stamped `datetime.now()` into the manuscript and the
token JSON: the test froze the exact input that was broken. The replacement,
`tests/test_regeneration_determinism.py`, pins nothing — it runs the real
generator script twice across a wall-clock second boundary and hashes the
artifacts. A probe that injects the value it is meant to be checking cannot
fail on it.

## Tests must be able to fail

A test that cannot fail is worse than no test — it reports safety it does not
provide. Two rules follow.

**Prefer strict comparisons to permissive ones.** `assert covered.mean_cover >
route.mean_cover` catches a `cover_weight` that stopped reaching the planner;
`>=` would pass even if the parameter were ignored entirely. Where this package
uses `>=`, it is because equality is a real intended outcome — never to be safe.

**Prove a guard fires by breaking its input.** The `require_outputs` gate in
`generate_variables` is exercised against a solution with *each* required
section removed in turn, not merely against the healthy one. That is why
`generate_variables` accepts an injected `solution=`: without an injection
point the guard would be untestable, and therefore decorative.

The anti-drift checks are held to the same standard:

* `test_all_manuscript_tokens_are_generated` scans the real `manuscript/NN_*.md`
  files, so it fails the moment prose cites a token the code does not produce.
* `test_config_mission_block_mirrors_settings` compares `config.yaml`'s
  reader-facing `mission:` echo to `settings.py` key for key, and asserts the
  key *sets* match — so adding a parameter to one side without the other fails,
  in both directions.
* `test_cello_layout_binds_each_part_to_its_own_slot` checks that each named
  slot is exactly as long as the part it names. This is a regression guard: the
  packer reorders parts internally, and a layout assembled by re-zipping
  placements against the caller's input order silently swaps slots between parts
  of different lengths.
* `test_step_cost_exposure_term_is_consumed` asserts the *exact* cost delta a
  given `cover_weight` must produce on a fully exposed cell, so the parameter
  cannot be quietly dropped from the cost model.

## Coverage gate

Coverage is measured on `src/` only, **line and branch**, and must be ≥90%:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

The achieved percentage and the test total are recorded in
[`_generated/COUNTS.md`](_generated/COUNTS.md) and nowhere else — no prose in
this repository quotes them, so no prose can go stale. What the documentation
claims is the *gate*, and the gate runs every time.

Coverage is a floor, not a goal. A few branches stay uncovered because they are
unreachable through any public path — the "goal is unreachable" guard in
`plan_route`, for instance, cannot fire on a fully connected 4-adjacent grid,
and `_sample_at`'s zero-width-span guard cannot fire on a monotone trajectory.
Those are kept as defensive guards against future callers. Where a guard turned
out to be both impossible to trigger *and* to provide no safety — an
`if area <= 0` behind a constructor that already rejects a non-positive caliber
— it was deleted rather than papered over with a coverage pragma.

## Test inventory

| File | Coverage focus |
| --- | --- |
| `tests/test_ballistics.py` | Projectile validation, drag/BC identities, atmospheric density, RK4 trajectory determinism, zero solving with bracket clamping and a full bisection budget, near/far-zero capture including its zero- and one-crossing degenerate cases, interpolation boundaries, free-fall derivative, drop, the closed-form time of flight against both the vacuum lower bound and the RK4 trajectory's own time array, windage and hold, all six ROE branches, cello-case packing with per-part slot binding, lane non-overlap, and width exhaustion |
| `tests/test_optics.py` | `ScopeSpec` validation, MOA↔mrad round trips, per-unit click value, whole-click rounding, mil-dot ranging and its inverse, holdover, parallax sign and its zero at the focus range, field of view, and the zero click schedule |
| `tests/test_countersniper.py` | Normal-CDF reference values, glint geometry (elevation and azimuth falloff), angular fraction and its saturation cap, contrast, the SNR range gradient, detection-probability monotonicity, sound speed and crack-bang round trip, exact two- and three-observer triangulation fixes, the structural zero of a two-bearing residual, a three-bearing positive control pinned to a hand-derived 20.4124 m residual, and singular/degenerate rejection |
| `tests/test_visibility.py` | LOS on flat ground and against a blocking ridge, out-of-bounds errors, full and range-limited viewsheds, elevation gain, overwatch ranking order and the visibility weight's effect, the range filter and weight-sum validation, `best_overwatch` returning `None` when nothing sees the target, and the positive control where the top-*scored* candidate is blind so `best_overwatch` picks a different cell |
| `tests/test_defection_protocol.py` | `RiskFactor` / `StageRiskInput` / `DefectionAssessment` validation, weighted stage scoring, an all-`go` plan, threshold and missing-stage errors, the KOSKOV conditional gate, no-go blocking of follow-on stages, evidence-check validation, weighted certainty, and the backstop verdict bands |
| `tests/test_terrain_ops.py` | Seeded grid determinism and shape/landcover validation, the landcover table, step-cost adjacency plus the exposure term's exact contribution, Dijkstra route determinism, the strict cover-vs-cost trade-off, the cover audit and the planner both checked against the test's own oracle, the audit grading a hand-picked non-Dijkstra path, and cover-height semantics |
| `tests/test_compute_mission.py` | Solution keys and cross-module values, byte-determinism, hash stability and shape, wind sensitivity, the strict cover-weight response, the reported overwatch nest being visible, and the cover term measured against both baselines (planner with the term off, and the grid mean) |
| `tests/test_mission.py` | Runtime-checkable protocol compliance, brief identity and content, recon findings, plan steps, deterministic execution and provenance, the full five-stage flow, and gadget registration both module-level and explicit |
| `tests/test_manuscript_variables.py` | Config loading and its three malformed-input rejections, token content, determinism with nothing pinned, the missing/blank `paper.date` rejection, the live token cross-reference, strict resolution failure, the `require_outputs` gate under each missing section, solution injection, and the `config.yaml` ↔ `settings.py` mirror |
| `tests/test_figures.py` | All four plates render to real files, byte-determinism across renders, and default output-directory resolution |
| `tests/test_scripts_smoke.py` | Every thin CLI runs as a real subprocess with exit code 0 and produces its expected stdout and artifacts |
| `tests/test_regeneration_determinism.py` | The byte-identical-regeneration claim itself: two full generator runs as real subprocesses, deliberately straddling a wall-clock second boundary, compared SHA-256 per file; plus an AST scan of `src/` for any clock call, with a positive control that plants five clock calls the scanner must report |

## Adding a test

Put it in the file matching the module. Cover the happy path, the boundary, and
every `raise` — then ask the question that matters: *what would have to break
for this assertion to fail?* If the answer is "nothing", rewrite it.
