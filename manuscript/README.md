# manuscript/ — SNIPER'S NEST

Sources for *The Living Daylights: SNIPER'S NEST — Special-Agent Mission
Software*: the paper's prose, its identity, and its bibliography.

## File roles

| File | Role |
| --- | --- |
| `00_abstract.md` … `07_scope_and_related_work.md` | The numbered prose sections, in render order. |
| `99_references.md` | Annotated reference list, grouped by what each source backs. |
| `references.bib` | BibTeX records. Real, checkable publications only. |
| `config.yaml` | Paper identity (title, subtitle, authors, keywords) plus a reader-facing `mission:` echo of `settings.py`. |
| `preamble.md` | LaTeX packages injected at PDF render time. |
| `SYNTAX.md` | Pandoc citation / figure / token syntax, with the live registries. |
| `layer_contract.yaml` | Declarative layer contract — which module may import what. |
| `AGENTS.md` | Agent directives for editing this directory. |

Only `[0-9][0-9]_*.md` files are hydrated and rendered; everything else is a
sidecar.

## Token protocol

Every metric flows through
[`../src/the_living_daylights/manuscript_variables.py`](../src/the_living_daylights/manuscript_variables.py)'s
`generate_variables()`, which reads `config.yaml` plus the deterministic
mission solution. **Never hand-author a number in prose.** The live
cross-reference test (`tests/test_manuscript_variables.py`) fails if any
placeholder in a numbered section is not generated, and strict resolution fails
the build if any placeholder survives substitution.

Two related rules:

* Test counts and coverage percentages appear only in
  [`../docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md). Prose
  describes the *gate*, never a snapshot.
* Parameters are authoritative in `settings.py`; `config.yaml`'s `mission:`
  block echoes them for readers and is pinned to the code by a test.

## Hydration

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

Writes the resolved sections to `output/manuscript/`, the token map to
`output/data/manuscript_variables.json`, and renders four figures to
`output/figures/` (ballistics trajectory, exfil route, glint-vs-range,
overwatch nests). All of `output/` is regenerable and git-ignored, so a rerun
must leave `git status` clean — that is a live determinism check.
