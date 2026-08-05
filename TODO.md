# SNIPER'S NEST — TODO

Status of `the_living_daylights` after the phase-5 documentation and
code-review pass. "Built" is what exists and is tested; "Open" is real
remaining work; nothing here is aspirational.

## Built

**Pure domain core** (`src/the_living_daylights/`) — stdlib + numpy only:

| Module | Built | Tests |
| --- | --- | --- |
| `ballistics.py` | RK4 point-mass trajectory, rifle zero + near/far zero, drop, time of flight, crosswind drift + wind hold, rules of engagement, cello-case shelf packing, assembly time | `tests/test_ballistics.py` |
| `optics.py` | MOA↔mrad, click value + whole-click solutions, mil-dot ranging + inverse, holdover, parallax, field of view, zero click schedule | `tests/test_optics.py` |
| `countersniper.py` | Glint geometry / contrast / angular fraction / SNR / detection CDF, sound speed, crack-bang delay + range, least-squares bearing triangulation with residual | `tests/test_countersniper.py` |
| `visibility.py` | Bresenham line of sight with clearance and first blocker, viewsheds, weighted overwatch ranking, `best_overwatch` | `tests/test_visibility.py` |
| `defection_protocol.py` | Staged weighted risk scoring, monotonic approval + plan gate, KOSKOV scenario; backstop `EvidenceCheck` / certainty / verdict | `tests/test_defection_protocol.py` |
| `terrain_ops.py` | Seeded elevation/landcover/cover grid, blended step cost, Dijkstra routing, separately implemented cover audit | `tests/test_terrain_ops.py` |
| `settings.py` | Every fixed mission parameter (single source of truth) | exercised throughout |
| `compute_mission.py` | The one deterministic mission solution + SHA-256 `input_hash` | `tests/test_compute_mission.py` |
| `mission.py` | Frozen BOND-API `MissionProvider` (brief/recon/plan/execute/debrief) + module-level `GADGETS` | `tests/test_mission.py` |
| `manuscript_variables.py` | Token hydration with an enforceable `require_outputs` gate and injectable solution; strict tree resolution | `tests/test_manuscript_variables.py` |
| `figures/plots.py` | Four deterministic plates (ballistics, exfil route, glint-vs-range, overwatch nests) | `tests/test_figures.py` |

**Thin scripts** — `brief.py`, `recon.py`, `plan.py`, `execute.py`,
`debrief.py`, `00_preflight.py`, `z_generate_manuscript_variables.py`, all
covered by real subprocess smoke tests.

**Manuscript** — the full canonical section set (`00`–`07`, `99`) plus
`preamble.md`, `config.yaml`, `references.bib`, and the directory's own README /
AGENTS / SYNTAX. Every metric arrives as a token; the bibliography cites real,
checkable sources.

**Documentation** — `README.md`, `AGENTS.md`, this file, and the full `docs/`
baseline (`README.md`, `AGENTS.md`, `agent_instructions.md`, `architecture.md`,
`testing_philosophy.md`, `_generated/COUNTS.md`).

**Gates** — `pytest --cov=src --cov-fail-under=90` green (live totals in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md)); `ruff` + `mypy`
clean; zero mocks; deterministic; zero `template[_]code_project` strings; own
git repo, path-scoped commits.

## Fixed in the phase-5 review

- `pack_cello_case` reported each part's lane and span by re-zipping placements
  against the caller's input order, while the packer sorts parts
  width-descending internally — so `barrel_receiver` (0.62 m) was reported in
  `stock`'s 0.48 m slot and vice versa. Placements now carry their own part;
  `test_cello_layout_binds_each_part_to_its_own_slot` is the regression guard.
- The manuscript's methodology described the glint geometry factor as a
  **cosine** sun-elevation term; the code uses `sin`.
- The methodology cited the ballistic holdover token as if it were the mil-dot
  *reticle span*, producing a false statement about how ranging works.
- `manuscript/config.yaml` declared its `mission:` block "the single
  authoritative source for the domain modules" — it is read by nothing. It is
  now labelled a reader-facing echo and pinned to `settings.py` by a test.
- `generate_variables`'s `require_outputs` guard could never fire. It now
  checks named required sections and accepts an injected `solution=`, so it is
  testable — and is tested against each section removed in turn.
- Removed two unreachable guards that provided no safety (`ballistics`
  zero-area check behind a validating constructor; a `tau <= 0` branch made
  dead by adding real `v0` validation to `time_of_flight`).
- Removed dead code: an unused `mountain_c` landcover alias and an unused
  `landcover` parameter on `terrain_ops._cover`.
- Strengthened weak assertions: the cover-weight trade-off is now `>` not `>=`
  (a `>=` would pass with the parameter ignored entirely), and the exposure
  term's exact cost contribution is asserted.

## Open

- **bond-utilities provenance (not yet bound).** The mission computes its own
  deterministic `input_hash`. When the shared helper lands, delegate outcome
  persistence to `bond_utilities.mission_io.record_provenance_outcome`.
  Acceptance: a recorded outcome whose provenance block equals `execute()`'s
  `Provenance` field for field.
- **Unreachable-by-construction guards.** `plan_route`'s "goal is unreachable"
  raise cannot fire on a fully connected 4-adjacent grid, `_sample_at`'s
  zero-width-span branch cannot fire on a monotone trajectory, and
  `capture_zero`'s exact-zero crossing needs a float sample landing precisely
  on the sight line. All are kept as defensive guards for future callers, and
  all are why `src/` coverage is not 100%. If the terrain model ever grows
  impassable cells, the first becomes live and needs a test. The authoritative,
  exhaustive list of uncovered lines and partial branches lives in
  [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — do not maintain a
  second enumeration here.
- **`plots.py` `best is None` branch** is uncovered: no seed currently produces
  a target that no candidate can see. Covering it needs a fixture grid rather
  than the mission's own, which would mean parameterizing the figure functions.

## Not in scope (deliberate)

Stochastic adversary modelling; full atmosphere (spin, Magnus, Coriolis,
transonic drag rise, layering); spectral or polarization radiometry; ballistic
shockwave geometry and acoustic multipath; bearing uncertainty models; earth
curvature or refraction in line of sight; human factors and communications.
These are enumerated with reasons in
[`manuscript/07_scope_and_related_work.md`](manuscript/07_scope_and_related_work.md).
