# Experimental setup

## Mission parameters

All parameters are fixed in the single source of truth
([`src/the_living_daylights/settings.py`](../src/the_living_daylights/settings.py))
and echoed for readers in [`manuscript/config.yaml`](config.yaml); a test pins
the echo to `settings.py` key for key, so the two cannot drift apart. Every
value below is read back out of the live mission solution as a token rather
than transcribed by hand.

### Ballistics

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

### Riflescope optics

| Parameter | Value |
|---|---|
| Magnification / objective | {{OPT_MAGNIFICATION}}x / {{OPT_OBJECTIVE_MM}} mm |
| Click value | {{OPT_CLICK_MRAD}} mrad |
| Ranging silhouette / reticle span | {{OPT_TARGET_SIZE_M}} m / {{MIL_READING_MILS}} mils |
| Parallax focus range | {{OPT_PARALLAX_FOCUS_M}} m |

### Countersniper detection

| Parameter | Value |
|---|---|
| Sun elevation / specular half-width | {{CS_SUN_ELEVATION_DEG}}° / {{CS_SPECULAR_HALF_DEG}}° |
| Sun–observer azimuth offset | {{CS_AZIMUTH_DELTA_DEG}}° |
| Lens reflectivity / resolution cell | {{CS_LENS_REFLECTIVITY}} / {{CS_RESOLUTION_MRAD}} mrad |
| Glint evaluation range | {{CS_GLINT_RANGE_M}} m |
| Air temperature / crack-bang delay | {{AIR_TEMP_C}} °C / {{CRACK_BANG_DELAY_S}} s |
| Triangulation observers | {{CS_NUM_OBSERVERS}} |

### Concealment rig

| Parameter | Value |
|---|---|
| Cello-case interior (L × W × D) | {{CELL_CASE_L_M}} × {{CELL_CASE_W_M}} × {{CELL_CASE_D_M}} m |
| Takedown components | {{CELL_NUM_PARTS}} ({{CELL_PART_NAMES}}) |

### Defection handling and terrain

| Parameter | Value |
|---|---|
| Defection stages | {{DEF_NUM_STAGES}} ({{DEF_STAGE_NAMES}}) |
| Defection thresholds (go / conditional) | {{DEF_GO_THRESHOLD}} / {{DEF_CONDITIONAL_THRESHOLD}} |
| Backstop checks | {{VER_NUM_CHECKS}} ({{VER_CHECK_LABELS}}) |
| Terrain seed / size / cell | seed {{TER_SEED}} · {{TER_N}}×{{TER_N}} · {{TER_CELL_M}} m |
| Route start → goal | {{TER_START}} → {{TER_GOAL}} |
| Overwatch eye height / clearance | {{OW_EYE_HEIGHT_M}} m / {{OW_CLEARANCE_M}} m |
| Overwatch candidate step / max range | every {{OW_CANDIDATE_STEP}} cells / {{OW_MAX_RANGE_CELLS}} cells |

## Software environment

Built and verified under Python {{PYTHON_VERSION}}. Deterministic by
construction: the mission solution uses a fixed seed ({{TER_SEED}}) and no
randomness beyond the seeded terrain, and every reported metric is recomputed
from typed, documented pure functions. Scripts are thin orchestrators;
business logic lives in `src/`.

The test count and achieved coverage are not quoted here — they are recorded
live in [`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md), and the
gate itself (`--cov-fail-under=90` on `src/`, line *and* branch) is what this
manuscript claims.

Manuscript hydrated at {{GENERATION_TIMESTAMP}}.
