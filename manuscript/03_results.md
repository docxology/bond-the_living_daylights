# Results

The deterministic mission solution ([`compute_mission.mission_solution()`](../src/the_living_daylights/compute_mission.py))
reports every number below; the manuscript never hand-authors a metric.

## Sniper ballistics

The {{BAL_ZERO_RANGE}} m zero requires an elevation of {{BAL_ELEVATION_MRAD}}
mrad for the {{BAL_CALIBER_MM}} mm round (BC {{BAL_BC}} kg/m²,
{{BAL_MUZZLE_VELOCITY}} m/s, {{BAL_BULLET_MASS_G}} g). The sight line and the
trajectory cross at the near zero {{BAL_NEAR_ZERO}} m and the primary far zero
{{BAL_FAR_ZERO}} m; at the {{BAL_TARGET_RANGE}} m target the round rides
{{BAL_DROP}} m below the line of departure with a {{BAL_TOF}} s time of flight.
A full-value {{BAL_WIND_MPS}} m/s crosswind deflects the round
{{BAL_WIND_DRIFT}} m, calling for a {{BAL_WIND_HOLD_MRAD}} mrad wind hold.
Figure [@fig:ballistics] shows the zeroed trajectory against the sight line
and the drift curve.

![Zeroed ballistic trajectory and crosswind drift](../output/figures/ballistics_trajectory.png){#fig:ballistics}

## Rules of engagement

The covering sniper's decision engine resolves the film's moral hinge
deterministically. The cellist — observed "cellist", non-hostile — resolves to
**{{ROE_CELLIST_MODE}}** ({{ROE_CELLIST_REASON}}): Bond refuses the lethal
shot. A hostile sentinel with a weapon present, but *not* the authorized asset,
resolves to **{{ROE_SENTINEL_MODE}}** ({{ROE_SENTINEL_REASON}}): the
trigger-guard shot disables the threat without an unlawful kill (see
[`ballistics.engagement_decision`](../src/the_living_daylights/ballistics.py)).

## The cello case

The {{CELL_NUM_PARTS}}-part takedown rifle ({{CELL_PART_NAMES}}) conceals in
the {{CELL_CASE_L_M}} x {{CELL_CASE_W_M}} x {{CELL_CASE_D_M}} m case interior:
packing returns `{{CELL_FITS}}` using {{CELL_LANES}} lanes, a longest-lane fill
of {{CELL_PACKED_LENGTH_M}} m, and an areal efficiency of
{{CELL_EFFICIENCY}}, with a {{CELL_ASSEMBLY_S}} s field assembly time (see
[`ballistics.pack_cello_case`](../src/the_living_daylights/ballistics.py)).

## Defection-handling protocol

The KOSKOV scenario runs through {{DEF_NUM_STAGES}} stages
({{DEF_STAGE_NAMES}}) with a plan score of {{DEF_PLAN_SCORE}} and an overall
verdict of **{{DEF_PLAN_VERDICT}}** against the
{{DEF_GO_THRESHOLD}}/{{DEF_CONDITIONAL_THRESHOLD}} thresholds, gated at the
**{{DEF_GATE}}** stage — the point where identity doubt and backstop
inconsistency surface. Earlier stages approve; later ones carry the plan only
under conditions.

## Mountain/desert terrain ops

On the seeded ({{TER_SEED}}) terrain grid, the planner routes
{{TER_DIST_KM}} km ({{TER_STEPS}} steps) from the entry cell to the exfil goal
at a blended cost of {{TER_COST}}, with a mean route concealment of
{{TER_MEAN_COVER}} and a worst-case (least-covered) segment of {{TER_MIN_COVER}}
at step {{TER_MIN_COVER_INDEX}}; {{TER_COVER_POINTS}} high-cover waypoints are
identified.

**Measured against baselines, the cover term is real but weak, and the route is
not a concealed one.** The same planner with the exposure term switched off
(`cover_weight = 0`) returns a route of {{TER_BARE_MEAN_COVER}} mean
concealment, so the term buys {{TER_COVER_TERM_GAIN}} of concealment — a real,
non-zero effect on a different path. But the grid's own mean concealment is
{{TER_FIELD_MEAN_COVER}}, and the shipped route's signed gap against it is
{{TER_COVER_VS_FIELD}} — the route is *less* concealed than an average cell.
At the mission's weighting the
blended cost is dominated by landcover traversal cost and climb, and
concealment is a mild preference rather than the objective. Calling this a
"covered exfil route" would overstate it. Raising `cover_weight` does clear the
field average, so the shortfall is a weighting choice and not a ceiling; both
relations are pinned in `tests/test_compute_mission.py`, so this paragraph
cannot drift from the numbers.

Run against the same waypoints, the `assess_cover` audit returns
{{TER_AUDIT_MEAN_COVER}}. That agreement is a cross-implementation check —
vectorised numpy against the planner's scalar loop, sharing no helper — and it
detects implementation drift only; both encode the same concealment definition,
so it is not independent corroboration of the model. Figure
[@fig:terrain] maps the route and its cover points on the concealment field.

![Planned exfil route on the concealment map](../output/figures/terrain_exfil_route.png){#fig:terrain}

## Countersniper optics

The {{OPT_MAGNIFICATION}}x mil-dot riflescope ({{OPT_OBJECTIVE_MM}} mm
objective, {{OPT_CLICK_MRAD}} mrad clicks) ranges the standing target at
{{OPT_MIL_RANGE_M}} m from the {{MIL_READING_MILS}}-mil reticle span and holds
{{OPT_HOLDOVER_MILS}} mils against the {{BAL_TARGET_RANGE}} m drop. The zero
dials onto the turret as {{OPT_ELEVATION_CLICKS}} elevation clicks and
{{OPT_WIND_CLICKS}} wind clicks; at the target range the first-order parallax
shift is {{OPT_PARALLAX_MM}} mm.

## Countersniper detection and localization

The hostile optic glints with a geometric brightness of {{CS_GLINT_GEOMETRY}}
at the {{CS_AZIMUTH_DELTA_DEG}}° sun–observer offset; the radiometric model
yields SNR {{CS_GLINT_SNR}} at {{CS_GLINT_RANGE_M}} m and a detection
probability of {{CS_GLINT_PDET}} (Figure [@fig:glint]). Acoustically, the
{{CRACK_BANG_DELAY_S}} s crack-bang delay at {{AIR_TEMP_C}} °C places the shot
{{CS_CRACK_BANG_M}} m away (sound speed {{CS_SOUND_SPEED}} m/s); crossed
bearings localize the hostile to ({{CS_TRI_X_M}}, {{CS_TRI_Y_M}}) m. The fit
also prints a {{CS_TRI_RESIDUAL_M}} m residual, and that number is reported
here only to be discounted: with {{CS_NUM_OBSERVERS}} bearings the least-squares
system is exactly determined, so the residual is identically zero by
construction for any non-parallel pair and the printed value is floating-point
rounding. It is not a measure of localization accuracy, and no accuracy claim
rests on it.

![Countersniper optic-glint detection probability vs range](../output/figures/glint_detection.png){#fig:glint}

## Overwatch selection

The extraction site sits at {{OW_TARGET_CELL}} — the terrain's global
elevation minimum, and therefore in a near-total blind spot. Sampling every
{{OW_CANDIDATE_STEP}} cells and keeping only positions within
{{OW_MAX_RANGE_CELLS}} cells leaves {{OW_NUM_CANDIDATES}} in-range candidates,
of which only {{OW_VISIBLE_CANDIDATES}} ({{OW_VISIBLE_FRACTION}} fraction) can
actually see the site over the intervening terrain and cover. Selection runs
through `best_overwatch`, which takes the top-scored candidate *that can see
the site*, not the top-scored candidate outright — a blind position keeps up to
0.60 of the score from proximity, cover, and elevation, so the two need not
coincide. The selected nest at {{OW_BEST_CELL}} commands the site from
{{OW_BEST_DISTANCE_M}} m with {{OW_BEST_ELEV_GAIN_M}} m of elevation advantage
and {{OW_BEST_COVER}} concealment, scoring {{OW_BEST_SCORE}} (Figure
[@fig:overwatch]).

![Ranked overwatch nests for the extraction site](../output/figures/overwatch_nests.png){#fig:overwatch}

## Evidence verification

The verify stage's backstop model accumulates {{VER_NUM_CHECKS}} weighted
checks ({{VER_CHECK_LABELS}}) into a certainty of {{VER_CERTAINTY}}, rendering
the verdict **{{VER_VERDICT}}**, which matches the staged assessment's
{{DEF_GATE}} gate. The two read no shared variable, but they are not
independent evidence: both `koskov_scenario` and `koskov_verification` are
hardcoded constant tables in one module, authored together to encode the film's
verification doubt. The match shows the staged and backstop scoring paths are
mutually consistent given consistent authored inputs — a design check, not a
corroborated finding.
