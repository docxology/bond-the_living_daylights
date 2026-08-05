---
title: "Manuscript directory: the_living_daylights"
type: "manuscript_guide"
version: "0.1.0"
---

# Manuscript (`the_living_daylights/manuscript/`)

Package-wide agent rules live in
[`../docs/agent_instructions.md`](../docs/agent_instructions.md). This file
covers **manuscript-specific** editing: what each file is, the token protocol,
the figure protocol, and the workflow for changing a section.

## File inventory

| File | Role | Token families | Figures |
|---|---|---|---|
| `00_abstract.md` | Abstract — the six concepts and their headline results | Ballistics, cello case, optics, countersniper, defection, verification, terrain, overwatch | None |
| `01_introduction.md` | The film as spec, the module inventory, protocol integration, reader's guide | `CODENAME` | None |
| `02_methodology.md` | Module-by-module derivation of every algorithm | All families; cites every bibliography key | None |
| `03_results.md` | The computed mission solution; **all four figures live here** | All result families | `fig:ballistics`, `fig:terrain`, `fig:glint`, `fig:overwatch` |
| `04_conclusion.md` | What was shown, and how the anti-drift guarantees are enforced | None | None |
| `05_experimental_setup.md` | Parameter tables by subsystem + software environment | Parameter tokens, `PYTHON_VERSION`, `MANUSCRIPT_DATE` | None |
| `06_reproducibility.md` | Determinism argument, artifact inventory, the verification gate | `TER_SEED`, `MANUSCRIPT_DATE` | None |
| `07_scope_and_related_work.md` | Explicit non-claims, related work, intended use | None | None |
| `99_references.md` | Annotated reference list grouped by what each source backs | `VERSION` | None |
| `config.yaml` | Paper identity, authors, keywords, and a reader-facing `mission:` echo of `settings.py` | — | — |
| `references.bib` | BibTeX records — real, checkable sources only | — | — |
| `preamble.md` | LaTeX packages injected at PDF render time | — | — |
| `layer_contract.yaml` | Declarative layer contract (which module may import what) | — | — |
| `SYNTAX.md` | Pandoc syntax plus the live token, citation, and figure registries | — | — |
| `README.md` | Human quick reference for this directory | — | — |
| `AGENTS.md` | This file | — | — |

Only `[0-9][0-9]_*.md` files are hydrated and rendered. Everything else here is
a sidecar and is never treated as prose.

## Token protocol

**Never hardcode a number in prose.** A hardcoded value is wrong the moment
`settings.py` changes or the solution is recomputed, and nothing will tell you.

Every metric is a brace-delimited token resolved by
[`../src/the_living_daylights/manuscript_variables.py`](../src/the_living_daylights/manuscript_variables.py)'s
`generate_variables()`, which reads `config.yaml` plus
[`../src/the_living_daylights/compute_mission.py`](../src/the_living_daylights/compute_mission.py)'s
`mission_solution()` — the single place any number in this package is computed.

Adding a token:

1. Expose the value from `mission_solution()`. A new top-level section also has
   to be listed in `manuscript_variables.REQUIRED_SOLUTION_SECTIONS`, or the
   hydration gate will not protect it.
2. Add the key to the `variables` dict in `generate_variables()`.
3. Cite it in a section and register its family in [`SYNTAX.md`](SYNTAX.md).
4. `tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`
   fails automatically if prose cites a token the code does not produce — there
   is no separate step to remember.

Checking for unresolved tokens after hydration:

```bash
uv run python scripts/z_generate_manuscript_variables.py   # strict: raises on any leftover
grep -r "{{" output/manuscript/ && echo "UNRESOLVED" || echo "clean"
```

Note: prose that needs to *mention* a placeholder must not write literal double
braces — strict resolution rejects the section. Describe it in words.

## Parameters live in two places, and they are pinned

`../src/the_living_daylights/settings.py` is authoritative. The `mission:` block
in `config.yaml` is a **reader-facing echo** so someone reading the paper can
see the parameters without opening the code; nothing reads it at runtime.

`tests/test_manuscript_variables.py::test_config_mission_block_mirrors_settings`
compares the two key for key **and** asserts the key sets match, so adding a
parameter to one side without the other fails the suite in either direction.

## Figure protocol

Figures are rendered by
[`../src/the_living_daylights/figures/plots.py`](../src/the_living_daylights/figures/plots.py)
from the same mission solution the prose reads, so a figure cannot disagree
with the number beside it. All four are cited from `03_results.md`. Rendering
is deterministic — the suite renders twice and compares bytes.

Add a figure by writing a `render_*_figure(output_dir)` function that takes its
data from `mission_solution()` or the pure core, adding it to
`render_all_figures()`, registering the label in [`SYNTAX.md`](SYNTAX.md), and
covering it in `tests/test_figures.py`.

## Bibliography

Every entry in `references.bib` must be a real publication a reader can look
up. Do not invent a citation, do not approximate a DOI, and if you are not
confident a source exists, delete it rather than ship it — a fabricated
citation is worse than a missing one. `99_references.md` carries the annotated
list, grouped by what each source backs in the code.

## Changing a section

1. Edit the `NN_*.md` source — never `output/manuscript/`, which is generated.
2. If the change introduces a number, add the token first (above).
3. If it introduces a modelling claim, verify it against the code. Two defects
   of exactly this kind were caught in review: prose describing a `sin` term as
   a cosine, and prose citing the ballistic-holdover token as if it were the
   mil-dot reticle span.
4. Re-hydrate and re-run the gates:

```bash
uv run python scripts/z_generate_manuscript_variables.py
uv run pytest tests/ --cov=src --cov-fail-under=90
git status --short   # output/ is git-ignored; a clean tree is the determinism check
```

## Prose standards

- No "In summary" / "In conclusion" closers.
- Active voice in methodology; explicit file paths when referring to code.
- One idea per paragraph.
- State non-claims explicitly rather than leaving scope implied —
  `07_scope_and_related_work.md` is the model.
- Never quote a test count or a coverage percentage. Those live only in
  [`../docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md); prose
  describes the gate.

## See also

- [`README.md`](README.md) — quick orientation for this directory.
- [`SYNTAX.md`](SYNTAX.md) — Pandoc syntax and the live registries.
- [`../docs/architecture.md`](../docs/architecture.md) — where every number comes from.
- [`../docs/agent_instructions.md`](../docs/agent_instructions.md) — package-wide rules.
- [`../src/the_living_daylights/manuscript_variables.py`](../src/the_living_daylights/manuscript_variables.py) — `generate_variables()`.
