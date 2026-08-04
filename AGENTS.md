# PROJECT BOND — the_living_daylights · SNIPER'S NEST

**Film:** The Living Daylights (1987) · **Mission codename:** SNIPER'S NEST

SNIPER'S NEST is a PROJECT BOND film package: deterministic, special-agent
mission software for the film's operational concepts. It implements the frozen
BOND-API `MissionProvider` protocol (`bond_api`) and is discovered by the suite
orchestrator by slug on `sys.path`.

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/the_living_daylights/ballistics.py`, `defection_protocol.py`, `terrain_ops.py`, `compute_mission.py`, `settings.py` | **Pure domain core** — infrastructure-free, deterministic, imports only stdlib + numpy. No `bond_api` requirement (usable standalone). |
| `src/the_living_daylights/mission.py` | **Thin adapter** — the only module that imports `bond_api`; binds the domain core to the frozen protocol and registers gadgets. |
| `src/the_living_daylights/manuscript_variables.py`, `figures/` | Manuscript hydration + deterministic figure rendering. |
| `scripts/` | Thin orchestrators per mission phase (brief/recon/plan/execute/debrief) + hydration/preflight. |
| Live counts | [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — do not hardcode test counts or coverage %. |

## Concepts

* **Sniper ballistics** — point-mass RK4 external ballistics: rifle zero
  (elevation + near/far zero), windage (drift + wind hold), rules-of-engagement
  (the trigger-guard hold), cello-case packing.
* **Defection handling** — a staged (contact → relocate), risk-scored protocol
  with weighted hazards, monotonic approval, and a plan gate.
* **Terrain ops** — seeded mountain/desert grid, cover-weighted Dijkstra
  routing, and independent cover audit.

## Protocol integration

`src/the_living_daylights/mission.py` exposes `MissionProvider` at module top
level (film = `the_living_daylights`). It implements the five-stage lifecycle
against `bond_api.protocol`'s frozen dataclasses and registers the film's
gadgets through `bond_api.registry.GadgetRegistry`.

Discovery: `bond_api.discovery.load_provider('the_living_daylights', ...)`
imports `the_living_daylights.mission`, binds `film`, and verifies the
runtime-checkable protocol.

## Verification

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
```

## Protocol for AI agents

Read [`docs/agent_instructions.md`](docs/agent_instructions.md),
[`docs/architecture.md`](docs/architecture.md), and
[`docs/testing_philosophy.md`](docs/testing_philosophy.md) before modifying the
project. This is a local-only working tree: no remote, never push.

See also the in-repo skill: `.agents/skills/the-living-daylights/SKILL.md`.
