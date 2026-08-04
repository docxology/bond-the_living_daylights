# Introduction

*The Living Daylights* (1987) is the mission that frames {{CODENAME}}: a
covering sniper must protect a high-value defection, carry a sniper rifle
concealed in a cello case, refuse a lethal shot at an innocent, and exfiltrate
through hostile mountain and desert terrain. Each beat is a tractable,
well-posed computation. This package turns those beats into deterministic
algorithms backed by real data and reproducible figures.

The software is structured as a pure, infrastructure-free domain core
([`src/the_living_daylights/`](../src/the_living_daylights/)):

* [**`ballistics.py`**](../src/the_living_daylights/ballistics.py) — rifle
  zero, windage, rules-of-engagement (the trigger-guard hold), and cello-case
  packing.
* [**`defection_protocol.py`**](../src/the_living_daylights/defection_protocol.py) —
  a staged, risk-scored defection-handling pipeline.
* [**`terrain_ops.py`**](../src/the_living_daylights/terrain_ops.py) —
  mountain/desert terrain modelling, least-cost route planning, and cover
  assessment.

The package integrates with the frozen BOND-API mission protocol:
[`mission.py`](../src/the_living_daylights/mission.py) implements the
`MissionProvider` lifecycle (brief, recon, plan, execute, debrief) against
`bond_api`'s frozen dataclasses and registers the film's gadgets. The mission
adapter and the manuscript both read from the single deterministic
[`compute_mission.mission_solution()`](../src/the_living_daylights/compute_mission.py),
so prose metrics are never hand-authored.

## Reader's guide

The manuscript is organized by the mission procedure: methodology (section 2)
derives each algorithm, results (section 3) reports the computed mission
solution with the two figures, experimental setup (section 5) fixes the
parameters, and reproducibility (section 6) ties results to hashes and the live
test gate.
