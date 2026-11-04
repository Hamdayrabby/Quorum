"""Shared data contracts for the Agent Wars pipeline.

Every layer (agents, orchestrator, UI) speaks only in these types, so the
Streamlit view can render any DebateState without knowing provider details.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgentRole(str, Enum):
    """The five pipeline roles, in execution order."""

    STRATEGIST = "strategist"
    CHALLENGER = "challenger"
    RESEARCHER = "researcher"
    DEVILS_ADVOCATE = "devils_advocate"
    SUPREME_JUDGE = "supreme_judge"


class AgentStatus(str, Enum):
    """Lifecycle states rendered as status pills in the UI."""

    WAITING = "waiting"
    THINKING = "thinking"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Outcome of a single agent invocation (success OR failure)."""

    role: AgentRole
    display_name: str
    model_name: str
    status: AgentStatus = AgentStatus.WAITING
    content: str = ""
    error: str | None = None
    latency_s: float = 0.0
    sources: list[tuple[str, str]] = field(default_factory=list)  # (title, url)

    @property
    def ok(self) -> bool:
        return self.status is AgentStatus.COMPLETED


@dataclass
class Verdict:
    """Structured Supreme Judge output.

    Scores are model-generated qualitative assessments (0-100), not objective
    measurements. ``parse_ok=False`` means the judge replied but its output
    could not be parsed as JSON; the UI must then show ``raw_text`` only and
    must never invent field values.
    """

    winner: str  # "PRO" | "CON" | "TIE"
    pro_score: int = 0
    con_score: int = 0
    explanation: str = ""
    strongest_argument: str = ""
    weakest_argument: str = ""
    key_disagreements: list[str] = field(default_factory=list)
    conclusion: str = ""
    fallacies: list[str] = field(default_factory=list)
    raw_text: str = ""
    parse_ok: bool = True


@dataclass
class DebateState:
    """Everything the UI needs to render the arena at any moment."""

    topic: str = ""
    mode: str = ""
    results: dict[AgentRole, AgentResult] = field(default_factory=dict)
    verdict: Verdict | None = None
    judge_error: str | None = None

    def get(self, role: AgentRole) -> AgentResult | None:
        return self.results.get(role)

    def completed_count(self) -> int:
        return sum(1 for r in self.results.values() if r.ok)
