# manuscript/ — SNIPER'S NEST

Manuscript identity and sections for *The Living Daylights: SNIPER'S NEST —
Special-Agent Mission Software*.

## File roles

| File | Role |
| --- | --- |
| `00_abstract.md` … `07_scope_and_related_work.md` | Numbered prose sections. |
| `99_references.md`, `references.bib` | References. |
| `config.yaml` | Paper identity + mission parameters (single source). |
| `config.yaml.example` | Reference copy of every configurable field. |
| `SYNTAX.md` | Pandoc citation / figure / cross-reference syntax. |
| `layer_contract.yaml` | Declarative layer contract (validation input). |

## Token protocol

Every metric flows through
[`src/the_living_daylights/manuscript_variables.py`](../src/the_living_daylights/manuscript_variables.py)'s
`generate_variables()`, which reads `config.yaml` plus the deterministic
mission solution. Never hand-author a number in prose. The live cross-reference
test (`tests/test_manuscript_variables.py`) fails if any `{{TOKEN}}` in a
numbered section is not generated.

## Hydration

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

writes the resolved sections to `output/manuscript/`, the token map to
`output/data/manuscript_variables.json`, and renders both figures to
`output/figures/`. `output/` is regenerable and git-ignored.
