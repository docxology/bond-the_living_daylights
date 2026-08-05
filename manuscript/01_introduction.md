# Introduction

*The Living Daylights* (1987) is the mission that frames {{CODENAME}}: a
covering sniper must protect a high-value defection, carry a sniper rifle
concealed in a cello case, refuse a lethal shot at an innocent, find and range
the hostile shooter working the same corridor, and exfiltrate through mountain
and desert terrain. Each beat is a tractable, well-posed computation. This
package turns those beats into deterministic algorithms backed by real data and
reproducible figures.

## The domain core

The software is structured as a pure, infrastructure-free domain core
([`src/the_living_daylights/`](../src/the_living_daylights/)). Every module
below is stdlib + numpy only — no `bond_api`, no I/O, no wall-clock, no global
RNG:

* [**`ballistics.py`**](../src/the_living_daylights/ballistics.py) — a
  point-mass RK4 external-ballistics core: rifle zero, near/far-zero capture,
  crosswind drift and the wind hold, rules of engagement (the trigger-guard
  hold), and deterministic cello-case shelf packing with field assembly time.
* [**`optics.py`**](../src/the_living_daylights/optics.py) — the riflescope:
  MOA↔mrad turret arithmetic, whole-click solutions, mil-dot reticle ranging
  and its inverse, ballistic holdover in mils, first-order parallax, and true
  field of view.
* [**`countersniper.py`**](../src/the_living_daylights/countersniper.py) —
  finding the other shooter: optic-glint radiometry (geometry factor, sky
  contrast, angular fraction, detection probability), acoustic crack-bang
  ranging with a temperature-dependent sound speed, and least-squares bearing
  triangulation of crossed azimuths.
* [**`visibility.py`**](../src/the_living_daylights/visibility.py) — terrain
  line of sight over a Bresenham cell walk, viewsheds, and the ranked
  overwatch (sniper's nest) selection the title's image demands.
* [**`defection_protocol.py`**](../src/the_living_daylights/defection_protocol.py) —
  a staged, risk-scored defection-handling pipeline with monotonic approval and
  a plan gate, plus the backstop evidence-verification model that corroborates
  that gate.
* [**`terrain_ops.py`**](../src/the_living_daylights/terrain_ops.py) —
  a seeded mountain/desert grid (elevation, landcover, standing cover),
  cover-weighted Dijkstra route planning, and an independent cover audit that
  grades any proposed path, not only the planner's own.
* [**`settings.py`**](../src/the_living_daylights/settings.py) — the single
  authoritative source of mission parameters, echoed for readers in
  [`manuscript/config.yaml`](config.yaml).
* [**`compute_mission.py`**](../src/the_living_daylights/compute_mission.py) —
  the one deterministic mission solution that composes all of the above.

## Protocol integration

The package integrates with the frozen BOND-API mission protocol:
[`mission.py`](../src/the_living_daylights/mission.py) implements the
`MissionProvider` lifecycle (brief, recon, plan, execute, debrief) against
`bond_api`'s frozen dataclasses and registers the film's field kit in a
module-level `GADGETS` registry. It is the only module in the package that
imports `bond_api`, and it carries no business logic of its own.

The mission adapter and the manuscript both read the single deterministic
[`compute_mission.mission_solution()`](../src/the_living_daylights/compute_mission.py),
so prose metrics are never hand-authored: every number below arrives as a
brace-delimited token hydrated by
[`manuscript_variables.py`](../src/the_living_daylights/manuscript_variables.py),
and a test fails the build if any placeholder in these sections is not
generated.

## Reader's guide

The manuscript follows the mission procedure: methodology (section 2) derives
each algorithm module by module, results (section 3) reports the computed
mission solution with the four figures, the conclusion (section 4) states what
was shown, experimental setup (section 5) fixes the parameters, reproducibility
(section 6) ties results to the provenance hash and the live test gate, and
section 7 states the scope boundary and the related work.
