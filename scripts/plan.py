#!/usr/bin/env python
"""SNIPER'S NEST — mission phase CLI: plan.

Prints the deterministic five-step mission plan.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from the_living_daylights.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    print("mission plan:")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.name}  ({step.action}) {step.params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
