#!/usr/bin/env python
"""SNIPER'S NEST — mission phase CLI: recon.

Surveys the environment and returns the film's reconnaissance findings.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from bond_api.protocol import ReconRequest  # noqa: E402

from the_living_daylights.mission import MissionProvider  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SNIPER'S NEST reconnaissance")
    parser.add_argument(
        "--goal", default="cover the defection at the extraction site", help="recon goal"
    )
    args = parser.parse_args(argv)
    report = MissionProvider().recon(ReconRequest(goal=args.goal))
    print(f"recon goal: {args.goal}")
    for finding in report.findings:
        print(f"  [{finding.label}] {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
