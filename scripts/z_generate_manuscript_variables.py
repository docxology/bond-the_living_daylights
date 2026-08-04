#!/usr/bin/env python
"""SNIPER'S NEST — manuscript variable hydration + figure rendering.

Strict by default: any unfinished ``{{TOKEN}}`` in a resolved manuscript
section fails the run. Writes ``output/data/manuscript_variables.json``,
``output/manuscript/*.md`` (resolved sections), and renders
``output/figures/*.png``. Regenerable, deterministic (run it last).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from the_living_daylights.figures.plots import render_all_figures  # noqa: E402
from the_living_daylights.manuscript_variables import (  # noqa: E402
    generate_variables,
    resolve_manuscript_tree,
)


def main(argv: list[str] | None = None) -> int:
    allow_draft = "--allow-draft" in (argv if argv is not None else sys.argv[1:])
    variables = generate_variables(require_outputs=not allow_draft)
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manuscript_variables.json").write_text(
        json.dumps(variables, indent=2, sort_keys=True), encoding="utf-8"
    )
    _out, resolved = resolve_manuscript_tree(variables, strict=not allow_draft)
    figures = render_all_figures()
    print(f"resolved {len(resolved)} manuscript sections under {_out}")
    print(f"tokens: {len(variables)}")
    for fig in figures:
        print(f"figure: {fig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
