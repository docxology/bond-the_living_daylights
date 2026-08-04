"""SNIPER'S NEST — mission configuration (single source of truth).

Holds the film's fixed operational parameters so the mission adapter
(:mod:`the_living_daylights.mission`), the manuscript token generator
(:mod:`the_living_daylights.manuscript_variables`), and the figure generators
all derive identical numbers from one place. Pure and infrastructure-free.
"""

from __future__ import annotations

from the_living_daylights.ballistics import CelloCase, Projectile

__all__ = [
    "CELLO_CASE",
    "CODENAME",
    "DEFECTION_CONDITIONAL_THRESHOLD",
    "DEFECTION_GO_THRESHOLD",
    "FILM",
    "KOSKOV",
    "MUZZLE_VELOCITY_MPS",
    "PACKAGE_VERSION",
    "PROJECTILE",
    "ROUTE_GOAL",
    "ROUTE_START",
    "SIGHT_HEIGHT_M",
    "SNIPER_ASSET",
    "TERRAIN_CELL_SIZE_M",
    "TERRAIN_N",
    "TERRAIN_SEED",
    "TITLE",
    "TARGET_RANGE_M",
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

# --- The cello case (concealment rig) ---
CELLO_CASE = CelloCase(interior_length_m=1.30, interior_width_m=0.45, interior_depth_m=0.24)
