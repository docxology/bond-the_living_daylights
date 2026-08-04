"""SNIPER'S NEST — mission configuration (single source of truth).

Holds the film's fixed operational parameters so the mission adapter
(:mod:`the_living_daylights.mission`), the manuscript token generator
(:mod:`the_living_daylights.manuscript_variables`), and the figure generators
all derive identical numbers from one place. Pure and infrastructure-free.
"""

from __future__ import annotations

from the_living_daylights.ballistics import CelloCase, Projectile
from the_living_daylights.optics import ScopeSpec

__all__ = [
    "AIR_TEMP_C",
    "CELLO_CASE",
    "CODENAME",
    "CRACK_BANG_DELAY_S",
    "DEFECTION_CONDITIONAL_THRESHOLD",
    "DEFECTION_GO_THRESHOLD",
    "FILM",
    "GLINT_RANGE_M",
    "KOSKOV",
    "LENS_REFLECTIVITY",
    "MIL_READING_MILS",
    "MUZZLE_VELOCITY_MPS",
    "OBSERVER_AZIMUTH_DEG",
    "OVERWATCH_CANDIDATE_STEP",
    "OVERWATCH_CLEARANCE_M",
    "OVERWATCH_EYE_HEIGHT_M",
    "OVERWATCH_MAX_RANGE_CELLS",
    "PACKAGE_VERSION",
    "PARALLAX_EYE_OFFSET_M",
    "PARALLAX_FOCUS_M",
    "PROJECTILE",
    "RESOLUTION_MRAD",
    "ROUTE_GOAL",
    "ROUTE_START",
    "SCOPE",
    "SIGHT_HEIGHT_M",
    "SNIPER_ASSET",
    "SPECULAR_HALF_WIDTH_DEG",
    "SUN_AZIMUTH_DEG",
    "SUN_ELEVATION_DEG",
    "TARGET_RANGE_M",
    "TARGET_SIZE_M",
    "TERRAIN_CELL_SIZE_M",
    "TERRAIN_N",
    "TERRAIN_SEED",
    "TITLE",
    "TRIANGULATION_BEARINGS",
    "TRIANGULATION_OBSERVERS",
    "WIND_MPS",
    "ZERO_RANGE_M",
]

PACKAGE_VERSION = "0.1.0"

#: Film identity — the package slug and manuscript identity.
FILM = "the_living_daylights"
TITLE = "The Living Daylights: SNIPER'S NEST"
CODENAME = "SNIPER'S NEST"

#: The defecting asset of record (General Koskov) and his field cover.
KOSKOV = "koskov"
SNIPER_ASSET = "general_koskov"

# --- Sniper ballistics (7.62mm/168gr service round in a takedown rifle) ---
MUZZLE_VELOCITY_MPS = 790.0
PROJECTILE = Projectile(mass_kg=0.0104, caliber_m=0.00782)
ZERO_RANGE_M = 300.0
SIGHT_HEIGHT_M = 0.07
TARGET_RANGE_M = 300.0
WIND_MPS = 5.0

# --- Defection-handling protocol thresholds ---
DEFECTION_GO_THRESHOLD = 0.40
DEFECTION_CONDITIONAL_THRESHOLD = 0.70

# --- Mountain/desert terrain (deterministic seeded grid) ---
TERRAIN_SEED = 7
TERRAIN_N = 32
TERRAIN_CELL_SIZE_M = 500.0
ROUTE_START = (0, 0)
ROUTE_GOAL = (TERRAIN_N - 1, TERRAIN_N - 1)

# --- Countersniper scope optics (takedown rifle's riflescope) ---
SCOPE = ScopeSpec(magnification=10.0, objective_diameter_mm=50.0, click_unit="mrad", click_size=0.1)
TARGET_SIZE_M = 1.8  # standing human silhouette for mil-dot ranging
MIL_READING_MILS = 6.0  # observed reticle span of the target
PARALLAX_EYE_OFFSET_M = 0.01  # shooter's eye displacement from the optical axis
PARALLAX_FOCUS_M = 150.0  # scope parallax-focus range

# --- Countersniper detection: sun/observer geometry + lens glint ---
SUN_ELEVATION_DEG = 35.0
SUN_AZIMUTH_DEG = 150.0
OBSERVER_AZIMUTH_DEG = 152.0  # 2 deg from the specular direction -> bright glint
SPECULAR_HALF_WIDTH_DEG = 3.0
LENS_REFLECTIVITY = 0.35
RESOLUTION_MRAD = 1.0
GLINT_RANGE_M = 800.0

# --- Countersniper acoustics + localization ---
AIR_TEMP_C = 20.0
CRACK_BANG_DELAY_S = 2.0
TRIANGULATION_OBSERVERS: tuple[tuple[float, float], ...] = ((0.0, 0.0), (100.0, 0.0))
TRIANGULATION_BEARINGS: tuple[float, ...] = (45.0, 135.0)

# --- Overwatch (sniper's nest selection) on the terrain grid ---
OVERWATCH_EYE_HEIGHT_M = 1.7
OVERWATCH_CLEARANCE_M = 0.3
OVERWATCH_MAX_RANGE_CELLS = 12
OVERWATCH_CANDIDATE_STEP = 3  # sample every 3rd cell row/col as a candidate nest

# --- The cello case (concealment rig) ---
CELLO_CASE = CelloCase(interior_length_m=1.30, interior_width_m=0.45, interior_depth_m=0.24)
