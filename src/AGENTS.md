# src/the_living_daylights — SNIPER'S NEST source

Pure, deterministic, infrastructure-free domain core plus a thin BOND-API
mission adapter.

| Module | Responsibility |
| --- | --- |
| `settings.py` | Mission parameters (single source of truth). |
| `ballistics.py` | External ballistics: `zero_scope`, `capture_zero`, `wind_drift`, `wind_hold_mrad`, `engagement_decision`, cello-case packing. |
| `defection_protocol.py` | Staged risk scoring: `assess_defection`, `stage_score`, `koskov_scenario`. |
| `terrain_ops.py` | `generate_terrain`, `plan_route` (Dijkstra), `step_cost`, `assess_cover`. |
| `compute_mission.py` | `mission_solution()`, `input_hash()` — the deterministic mission result. |
| `manuscript_variables.py` | `generate_variables()` — `{{TOKEN}}` hydration. |
| `figures/plots.py` | `render_ballistics_figure`, `render_terrain_figure`. |
| `mission.py` | `MissionProvider` — the frozen BOND-API adapter + gadget registration. |

**Purity rule:** the core modules (`settings`, `ballistics`,
`defection_protocol`, `terrain_ops`, `compute_mission`) import stdlib + numpy
only and are importable without `bond_api`. Only `mission.py` may import
`bond_api`. `manuscript_variables.py` and `figures/` may import `yaml` /
`matplotlib`.

**Determinism:** fixed seeds, no global RNG, no wall-clock in persisted
artifacts (except the regeneration timestamp).
