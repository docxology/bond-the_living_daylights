# docs/ — SNIPER'S NEST documentation hub

Documentation for `the_living_daylights`, the PROJECT BOND film package for
*The Living Daylights* (1987), mission codename **SNIPER'S NEST**. This
directory holds the operating rules and the design record; the code's own
docstrings hold the per-function contracts.

## What lives here

| File | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Agent-facing rulebook for this directory: conventions, invariants, verification commands. |
| [`agent_instructions.md`](agent_instructions.md) | The hard behavioral rules — scope, purity, zero mocks, frozen protocol, token discipline. Read first. |
| [`architecture.md`](architecture.md) | Module-by-module architecture of `src/`, the dependency direction, how the pieces compose, and how `mission.py` implements the frozen `bond_api` `MissionProvider`. |
| [`testing_philosophy.md`](testing_philosophy.md) | Why there are no mocks, what "real data" means here, how determinism is proven, and the per-file test inventory. |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | **Regenerated, not hand-written.** The live test total and achieved coverage. Nothing else in the repo quotes those two numbers. |

## Reading order

1. [`../AGENTS.md`](../AGENTS.md) — package overview, layer contract, verification commands.
2. [`agent_instructions.md`](agent_instructions.md) — the constraints you must not break.
3. [`architecture.md`](architecture.md) — where a new concept belongs and why.
4. [`testing_philosophy.md`](testing_philosophy.md) — how to write a test that counts.

## The one-paragraph version

A pure, infrastructure-free domain core (`ballistics`, `optics`,
`countersniper`, `visibility`, `defection_protocol`, `terrain_ops`, driven by
`settings` and composed by `compute_mission`) sits beneath a single thin
adapter, `mission.py`, which is the only module that imports `bond_api`.
Everything the package reports — the mission outcome, the manuscript, the
figures — derives from one call to `compute_mission.mission_solution()`, so the
three can never disagree. Metrics reach the manuscript only as tokens hydrated
by `manuscript_variables.py`; none is typed into prose.

## Related documents outside this directory

* [`../README.md`](../README.md) — what the package is, install and run.
* [`../AGENTS.md`](../AGENTS.md) — the package-level layer contract.
* [`../TODO.md`](../TODO.md) — open work, accepted limitations, and the verification gate.
* [`../STANDALONE.md`](../STANDALONE.md) — the standalone-fork contract.
* [`../manuscript/`](../manuscript/) — the paper, its config, and its bibliography.
* [`../.agents/skills/the-living-daylights/SKILL.md`](../.agents/skills/the-living-daylights/SKILL.md) — the in-repo agent skill descriptor.
