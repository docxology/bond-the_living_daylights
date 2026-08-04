"""Pytest fixtures for SNIPER'S NEST.

Adds ``src/`` to ``sys.path`` (required for ``the_living_daylights`` imports)
and pins the matplotlib backend to Agg so figure tests never open a display.
No mocks — all tests use real computation and real data.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))
