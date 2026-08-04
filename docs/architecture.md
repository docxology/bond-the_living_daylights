# SNIPER'S NEST — Architecture

## Layers

```
src/the_living_daylights/
  settings.py            mission parameters (single source of truth)
  ballistics.py          pure external-ballistics core (stdlib + math only)
  defection_protocol.py  pure staged risk-scored protocol (stdlib only)
  terrain_ops.py         pure terrain grid + Dijkstra routing (numpy)
  compute_mission.py     the single deterministic mission solution
  manuscript_variables.py  {{TOKEN}} hydration (config + solution)
  figures/plots.py       deterministic matplotlib plates
  mission.py             THIN adapter → imports bond_api (the only file that does)
scripts/                 thin per-phase CLIs (brief/recon/plan/execute/debrief ...)
tests/                   real-data, zero-mock tests
```

## Dependency direction

```
scripts/  →  src/the_living_daylights (mission, manuscript_variables, figures)
mission.py → bond_api (frozen protocol) → src pure core
src pure core → stdlib + numpy only   (NO bond_api, NO infrastructure)
manuscript_variables → compute_mission + config.yaml
```

The arrow is one-directional. The pure core can be lifted into any Python
environment without `bond_api`; `mission.py` is the single integration seam to
the frozen protocol.

## Where to add a concept

1. Add pure logic to the matching `src/the_living_daylights/*.py` module
   (stdlib + numpy only).
2. Expose any new number through `compute_mission.mission_solution()`.
3. Surface it as a `{{TOKEN}}` in `manuscript_variables.generate_variables()`.
4. Add a real-data test file under `tests/` (no mocks), and a live assertion in
   `tests/test_manuscript_variables.py` if you added a token.
5. Re-run the gates (see `agent_instructions.md`).

## Constraints

- `mission.py` must not grow business logic; it only adapts and registers
  gadgets.
- Results must be deterministic: fixed seeds, no global RNG, no wall-clock in
  persisted artifacts.
