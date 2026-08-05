#!/usr/bin/env python
"""SNIPER'S NEST — manuscript variable hydration + figure rendering.

Strict by default: any unfinished ``{{TOKEN}}`` in a resolved manuscript
section fails the run. Writes ``output/data/manuscript_variables.json``,
``output/manuscript/*.md`` (resolved sections), and renders
``output/figures/*.png``. Regenerable, deterministic (run it last).

Reads no wall clock, so two runs write byte-identical trees.
``--output-root DIR`` redirects every artifact under ``DIR`` instead of the
package's ``output/``; that is what lets
``tests/test_regeneration_determinism.py`` compare two full regenerations
without touching the package tree.
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


def _output_root(args: list[str], default: Path) -> Path:
    """Resolve ``--output-root DIR``, defaulting to the package's ``output/``."""
    if "--output-root" not in args:
        return default
    index = args.index("--output-root")
    if index + 1 >= len(args):
        raise SystemExit("--output-root requires a directory argument")
    return Path(args[index + 1]).resolve()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    allow_draft = "--allow-draft" in args
    variables = generate_variables(require_outputs=not allow_draft)
    root = Path(__file__).resolve().parent.parent
    out_root = _output_root(args, root / "output")
    data_dir = out_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manuscript_variables.json").write_text(
        json.dumps(variables, indent=2, sort_keys=True), encoding="utf-8"
    )
    _out, resolved = resolve_manuscript_tree(
        variables, output_dir=out_root / "manuscript", strict=not allow_draft
    )
    figures = render_all_figures(out_root / "figures")
    print(f"resolved {len(resolved)} manuscript sections under {_out}")
    print(f"tokens: {len(variables)}")
    for fig in figures:
        print(f"figure: {fig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
