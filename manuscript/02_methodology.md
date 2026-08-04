# Methodology

Three concept modules define the algorithms: sniper ballistics, staged
defection handling, and terrain routing. All are deterministic and
infrastructure-free.

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
compact takedown rifle; `pack_cello_case` runs deterministic bottom-left shelf
packing to decide whether the {{CELL_NUM_PARTS}} components fit the cello
case, reporting {{CELL_LANES}} lanes at {{CELL_EFFICIENCY}} packing efficiency
and a {{CELL_ASSEMBLY_S}} s field assembly time.

## Defection-handling protocol (`defection_protocol.py`)

`assess_defection` evaluates an ordered, fixed sequence of stages
(contact, snatch, verify, exfiltrate, relocate). Each stage carries weighted
risk factors; the stage hazard is the exposure-weighted mean of factor scores,
and approval is monotonic — a stage cannot proceed until its predecessors pass,
and the first non-`go` stage becomes the plan gate. The canonical KOSKOV
scenario (`koskov_scenario`) is deterministic by construction.

## Terrain ops (`terrain_ops.py`)

`generate_terrain` builds a seeded elevation + landcover + cover grid
(`landcover_name` indexes the table). `step_cost` blends per-metre landcover
cost, an ascent penalty, and an exposure penalty `cover_weight·(1 − cover)`.
`plan_route` runs Dijkstra's algorithm over 4-adjacent moves with strict
tie-breaking to find the least-cost path; `assess_cover` audits any route's
concealment (mean cover, cover points, and the least-covered segment).

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
  (`mil_dot_range`) fixes the target at {{OPT_MIL_RANGE_M}} m from a
  {{OPT_HOLDOVER_MILS}} mil reticle span; `holdover_mils` converts the
  ballistic drop into the reticle holdover, and `parallax_shift_m` models the
  first-order sight shift when the target range differs from the
  parallax-focus range ({{OPT_PARALLAX_MM}} mm at the {{BAL_TARGET_RANGE}} m
  target). Ranging follows the standard mil-dot doctrine
  [@fm2310sniper].

## Countersniper detection (`countersniper.py`)

A hostile sniper is found three ways, all deterministic:

* **Optic glint** — the lens reflects sunlight: `glint_geometry_factor`
  combines a cosine sun-elevation term with a specular azimuth falloff
  ({{CS_GLINT_GEOMETRY}} at the mission's {{CS_AZIMUTH_DELTA_DEG}}° sun–observer
  offset), and `glint_contrast` compares the reflected radiance against sky
  radiance (the solar reference follows [@astmg173]). `glint_snr` multiplies
  that range-independent contrast by the lens's angular size at the observer,
  so SNR falls as range²; `glint_detection_probability` is the
  signal-detection CDF of SNR against a threshold
  ([@vantrees1968]). At {{CS_GLINT_RANGE_M}} m the hostile optic yields
  SNR {{CS_GLINT_SNR}} and P(det) = {{CS_GLINT_PDET}}.
* **Acoustic crack-bang** — the flash-to-bang delay scaled by the speed of
  sound `c(T) = 331.3 + 0.606·T` ([@kinsler2000]) places the shot
  {{CS_CRACK_BANG_M}} m away from the {{CRACK_BANG_DELAY_S}} s delay; the
  mission's {{CS_SOUND_SPEED}} m/s at {{AIR_TEMP_C}} °C.
* **Bearing triangulation** — `triangulate_position` solves the least-squares
  intersection of true-azimuth bearings: the normal equations place the
  hostile at ({{CS_TRI_X_M}}, {{CS_TRI_Y_M}}) m with a
  {{CS_TRI_RESIDUAL_M}} m residual (acoustic localization per
  [@duckworth1996counter], [@bedford2008modelling]).

## Terrain visibility (`visibility.py`)

`line_of_sight` walks a deterministic Bresenham cell line between two cells and
blocks when an intermediate cell's terrain+cover top rises above the
interpolated sight ray minus a clearance; `viewshed` collects every cell
visible from an observer. `rank_overwatch_positions` scores candidate sniper
nests for the extraction site as a weighted blend of target visibility,
proximity, cover, and elevation advantage; `best_overwatch` returns the top
visible position. Viewshed methodology follows the terrain-visibility
literature [@fisher1996viewshed].

## Evidence verification (`defection_protocol.py`)

The verify stage's backstop model (`EvidenceCheck`, `verification_certainty`,
`backstop_verdict`) accumulates weighted evidence into a certainty score and
maps it onto cleared/conditional/rejected verdicts — the operational analogue
of sequential verification against documentary and telegraphic backstops.
