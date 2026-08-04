# src/the_living_daylights

Pure, deterministic SNIPER'S NEST domain core plus the thin BOND-API mission
adapter. See [`AGENTS.md`](AGENTS.md) for the module map and the purity rule
(core modules import stdlib + numpy only; only `mission.py` imports `bond_api`).

Quick entry points:

```python
from the_living_daylights import ballistics, defection_protocol, terrain_ops
from the_living_daylights.compute_mission import mission_solution, input_hash
from the_living_daylights.mission import MissionProvider  # Bond-API adapter
```
