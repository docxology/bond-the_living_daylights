#!/usr/bin/env python
"""SNIPER'S NEST — mission phase CLI: debrief.

Executes the mission and prints the outcome plus the standing lessons.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from bond_api.protocol import ReconRequest, run_mission  # noqa: E402

from the_living_daylights.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    debrief = run_mission(provider, ReconRequest(goal="cover the defection at the extraction site"))
    print(f"debrief: {provider.film} — success={debrief.outcome.success}")
    print("lessons learned:")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0 if debrief.outcome.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
