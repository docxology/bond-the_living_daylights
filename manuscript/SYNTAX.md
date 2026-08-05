# Manuscript Syntax Reference — the_living_daylights (SNIPER'S NEST)

The Pandoc conventions this manuscript actually uses, and the live registries of
its figures and tokens. Everything below is checked against the files on disk;
if you add a figure or a token, update the matching registry here.

## Token protocol (the rule that matters)

Numbers never appear as literals in prose. Every metric is written as a
brace-delimited token and substituted at hydration time:

```markdown
The zero requires an elevation of {{BAL_ELEVATION_MRAD}} mrad.
```

Pipeline:

1. `scripts/z_generate_manuscript_variables.py` calls
   `src/the_living_daylights/manuscript_variables.py::generate_variables()`.
2. `generate_variables()` reads [`config.yaml`](config.yaml) plus the
   deterministic solution from
   `src/the_living_daylights/compute_mission.py::mission_solution()`, and is
   guarded by `REQUIRED_SOLUTION_SECTIONS`.
3. The script writes the whole mapping to
   `output/data/manuscript_variables.json`.
4. `resolve_manuscript_tree()` copies each `NN_*.md` into `output/manuscript/`,
   substituting every token. In strict mode (the default) any leftover
   placeholder raises and the run fails.

**Adding a token**

1. Expose the value from `mission_solution()` (a new top-level section must also
   be added to `REQUIRED_SOLUTION_SECTIONS`).
2. Add the key to the `variables` dict in `generate_variables()`.
3. Cite it in a section. `tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`
   fails automatically if a section cites a token the code does not produce.
4. Check it: `uv run python -c "import json;print(json.load(open('output/data/manuscript_variables.json'))['MY_TOKEN'])"`

**Gotcha.** Prose that needs to *talk about* a placeholder must not write
literal double braces — strict resolution treats them as unresolved tokens and
fails the section. Describe them in words instead.

### Token families

| Prefix | Source section of the mission solution | Examples |
|---|---|---|
| `BAL_` | `ballistics` | `BAL_ELEVATION_MRAD`, `BAL_NEAR_ZERO`, `BAL_WIND_HOLD_MRAD` |
| `ROE_` | `rules_of_engagement` | `ROE_CELLIST_MODE`, `ROE_SENTINEL_REASON` |
| `OPT_` | `optics` (+ scope settings) | `OPT_MIL_RANGE_M`, `OPT_ELEVATION_CLICKS`, `OPT_PARALLAX_MM` |
| `CS_` | `countersniper` | `CS_GLINT_SNR`, `CS_CRACK_BANG_M`, `CS_TRI_RESIDUAL_M` |
| `OW_` | `overwatch` | `OW_BEST_CELL`, `OW_VISIBLE_FRACTION`, `OW_MAX_RANGE_CELLS` |
| `VER_` | `verification` | `VER_CERTAINTY`, `VER_VERDICT`, `VER_CHECK_LABELS` |
| `CELL_` | `cello_case` | `CELL_LANES`, `CELL_PACKED_LENGTH_M`, `CELL_CASE_L_M` |
| `DEF_` | `defection` | `DEF_PLAN_VERDICT`, `DEF_GATE`, `DEF_STAGE_NAMES` |
| `TER_` | `terrain` | `TER_DIST_KM`, `TER_MEAN_COVER`, `TER_AUDIT_MEAN_COVER` |
| (identity / env) | `config.yaml`, `settings.py`, platform | `TITLE`, `CODENAME`, `VERSION`, `CONFIG_KEYWORDS`, `PYTHON_VERSION`, `GENERATION_TIMESTAMP` |

The authoritative list is the `variables` dict in `manuscript_variables.py`; the
hydrated snapshot is `output/data/manuscript_variables.json`.

## Citation syntax (Pandoc)

```markdown
[@fm2310sniper]                              <!-- single -->
[@duckworth1996counter; @ledeczi2005countersniper]   <!-- multiple -->
[@mccoy1999, pp. 42-45]                      <!-- with locator -->
@dijkstra1959 showed that...                 <!-- narrative -->
```

Every key must exist in [`references.bib`](references.bib). Never write raw
`\cite{}` in Markdown. The full annotated list is in
[`99_references.md`](99_references.md).

### Citation key registry

| Key | Backs |
|---|---|
| `mccoy1999` | Point-mass drag model, `ballistics.py` |
| `fm2310sniper` | Mil-dot ranging doctrine, `optics.py` |
| `duckworth1996counter`, `ledeczi2005countersniper` | Acoustic shooter localization, `countersniper.py` |
| `vantrees1968` | Signal-detection formulation for `glint_detection_probability` |
| `astmg173` | Reference solar irradiance in the glint energy budget |
| `kinsler2000` | Temperature-dependent speed of sound |
| `bresenham1965` | Integer cell walk in `visibility.line_of_sight` |
| `fisher1996viewshed` | Viewshed methodology |
| `dijkstra1959` | Least-cost routing in `terrain_ops.plan_route` |
| `friedman2026sniper`, `bondapi2026` | This package and the frozen suite protocol |

## Figure references

```markdown
![Zeroed ballistic trajectory and crosswind drift](../output/figures/ballistics_trajectory.png){#fig:ballistics}

Figure [@fig:ballistics] shows the zeroed trajectory.
```

Images must exist under `output/figures/` at render time — run
`scripts/z_generate_manuscript_variables.py` first. Captions are self-contained:
they become the PDF caption and the HTML alt text.

### Figure label registry

| Label | PNG | Generator in `src/the_living_daylights/figures/plots.py` | Cited in |
|---|---|---|---|
| `{#fig:ballistics}` | `output/figures/ballistics_trajectory.png` | `render_ballistics_figure()` | `03_results.md` |
| `{#fig:terrain}` | `output/figures/terrain_exfil_route.png` | `render_terrain_figure()` | `03_results.md` |
| `{#fig:glint}` | `output/figures/glint_detection.png` | `render_glint_figure()` | `03_results.md` |
| `{#fig:overwatch}` | `output/figures/overwatch_nests.png` | `render_overwatch_figure()` | `03_results.md` |

`render_all_figures()` renders all four. There are currently **no** numbered
equation labels, table labels, or section labels in this manuscript; if you add
one, use the Pandoc bracket form (`[@eq:label]`, `[@tbl:label]`,
`[@sec:label]`) and register it here. Never use raw LaTeX `\ref` / `\eqref`.

## Section order

```text
00_abstract.md                → Abstract
01_introduction.md            → Introduction
02_methodology.md             → Methodology
03_results.md                 → Results
04_conclusion.md              → Conclusion
05_experimental_setup.md      → Experimental setup
06_reproducibility.md         → Reproducibility
07_scope_and_related_work.md  → Scope and related work
99_references.md              → References
```

Sections are assembled in lexicographic order, so `00_` puts the abstract first
and `99_` puts the references last. `resolve_manuscript_tree()` processes
exactly the `[0-9][0-9]_*.md` glob — sidecars like this file, `README.md`,
`AGENTS.md`, `preamble.md`, and `layer_contract.yaml` are never hydrated or
rendered as prose.

## Preamble

[`preamble.md`](preamble.md) holds the LaTeX packages injected at PDF render
time. Do not duplicate a package that is already there, and remember that
tolerance/hfuzz changes affect line-breaking across the whole document.

## BibTeX entry format

```bibtex
@article{dijkstra1959,
  author  = {Dijkstra, Edsger W.},
  title   = {A note on two problems in connexion with graphs},
  journal = {Numerische Mathematik},
  year    = {1959},
  volume  = {1},
  number  = {1},
  pages   = {269--271},
  doi     = {10.1007/BF01386390}
}
```

Keys are lowercase alphanumeric with optional underscores. Every entry carries
at minimum `author`, `title`, and `year`. **Every entry must be a real,
checkable publication.** If you cannot verify a source exists, delete it rather
than ship it — a fabricated citation is worse than a missing one.

## Prose conventions

- No "In summary" / "In conclusion" openers at section ends.
- Active voice in methodology.
- Reference code by explicit path — `src/the_living_daylights/optics.py`, not
  "the optics module".
- One idea per paragraph.
- No metric typed as a literal. Ever.

## See also

- [`README.md`](README.md) — what each file in this directory is for.
- [`AGENTS.md`](AGENTS.md) — agent directives for editing the manuscript.
- [`../docs/architecture.md`](../docs/architecture.md) — where the numbers come from.
- [`../docs/agent_instructions.md`](../docs/agent_instructions.md) — the package-wide rules.
