#!/usr/bin/env python
"""SNIPER'S NEST — mission phase CLI: execute.

Runs the mission and prints the deterministic outcome with provenance.
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
    outcome = debrief.outcome
    r = outcome.results
    b = r["ballistics"]
    print(f"mission: {provider.film} / {provider.brief().codename}")
    print(f"success: {outcome.success}")
    print(
        f"  fused zero   : {b['elevation_mrad']:.2f} mrad  (near {b['near_zero_m']:.1f} m, far {b['far_zero_m']:.1f} m)"
    )
    print(f"  wind drift   : {b['wind_drift_m']:.3f} m  ->  hold {b['wind_hold_mrad']:.2f} mrad")
    print(
        f"  defection    : {r['defection']['plan_verdict']} (gate: {r['defection']['gate_stage']})"
    )
    print(
        f"  terrain      : {r['terrain']['route_distance_m'] / 1000:.2f} km, mean cover {r['terrain']['mean_cover']:.3f}"
    )
    print(f"  cello case   : fits={r['cello_case']['fits']}, lanes={r['cello_case']['lanes_used']}")
    prov = outcome.provenance
    print(f"provenance    : v{prov.package_version} seed {prov.seed} hash {prov.input_hash[:16]}")
    return 0 if outcome.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
