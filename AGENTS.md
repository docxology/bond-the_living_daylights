# PROJECT BOND — the_living_daylights · SNIPER'S NEST

**Film:** The Living Daylights (1987) · **Mission codename:** SNIPER'S NEST

SNIPER'S NEST is a PROJECT BOND film package: deterministic, special-agent
mission software for the film's operational concepts. It implements the frozen
BOND-API `MissionProvider` protocol (`bond_api`) and is discovered by the suite
orchestrator by slug on `sys.path`.

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/the_living_daylights/{ballistics,optics,countersniper,visibility,defection_protocol,terrain_ops,settings,compute_mission}.py` | **Pure domain core** — infrastructure-free, deterministic, stdlib + numpy only. No `bond_api` requirement (importable standalone). |
| `src/the_living_daylights/mission.py` | **Thin adapter** — the only module that imports `bond_api`; binds the domain core to the frozen protocol and registers gadgets. No business logic. |
| `src/the_living_daylights/manuscript_variables.py`, `figures/` | Manuscript token hydration and deterministic figure rendering; both read `compute_mission`. |
| `scripts/` | Thin orchestrators per mission phase (brief/recon/plan/execute/debrief) plus preflight and hydration. Parse, call `src/`, print. |
| `manuscript/config.yaml` `mission:` block | A reader-facing **echo** of `settings.py`, pinned to it by a test. `settings.py` is authoritative. |
| Live counts | [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — do not hardcode test counts or coverage % anywhere else. |

## Concepts

* **Sniper ballistics** — point-mass RK4 external ballistics: rifle zero
  (elevation + near/far zero), drop and time of flight, windage (drift + wind
  hold), rules of engagement (the trigger-guard hold), cello-case packing.
* **Riflescope optics** — MOA/mrad turret math and whole-click solutions,
  mil-dot reticle ranging and its inverse, ballistic holdover, first-order
  parallax, true field of view.
* **Countersniper detection** — radiometric optic-glint detection (geometry
  factor, sky contrast, angular fraction, SNR, detection CDF), acoustic
  crack-bang ranging with a temperature-dependent sound speed, and
  least-squares bearing triangulation with a residual.
* **Terrain visibility** — Bresenham line of sight with a clearance, viewsheds,
  and ranked overwatch (sniper's nest) selection.
* **Defection handling** — a staged (contact → relocate), risk-scored protocol
  with weighted hazards, monotonic approval, and a plan gate.
* **Evidence verification** — an independent backstop model (weighted checks →
  certainty → cleared/conditional/rejected) that corroborates the plan gate
  without sharing its inputs.
* **Terrain ops** — seeded mountain/desert grid, cover-weighted Dijkstra
  routing, and an independent cover audit for any proposed path.

Everything above is composed by `compute_mission.mission_solution()`, the single
place any number is computed.

## Protocol integration

`src/the_living_daylights/mission.py` exposes `MissionProvider` at module top
level (`film = "the_living_daylights"`). It implements the five-stage lifecycle
against `bond_api.protocol`'s frozen dataclasses and registers the film's
gadgets through `bond_api.registry.GadgetRegistry`, binding them into the
module-level `GADGETS` at import.

Discovery: `bond_api.discovery.load_provider('the_living_daylights', ...)`
imports `the_living_daylights.mission`, binds `film`, and verifies the
runtime-checkable protocol.

**Frozen.** `MissionProvider`, its five method names and signatures, the `film`
attribute, `GADGETS`, and `register_gadgets` are consumed across the suite by
`bond-cli`, the coordinator's reconcile pass, and the orchestrator. Do not
change their public shape — deepen inside the package instead.

## Build and run

```bash
uv sync --extra dev

uv run python scripts/00_preflight.py                     # environment check
uv run python scripts/brief.py                            # mission brief
uv run python scripts/recon.py --goal "cover the handoff" # recon report
uv run python scripts/plan.py                             # the eight-step plan
uv run python scripts/execute.py                          # outcome + provenance
uv run python scripts/debrief.py                          # lessons learned
uv run python scripts/z_generate_manuscript_variables.py  # manuscript + four figures
```

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "no mocks"
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo "no lineage"
git status --short   # clean after the path-scoped commit
```

The gate is ≥90% line **and** branch coverage on `src/`, zero mocks, zero
failures, `ruff` and `mypy` clean. Achieved figures are in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md); this file states the
gate, not a snapshot.

Note that `scripts/z_generate_manuscript_variables.py` writes only into the
git-ignored `output/` tree, so running it must leave `git status` clean — that
is a live determinism check, not just a build step.

## Protocol for AI agents

Read [`docs/agent_instructions.md`](docs/agent_instructions.md),
[`docs/architecture.md`](docs/architecture.md), and
[`docs/testing_philosophy.md`](docs/testing_philosophy.md) before modifying
anything. This is a local-only working tree: no remote, never push, commit
path-scoped inside this package only.

See also the in-repo skill:
[`.agents/skills/the-living-daylights/SKILL.md`](.agents/skills/the-living-daylights/SKILL.md).
