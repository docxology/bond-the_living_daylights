# SNIPER'S NEST — Live Counts

> Regenerable. Do not hand-edit prose metrics elsewhere; this file is the live
> record of measured test totals and coverage. Every other document in this
> package describes the *gate*, not these numbers.

| Metric | Value |
| --- | --- |
| Test count | 125 |
| Coverage (line + branch, `src/`) | 99.44% |
| Coverage gate | `--cov-fail-under=90` |
| Failures / errors / skips | 0 / 0 / 0 |
| Mock-framework usages | 0 (enforced by `tests/test_no_mock_frameworks.py`, AST scan of `src/`, `tests/`, `scripts/`) |
| Python | 3.14.6 |

Command used to regenerate:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

## Uncovered remainder — the complete list

Three missed statements and five partial branches, enumerated in full from the
run above (`coverage json`) rather than summarised. Each entry names the exact
line so the list can be checked against the report instead of trusted:

| Location | Kind | What it is |
| --- | --- | --- |
| `ballistics.py` 304→305, line 305 | branch + line | `_sample_at`'s zero-width-span guard (`x1 == x0`); the RK4 sampler advances downrange every step, so two identical `x` values do not occur on the public paths |
| `ballistics.py` 383→384, line 384 | branch + line | `capture_zero`'s exact-zero crossing (`diff == 0.0`); a float trajectory sample landing exactly on the sight line |
| `figures/plots.py` 183→186 | branch | the `best is None` arm of the overwatch plate; `render_overwatch_figure` reads the live solution, in which one candidate is visible, and takes no injection point |
| `terrain_ops.py` 253→268 | branch | Dijkstra's heap running empty rather than reaching the goal — only possible on a disconnected grid |
| `terrain_ops.py` 268→269, line 269 | branch + line | the unreachable-goal `raise` that the empty-heap exit leads to |

All five are defensive guards on a 4-connected, fully reachable grid and a
strictly advancing integrator; none is reachable through the public API as
currently parameterised. The list is exhaustive: the earlier version of this
paragraph named four items and omitted `manuscript_variables.py 104→112`, which
was a *reachable* public branch (`require_outputs=False`) rather than a
defensive guard. It is now covered by
`test_require_outputs_false_actually_disables_the_gate`, and no undocumented
uncovered line remains.
