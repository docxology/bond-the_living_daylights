# Methodology

Six concept modules define the algorithms, in mission order: sniper ballistics
(`ballistics.py`), riflescope optics (`optics.py`), countersniper detection and
localization (`countersniper.py`), terrain visibility and overwatch selection
(`visibility.py`), staged defection handling with backstop evidence
verification (`defection_protocol.py`), and terrain routing (`terrain_ops.py`).
`settings.py` fixes their parameters and `compute_mission.py` composes them into
one solution. All are deterministic and infrastructure-free: stdlib and numpy
only, no I/O, no wall-clock, and no randomness beyond the seeded terrain grid.

## Sniper ballistics (`ballistics.py`)

The round is modelled as a **point-mass projectile with quadratic air drag**
plus gravity, integrated with a fixed-step classical RK4
(`ballistics.trajectory`). The drag deceleration follows the standard law
`a_drag = (rho·A·C_d / 2m)·v²`; the ballistic coefficient
`BC = m / (A·C_d)` for the {{BAL_CALIBER_MM}} mm service round is
{{BAL_BC}} kg/m² at a muzzle velocity of {{BAL_MUZZLE_VELOCITY}} m/s and bullet
mass {{BAL_BULLET_MASS_G}} g.

**Rifle zero.** `ballistics.zero_scope` solves the muzzle elevation such that
the round lands at height zero at the zero range {{BAL_ZERO_RANGE}} m while the
sight line — starting `{{BAL_SIGHT_HEIGHT}}` m above bore — passes through the
same point. Bisection on the simulated impact height yields an elevation of
{{BAL_ELEVATION_MRAD}} mrad. `capture_zero` then returns the two ranges where
the trajectory crosses the sight line: near {{BAL_NEAR_ZERO}} m and far
{{BAL_FAR_ZERO}} m.

**Windage.** Crosswind is treated as a drag-driven lateral relaxation toward
the wind speed. `ballistics.wind_drift` integrates the lateral offset; at the
{{BAL_TARGET_RANGE}} m target a {{BAL_WIND_MPS}} m/s full-value wind produces a
{{BAL_WIND_DRIFT}} m drift, i.e. a {{BAL_WIND_HOLD_MRAD}} mrad wind hold.
`wind_hold_mrad` returns `-drift / range · 1000`.

**Rules of engagement.** `ballistics.engagement_decision` encodes the film's
central morality: lethal fire only on a confirmed hostile target. A hostile
non-target whose weapon is present draws a **trigger-guard**
(`disable_weapon`) shot rather than a kill, so an innocent third party — the
cellist — is never engaged.

**The cello case.** `disassemble_takedown_rifle` returns the components of a
compact takedown rifle ({{CELL_PART_NAMES}}); `pack_cello_case` runs
deterministic bottom-left shelf packing to decide whether the
{{CELL_NUM_PARTS}} components fit a {{CELL_CASE_L_M}} x {{CELL_CASE_W_M}} x
{{CELL_CASE_D_M}} m case interior. Parts are laid along the case's long axis
and processed width-descending, opening a new lane across the case's width when
the current lane runs out of length; each part must also clear the interior
cross-section on its own. The rig packs into {{CELL_LANES}} lanes with a
longest-lane fill of {{CELL_PACKED_LENGTH_M}} m and an areal packing efficiency
of {{CELL_EFFICIENCY}} (the parts' summed footprint over the case floor), and
`assembly_time` gives a {{CELL_ASSEMBLY_S}} s field assembly time. Because the
packer reorders parts internally, each placement carries the part it belongs
to, so a reported slot is always the slot of the part it names.

## Countersniper optics (`optics.py`)

The riflescope is a fixed-parameter `ScopeSpec` ({{OPT_MAGNIFICATION}}x,
{{OPT_OBJECTIVE_MM}} mm objective, {{OPT_CLICK_MRAD}} mrad clicks). Two
conversion families matter operationally:

* **Turret clicks** — `clicks_for_angle` converts an angular correction
  (milliradians) into whole clicks of the turret's click unit, and
  `zero_click_schedule` turns the ballistic solution into the scope's
  elevation/wind click counts ({{OPT_ELEVATION_CLICKS}} elevation /
  {{OPT_WIND_CLICKS}} wind for the zeroed mission).
* **Mil-dot ranging** — the milliradian relation `range = size·1000/mils`
  (`mil_dot_range`) fixes an {{OPT_TARGET_SIZE_M}} m standing silhouette
  spanning {{MIL_READING_MILS}} mils on the reticle at {{OPT_MIL_RANGE_M}} m,
  and `mils_for_size` inverts it. `holdover_mils` converts the ballistic drop
  into a {{OPT_HOLDOVER_MILS}} mil reticle holdover, and `parallax_shift_m`
  models the first-order sight shift when the target range differs from the
  {{OPT_PARALLAX_FOCUS_M}} m parallax-focus range ({{OPT_PARALLAX_MM}} mm at
  the {{BAL_TARGET_RANGE}} m target). `field_of_view_m` divides the eyepiece's
  apparent field by the magnification and returns the chord at range. Ranging
  follows the standard mil-dot doctrine [@fm2310sniper].

## Countersniper detection (`countersniper.py`)

A hostile sniper is found three ways, all deterministic:

* **Optic glint** — the lens reflects sunlight. `glint_geometry_factor`
  multiplies a `sin(sun elevation)` illumination term (a higher sun puts more
  direct irradiance on the lens; {{CS_SUN_ELEVATION_DEG}}° here) by a Gaussian
  specular falloff `exp(-(Δaz/half-width)²)` with a
  {{CS_SPECULAR_HALF_DEG}}° half-width, giving {{CS_GLINT_GEOMETRY}} at the
  mission's {{CS_AZIMUTH_DELTA_DEG}}° sun–observer offset. `glint_contrast`
  spreads the collected power `I·A·ρ·g` (reflectivity ρ =
  {{CS_LENS_REFLECTIVITY}}) over the specular cone's solid angle and divides by
  sky radiance; range cancels, which is why glints stay visible far out (the
  solar reference follows [@astmg173]). `glint_angular_fraction` then supplies
  the range dependence — the lens's solid angle `A/R²` over one
  {{CS_RESOLUTION_MRAD}} mrad resolution cell, capped at 1 — so `glint_snr`
  falls as 1/range² once the lens no longer fills a cell.
  `glint_detection_probability` is the signal-detection CDF of SNR against a
  threshold ([@vantrees1968]). At {{CS_GLINT_RANGE_M}} m the hostile optic
  yields SNR {{CS_GLINT_SNR}} and P(det) = {{CS_GLINT_PDET}}.
* **Acoustic crack-bang** — the flash-to-bang delay scaled by the speed of
  sound `c(T) = 331.3 + 0.606·T` ([@kinsler2000]) places the shot
  {{CS_CRACK_BANG_M}} m away from the {{CRACK_BANG_DELAY_S}} s delay; the
  mission's {{CS_SOUND_SPEED}} m/s at {{AIR_TEMP_C}} °C.
* **Bearing triangulation** — `triangulate_position` minimizes the summed
  squared perpendicular distance from a point to each observer's bearing line,
  solving the resulting 2x2 normal equations in closed form and rejecting a
  singular (parallel or collinear) system rather than returning a fictitious
  fix. From {{CS_NUM_OBSERVERS}} observers the crossed bearings place the
  hostile at ({{CS_TRI_X_M}}, {{CS_TRI_Y_M}}) m with an RMS perpendicular
  residual of {{CS_TRI_RESIDUAL_M}} m (acoustic shooter localization per
  [@duckworth1996counter], [@ledeczi2005countersniper]).

## Terrain visibility (`visibility.py`)

`line_of_sight` walks a deterministic integer Bresenham cell line
[@bresenham1965] between observer and target and blocks when an intermediate
cell's terrain-plus-cover top rises above the linearly interpolated sight ray
minus a clearance ({{OW_CLEARANCE_M}} m here); the ray runs from
`elevation + eye height` ({{OW_EYE_HEIGHT_M}} m) at each end. `viewshed`
collects every cell visible from an observer in a deterministic row-major scan
and reports the visible count and fraction; viewshed methodology follows the
terrain-visibility literature [@fisher1996viewshed].

`rank_overwatch_positions` scores each candidate nest as
`w_vis·visible + w_dist·(1 − d/d_max) + w_cover·cover + w_elev·gain/gain_max`
with weights (0.40, 0.25, 0.20, 0.15) that are validated to sum to 1;
candidates beyond {{OW_MAX_RANGE_CELLS}} cells are dropped as out of practical
engagement range, and distance and elevation gain are normalized over the
surviving set. Positions that cannot see the target keep their other terms but
score zero for visibility, so the ranking stays total and deterministic (ties
break on cell order). `best_overwatch` returns the top-ranked *visible*
candidate, or `None` when nothing sees the site.

## Defection-handling protocol (`defection_protocol.py`)

`assess_defection` evaluates an ordered, fixed sequence of
{{DEF_NUM_STAGES}} stages ({{DEF_STAGE_NAMES}}). Each stage carries weighted
`RiskFactor`s; the stage hazard is the exposure-weighted mean
`sum(w_i·s_i)/sum(w_i)` clamped to [0, 1], so a dominant high-score factor
cannot be averaged away by benign ones. A stage is `go` at or below the
{{DEF_GO_THRESHOLD}} threshold, `conditional` at or below
{{DEF_CONDITIONAL_THRESHOLD}}, and `no-go` above it; the plan score is the
conservative maximum across stages.

Approval is **monotonic**: the assessment walks the stages in order, marking
each `approved` while every predecessor is `go`. The first stage whose verdict
is not `go` becomes the **plan gate**, and a `no-go` at any stage blocks every
stage after it. The protocol validates membership of the canonical stage set
rather than position, so a caller may supply the stages in its own order. The
canonical KOSKOV scenario (`koskov_scenario`) fixes the factor weights and
scores, so the mission's report is reproducible.

## Evidence verification (`defection_protocol.py`)

The verify stage's backstop model (`EvidenceCheck`, `verification_certainty`,
`backstop_verdict`) accumulates {{VER_NUM_CHECKS}} weighted checks
({{VER_CHECK_LABELS}}) into a certainty score under the same exposure-weighting
scheme as `stage_score`, then maps that certainty onto a
cleared/conditional/rejected verdict — the operational analogue of sequential
verification against documentary and telegraphic backstops. It is an
*independent* corroboration of the staged assessment: the two models share no
inputs, so agreement between the plan gate and the backstop verdict is
evidence, not tautology.

## Terrain ops (`terrain_ops.py`)

`generate_terrain` builds a seeded elevation + landcover + standing-cover grid:
elevation is a wrap-padded 3x3-blurred Gaussian field renormalized to the
requested relief, landcover is a seeded categorical draw over the table
(`landcover_name` indexes it), and cover height is the landcover's base cover
plus seeded jitter. Effective concealment is the cover height normalized to the
{{TER_CELL_M}} m cell's cover threshold and clipped to [0, 1] — a pure function
of the cover-height field, so an edited field is honoured verbatim downstream.

`step_cost` blends the per-metre landcover cost, an ascent penalty proportional
to the climb per cell, and an exposure penalty `cover_weight·(1 − cover)`, then
scales by the cell size. `plan_route` runs Dijkstra's algorithm
[@dijkstra1959] over 4-adjacent moves with strict `(cost, row, col)`
tie-breaking, which is what makes the route byte-reproducible. `assess_cover`
is an *independent* audit that grades any proposed path — not only Dijkstra's —
reporting mean and minimum concealment, the least-covered step, the
high-concealment waypoints, and per-waypoint cover.

## Composition (`compute_mission.py`)

`mission_solution()` is the single entry point that runs every module above
against `settings.py` and returns one nested mapping: ballistics, rules of
engagement, optics, countersniper, cello case, defection, verification,
terrain, and overwatch. The extraction site is defined non-arbitrarily as the
grid's global elevation minimum ({{OW_TARGET_CELL}}) — a wadi-like low point,
the hardest kind of site to overwatch — and candidate nests are sampled every
{{OW_CANDIDATE_STEP}} cells in each axis.

`input_hash()` fingerprints that mapping as canonical compact JSON with sorted
keys under SHA-256. The mission adapter, the manuscript token map, and the
figures all read the same call, so no consumer can report a number the others
did not compute.
