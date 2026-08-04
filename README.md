# SNIPER'S NEST

**The Living Daylights: SNIPER'S NEST — Special-Agent Mission Software**

A deterministic PROJECT BOND film package modeling the operational concepts of
*The Living Daylights* (1987): sniper ballistics, staged defection handling,
and mountain/desert terrain operations. It implements the frozen BOND-API
`MissionProvider` protocol and is discovered by the suite orchestrator.

## Concepts (pure, deterministic, tested)

| Module | Concept |
| --- | --- |
| [`src/the_living_daylights/ballistics.py`](src/the_living_daylights/ballistics.py) | Rifle zero (elevation + near/far zero), windage (drift + wind hold), rules-of-engagement (the trigger-guard hold), cello-case packing. Point-mass RK4 external ballistics. |
| [`src/the_living_daylights/defection_protocol.py`](src/the_living_daylights/defection_protocol.py) | Staged (contact → relocate), risk-scored defection handling with monotonic approval and a plan gate. |
| [`src/the_living_daylights/terrain_ops.py`](src/the_living_daylights/terrain_ops.py) | Seeded mountain/desert grid, cover-weighted Dijkstra routing, and independent cover audit. |
| [`src/the_living_daylights/compute_mission.py`](src/the_living_daylights/compute_mission.py) | The single deterministic mission solution that both the mission report and the manuscript read. |
| [`src/the_living_daylights/mission.py`](src/the_living_daylights/mission.py) | Thin adapter implementing the frozen BOND-API mission protocol + gadget registry. |

## Quick start

```bash
uv sync --extra dev
uv run python scripts/execute.py      # run the full mission, print outcome + provenance
uv run python scripts/brief.py        # mission brief
uv run python scripts/z_generate_manuscript_variables.py   # hydrate manuscript + figures
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Figures land under `output/figures/` (ballistics trajectory + terrain exfil
route); the resolved manuscript under `output/manuscript/`.

## Verification

≥90% line+branch coverage on `src/`, zero mocks, deterministic, `ruff` and
`mypy` clean on `src/` and `scripts/`. Live counts:
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).

Local-only working tree: no remote, never push.
