# TODO — the_living_daylights (SNIPER'S NEST)

SNIPER'S NEST is the PROJECT BOND film package for *The Living Daylights* (1987):
a deterministic domain core (sniper ballistics, riflescope optics, countersniper
glint/acoustic/triangulation detection, terrain line-of-sight and overwatch
ranking, a staged defection-handling protocol, and cover-weighted mountain/desert
routing) behind the frozen BOND-API `MissionProvider`. Measured on this machine on
2026-08-05, on the tree this file is committed with: **129 tests pass, 0 failures / 0 errors / 0 skips,
99.44% line+branch coverage on `src/`** (`uv run pytest tests/ --cov=src
--cov-fail-under=90`, Python 3.14.6), with `ruff check`, `ruff format --check`, and
`mypy src/ scripts/` all clean. The two SEVERE adversarial-audit findings (an
algebraically inverted `time_of_flight`, and a "cover audit" that shared its
private summary helper with the planner) are fixed and regression-pinned; what
remains below is real.

## Open work

### Correctness

**C1 — `assess_cover`'s `waypoint_cover` silently collapses a revisited cell.**
`src/the_living_daylights/terrain_ops.py:338` builds the map as a dict
comprehension keyed on `f"{r},{c}"`, so a path that visits the same cell twice
yields fewer entries than it has waypoints — while the docstring at
`terrain_ops.py:309` promises "per-waypoint concealment". `mean_cover`,
`min_cover`, and `min_cover_index` are computed over the full array and are
correct; only the reported map is lossy. Latent today because Dijkstra never
revisits a cell, but `assess_cover` is documented (`terrain_ops.py:305-307`) as
grading "an arbitrary sequence of waypoints — connected or not", so a caller
grading a hand-drawn there-and-back path gets a short map with no error.
*Done when:* either the return type carries one entry per waypoint in path order
(keyed by index, or a tuple), or the docstring states the dedup and
`assess_cover` raises on a repeated waypoint — and a test grades a path
containing a repeat and asserts the map's length against the path's.
*Command:* `uv run pytest tests/test_terrain_ops.py -v`

### Verification

**V1 — the overwatch visibility gate is green-by-construction on the shipped
configuration.** *(carried from the unresolved audit list.)*
`src/the_living_daylights/compute_mission.py:158` correctly selects the reported
nest through `visibility.best_overwatch` (top-scored *visible* candidate) rather
than `ranked[0]` (top-scored, possibly blind). The policy is right, but on the
mission's own terrain the two coincide: I re-measured it this session —
`ranked[0]` and `best_overwatch` both return cell `(6, 0)` at score
`0.71375`, and exactly 1 of 16 candidates is visible at all. Reverting
`compute_mission.py:158` to `ranked[0]` therefore leaves 125/125 passing. The
falsifying case lives only in a constructed grid
(`tests/test_visibility.py:105-133`,
`test_best_overwatch_skips_a_blind_top_scorer`), not on the production path. The
limitation is stated honestly in `tests/test_compute_mission.py:60-69` and
`manuscript/02_methodology.md:155-163` — it is disclosed, not bound.
*Done when:* mutating `compute_mission.py:158` to `ranked[0]` turns the suite red.
That needs an injection point — `mission_solution()`
(`compute_mission.py:33-35`) currently accepts only `wind_mps` and
`cover_weight`, so add an injectable terrain grid / candidate set, or find a
`TERRAIN_SEED` + `OVERWATCH_CANDIDATE_STEP` pair where a blind candidate
out-scores the visible one and pin the shipped solution against it.
*Command:* edit line 158 to `best = ranked[0]`, then
`uv run pytest tests/ -q` — it must fail. Revert.

**V2 — the plan gate / backstop verdict pairing has no negative control.**
*(carried from the unresolved audit list.)* `defection_protocol.koskov_scenario()`
(`src/the_living_daylights/defection_protocol.py:205`) and
`koskov_verification()` (`:312`) are two authored constant tables whose verdicts
agree. The manuscript no longer calls this independent corroboration
(`manuscript/04_conclusion.md:36-38`,
`manuscript/07_scope_and_related_work.md:64-66`), which is correct — but nothing
proves the pairing is even a *design-consistency* check, because no test shows
the two models can disagree. `tests/test_defection_protocol.py:62` and `:136`
each pin one model in isolation.
*Done when:* a test perturbs one table (e.g. raises a `RiskFactor` score past the
no-go threshold, or drops a passing `EvidenceCheck`) and asserts that exactly one
of the two verdicts moves — so agreement on the shipped tables is a fact that
could have come out otherwise.
*Command:* `uv run pytest tests/test_defection_protocol.py -v`

**V3 — the SPIE reference DOI has never been checked to resolve.**
*(carried from the unresolved audit list.)* `manuscript/references.bib:35` and
`manuscript/99_references.md:24` carry `10.1117/12.266747` for
`duckworth1996counter`. That digit correction arrived as an unattributed working-tree
edit, was absorbed by commit `1853596`, and is now internally consistent across both
files — but nobody has confirmed the DOI resolves to the cited paper. No other
reference in the file has been re-checked either.
*Done when:* every DOI in `manuscript/references.bib` has been resolved once
against doi.org and the result recorded (a check date in a comment, or a note in
`manuscript/AGENTS.md`).
*Command:* `curl -sIL https://doi.org/10.1117/12.266747 | head -1` (needs network
egress to doi.org, which the current sandbox denies — run it outside the sandbox).

**V4 — `figures/plots.py` `best is None` arm is unreachable in test.**
`src/the_living_daylights/figures/plots.py:183->186` is the only uncovered branch
outside the defensive-guard set (see Known limitations). `render_overwatch_figure`
(`plots.py:163-166`) reads `mission_solution()` directly and takes no injection
point, and no shipped seed produces a target that nothing can see.
*Done when:* `render_overwatch_figure` accepts an injected solution (mirroring
`manuscript_variables.py`'s injectable `solution=`), and a test renders a
figure from a solution whose `overwatch.best_cell` is `None`.
*Command:* `uv run pytest tests/test_figures.py --cov=src/the_living_daylights/figures --cov-report=term-missing`
— `plots.py` reaches 100%.

### Documentation

**D1 — the manuscript's reproducibility recipe type-checks less than the package
claims.** `manuscript/06_reproducibility.md:36` gives `uv run mypy src/`, while
`README.md:95` and `AGENTS.md:87` both give `uv run mypy src/ scripts/`, and
`README.md:99` claims mypy cleanliness "on `src/` and `scripts/`". An explicit
path argument overrides `pyproject.toml`'s `files = ["src", "scripts"]`, so a
reader following the manuscript never type-checks `scripts/`.
*Done when:* the three commands are identical.
*Command:* `grep -rn "mypy" README.md AGENTS.md manuscript/06_reproducibility.md`
— one command string.

**D2 — `AGENTS.md:88` documents a weaker no-mock check than the one that ships.**
The line is
`grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "no mocks"`.
It scans only `tests/`, matches four literal strings (an aliased
`import unittest.mock as m` slips through), and `|| echo` swallows the exit code
so it can never fail a gate. The real gate is
`tests/test_no_mock_frameworks.py:25` (`SCANNED_DIRS = ("src", "tests",
"scripts")`, AST-parsed, with a planted-mock positive control at `:111` and a
non-vacuity control at `:97`).
*Done when:* `AGENTS.md` cites `tests/test_no_mock_frameworks.py` instead of the
grep, matching how `manuscript/06_reproducibility.md:38-46` already describes it.
*Command:* `grep -n "MagicMock" AGENTS.md` — no match.

### Extension

**E1 — bind outcome persistence to the shared bond-utilities helper.** The blocker
recorded in the previous TODO is gone: `bond_utilities.mission_io.record_provenance_outcome`
now exists (`../bond-utilities/src/bond_utilities/mission_io.py:153`), alongside
`verify_provenance` (`:212`) and `append_outcome` (`:296`). This package still
computes its own hash — `mission.py:207` fills `Provenance(input_hash=input_hash())`
from `compute_mission.input_hash()` — and `pyproject.toml` does not depend on
`bond-utilities` at all.
*Done when:* a persisted record's `provenance` block equals `execute()`'s
`Provenance` field for field, and `verify_provenance(record)` is `True`.
*Command:* `uv run pytest tests/test_mission.py -k provenance -v`

## Known limitations (not bugs)

* **The two-bearing triangulation residual is arithmetic, not a measurement.**
  `settings.TRIANGULATION_OBSERVERS` holds exactly two observers, so the
  least-squares fit is two equations in two unknowns and the residual is
  identically zero for any non-parallel pair. It is not evidence of localization
  accuracy. Pinned by `tests/test_countersniper.py:96`
  (`test_two_bearing_residual_is_zero_by_construction_not_measured`) with a
  positive control at `:117` proving the residual code path can report a real
  number. Making it informative needs a bearing-uncertainty model, which
  `manuscript/07_scope_and_related_work.md` declares out of scope. **If a noise
  model is ever added, this stops being a limitation and the disclosure
  paragraphs must be revisited.**
* **The defection scenario and its backstop verification are both authored
  tables.** There is no independent scenario source for a fictional mission —
  any second table would be written by the same hand. The manuscript says so
  outright (`04_conclusion.md:36-38`). V2 above is about binding the weaker
  consistency claim, not about manufacturing independence.
* **The cover audit is a cross-implementation check, not corroboration.**
  `terrain_ops.assess_cover` (vectorised numpy) and `_summarize` (scalar loop)
  no longer share a helper, and `tests/test_terrain_ops.py` checks both against
  the test's own re-derived oracle rather than against each other. That catches
  implementation drift; both still encode one concealment definition, so a wrong
  definition would be reproduced identically by both.
* **The exfil route is below the field's mean concealment.** Measured, not
  hidden: the shipped route scores ~0.484 mean cover against a grid mean of
  ~0.490. `compute_mission.py:129-136` computes the `cover_weight=0.0` baseline
  and the field mean so the comparison is reported rather than asserted.
* **Five uncovered defensive guards keep `src/` off 100%.** `_sample_at`'s
  zero-width span, `capture_zero`'s exact-zero crossing, Dijkstra's empty-heap
  exit and the unreachable-goal `raise`. All are unreachable on a 4-connected
  grid and a strictly advancing integrator. The exhaustive line-by-line list is
  `docs/_generated/COUNTS.md` — do not maintain a second enumeration. (V4's
  `plots.py` branch is listed there too, but is closeable, so it is a TODO.)
* **Out of scope by design:** stochastic adversary modelling; full atmosphere
  (spin, Magnus, Coriolis, transonic drag rise, layering); spectral or
  polarization radiometry; ballistic shockwave geometry and acoustic multipath;
  bearing uncertainty; earth curvature and refraction in line of sight; human
  factors and communications. Each is listed with a reason in
  `manuscript/07_scope_and_related_work.md`.

## Verification

Run from this directory. All four are green at commit `1853596`.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
# -> 125 passed; TOTAL 99.44% (line+branch on src/); gate is 90%.
#    This command enforces coverage AND the no-mock AST scan
#    (tests/test_no_mock_frameworks.py). It does NOT run ruff or mypy.

uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
# -> "All checks passed!" and "39 files already formatted".

uv run mypy src/ scripts/
# -> "Success: no issues found in 20 source files".

uv run python scripts/z_generate_manuscript_variables.py && git status --short
# -> writes only into the git-ignored output/ tree; git status must stay empty.
#    NOTE this proves hygiene, not determinism: output/ is git-ignored, so a
#    clean status survives a generator that writes different bytes every run.
#    Determinism is bound by tests/test_regeneration_determinism.py (two full
#    subprocess regenerations across a second boundary, SHA-256 per file).

# The same two-run comparison, by hand:
R1=$(mktemp -d); R2=$(mktemp -d)
uv run python scripts/z_generate_manuscript_variables.py --output-root "$R1" >/dev/null
sleep 1
uv run python scripts/z_generate_manuscript_variables.py --output-root "$R2" >/dev/null
diff -r "$R1" "$R2" && echo "byte-identical"
# -> "byte-identical".
```

Live measured totals live in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
By "checked in" this file means the working tree of this standalone checkout,
whose canonical remote is the public
`github.com/docxology/bond-the_living_daylights`: commit path-scoped inside this
package only, and never force-push or rewrite history.


## Round-2 (2026-08-06)

Hostile-review pass and manuscript deepening. Measured on this machine on
2026-08-06 on the tree this section is committed with: **135 tests pass, 0
failures / 0 errors / 0 skips, 99.52% line+branch coverage on `src/`**
(`uv run pytest tests/ --cov=src --cov-fail-under=90`, Python 3.14.6), with
`ruff check`, `ruff format --check`, and `mypy src/ scripts/` all clean
(baseline before this round: 129 tests, 99.44%).

### Findings fixed, with test evidence

| # | Defect (hostile-review) | Fix | Regression / negative control |
|---|---|---|---|
| F1 | `terrain_ops.assess_cover`'s `waypoint_cover` was a dict keyed `"r,c"`, so a path revisiting a cell silently dropped a concealment reading — contradicting the "per-waypoint concealment" docstring (C1). `mean_cover`/`min_cover`/`cover_points` were always right; only the map was lossy. | `waypoint_cover` is now a tuple of `(cell, cover)` pairs, one per waypoint in path order | `test_assess_cover_keeps_one_entry_per_repeated_waypoint` grades a path containing `(0,0)` twice and asserts the map length equals the path length and the revisit appears twice |
| F2 | `optics.mil_dot_range(-1, 6)` returned **−167 m** and `mil_dot_range(0, 6)` returned **0 m** with no error; `mils_for_size` had the same gap — a non-positive target size silently produced a nonsense range on a ranging relation. | reject `target_size_m <= 0` in `mil_dot_range` and `mils_for_size` with `ValueError` | `test_mil_dot_range_and_inverse_reject_non_positive_target_size` asserts the four raises and that a positive silhouette still ranges (1.8 m / 6 mils → 300 m) |
| F3 | `ballistics.wind_hold_mrad(0, ...)` raised an opaque **`ZeroDivisionError`** (the hold divides by range); `wind_drift` accepted a zero range silently. | reject non-positive `range_m` in both with `ValueError`, matching `time_of_flight`/`drop_at_range` | `test_wind_functions_validate_range` asserts both raise on `0.0` and `-10.0` and that zero wind at a positive range still yields a zero hold |
| F4 | `countersniper.triangulate_position` returned `(nan, nan, nan)` for a NaN bearing or inf observer — a **fail-open** on a detection/localization path (the Nan/inf-propagation class). | reject any non-finite observer coordinate or bearing with `ValueError`; finite inputs ⇒ finite determinant, so one guard roots it out | `test_triangulate_position_rejects_non_finite_inputs` asserts NaN bearing, inf observer, and `-inf` bearing all raise, and the valid pair still yields a finite fix |
| F5 | (V2) nothing proved the plan-gate / backstop-verdict agreement was even a *design*-consistency check — no test showed the two scoring paths can disagree. | — (test-only) | `test_plan_gate_and_backstop_can_disagree` perturbs **only** the `verify` stage over the no-go threshold and asserts the plan verdict moves to `no-go` while the untouched backstop stays `conditional` — they genuinely can diverge, so shipped agreement is a real fact |
| F6 | (V4) `figures/plots.py`'s `best is None` arm of `render_overwatch_figure` was the last uncovered branch outside the defensive-guard set, with no injection point (the shipped grid always has a visible nest). | `render_overwatch_figure` gained an injectable `solution=` (mirroring `manuscript_variables`) | `test_render_overwatch_figure_none_best` renders the plate from a solution whose `overwatch.best_cell` is `None`; `plots.py` is now **100%** (previous 99.22%) |

### Documentation tightened

* (D1) `manuscript/06_reproducibility.md`'s gate block now runs
  `uv run mypy src/ scripts/`, matching `README.md` and `AGENTS.md` (it had
  `uv run mypy src/`, so a reader never type-checked `scripts/`).
* (D2) `AGENTS.md`, `docs/AGENTS.md`, and `docs/agent_instructions.md` now
  cite `tests/test_no_mock_frameworks.py` as the no-mock gate (the AST scan)
  instead of a four-literal `grep ... || echo "no mocks"` that could never
  fail and could miss an aliased import.
* (V3) every DOI in `manuscript/references.bib` was resolved at doi.org on
  2026-08-06 and the results recorded as a header comment: the corrected
  `10.1117/12.266747` resolves to Duckworth, Gilbert & Barger, *Proc. SPIE*
  2938:262–275 (the cited paper), and the `ledeczi2005`, `dijkstra1959`, and
  `bresenham1965` DOIs all resolve to their cited works.
* `manuscript/02_methodology.md` gained an **Input-contract hardening**
  subsection documenting the four new numeric guards (F2–F6 style) with their
  owning regression tests. Prose stays token-free metric-wise.

### Remainder for a future round

* **V1 (carried):** `compute_mission`'s overwatch visibility gate is still
  green-by-construction on the shipped terrain — with candidate steps 1–3 the
  top-scored candidate is visible at every density probed this round, so
  `best_overwatch` and `ranked[0]` coincide. The policy is correct and the
  limitation is disclosed in `02_methodology.md` and
  `tests/test_compute_mission.py`; binding it at the compute layer needs a
  mission-solution injection point for the terrain grid / candidate set (or a
  constructed-grid falsifying case), which would change what
  "the single place any number is computed" accepts. Deliberately not churned
  this round.
* **TODO C1's alternative branch** (docstring states the dedup and raises on a
  repeated waypoint) was not taken; instead the map now carries one entry per
  waypoint, which preserves the data.
* The three remaining uncovered locations (`ballistics.py` 305, 384;
  `terrain_ops.py` 253→268, 269) are unreachable defensive guards on a
  4-connected grid and a strictly advancing integrator; a future hardening
  could add a disconnected-grid injection to close the Dijkstra pair, but they
  are disclosed in `docs/_generated/COUNTS.md` and are not bugs.
