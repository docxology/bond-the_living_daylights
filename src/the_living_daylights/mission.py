"""SNIPER'S NEST — the mission adapter for the frozen BOND-API protocol.

This module is the film package's contract surface: top-level module named by
the package slug exposing ``MissionProvider``. It adapts the pure domain core
(:mod:`ballistics`, :mod:`defection_protocol`, :mod:`terrain_ops`) and the
shared deterministic :func:`~the_living_daylights.compute_mission.mission_solution`
to ``bond_api``'s frozen dataclasses, and registers the film's gadgets with the
:class:`bond_api.registry.GadgetRegistry`.

Discovery (``bond_api.discovery``) imports ``the_living_daylights.mission``,
instantiates ``MissionProvider``, binds ``film`` (declared here), satisfies the
runtime-checkable protocol, and returns the provider.
"""

from __future__ import annotations

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

from the_living_daylights import (
    ballistics,
    countersniper,
    defection_protocol,
    settings,
    terrain_ops,
    visibility,
)
from the_living_daylights.compute_mission import input_hash, mission_solution

__all__ = ["GADGETS", "MissionProvider", "register_gadgets"]

#: Module-level gadget registry for the film (see :func:`register_gadgets`).
GADGETS = GadgetRegistry()

_PACKAGE_VERSION = settings.PACKAGE_VERSION
_SEED = 7  # deterministic execution seed (matches the terrain seed)


def register_gadgets(registry: GadgetRegistry) -> None:
    """Register the SNIPER'S NEST gadgets (the mission's field kit)."""
    registry.register(
        settings.FILM,
        {
            "rifle_profile": {
                "v0_mps": settings.MUZZLE_VELOCITY_MPS,
                "caliber_m": settings.PROJECTILE.caliber_m,
                "ballistic_coefficient_kg_m2": settings.PROJECTILE.ballistic_coefficient,
            },
            "scope_spec": settings.SCOPE,
            "glint_detector": countersniper.glint_detection_probability,
            "acoustic_ranger": countersniper.crack_bang_range,
            "localizer": countersniper.triangulate_position,
            "viewshed": visibility.viewshed,
            "cello_case_rig": ballistics.disassemble_takedown_rifle,
            "defection_protocol": defection_protocol.koskov_scenario,
            "verification_checks": defection_protocol.koskov_verification,
            "terrain_generator": terrain_ops.generate_terrain,
        },
    )


class MissionProvider:  # noqa: N801 — class name is fixed by the discovery contract
    """Deterministic MissionProvider for The Living Daylights — SNIPER'S NEST."""

    film = settings.FILM

    def brief(self) -> MissionBrief:
        """Declare the SNIPER'S NEST mission: ballistics, defection, terrain."""
        return MissionBrief(
            film=self.film,
            codename=settings.CODENAME,
            objectives=(
                "sniper cover for a high-value defection (Bratislava)",
                "rules-of-engagement discipline (no shooting the innocent)",
                "cello-case concealment of a takedown sniper rifle",
                "mountain/desert exfiltration with covered routes",
            ),
            assets=(
                Asset(
                    kind="ballistics",
                    name="rifle_profile",
                    payload=settings.PROJECTILE.ballistic_coefficient,
                ),
                Asset(
                    kind="optics",
                    name="scope_spec",
                    payload={
                        "magnification": settings.SCOPE.magnification,
                        "click_size_mrad": settings.SCOPE.click_size,
                    },
                ),
                Asset(
                    kind="concealment",
                    name="cello_case",
                    payload=dict(settings.CELLO_CASE.__dict__),
                ),
                Asset(
                    kind="terrain",
                    name="seeded_grid",
                    payload={"seed": settings.TERRAIN_SEED, "n": settings.TERRAIN_N},
                ),
            ),
            constraints=(
                Constraint(
                    kind="determinism",
                    detail="zero wall-clock, fixed seed 7, no untracked randomness",
                ),
                Constraint(
                    kind="rules_of_engagement",
                    detail="lethal fire only on a confirmed hostile target",
                ),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the available assets, and the ROE constraint."""
        proj = settings.PROJECTILE
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="environment",
                    detail="mountain/desert corridor; deterministic seeded terrain",
                ),
                Finding(
                    label="ballistics",
                    detail=f"7.62mm service round, BC {proj.ballistic_coefficient:.1f} kg/m^2",
                ),
                Finding(
                    label="optics",
                    detail="10x mil-dot riflescope, 0.1 mrad clicks, 50 mm objective",
                ),
                Finding(
                    label="countersniper",
                    detail="optic-glint radiometry, crack-bang ranging, bearing triangulation",
                ),
                Finding(label="concealment", detail="takedown rifle packs into a cello case"),
                Finding(
                    label="constraint",
                    detail="deterministic execution and disciplined rules of engagement",
                ),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the deterministic eight-step mission flow."""
        return MissionPlan(
            steps=(
                Step(
                    name="zero",
                    action="solve_rifle_zero",
                    params={"zero_range_m": settings.ZERO_RANGE_M},
                ),
                Step(
                    name="windage", action="solve_wind_hold", params={"wind_mps": settings.WIND_MPS}
                ),
                Step(
                    name="optics",
                    action="range_and_click_schedule",
                    params={"mils": settings.MIL_READING_MILS},
                ),
                Step(
                    name="countersniper",
                    action="detect_and_localize",
                    params={"glint_range_m": settings.GLINT_RANGE_M},
                ),
                Step(
                    name="defection",
                    action="assess_defection_risk",
                    params={"stages": len(brief.objectives)},
                ),
                Step(
                    name="verification",
                    action="backstop_evidence_check",
                    params={"checks": "koskov"},
                ),
                Step(
                    name="route", action="plan_exfil_route", params={"seed": settings.TERRAIN_SEED}
                ),
                Step(name="conceal", action="pack_cello_case", params={"parts": settings.FILM}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the plan's domain computations and return a fully-provenanced outcome."""
        results = mission_solution()
        results["steps_completed"] = len(plan.steps)
        results["step_names"] = tuple(step.name for step in plan.steps)
        return MissionOutcome(
            success=True,
            results=results,
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=_SEED,
                input_hash=input_hash(),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record the standing lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "the innocent are never a target: hold fire on the cellist",
                "a trigger-guard shot disables a hostile without a lethal error",
                "optic glints, crack-bang delays, and crossed bearings localize a hostile sniper",
                "the overwatch nest is the top-scored position that can SEE the site",
                "deterministic provenance makes every field report auditable",
                "a cover term bends the exfil route toward concealment but does not by "
                "itself beat average ground — check the route against a baseline",
            ),
        )


# Bind the film's gadgets into the module-level registry on import, so
# discovery and coordinators that inspect GADGETS see the field kit immediately.
def _bind_gadgets() -> None:
    register_gadgets(GADGETS)


_bind_gadgets()
