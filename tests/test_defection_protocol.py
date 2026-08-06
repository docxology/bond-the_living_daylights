"""Real-data tests for :mod:`the_living_daylights.defection_protocol`."""

from __future__ import annotations

import math

import pytest

from the_living_daylights import defection_protocol as d


def test_riskfactor_validation() -> None:
    with pytest.raises(ValueError):
        d.RiskFactor("", 0.5, 0.5)
    with pytest.raises(ValueError):
        d.RiskFactor("x", -0.1, 0.5)
    with pytest.raises(ValueError):
        d.RiskFactor("x", 1.5, 0.5)
    with pytest.raises(ValueError):
        d.RiskFactor("x", 0.5, -0.1)
    with pytest.raises(ValueError):
        d.RiskFactor("x", 0.5, 1.5)


def test_stage_input_validation() -> None:
    factor = d.RiskFactor("r", 1.0, 0.5)
    with pytest.raises(ValueError):
        d.StageRiskInput("", (factor,))
    with pytest.raises(ValueError):
        d.StageRiskInput("s", [factor])
    with pytest.raises(ValueError):
        d.StageRiskInput("s", (d.RiskFactor("r", 0.0, 0.5),))


def test_stage_score_weighted_mean() -> None:
    assert math.isclose(d.stage_score((d.RiskFactor("a", 1.0, 0.5),)), 0.5)
    with pytest.raises(ValueError):
        d.stage_score((d.RiskFactor("a", 0.0, 0.5),))


def test_assess_all_go() -> None:
    inputs = tuple(d.StageRiskInput(s, (d.RiskFactor("r", 1.0, 0.1),)) for s in d.DEFAULT_STAGES)
    assessment = d.assess_defection(inputs)
    assert assessment.plan_verdict == "go"
    assert assessment.gate_stage is None
    assert all(status == "approved" for _, status in assessment.approval)


def test_assess_validation_errors() -> None:
    scenario = d.koskov_scenario()
    with pytest.raises(ValueError):
        d.assess_defection(list(scenario) * 2)  # duplicate stage
    missing = tuple(s for s in scenario if s.stage != "verify")
    with pytest.raises(ValueError):
        d.assess_defection(missing)
    with pytest.raises(ValueError):
        d.assess_defection(scenario, go_threshold=0.7, conditional_threshold=0.3)
    with pytest.raises(ValueError):
        d.assess_defection(scenario, go_threshold=-0.1)


def test_koskov_scenario_conditional_with_gate() -> None:
    assessment = d.assess_defection(d.koskov_scenario())
    assert assessment.plan_verdict == "conditional"
    assert assessment.gate_stage == "verify"
    assert len(assessment.stages) == len(d.DEFAULT_STAGES)
    scores = {s.stage: s.score for s in assessment.stages}
    assert scores["contact"] < scores["verify"] < scores["exfiltrate"]
    assert math.isclose(assessment.plan_score, max(scores.values()))
    # early stages approved, the risky ones conditioned
    statuses = dict(assessment.approval)
    assert statuses["contact"] == "approved"
    assert statuses["verify"] == "conditional"


def test_assess_no_go_blocks_follow_on() -> None:
    inputs = tuple(d.StageRiskInput(s, (d.RiskFactor("r", 1.0, 0.9),)) for s in d.DEFAULT_STAGES)
    assessment = d.assess_defection(inputs)
    assert assessment.plan_verdict == "no-go"
    assert assessment.gate_stage == "contact"
    assert assessment.approval[0][1] == "blocked"
    assert all(status == "blocked" for _, status in assessment.approval[1:])


def test_assessment_dataclass_validation() -> None:
    with pytest.raises(ValueError):
        d.StageAssessment("s", (), -0.1, "go")
    with pytest.raises(ValueError):
        d.StageAssessment("s", (), 1.5, "go")
    with pytest.raises(ValueError):
        d.StageAssessment("s", (), 0.5, "bogus")
    with pytest.raises(ValueError):
        d.DefectionAssessment([], 0.5, "go", (), None)
    with pytest.raises(ValueError):
        d.DefectionAssessment((), -0.1, "go", (), None)
    with pytest.raises(ValueError):
        d.DefectionAssessment((), 0.5, "bogus", (), None)


# --- evidence verification ---


def test_evidence_check_validation() -> None:
    with pytest.raises(ValueError):
        d.EvidenceCheck("", 0.5, 0.5)
    with pytest.raises(ValueError):
        d.EvidenceCheck("x", -0.1, 0.5)
    with pytest.raises(ValueError):
        d.EvidenceCheck("x", 1.5, 0.5)
    with pytest.raises(ValueError):
        d.EvidenceCheck("x", 0.5, -0.1)
    with pytest.raises(ValueError):
        d.EvidenceCheck("x", 0.5, 1.5)


def test_verification_certainty_weighted_mean() -> None:
    checks = (d.EvidenceCheck("a", 1.0, 0.5),)
    assert math.isclose(d.verification_certainty(checks), 0.5)
    checks_two = (d.EvidenceCheck("a", 0.5, 1.0), d.EvidenceCheck("b", 0.5, 0.0))
    assert math.isclose(d.verification_certainty(checks_two), 0.5)
    with pytest.raises(ValueError):
        d.verification_certainty((d.EvidenceCheck("a", 0.0, 0.5),))


def test_backstop_verdict_thresholds() -> None:
    assert d.backstop_verdict(0.9) == "cleared"
    assert d.backstop_verdict(0.7) == "conditional"
    assert d.backstop_verdict(0.3) == "rejected"
    assert d.backstop_verdict(0.85) == "cleared"  # hard threshold inclusive
    with pytest.raises(ValueError):
        d.backstop_verdict(1.5)
    with pytest.raises(ValueError):
        d.backstop_verdict(0.5, soft_threshold=0.7, hard_threshold=0.6)


def test_koskov_verification_certainty_and_verdict() -> None:
    checks = d.koskov_verification()
    assert len(checks) == 4
    certainty = d.verification_certainty(checks)
    assert math.isclose(certainty, 0.67, abs_tol=1e-9)
    assert d.backstop_verdict(certainty) == "conditional"


def test_plan_gate_and_backstop_can_disagree() -> None:
    """Negative control (V2): the two authored tables are not coupled.

    Perturbing ONLY the staged scenario — pushing the ``verify`` stage over the
    no-go threshold — must move the plan verdict while the backstop evidence
    (left untouched) stays. If one model were a projection of the other they
    could not diverge this way, so the shipped agreement is a real fact that
    could have come out otherwise.
    """
    scenario = [
        s
        if s.stage != "verify"
        else d.StageRiskInput("verify", (d.RiskFactor("identity breakdown", 1.0, 0.9),))
        for s in d.koskov_scenario()
    ]
    plan = d.assess_defection(tuple(scenario))
    backstop = d.backstop_verdict(d.verification_certainty(d.koskov_verification()))
    assert plan.plan_verdict == "no-go"  # only the staged table moved
    assert backstop == "conditional"  # evidence table untouched
    assert plan.plan_verdict != backstop  # they genuinely can disagree
    # and on the shipped tables they agree by construction of both, not coupling
    shipped = d.assess_defection(d.koskov_scenario())
    assert shipped.plan_verdict == backstop == "conditional"
