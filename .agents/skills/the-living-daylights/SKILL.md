---
name: the-living-daylights
description: PROJECT BOND film package (The Living Daylights, 1987) — SNIPER'S NEST: sniper ballistics, defection handling, terrain ops; frozen BOND-API provider.
version: 0.2.0
author: Active Inference Institute
license: MIT
tags: [bond, mission, ballistics, defection-protocol, terrain-ops, deterministic]
---

# the-living-daylights

Project-scoped skill for the in-repo PROJECT BOND film package at
`projects/working/bond/the_living_daylights/`. Load this when working inside the
project. **Mission codename: SNIPER'S NEST.**

## When to Use

- Working inside `the_living_daylights` — running the mission CLIs, editing the
  domain core, or regenerating outputs.
- Implementing or verifying the frozen BOND-API `MissionProvider` for this film.
- Validating the package contracts (pure core, layer boundaries, no-mocks,
  determinism) after changes.

## Quick Reference

```bash
# From this package directory
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/execute.py              # run the full deterministic mission
uv run python scripts/z_generate_manuscript_variables.py   # hydrate manuscript + figures
```

## Pitfalls

- **Keep the core pure.** `ballistics.py`, `defection_protocol.py`,
  `terrain_ops.py`, `compute_mission.py`, `settings.py` import stdlib + numpy
  only. Only `mission.py` may import `bond_api`.
- **Frozen protocol.** Implement `MissionProvider` against `bond_api.protocol`
  exactly; never invent types.
- **No mocks.** All tests use real data and real computation, deterministically.
- **Outputs are disposable.** Never hand-edit `output/` — regenerate from
  source and config (`z_generate_manuscript_variables.py`).
- **No lineage.** The tree must stay free of `template_code_project` strings
  (verify with `rg`).
- **Deterministic.** Fixed seed (7), no wall-clock in persisted artifacts.
- **Local-only.** No remote; commit inside this package's own git repo with
  path-scoped commits.

## Cross-refs

- Package contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO (what's built + integration points): [`TODO.md`](../../../TODO.md)
- Mission protocol references live in the external skill
  `bond-suite-package-development` (`references/bond-api-phase1.md`).
