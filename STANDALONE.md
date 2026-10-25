# SNIPER'S NEST — standalone package

**The Living Daylights: SNIPER'S NEST — Special-Agent Mission Software**

A deterministic PROJECT BOND film package: sniper ballistics (rifle zero,
windage, rules of engagement, the cello case), riflescope optics, countersniper
detection and localization, terrain visibility and overwatch selection, staged
risk-scored defection handling with backstop evidence verification, and
mountain/desert terrain operations. It implements the frozen BOND-API
`MissionProvider` protocol.

- **Standalone checkout** — canonical remote
  `github.com/docxology/bond-the_living_daylights` (private). No DOI has been
  minted, so the publication sidecars (`CITATION.cff`, `.zenodo.json`,
  `codemeta.json`) carry no DOI or repository URL.
- **Pure domain core** — `src/the_living_daylights/` (stdlib + numpy only) is
  importable without `bond_api`; `mission.py` is the single protocol seam.
- **Deterministic** — fixed seeds, no wall-clock in persisted artifacts.
- **Verified** — ≥90% line+branch coverage on `src/`, zero mocks, `ruff` +
  `mypy` clean.

## Run it

Inside the suite working tree, where `[tool.uv.sources]` resolves `bond-api`:

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/execute.py                          # run the mission
uv run python scripts/z_generate_manuscript_variables.py   # manuscript + figures
```

## Bare clone

`bond-api` is a suite-local package: it is not on PyPI, and `[tool.uv.sources]`
pins the monorepo working-tree path, so `uv sync` cannot resolve it here. Every
gate still runs once `bond_api` is on the interpreter path:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy matplotlib pyyaml pytest pytest-cov ruff mypy types-PyYAML
PYTHONPATH=src:<dir holding bond_api/> \
  .venv/bin/python -m pytest tests/ --cov=src --cov-fail-under=90
```

`src` belongs on `PYTHONPATH`, not just in pytest's `pythonpath` ini, because
several tests exercise the core in a spawned interpreter.

`pyproject.toml` carries the `pytest`, `coverage`, `mypy` **and** `ruff`
settings, so every gate behaves identically here and in the suite.

Stays in the PROJECT BOND suite layout under `projects/working/bond/` when used
there; integrity is enforced by the BOND guardrails and the package's own gates.
