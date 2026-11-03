# SNIPER'S NEST

**The Living Daylights: SNIPER'S NEST — Special-Agent Mission Software**

A deterministic PROJECT BOND film package modeling the operational concepts of
*The Living Daylights* (1987). It implements the frozen BOND-API
`MissionProvider` protocol and is discovered by the suite orchestrator under the
slug `the_living_daylights`.

## The film is the spec

Every module below implements something the film actually turns on:

| Film beat | What the code computes |
| --- | --- |
| A sniper rifle carried through Bratislava in a cello case | Deterministic shelf packing of a takedown rifle into a case interior, with lane layout and field assembly time |
| Bond covering a defection from an overwatch position | Terrain line of sight, viewsheds, and a *ranked* overwatch selection for the extraction site |
| Bond deliberately shooting the rifle out of the cellist's hands instead of killing her | A rules-of-engagement precedence chain that resolves to a trigger-guard weapon-disable rather than a lethal shot |
| A hostile sniper working the same corridor | Optic-glint radiometry, acoustic crack-bang ranging, and least-squares bearing triangulation |
| Koskov's defection, and the doubt about it | A staged, risk-scored handling protocol with a plan gate, plus a separately parameterised backstop evidence-verification model (both are authored constant tables — their agreement is a design check, not independent evidence) |
| Exfiltration across Afghan mountain and desert | A seeded terrain grid and cover-weighted least-cost routing, reported against measured baselines (the route sits *below* the grid's mean concealment), with a second-implementation cover audit |

## Modules

Pure domain core — stdlib + numpy only, no `bond_api`, no I/O, no wall-clock:

| Module | What it computes |
| --- | --- |
| [`src/the_living_daylights/ballistics.py`](src/the_living_daylights/ballistics.py) | Point-mass RK4 external ballistics: rifle zero, near/far-zero capture, drop, time of flight, crosswind drift and the wind hold, rules of engagement (the trigger-guard hold), and cello-case shelf packing with assembly time. |
| [`src/the_living_daylights/optics.py`](src/the_living_daylights/optics.py) | Riflescope: MOA↔mrad turret math, whole-click solutions, mil-dot reticle ranging and its inverse, ballistic holdover, first-order parallax, true field of view. |
| [`src/the_living_daylights/countersniper.py`](src/the_living_daylights/countersniper.py) | Countersniper detection: optic-glint geometry, sky contrast, angular fraction and SNR, detection probability; temperature-dependent sound speed and crack-bang ranging; least-squares bearing triangulation with a residual. |
| [`src/the_living_daylights/visibility.py`](src/the_living_daylights/visibility.py) | Bresenham line of sight with a clearance, viewsheds, and weighted overwatch (sniper's nest) ranking over candidate positions. |
| [`src/the_living_daylights/defection_protocol.py`](src/the_living_daylights/defection_protocol.py) | Staged, risk-scored defection handling with monotonic approval and a plan gate, plus the backstop evidence-verification model (`EvidenceCheck`, certainty, verdict). |
| [`src/the_living_daylights/terrain_ops.py`](src/the_living_daylights/terrain_ops.py) | Seeded mountain/desert grid (elevation, landcover, standing cover), cover-weighted Dijkstra routing, and a separately implemented cover audit for any proposed path (vectorised numpy vs the planner's scalar loop — a cross-implementation check, not independent evidence). |
| [`src/the_living_daylights/settings.py`](src/the_living_daylights/settings.py) | Every fixed mission parameter — the single source of truth. |
| [`src/the_living_daylights/compute_mission.py`](src/the_living_daylights/compute_mission.py) | The one deterministic mission solution, plus its SHA-256 provenance `input_hash`. |

Presentation and integration:

| Module | Role |
| --- | --- |
| [`src/the_living_daylights/mission.py`](src/the_living_daylights/mission.py) | Thin adapter implementing the frozen BOND-API `MissionProvider` + the `GADGETS` registry. The only module importing `bond_api`. |
| [`src/the_living_daylights/manuscript_variables.py`](src/the_living_daylights/manuscript_variables.py) | Hydrates manuscript tokens from `manuscript/config.yaml` + the mission solution; fails loudly on a missing result section or an unresolved placeholder. |
| [`src/the_living_daylights/figures/plots.py`](src/the_living_daylights/figures/plots.py) | Four deterministic plates: ballistics trajectory, exfil route, glint-vs-range, overwatch nests. |

## The MissionProvider surface

`mission.py` exposes the frozen five-stage lifecycle plus the gadget registry.
This shape is consumed suite-wide by `bond-cli`, the coordinator, and the
orchestrator, and does not change:

```python
from the_living_daylights.mission import GADGETS, MissionProvider, register_gadgets

provider = MissionProvider()
provider.film                      # "the_living_daylights"
brief    = provider.brief()        # -> MissionBrief   (objectives, assets, constraints)
report   = provider.recon(request) # -> ReconReport    (findings)
plan     = provider.plan(brief)    # -> MissionPlan    (8 deterministic steps)
outcome  = provider.execute(plan)  # -> MissionOutcome (results + Provenance/input_hash)
debrief  = provider.debrief(outcome)  # -> Debrief     (outcome + lessons)
```

`GADGETS` is a `bond_api.registry.GadgetRegistry` populated at import time with
the film's field kit (rifle profile, scope spec, glint detector, acoustic
ranger, localizer, viewshed, cello-case rig, defection protocol, verification
checks, terrain generator). Discovery goes through
`bond_api.discovery.load_provider('the_living_daylights', …)`.

## Quick start

```bash
uv sync --extra dev

uv run python scripts/00_preflight.py                     # environment check
uv run python scripts/brief.py                            # mission brief
uv run python scripts/recon.py --goal "cover the handoff" # recon report
uv run python scripts/plan.py                             # the eight-step plan
uv run python scripts/execute.py                          # run it; prints outcome + provenance
uv run python scripts/debrief.py                          # lessons learned

uv run python scripts/z_generate_manuscript_variables.py  # hydrate manuscript + render figures
```

Figures land in `output/figures/` (ballistics trajectory, exfil route, glint
detection, overwatch nests); the resolved manuscript in `output/manuscript/`;
the token map in `output/data/manuscript_variables.json`. All of `output/` is
regenerable and git-ignored.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

The package holds ≥90% line **and** branch coverage on `src/` with zero mocks,
deterministic results, and `ruff` + `mypy` clean on `src/` and `scripts/`. The
achieved test total and coverage percentage are recorded only in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — no prose here quotes
them, so none can go stale.

## Documentation

* [`docs/README.md`](docs/README.md) — documentation index and reading order.
* [`docs/architecture.md`](docs/architecture.md) — module-by-module architecture.
* [`docs/agent_instructions.md`](docs/agent_instructions.md) — hard rules for modifying the package.
* [`docs/testing_philosophy.md`](docs/testing_philosophy.md) — the no-mock, real-data, determinism doctrine.
* [`AGENTS.md`](AGENTS.md) — layer contract and verification.
* [`TODO.md`](TODO.md) — open work, accepted limitations, and the verification gate.
* [`manuscript/`](manuscript/) — the paper, its config, and its bibliography.

This tree is a standalone checkout of the PROJECT BOND film package
`the_living_daylights` (originally `projects/working/bond/the_living_daylights`
in the suite working tree). Its canonical remote is
`github.com/docxology/bond-the_living_daylights` (private); no DOI has been
minted. `uv sync` resolves `bond-api` — the frozen protocol dependency — from
the vendored copy at `vendor/bond-api/`, because it is not installable from an
index; [`STANDALONE.md`](STANDALONE.md) records the provenance, the refresh
command, and the check that runs in this tree's own gate.
