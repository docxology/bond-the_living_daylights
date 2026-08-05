# Conclusion

SNIPER'S NEST demonstrates that a special-agent mission's operational concepts
can be turned into real, deterministic, testable algorithms. The package:

* solves the **sniper ballistics** problem — zero, windage, rules-of-engagement,
  and cello-case concealment — with a physically grounded point-mass integrator;
* runs a **staged, risk-scored defection protocol** whose hazard model renders
  the canonical scenario conditional at the verify gate, alongside an
  **evidence-verification** model whose weighted backstop checks land on the
  same verdict from a separately authored table;
* plans **mountain/desert routes with a measured cover term** on a seeded,
  reproducible terrain grid, and selects the **overwatch nest** — the
  top-scored position that actually sees the extraction site, with concealment
  and elevation advantage;
* fights the **countersniper duel** — mil-dot ranging and click solutions on
  the riflescope, radiometric optic-glint detection, acoustic crack-bang
  ranging, and least-squares bearing triangulation of a hostile position;
* binds all of it to the frozen BOND-API `MissionProvider` protocol so the
  orchestrator can drive the film generically, with full deterministic
  provenance on every outcome.

The architecture keeps a pure, infrastructure-free domain core beneath a thin
mission adapter, and forces every reported metric through a single
deterministic solution — so the manuscript, the mission report, and the figures
cannot drift. That claim is enforced, not asserted: the token cross-reference
test fails on any placeholder the code does not generate, the hydration gate is
tested against a solution with each required section removed in turn, and the
reader-facing parameter echo in `config.yaml` is pinned key-for-key to
`settings.py`. Test count and achieved coverage live in
[`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md) rather than in this
prose, so no stated figure can outlive the run that produced it.

Two pairs of models cross-check each other, and it is worth being exact about
how much that is worth. The staged defection assessment and the backstop
evidence check read no shared variable, yet both are constant tables authored
in one module to encode one story beat, so their agreement is a
design-consistency check and not independent corroboration. The planner's route
summary and the cover audit are genuinely different code paths — a scalar loop
and a vectorised numpy pass, sharing no helper — so their agreement rules out
implementation drift, but both encode a single concealment definition and
neither can catch that definition being wrong. Each is therefore checked in the
suite against a third calculation performed in the test itself, and the earlier
claim that these pairings made the numbers "confirmed rather than
self-reported" was too strong.

Two further limitations belong in the summary rather than in a footnote. The
bearing-triangulation residual is identically zero for the mission's two
observers — the system is exactly determined, so that number measures nothing
and no localization accuracy follows from it. And the exfil route is *not* a
concealed route: the cover term has a real, measured effect against the same
planner with the term disabled, but the resulting path still sits below the
terrain's own mean concealment at the shipped weighting.

The triggering image of the title, the *trigger-guard* hold, is
not an arbitrary flourish: it falls out of the rules-of-engagement model as the
correct action when an innocent is not a target and a hostile's weapon is.
