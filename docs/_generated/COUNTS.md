# SNIPER'S NEST — Live Counts

> Regenerable. Do not hand-edit prose metrics elsewhere; this file is the live
> record of measured test totals and coverage. Every other document in this
> package describes the *gate*, not these numbers.

| Metric | Value |
| --- | --- |
| Test count | 111 |
| Coverage (line + branch, `src/`) | 99.37% |
| Coverage gate | `--cov-fail-under=90` |
| Failures / errors / skips | 0 / 0 / 0 |
| Mock-framework usages | 0 |
| Python | 3.14.6 |

Command used to regenerate:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Uncovered remainder — all deliberate, and documented in
[`../../TODO.md`](../../TODO.md): `ballistics._sample_at`'s zero-width-span
guard and `capture_zero`'s exact-zero crossing branch, `terrain_ops.plan_route`'s
unreachable-goal guard, and `figures/plots.py`'s `best is None` branch. None is
reachable through the public paths as currently parameterized; each is kept as
a defensive guard for future callers.
