"""the_living_daylights — SNIPER'S NEST mission software.

Pure-domain core (infrastructure-free) for The Living Daylights (1987):
:mod:`ballistics` (rifle zero, windage, the cello case),
:mod:`defection_protocol` (staged, risk-scored defection handling), and
:mod:`terrain_ops` (mountain/desert routes and cover). :mod:`mission` is the
thin adapter that binds this core to the FROZEN ``bond_api`` protocol.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
