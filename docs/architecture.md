# SNIPER'S NEST — Architecture

## Layer map

```
src/the_living_daylights/
  settings.py              mission parameters — the single source of truth
  ballistics.py            point-mass RK4 external ballistics + the cello case
  optics.py                riflescope click math, mil-dot ranging, parallax, FOV
  countersniper.py         optic-glint radiometry, acoustic ranging, triangulation
  visibility.py            line of sight, viewsheds, overwatch ranking
  defection_protocol.py    staged risk scoring + backstop evidence verification
  terrain_ops.py           seeded terrain grid, cover-weighted Dijkstra, cover audit
  compute_mission.py       THE one deterministic mission solution + provenance hash
  manuscript_variables.py  token hydration from config.yaml + the solution
  figures/plots.py         four deterministic matplotlib plates
  mission.py               THIN adapter — the only module that imports bond_api
scripts/                   thin per-phase CLIs (brief/recon/plan/execute/debrief …)
tests/                     real-data, zero-mock tests (one file per module)
```

## The modules, and what each computes

### `settings.py` — parameters

Every fixed number the mission uses: the projectile and muzzle velocity, zero
and target ranges, the `ScopeSpec`, sun/observer geometry and lens properties
for glint, air temperature and the crack-bang delay, triangulation observers
and bearings, overwatch eye height / clearance / range / candidate step,
defection thresholds, terrain seed and geometry, and the `CelloCase` interior.
Imports only `ballistics` and `optics` (for their dataclasses).
`manuscript/config.yaml` carries a **reader-facing echo** of these values,
pinned to this module by
`tests/test_manuscript_variables.py::test_config_mission_block_mirrors_settings`.

### `ballistics.py` — external ballistics and the concealment rig

* `Projectile`, `standard_atmosphere_density`, `drag_factor`,
  `ballistic_coefficient` — the drag model `a = ρ·A·C_d/(2m)·v²`, with an
  exponential barometric density for altitude.
* `trajectory` — fixed-step classical RK4 over the 6-D `(x, y, z, vx, vy, vz)`
  flight ODE with a crosswind term. No RNG, no adaptive stepping, so runs are
  byte-identical.
* `zero_scope` — bisection on the simulated impact height for the muzzle
  elevation that puts the round on the sight line at the zero range;
  `capture_zero` returns the near and far crossings of that sight line.
* `drop_at_range`, `time_of_flight` — integrated drop, and a closed-form
  constant-drag-decay flight time.
* `wind_drift`, `wind_hold_mrad` — lateral crosswind offset and the milliradian
  hold that cancels it.
* `engagement_decision` — the rules-of-engagement precedence chain that yields
  the film's trigger-guard hold.
* `disassemble_takedown_rifle`, `pack_cello_case`, `assembly_time` — the
  bottom-left shelf packer that decides whether the takedown rifle hides in a
  cello case. Placements carry the part they belong to, so a reported slot is
  always the slot of the part it names.

### `optics.py` — the riflescope

`ScopeSpec` plus `moa_to_mrad` / `mrad_to_moa` / `click_value_mrad` /
`clicks_for_angle` / `angle_from_clicks` (whole-click turret arithmetic),
`mil_dot_range` / `mils_for_size` (the milliradian ranging relation and its
inverse), `holdover_mils` (drop → reticle holdover), `parallax_shift_m`
(first-order sight shift off the parallax-focus range), `field_of_view_m`, and
`zero_click_schedule` (ballistic solution → elevation/wind click counts).

### `countersniper.py` — finding the other shooter

* `glint_geometry_factor` — `sin(sun elevation)` illumination times a Gaussian
  specular azimuth falloff.
* `glint_contrast` — reflected radiance over sky radiance; **range-independent**.
* `glint_angular_fraction` — the lens's solid angle over one resolution cell,
  capped at 1; this is where the `1/range²` behavior enters.
* `glint_snr`, `glint_detection_probability`, `normal_cdf` — SNR and its
  signal-detection CDF against a threshold.
* `speed_of_sound`, `crack_bang_delay`, `crack_bang_range` — flash-to-bang
  range with `c(T) = 331.3 + 0.606·T`.
* `triangulate_position` — closed-form least-squares intersection of
  true-azimuth bearings with an RMS perpendicular residual; raises on a
  singular (parallel/collinear) system rather than returning a fictitious fix.

### `visibility.py` — terrain visibility and the sniper's nest

`line_of_sight` (integer Bresenham cell walk against the interpolated sight ray
minus a clearance, returning the first blocker), `viewshed` (deterministic
row-major scan → visible cells, count, fraction), `elevation_gain`,
`OverwatchRanking`, `rank_overwatch_positions` (weighted blend of visibility,
proximity, cover, and elevation advantage, normalized over the candidate set,
with weights validated to sum to 1), and `best_overwatch` (top-ranked *visible*
candidate, or `None`). A blind candidate keeps up to 0.60 of the score, so
`ranked[0]` can be blind; `compute_mission` selects through `best_overwatch`.

### `defection_protocol.py` — the staged plan and its backstop

`RiskFactor`, `StageRiskInput`, `StageAssessment`, `DefectionAssessment`;
`stage_score` (exposure-weighted mean, clamped); `assess_defection` (monotonic
approval — the first non-`go` stage becomes the plan gate, and a `no-go` blocks
everything after it); `koskov_scenario` (the canonical fixed scenario).
Separately, the verification backstop: `EvidenceCheck`,
`verification_certainty`, `backstop_verdict`, `koskov_verification`. The two
halves read no shared variable, but both `koskov_scenario` and
`koskov_verification` are hardcoded constant tables authored here together to
encode one story beat. Their agreement is a design-consistency check between
two scoring paths — not corroboration.

### `terrain_ops.py` — ground and routes

`TerrainGrid` (elevation, landcover, cover height; validated square and
in-table), `generate_terrain` (seeded blurred Gaussian relief + categorical
landcover + jittered cover height), `landcover_name`, `step_cost` (landcover
cost + ascent penalty + `cover_weight·(1 − cover)` exposure, scaled by cell
size), `plan_route` (Dijkstra over 4-adjacent moves with strict tie-breaking),
`RouteResult`, and `assess_cover` — a **separately implemented** audit
(vectorised numpy; it deliberately does not call `_summarize`) that grades any
proposed path, not only the planner's own. Agreement with the planner's summary
catches implementation drift; it is not independent evidence, since both encode
one concealment definition.

### `compute_mission.py` — the single solution

`mission_solution()` runs every module above against `settings.py` and returns
one nested mapping (`ballistics`, `rules_of_engagement`, `optics`,
`countersniper`, `cello_case`, `defection`, `verification`, `terrain`,
`overwatch`, `determinism`). `input_hash()` is its SHA-256 over canonical
compact JSON with sorted keys. This is the *only* place the numbers are
computed; the mission adapter, the manuscript, and the figures are all readers.

### `manuscript_variables.py` and `figures/plots.py` — presentation

`generate_variables()` maps the solution plus `manuscript/config.yaml` onto the
token map, guarded by `REQUIRED_SOLUTION_SECTIONS` (and accepting an injected
`solution=` so that guard is testable rather than decorative);
`resolve_manuscript_tree()` substitutes into `manuscript/NN_*.md` and fails on
any leftover placeholder. `plots.py` renders four plates — ballistics, terrain
route, glint-vs-range, overwatch nests — from the same solution.

## `mission.py` and the frozen protocol

`mission.py` is the package's contract surface and holds no business logic. It
implements the `bond_api` `MissionProvider` structurally — a top-level class of
that exact name whose `film` attribute is the package slug — across the frozen
five-stage lifecycle:

| Stage | Signature | What it does here |
| --- | --- | --- |
| `brief` | `() -> MissionBrief` | Declares objectives, `Asset`s (rifle profile, scope spec, cello case, seeded grid) and `Constraint`s (determinism, rules of engagement). |
| `recon` | `(ReconRequest) -> ReconReport` | Returns `Finding`s for the goal, environment, ballistics, optics, countersniper means, concealment, and constraints. |
| `plan` | `(MissionBrief) -> MissionPlan` | An eight-`Step` deterministic flow: zero → windage → optics → countersniper → defection → verification → route → conceal. |
| `execute` | `(MissionPlan) -> MissionOutcome` | Calls `mission_solution()`, annotates the completed steps, and attaches a `Provenance` carrying the package version, the fixed seed, `input_hash()`, and a zero wall time (no clock in a persisted artifact). |
| `debrief` | `(MissionOutcome) -> Debrief` | Wraps the outcome with the standing lessons. |

Gadgets are registered through `bond_api.registry.GadgetRegistry` by
`register_gadgets(registry)`, and bound into the module-level `GADGETS` at
import time so a coordinator that merely inspects the module sees the field kit.
Discovery (`bond_api.discovery.load_provider('the_living_daylights', …)`)
imports `the_living_daylights.mission`, binds `film`, and verifies the
runtime-checkable protocol.

**This public shape is frozen.** `bond-cli`, the coordinator's reconcile pass,
and the orchestrator consume `MissionProvider`, the five method names, and
`GADGETS` across every package in the suite. Deepen inside the package; do not
rename or re-signature these.

## Dependency direction

```
scripts/              →  src/the_living_daylights (mission, manuscript_variables, figures)
mission.py            →  bond_api (frozen protocol)  +  the pure core
manuscript_variables  →  compute_mission  +  manuscript/config.yaml
figures/plots.py      →  compute_mission  +  the pure core
compute_mission       →  ballistics, optics, countersniper, visibility,
                         defection_protocol, terrain_ops, settings
pure core             →  stdlib + numpy ONLY   (no bond_api, no I/O, no infrastructure)
```

The arrows are one-directional. The pure core lifts into any Python environment
without `bond_api`; `mission.py` is the single integration seam. Nothing in the
core imports `mission`, `manuscript_variables`, or `figures`.

## Where to add a concept

1. Add pure logic to the matching `src/the_living_daylights/*.py` module — or a
   new one, if it is genuinely a new concept (stdlib + numpy only, full type
   hints, a docstring stating the model and its units).
2. Put its fixed parameters in `settings.py` **and** echo them in
   `manuscript/config.yaml`; the mirror test fails until you do both.
3. Expose any new number through `compute_mission.mission_solution()`. If it is
   a new top-level section, add it to
   `manuscript_variables.REQUIRED_SOLUTION_SECTIONS`.
4. Surface it as a token in `manuscript_variables.generate_variables()` and cite
   the token — never the literal number — in `manuscript/NN_*.md`.
5. Add a real-data test file (or extend the matching one) under `tests/`, with
   no mocks, covering the happy path, the edge cases, and the error branches.
6. Re-run the gates (see [`agent_instructions.md`](agent_instructions.md)) and
   regenerate [`_generated/COUNTS.md`](_generated/COUNTS.md).

## Constraints

- `mission.py` must not grow business logic; it adapts and registers, nothing more.
- The public shape of `MissionProvider` and `GADGETS` is frozen across the suite.
- Results must be deterministic: fixed seeds, no global RNG, no wall-clock in
  persisted artifacts (the manuscript's regeneration timestamp is the one
  documented exception).
- No metric may be hand-authored in prose; it must arrive as a token.
- Everything under `output/` is regenerable and git-ignored.
