# docs/ — SNIPER'S NEST documentation hub

| File | Purpose |
| --- | --- |
| `agent_instructions.md` | Behavioral rules for AI agents (read first). |
| `architecture.md` | Layer boundaries and dependency direction. |
| `testing_philosophy.md` | Zero-mock, real-data, determinism, coverage gate. |
| `_generated/COUNTS.md` | Live test count + achieved coverage. |
| `AGENTS.md` | This directory index. |

The package top-level `AGENTS.md` and `docs/architecture.md` encode the layer
contract: a pure domain core beneath the thin `bond_api` mission adapter.

## Reading order

1. `../AGENTS.md` — package overview and verification.
2. `agent_instructions.md` — operational constraints.
3. `architecture.md` — where code belongs.
4. `testing_philosophy.md` — how tests are written.
