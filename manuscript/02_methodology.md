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
