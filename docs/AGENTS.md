# docs/ — SNIPER'S NEST agent documentation

Operational rulebook for agents and developers inside `the_living_daylights`.
Every file is a hard constraint, not a suggestion.

| File | Purpose |
| --- | --- |
| `agent_instructions.md` | Behavioral rules (read first). |
| `architecture.md` | Layer boundaries + dependency direction. |
| `testing_philosophy.md` | Zero-mock, real-data, determinism, coverage gate. |
| `_generated/COUNTS.md` | Live test count + achieved coverage. |
| `README.md` | Quick navigation. |

## Key conventions

- **Pure core / thin adapter.** The domain modules are infrastructure-free;
  `mission.py` is the only `bond_api` import.
- **Zero mocks.** No `unittest.mock` / `MagicMock` anywhere in `tests/`.
- **Determinism.** Fixed seeds; no wall-clock in persisted artifacts.
- **No hardcoded metrics in prose.** All numbers hydrate through
  `manuscript_variables.generate_variables()`.
- **No lineage.** The tree stays free of `template[_]code_project` strings.

## Verification

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
```

Live counts: [`_generated/COUNTS.md`](_generated/COUNTS.md).
