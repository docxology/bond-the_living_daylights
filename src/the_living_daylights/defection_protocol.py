"""SNIPER'S NEST — staged, risk-scored defection handling.

Pure, infrastructure-free, deterministic protocol for handling a high-value
asset's defection, modeled on The Living Daylights' opening act: General
Koskov defects from Bratislava with a cellist's cover and sniper overwatch.

The protocol is *staged* — a fixed ordered sequence of handling stages — and
*risk-scored* — each stage carries weighted risk factors whose scores combine
into a per-stage hazard that gates the stage's approval. An overall plan score
is the conservative maximum across stages; approval is monotonic (a stage
cannot be approved until every prior stage is approved or conditioned).

Deterministic: no RNG, no wall-clock — all values derive from the supplied
factors and thresholds.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = [
    "CONSTANT_TOLERANCE",
    "DEFAULT_STAGES",
    "DefectionAssessment",
    "RiskFactor",
    "StageRiskInput",
    "StageAssessment",
    "assess_defection",
    "koskov_scenario",
    "stage_score",
]

#: Stages of the defection-handling protocol, in execution order.
DEFAULT_STAGES = ("contact", "snatch", "verify", "exfiltrate", "relocate")

#: Equality tolerance for clamped/rounded scores.
CONSTANT_TOLERANCE = 1e-9


@dataclass(frozen=True)
class RiskFactor:
    """A single weighed, scored risk driver for a defection stage."""

    label: str
    weight: float  # relative importance within a stage
    score: float  # observed hazard, 0 (benign) .. 1 (critical)

    def __post_init__(self) -> None:
        if self.label is None or not str(self.label).strip():
            raise ValueError("RiskFactor.label must be a non-empty string")
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError("RiskFactor.weight must be in [0, 1]")
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("RiskFactor.score must be in [0, 1]")


@dataclass(frozen=True)
class StageRiskInput:
    """A stage's risk profile: a stage name and its weighted factors."""

    stage: str
    factors: tuple[RiskFactor, ...]

    def __post_init__(self) -> None:
        if self.stage is None or not str(self.stage).strip():
            raise ValueError("StageRiskInput.stage must be a non-empty string")
        if not isinstance(self.factors, tuple):
            raise ValueError("StageRiskInput.factors must be a tuple of RiskFactor")
        total = sum(f.weight for f in self.factors)
        if total <= 0:
            raise ValueError("StageRiskInput factors must carry positive total weight")


@dataclass(frozen=True)
class StageAssessment:
    """A stage's computed hazard score and verdict."""

    stage: str
    factors: tuple[RiskFactor, ...]
    score: float
    verdict: str  # "go" | "conditional" | "no-go"

    def __post_init__(self) -> None:
        if self.score < 0.0 or self.score > 1.0:
            raise ValueError("StageAssessment.score must be in [0, 1]")
        if self.verdict not in ("go", "conditional", "no-go"):
            raise ValueError("StageAssessment.verdict must be one of go/conditional/no-go")


@dataclass(frozen=True)
class DefectionAssessment:
    """The full plan: per-stage assessments, plan verdict, and approval path."""

    stages: tuple[StageAssessment, ...]
    plan_score: float
    plan_verdict: str
    approval: tuple[tuple[str, str], ...]  # (stage, status: approved|conditional|blocked)
    gate_stage: str | None  # first stage that conditions/blocks the plan

    def __post_init__(self) -> None:
        if not isinstance(self.stages, tuple):
            raise ValueError("DefectionAssessment.stages must be a tuple")
        if not (0.0 <= self.plan_score <= 1.0):
            raise ValueError("DefectionAssessment.plan_score must be in [0, 1]")
        if self.plan_verdict not in ("go", "conditional", "no-go"):
            raise ValueError("DefectionAssessment.plan_verdict must be one of go/conditional/no-go")


def stage_score(factors: Sequence[RiskFactor]) -> float:
    """Weighted-mean hazard for a stage's factors, clamped to ``[0, 1]``.

    ``score = clamp(sum(w_i * s_i) / sum(w_i))`` — the exposure-weighted mean of
    the factor hazards, so a dominant high-score factor cannot be hidden by
    benign ones. Deterministic given the factors.
    """
    total_weight = sum(f.weight for f in factors)
    if total_weight <= 0:
        raise ValueError("stage_score requires positive total factor weight")
    weighted = sum(f.weight * f.score for f in factors)
    return max(0.0, min(1.0, weighted / total_weight))


def _verdict(score: float, go: float, conditional: float) -> str:
    if score <= go + CONSTANT_TOLERANCE:
        return "go"
    if score <= conditional + CONSTANT_TOLERANCE:
        return "conditional"
    return "no-go"


def assess_defection(
    inputs: Sequence[StageRiskInput],
    *,
    go_threshold: float = 0.40,
    conditional_threshold: float = 0.70,
) -> DefectionAssessment:
    """Assess a staged defection plan and produce its approval path.

    Each stage's weighted risk is compared against ``go_threshold`` and
    ``conditional_threshold``; an overall plan score is the conservative
    maximum stage score. Approval is monotonic: the first stage whose verdict
    is not ``go`` marks the plan gate and blocks all later stages unless they
    were already approved.

    Raises:
        ValueError: if a stage repeats, thresholds are inverted, or a stage
            name appears in an unexpected position of :data:`DEFAULT_STAGES`.
    """
    if go_threshold < 0.0 or conditional_threshold < go_threshold or conditional_threshold > 1.0:
        raise ValueError("thresholds must satisfy 0 <= go_threshold <= conditional_threshold <= 1")

    names = [inp.stage for inp in inputs]
    if len(set(names)) != len(names):
        raise ValueError("defection stages must be unique")
    for expected in DEFAULT_STAGES:
        if expected not in names:
            raise ValueError(f"defection plan is missing stage {expected!r}")

    assessments: list[StageAssessment] = []
    plan_score = 0.0
    for inp in inputs:
        score = stage_score(inp.factors)
        verdict = _verdict(score, go_threshold, conditional_threshold)
        plan_score = max(plan_score, score)
        assessments.append(
            StageAssessment(stage=inp.stage, factors=inp.factors, score=score, verdict=verdict)
        )

    plan_verdict = _verdict(plan_score, go_threshold, conditional_threshold)

    # ordered approval path: stages that are already go are approved; the first
    # non-go stage becomes the gate and blocks itself and everything after.
    approval: list[tuple[str, str]] = []
    gate_stage: str | None = None
    blocked = False
    for sa in assessments:
        if blocked:
            approval.append((sa.stage, "blocked"))
            continue
        if sa.verdict == "go":
            approval.append((sa.stage, "approved"))
        else:
            approval.append((sa.stage, "conditional" if sa.verdict == "conditional" else "blocked"))
            if gate_stage is None:
                gate_stage = sa.stage
            if sa.verdict == "no-go":
                blocked = True

    return DefectionAssessment(
        stages=tuple(assessments),
        plan_score=plan_score,
        plan_verdict=plan_verdict,
        approval=tuple(approval),
        gate_stage=gate_stage,
    )


def koskov_scenario() -> tuple[StageRiskInput, ...]:
    """The canonical KOSKOV defection scenario (deterministic defaults).

    Encodes The Living Daylights' opening: Koskov's snatch from Bratislava
    with a cellist cover, verification doubt (his volte-face), a border
    crossing, and desert/mountain exfiltration. Values are fixed so the
    mission's report is reproducible.
    """
    return (
        StageRiskInput(
            stage="contact",
            factors=(
                RiskFactor("host surveillance", 0.30, 0.30),
                RiskFactor("asset composure", 0.30, 0.35),
                RiskFactor("channel security", 0.40, 0.25),
            ),
        ),
        StageRiskInput(
            stage="snatch",
            factors=(
                RiskFactor("border pressure", 0.30, 0.50),
                RiskFactor("sniper overwatch coverage", 0.30, 0.30),
                RiskFactor("extraction speed", 0.20, 0.35),
                RiskFactor("team signalling", 0.20, 0.40),
            ),
        ),
        StageRiskInput(
            stage="verify",
            factors=(
                RiskFactor("identity doubt", 0.30, 0.60),
                RiskFactor("debriefer skill", 0.30, 0.30),
                RiskFactor("backstop checks", 0.40, 0.50),
            ),
        ),
        StageRiskInput(
            stage="exfiltrate",
            factors=(
                RiskFactor("border crossing", 0.35, 0.70),
                RiskFactor("desert/terrain hazards", 0.30, 0.50),
                RiskFactor("hostile patrols", 0.35, 0.60),
            ),
        ),
        StageRiskInput(
            stage="relocate",
            factors=(
                RiskFactor("false identity", 0.30, 0.60),
                RiskFactor("safehouse readiness", 0.30, 0.50),
                RiskFactor("follow-on pursuit", 0.40, 0.65),
            ),
        ),
    )
