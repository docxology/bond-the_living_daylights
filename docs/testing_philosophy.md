# SNIPER'S NEST — Testing Philosophy

## Zero-mock, real-data determinism

All tests use real computation and real data. There is no mocking framework
anywhere in `tests/` (no `unittest.mock` / `MagicMock` / `@patch` /
`create_autospec`). A mock test can pass while the domain logic is wrong; a
real-data test cannot. Determinism is enforced by construction: fixed seeds
(terrain), no global RNG, no wall-clock in persisted artifacts.

## Coverage gate

Coverage is measured on `src/` only (line **and** branch) and must be ≥90%:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Live count + coverage live in [`_generated/COUNTS.md`](_generated/COUNTS.md).

## Test inventory

| File | Coverage focus |
| --- | --- |
| `tests/test_ballistics.py` | Zero, near/far zero, windage, ROE (trigger-guard), cello-case packing, validation branches, determinism |
| `tests/test_defection_protocol.py` | Weighted hazards, go/conditional/no-go verdicts, monotonic approval, gate, validation |
| `tests/test_terrain_ops.py` | Seeded grid, step costs, Dijkstra route, cover trade-off, cover audit, validation |
| `tests/test_compute_mission.py` | Mission solution keys, determinism, input hash, parameter sensitivity |
| `tests/test_mission.py` | Protocol compliance, full lifecycle, deterministic provenance, gadget registration |
| `tests/test_manuscript_variables.py` | Token map, live `{{TOKEN}}` cross-reference, strict resolution |
| `tests/test_figures.py` | Ballistics + terrain plates render to real files |
| `tests/test_scripts_smoke.py` | Thin CLIs run via `sys.executable` subprocess and produce expected output/artifacts |

## Determinism proofs

- identical mission solution across calls (byte-equal dicts);
- identical provenance `input_hash` across calls;
- identical terrain route across re-runs for a fixed seed;
- the manuscript cross-reference test guarantees every placeholder in
  `manuscript/[0-9]*.md` is generated.
