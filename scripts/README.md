# scripts/ — thin mission CLIs

Thin orchestrators per mission phase. Business logic lives in `src/`; each
script only bootstraps `src/` onto `sys.path`, instantiates the provider, calls
a phase, and prints the result.

| Script | Phase |
| --- | --- |
| `brief.py` | Print the mission brief. |
| `recon.py` | Run reconnaissance (`--goal`). |
| `plan.py` | Print the mission plan. |
| `execute.py` | Run the full deterministic mission, print outcome + provenance. |
| `debrief.py` | Run the mission and print lessons learned. |
| `z_generate_manuscript_variables.py` | Hydrate manuscript tokens + render figures. |
| `00_preflight.py` | Verify the protocol + provider are importable. |

```bash
uv run python scripts/brief.py
uv run python scripts/execute.py
uv run python scripts/z_generate_manuscript_variables.py
```
