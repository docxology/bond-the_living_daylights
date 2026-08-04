#!/usr/bin/env python
"""SNIPER'S NEST — mission phase CLI: brief.

Prints the film's mission brief (objectives, assets, constraints).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from the_living_daylights.mission import MissionProvider  # noqa: E402


def main() -> int:
    brief = MissionProvider().brief()
    print(f"film:     {brief.film}")
    print(f"codename: {brief.codename}")
    print("objectives:")
    for obj in brief.objectives:
        print(f"  - {obj}")
    print("assets:")
    for asset in brief.assets:
        print(f"  - {asset.kind}:{asset.name} = {asset.payload}")
    print("constraints:")
    for constraint in brief.constraints:
        print(f"  - {constraint.kind}: {constraint.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
