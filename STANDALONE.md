# SNIPER'S NEST — standalone package

**The Living Daylights: SNIPER'S NEST — Special-Agent Mission Software**

A deterministic PROJECT BOND film package: sniper ballistics (rifle zero,
windage, rules of engagement, the cello case), riflescope optics, countersniper
detection and localization, terrain visibility and overwatch selection, staged
risk-scored defection handling with backstop evidence verification, and
mountain/desert terrain operations. It implements the frozen BOND-API
`MissionProvider` protocol.

- **Standalone checkout** — canonical remote
  `github.com/docxology/bond-the_living_daylights` (public). No DOI has been
  minted, so the publication sidecars (`CITATION.cff`, `.zenodo.json`,
  `codemeta.json`) carry no DOI or repository URL.
- **Pure domain core** — `src/the_living_daylights/` (stdlib + numpy only) is
  importable without `bond_api`; `mission.py` is the single protocol seam.
- **Deterministic** — fixed seeds, no wall-clock in persisted artifacts.
- **Verified** — ≥90% line+branch coverage on `src/`, zero mocks, `ruff` +
  `mypy` clean.

## Run it

The checkout is self-contained — `bond-api` is vendored at `vendor/bond-api/`:

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/execute.py                          # run the mission
uv run python scripts/z_generate_manuscript_variables.py   # manuscript + figures
```

## Any clone

`bond-api` is vendored at `vendor/bond-api/` — a byte-for-byte copy of
`docxology/bond-api` at the commit recorded in `vendor/bond-api/PROVENANCE.json`
— and `[tool.uv.sources]` points at it, so `uv sync` resolves in any clone, with
no sibling or suite directory present. That is what Dependabot's update jobs
need: they check out this repository alone.

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
```

`scripts/vendor.py --check` — also run by `tests/test_vendor_provenance.py`
inside the gate above — fails if any vendored file drifts from its record: the
copy is a dependency, not a fork, so an edit belongs upstream and comes back
through `scripts/vendor.py --refresh --from <bond-api checkout>`.
`vendor/bond-api/VENDOR.md` carries the provenance table for a reader.

`pyproject.toml` carries the `pytest`, `coverage`, `mypy` **and** `ruff`
settings, so every gate behaves identically here and in the suite.

Stays in the PROJECT BOND suite layout under `projects/working/bond/` when used
there; integrity is enforced by the BOND guardrails and the package's own gates.
