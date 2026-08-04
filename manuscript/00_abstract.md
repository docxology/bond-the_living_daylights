# Abstract

{{TITLE}} (mission codename **{{CODENAME}}**) is deterministic
special-agent mission software for *The Living Daylights* (1987). It models
three operational concepts with real, reproducible computation:

* **Sniper ballistics** — a plug-and-play point-mass external-ballistics core
  that solves the rifle zero (fusing the trajectory to the sight line at
  {{BAL_ZERO_RANGE}} m), captures the near/far zero, and solves windage (a
  {{BAL_WIND_MPS}} m/s full-value crosswind imposes a {{BAL_WIND_DRIFT}} m drift
  requiring a {{BAL_WIND_HOLD_MRAD}} mrad hold), all embedded in a takedown
  rifle that conceals inside a cello case ({{CELL_FITS}}, {{CELL_LANES}} lanes,
  {{CELL_EFFICIENCY}} packing efficiency, {{CELL_ASSEMBLY_S}} s field assembly).
* **Defection-handling protocol** — a staged, risk-scored pipeline
  ({{DEF_NUM_STAGES}} stages) whose weighted hazard model renders the canonical
  KOSKOV scenario {{DEF_PLAN_VERDICT}} with a {{DEF_GATE}} gate stage.
* **Mountain/desert terrain ops** — a seeded ({{TER_SEED}}) terrain grid
  ([@fig:ballistics]) on which a least-cost Dijkstra planner finds covered
  exfil routes ({{TER_DIST_KM}} km, mean concealment {{TER_MEAN_COVER}}).

All results derive from a single deterministic mission solution
([`src/the_living_daylights/compute_mission.py`](../src/the_living_daylights/compute_mission.py))
so the manuscript, the mission report, and the figures can never drift apart.
Keywords: {{CONFIG_KEYWORDS}}.
