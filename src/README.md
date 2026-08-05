# src/the_living_daylights

Pure, deterministic SNIPER'S NEST domain core plus the thin BOND-API mission
adapter. See [`AGENTS.md`](AGENTS.md) for the module map and the purity rule
(core modules import stdlib + numpy only; only `mission.py` imports `bond_api`).

Quick entry points:

```python
from the_living_daylights import (
    ballistics,  # rifle zero, windage, ROE, the cello case
    optics,  # click math, mil-dot ranging, holdover, parallax
    countersniper,  # optic glint, crack-bang ranging, triangulation
    visibility,  # line of sight, viewsheds, overwatch ranking
    defection_protocol,  # staged risk scoring + evidence verification
    terrain_ops,  # seeded grid, cover-weighted Dijkstra, cover audit
    settings,  # every fixed mission parameter
)
from the_living_daylights.compute_mission import input_hash, mission_solution
from the_living_daylights.mission import GADGETS, MissionProvider  # BOND-API adapter
```

`mission_solution()` is the one place any number is computed; the mission
adapter, the manuscript, and the figures are all readers of it.
