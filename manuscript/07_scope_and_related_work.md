# Scope and related work

## Scope boundary

SNIPER'S NEST models the deterministic core of a special-agent mission only. It
does **not** simulate aerodynamics beyond the point-mass quadratic-drag law
(no spin, Coriolis, Magnus, or atmospheric layering), nor does it model
adversarial stochastics, human factors, or network communications. Terrain is a
seeded grid of landcover and concealment; the planner optimizes a blended
cost, not a full line-of-sight ballistic occlusion query. These simplifications
are deliberate: they keep every result deterministic, fast, and auditable.

## Relation to the broader simulation canon

* **External ballistics** — the point-mass drag model follows the standard
  small-arms treatment (a quadratic drag law with a ballistic coefficient);
  the zeroing and windage geometry mirrors conventional rifle-zero practice,
  with near/far zero capture.
* **Risk-gated decision procedures** — the discrete, thresholded approval path
  of `defection_protocol.py` is a classic monotone decision chain; its weighted
  hazard scoring follows a transparent exposure-weighting scheme.
* **Terrain routing** — Dijkstra's algorithm over a cost grid is the canonical
  least-cost routing method; the contribution here is the *cover* term that
  folds concealment into route cost and an independent cover audit.

## Intended use

The package is one film in the PROJECT BOND suite. Its role is to implement the
frozen BOND-API `MissionProvider` contract with a real, deterministic,
well-tested domain core, and to serve as a canonical example of converting a
template scaffold into a standalone mission package. It is local-only and is
discovered by the suite orchestrator via `bond_api`.
