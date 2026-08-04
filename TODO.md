# SNIPER'S NEST — TODO

## Built (phase 2 + phase 4 deep improvement)

- **Pure domain core** (`src/the_living_daylights/`)
  - `ballistics.py` — point-mass RK4 external ballistics: rifle zero,
    near/far-zero capture, windage, rules-of-engagement (trigger-guard hold),
    cello-case packing. Real-data tests: `tests/test_ballistics.py`.
  - `optics.py` — countersniper scope optics: MOA/mrad click math, mil-dot
    reticle ranging, holdover, first-order parallax, field of view. Tests:
    `tests/test_optics.py`.
  - `countersniper.py` — radiometric optic-glint detection, acoustic
    crack-bang ranging, least-squares bearing triangulation. Tests:
    `tests/test_countersniper.py`.
  - `visibility.py` — terrain line-of-sight + viewsheds + ranked overwatch
    (sniper's nest) selection. Tests: `tests/test_visibility.py`.
  - `defection_protocol.py` — staged, risk-scored defection handling with
    monotonic approval + plan gate, plus backstop **evidence verification**
    (`EvidenceCheck`, `verification_certainty`, `backstop_verdict`). Tests:
    `tests/test_defection_protocol.py`.
  - `terrain_ops.py` — seeded mountain/desert grid, cover-weighted Dijkstra
    routing, cover audit. Tests: `tests/test_terrain_ops.py`.
  - `compute_mission.py` — single deterministic mission solution (ballistics,
    optics, countersniper, overwatch, defection + verification, terrain) shared
    by mission report, manuscript tokens, and provenance `input_hash`.
  - `settings.py` — single source of mission parameters.
  - `mission.py` — `MissionProvider` implementing the frozen BOND-API protocol
    (brief/recon/plan/execute/debrief) with UNCHANGED public shape; registers
    the enlarged gadget kit with `bond_api.registry.GadgetRegistry`.
  - `manuscript_variables.py` — `{{TOKEN}}` hydration from config + solution.
  - `figures/plots.py` — four deterministic figures (ballistics, terrain
    route, glint, overwatch nests).
- **Thin scripts/** — per-phase CLIs: `brief.py`, `recon.py`, `plan.py`,
  `execute.py`, `debrief.py`, plus `00_preflight.py`, `z_generate_manuscript_variables.py`.
- **Manuscript** — SNIPER'S NEST identity + sections, deterministic figures,
  token-injected metrics, real bibliography (FM 23-10 mil-dot, acoustic
  sniper-localization, viewshed, detection-theory, sound-speed sources).
- **Gates** — `pytest --cov=src --cov-fail-under=90` green (live count in
  `docs/_generated/COUNTS.md`); `ruff` + `mypy` clean; no mocks; deterministic;
  `template[_]code_project` lineage zero; own git repo, path-scoped commit.

## Declared integration points

- **bond-api (FROZEN)** — `mission.py` implements `MissionProvider` against
  `bond_api.protocol` and registers gadgets against `bond_api.registry`
  (path dep wired in `pyproject.toml`). No protocol changes are permitted.
- **bond-utilities provenance (not yet bound)** — the mission currently
  computes its own deterministic `input_hash`. When the shared helper is
  available, delegate outcome persistence to
  `bond_utilities.mission_io.record_provenance_outcome` (acceptance: a
  recorded outcome whose provenance block matches `execute()`'s Provenance).
- **orchestrator discovery** — the package is discoverable as
  `the_living_daylights` via `bond_api.discovery.load_provider` once `src/` is
  on the orchestrator's path.

## Not in scope

- Stochastic adversary modelling, full atmosphere (spin/Magnus/Coriolis), or
  line-of-sight occlusion queries — intentionally kept deterministic.
