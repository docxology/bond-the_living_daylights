# Experimental setup

## Mission parameters

All parameters are fixed in the single source of truth
([`src/the_living_daylights/settings.py`](../src/the_living_daylights/settings.py))
and echoed in [`manuscript/config.yaml`](config.yaml).

| Parameter | Value |
|---|---|
| Film / mission codename | {{IDENTITY}} / {{CODENAME}} |
| Muzzle velocity | {{BAL_MUZZLE_VELOCITY}} m/s |
| Bullet mass | {{BAL_BULLET_MASS_G}} g |
| Caliber | {{BAL_CALIBER_MM}} mm |
| Ballistic coefficient | {{BAL_BC}} kg/m² |
| Zero range | {{BAL_ZERO_RANGE}} m |
| Sight height over bore | {{BAL_SIGHT_HEIGHT}} m |
| Target range / wind | {{BAL_TARGET_RANGE}} m / {{BAL_WIND_MPS}} m/s |
| Defection thresholds (go / conditional) | {{DEF_GO_THRESHOLD}} / {{DEF_CONDITIONAL_THRESHOLD}} |
| Terrain seed / size / cell | seed {{TER_SEED}} · {{TER_N}}×{{TER_N}} · {{TER_CELL_M}} m |

## Software environment

Built and verified under Python {{PYTHON_VERSION}}. Deterministic by
construction: the mission solution uses a fixed seed ({{TER_SEED}}) and no
randomness beyond the seeded terrain, and every reported metric is recomputed
from typed, documented pure functions. Scripts are thin orchestrators;
business logic lives in `src/`.

Manuscript hydrated at {{GENERATION_TIMESTAMP}}.
