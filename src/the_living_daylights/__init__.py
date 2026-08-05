"""the_living_daylights — SNIPER'S NEST mission software.

Pure-domain core (infrastructure-free) for The Living Daylights (1987):

* :mod:`ballistics` — point-mass RK4 external ballistics: rifle zero, near/far
  zero capture, windage, rules of engagement, and cello-case packing;
* :mod:`optics` — riflescope click math, mil-dot ranging, holdover, parallax,
  and field of view;
* :mod:`countersniper` — optic-glint radiometry, acoustic crack-bang ranging,
  and least-squares bearing triangulation;
* :mod:`visibility` — terrain line of sight, viewsheds, and overwatch (sniper's
  nest) ranking;
* :mod:`defection_protocol` — staged, risk-scored defection handling plus the
  backstop evidence-verification model;
* :mod:`terrain_ops` — seeded mountain/desert grid, cover-weighted Dijkstra
  routing, and the independent cover audit;
* :mod:`settings` — the single source of mission parameters;
* :mod:`compute_mission` — the one deterministic mission solution every
  consumer reads.

:mod:`mission` is the thin adapter that binds this core to the FROZEN
``bond_api`` protocol; :mod:`manuscript_variables` and :mod:`figures.plots`
hydrate the manuscript and its plates from the same solution.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
