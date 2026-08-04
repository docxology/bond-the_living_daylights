"""Real-data tests for the SNIPER'S NEST mission adapter (frozen BOND-API)."""

from __future__ import annotations

from bond_api.protocol import MissionProvider as Protocol
from bond_api.protocol import ReconRequest, run_mission
from bond_api.registry import GadgetRegistry

from the_living_daylights.mission import GADGETS, MissionProvider, register_gadgets


def test_isinstance_runtime_checkable_protocol() -> None:
    assert isinstance(MissionProvider(), Protocol)


def test_brief_identity_and_content() -> None:
    brief = MissionProvider().brief()
    assert brief.film == "the_living_daylights"
    assert brief.codename == "SNIPER'S NEST"
    assert len(brief.objectives) >= 3
    assert brief.assets and brief.constraints


def test_recon_findings() -> None:
    report = MissionProvider().recon(ReconRequest(goal="recon the extraction site"))
    assert len(report.findings) > 0
    assert any(f.label == "goal" for f in report.findings)


def test_plan_steps() -> None:
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    assert len(plan.steps) >= 4
    assert plan.steps[0].action == "solve_rifle_zero"
    names = [step.name for step in plan.steps]
    assert {"optics", "countersniper", "verification"} <= set(names)


def test_execute_deterministic_and_provenance() -> None:
    provider = MissionProvider()
    o1 = provider.execute(provider.plan(provider.brief()))
    o2 = provider.execute(provider.plan(provider.brief()))
    assert o1.results == o2.results
    assert o1.provenance.input_hash == o2.provenance.input_hash
    assert o1.success is True
    assert o1.provenance.wall_time_s == 0.0


def test_full_mission_flow() -> None:
    debrief = run_mission(MissionProvider(), ReconRequest(goal="cover the defection"))
    assert debrief.outcome.success is True
    assert len(debrief.lessons) > 0
    assert debrief.outcome.results["defection"]["gate_stage"] == "verify"
    assert "optics" in debrief.outcome.results
    assert "countersniper" in debrief.outcome.results
    assert "overwatch" in debrief.outcome.results
    assert "verification" in debrief.outcome.results


def test_gadget_registration_module_and_explicit() -> None:
    assert GADGETS.contains("the_living_daylights", "rifle_profile")
    registry = GadgetRegistry()
    register_gadgets(registry)
    assert registry.lookup("the_living_daylights", "cello_case_rig") is not None
    assert set(registry.gadgets_for("the_living_daylights")) >= {
        "rifle_profile",
        "terrain_generator",
        "scope_spec",
        "glint_detector",
        "viewshed",
        "verification_checks",
    }
