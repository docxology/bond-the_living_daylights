# Scope and related work

## Scope boundary

SNIPER'S NEST models the deterministic core of a special-agent mission only.
Stated as explicit non-claims:

* **Aerodynamics** stop at the point-mass quadratic-drag law with a constant
  drag coefficient. There is no spin drift, no Magnus effect, no Coriolis term,
  no transonic drag rise, and no atmospheric layering; the barometric density
  helper is a single exponential scale height, not a standard-atmosphere table.
* **Radiometry** is a first-order energy budget. Sky radiance is a fixed
  daylight constant, the lens is a single specular reflector with one
  reflectivity, and there is no spectral, polarization, or
  atmospheric-extinction treatment. The detection curve is a normal CDF over
  SNR, not a measured ROC.
* **Acoustics** use only the flash-to-bang delay against a linear
  temperature-dependent sound speed. There is no ballistic shockwave (Mach
  cone) geometry, no multipath or reverberation, and no wind-borne refraction.
* **Localization** is a noiseless least-squares bearing intersection. Bearings
  carry no uncertainty model, so the reported residual measures geometric
  consistency of the observations, not positional accuracy. At the mission's
  two observers it does not even measure that: two non-parallel bearings give
  an exactly determined system whose residual is identically zero, so the value
  printed in the results is rounding noise and carries no information at all.
  A residual becomes informative only with three or more inconsistent bearings.
* **Terrain** is a seeded grid of elevation, landcover, and standing cover.
  Routing is 4-adjacent Dijkstra on a blended cost; visibility is a single-ray
  Bresenham walk with a fixed clearance and no earth curvature, refraction, or
  sub-cell relief. The planner optimizes that blended cost, not a full
  line-of-sight ballistic occlusion query.
* **Adversaries and humans** are not modelled at all: no stochastic opponent,
  no reaction times, no human factors, no communications network.

These simplifications are deliberate. They are what keep every result
deterministic, fast, and auditable, and they are why the package can assert
byte-identical reruns rather than statistical agreement.

## Relation to the broader simulation canon

* **External ballistics** — the point-mass drag model with a ballistic
  coefficient is the standard small-arms treatment [@mccoy1999]; the zeroing
  and windage geometry mirrors conventional rifle-zero practice, with near/far
  zero capture. Mil-dot ranging follows established sniper doctrine
  [@fm2310sniper].
* **Countersniper detection** — acoustic shooter localization from crossed
  bearings is the operating principle of fielded countersniper systems
  [@duckworth1996counter; @ledeczi2005countersniper]; the glint model is an
  energy-budget reduction of optical retro-reflection detection, and the
  detection probability is the classical signal-detection formulation
  [@vantrees1968] against a reference solar irradiance [@astmg173]. The
  temperature-dependent sound speed is the standard linear approximation
  [@kinsler2000].
* **Terrain visibility** — line of sight over a rasterized cell walk
  [@bresenham1965] and the accumulation of visible cells into a viewshed are
  the canonical GIS treatment [@fisher1996viewshed]. The contribution here is
  not the viewshed itself but the *ranking*: turning visibility into an
  overwatch-selection objective alongside proximity, concealment, and elevation
  advantage.
* **Risk-gated decision procedures** — the discrete, thresholded approval path
  of `defection_protocol.py` is a classic monotone decision chain; its weighted
  hazard scoring follows a transparent exposure-weighting scheme. The
  contribution is pairing a staged plan gate with a separately parameterised
  evidence-verification model. Both scenarios are authored constant tables, so
  the pairing is a structural one; agreement between them is not independent
  evidence and is not offered as such.
* **Terrain routing** — Dijkstra's algorithm over a cost grid [@dijkstra1959]
  is the canonical least-cost routing method; the contribution here is the
  *cover* term that folds concealment into route cost — reported against two
  measured baselines (the same planner with the term off, and the grid's own
  mean concealment) rather than asserted — plus a cover audit that can grade
  any proposed path, not only the planner's own.

## Intended use

The package is one film in the PROJECT BOND suite. Its role is to implement the
frozen BOND-API `MissionProvider` contract with a real, deterministic,
well-tested domain core, and to serve as a canonical example of converting a
template scaffold into a standalone mission package. It is local-only and is
discovered by the suite orchestrator via `bond_api`.
