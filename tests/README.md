# tests/ — SNIPER'S NEST

Real-data, zero-mock test suite for the pure domain core, the BOND-API mission
adapter, manuscript hydration, figures, and thin CLIs. See
[`../docs/testing_philosophy.md`](../docs/testing_philosophy.md).

Run with coverage (line + branch, ≥90% on `src/`):

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

`conftest.py` pins `MPLBACKEND=Agg` and adds `src/` to `sys.path`.
