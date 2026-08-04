# scripts/ — AGENTS.md

Thin orchestrators for the SNIPER'S NEST mission. Scripts are glue: they
bootstrap `src/` onto `sys.path`, instantiate the mission provider, call one
phase, and print the result. All business logic lives in `src/the_living_daylights/`.

| Script | Phase / role |
| --- | --- |
| `brief.py` / `recon.py` / `plan.py` / `execute.py` / `debrief.py` | One per mission lifecycle phase. |
| `z_generate_manuscript_variables.py` | Hydrate manuscript tokens + render figures. |
| `00_preflight.py` | Verify protocol + provider importable. |

Run with `uv run python scripts/<name>.py` from this package directory. Keep
scripts thin; never move math into them.
