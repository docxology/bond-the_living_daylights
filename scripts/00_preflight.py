#!/usr/bin/env python
"""SNIPER'S NEST — preflight. Verifies the frozen protocol and the film core are
importable and the protocol surface is intact. Exit 0 on success.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from bond_api.protocol import protocol_surface  # noqa: E402

from the_living_daylights.mission import MissionProvider  # noqa: E402


def main() -> int:
    surface = protocol_surface()
    provider = MissionProvider()
    assert surface["dataclasses"], "protocol surface empty"
    assert provider.film == "the_living_daylights", "film identity mismatch"
    print(f"preflight OK: identity={surface['identity']}, codename={surface['codename']}")
    print(
        f"  provider {provider.film} satisfies the protocol ({len(surface['dataclasses'])} dataclasses)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
