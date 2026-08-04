# Abstract

{{TITLE}} (mission codename **{{CODENAME}}**) is deterministic
special-agent mission software for *The Living Daylights* (1987). It models
six operational concepts with real, reproducible computation:

* **Sniper ballistics** — a plug-and-play point-mass external-ballistics core
  that solves the rifle zero (fusing the trajectory to the sight line at
  {{BAL_ZERO_RANGE}} m), captures the near/far zero, and solves windage (a
  {{BAL_WIND_MPS}} m/s full-value crosswind imposes a {{BAL_WIND_DRIFT}} m drift
  requiring a {{BAL_WIND_HOLD_MRAD}} mrad hold), all embedded in a takedown
  rifle that conceals inside a cello case ({{CELL_FITS}}, {{CELL_LANES}} lanes,
  {{CELL_EFFICIENCY}} packing efficiency, {{CELL_ASSEMBLY_S}} s field assembly).
* **Countersniper optics** — the {{OPT_MAGNIFICATION}}x mil-dot riflescope
  ranges the {{OPT_MIL_RANGE_M}} m target from a {{OPT_HOLDOVER_MILS}} mil
  holdover and dials the {{OPT_ELEVATION_CLICKS}}/{{OPT_WIND_CLICKS}}
  click solution; glint radiometry detects a hostile optic at
  {{CS_GLINT_PDET}} probability at {{CS_GLINT_RANGE_M}} m.
* **Countersniper detection** — a hostile sniper is ranged acoustically
  ({{CS_CRACK_BANG_M}} m from the crack-bang delay) and localized by crossed
  bearings to ({{CS_TRI_X_M}}, {{CS_TRI_Y_M}}) m.
* **Defection-handling protocol** — a staged, risk-scored pipeline
  ({{DEF_NUM_STAGES}} stages) whose weighted hazard model renders the canonical
  KOSKOV scenario {{DEF_PLAN_VERDICT}} with a {{DEF_GATE}} gate stage and
  {{VER_CERTAINTY}} backstop certainty ({{VER_VERDICT}}).
* **Mountain/desert terrain ops** — a seeded ({{TER_SEED}}) terrain grid on
  which a least-cost Dijkstra planner finds covered exfil routes
  ({{TER_DIST_KM}} km, mean concealment {{TER_MEAN_COVER}}).
* **Overwatch selection** — of {{OW_NUM_CANDIDATES}} in-range candidate
  positions only {{OW_VISIBLE_CANDIDATES}} see the extraction site; the ranked
  best nest at {{OW_BEST_CELL}} commands it from {{OW_BEST_DISTANCE_M}} m with
  {{OW_BEST_ELEV_GAIN_M}} m elevation advantage.

All results derive from a single deterministic mission solution
([`src/the_living_daylights/compute_mission.py`](../src/the_living_daylights/compute_mission.py))
so the manuscript, the mission report, and the figures can never drift apart.
Keywords: {{CONFIG_KEYWORDS}}.
