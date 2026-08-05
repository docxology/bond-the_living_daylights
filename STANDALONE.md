# SNIPER'S NEST — standalone package

**The Living Daylights: SNIPER'S NEST — Special-Agent Mission Software**

A deterministic PROJECT BOND film package: sniper ballistics (rifle zero,
windage, rules of engagement, the cello case), riflescope optics, countersniper
detection and localization, terrain visibility and overwatch selection, staged
risk-scored defection handling with backstop evidence verification, and
mountain/desert terrain operations. It implements the frozen BOND-API
`MissionProvider` protocol.

- **Local-only working tree** — no remote, never push.
- **Pure domain core** — `src/the_living_daylights/` (stdlib + numpy only) is
  importable without `bond_api`; `mission.py` is the single protocol seam.
- **Deterministic** — fixed seeds, no wall-clock in persisted artifacts.
- **Verified** — ≥90% line+branch coverage on `src/`, zero mocks, `ruff` +
  `mypy` clean.

Keep in the PROJECT BOND suite layout under `projects/working/bond/`; integrity
is enforced by the BOND guardrails and the package's own gates.
