# Reproducibility

## Determinism

Every number in this manuscript is a pure function of fixed, documented inputs
([`src/the_living_daylights/settings.py`](../src/the_living_daylights/settings.py)).
The mission solution uses a fixed seed ({{TER_SEED}}); the only randomness in
the whole stack is the seeded terrain generator in
[`terrain_ops.generate_terrain`](../src/the_living_daylights/terrain_ops.py),
which is itself deterministic for a fixed seed. No wall-clock value enters any
persisted artifact except the regeneration timestamp of this manuscript
({{GENERATION_TIMESTAMP}}).

The BOND-API `MissionOutcome` carries a Provenance record with a stable
`input_hash` (a sha256 of the canonical mission solution), so any report can be
audited against the code without re-running the film's I/O.

## Artifacts and regeneration

| Artifact | Producer | Location |
|---|---|---|
| Mission report / figures | [`scripts/execute.py`](../scripts/execute.py), [`scripts/z_generate_manuscript_variables.py`](../scripts/z_generate_manuscript_variables.py) | `output/` (regenerable, git-ignored) |
| Resolved manuscript sections | `z_generate_manuscript_variables.py` | `output/manuscript/` |
| Ballistics + terrain figures | [`src/the_living_daylights/figures/plots.py`](../src/the_living_daylights/figures/plots.py) | `output/figures/ballistics_trajectory.png`, `output/figures/terrain_exfil_route.png` |
| Hydrated token map | `z_generate_manuscript_variables.py` | `output/data/manuscript_variables.json` |

## Verification gate

The package is verified end-to-end with:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

This enforces ≥90% line+**branch** coverage on `src/` with real data and zero
mocks, alongside `ruff` and `mypy` cleanliness on `src/` and `scripts/`. The
manuscript's token cross-reference test
([`tests/test_manuscript_variables.py`](../tests/test_manuscript_variables.py))
guarantees every placeholder in these sections is generated. Re-running
`z_generate_manuscript_variables.py` regenerates a byte-identical, git-clean
tree — a live determinism proof.
