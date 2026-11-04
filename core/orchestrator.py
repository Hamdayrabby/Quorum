"""Debate pipeline: four staged rounds over the five agents with live updates.

Stages run sequentially while agents inside a stage run concurrently (that
parallelism is the model-diversity demonstration). ``run_debate`` never
raises: agent classes already contain their own failures, the gather calls
add a safety net against unexpected crashes, and the judge stage is guarded,
so the UI always receives a renderable ``DebateState``.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress

from agents.base import BaseAgent
from agents.challenger import ChallengerAgent
from agents.devils_advocate import DevilsAdvocateAgent
from agents.researcher import ResearcherAgent
from agents.strategist import StrategistAgent
from agents.supreme_judge import SupremeJudgeAgent
from core.api_client import LLMClient
from core.config import AGENT_CONFIGS
from core.models import AgentResult, AgentRole, AgentStatus, DebateState, Verdict

ClientFactory = Callable[[AgentRole], LLMClient]

_ROLE_AGENT_CLASSES: dict[AgentRole, type[BaseAgent]] = {
    AgentRole.STRATEGIST: StrategistAgent,
    AgentRole.CHALLENGER: ChallengerAgent,
    AgentRole.RESEARCHER: ResearcherAgent,
    AgentRole.DEVILS_ADVOCATE: DevilsAdvocateAgent,
    AgentRole.SUPREME_JUDGE: SupremeJudgeAgent,
}

_ANALYSIS_SEPARATOR = "\n\n---\n\n"


def _default_client_factory(role: AgentRole) -> LLMClient:
    return LLMClient(AGENT_CONFIGS[role])


class DebateOrchestrator:
    """Runs the debate and reports state after every status change."""

    def __init__(self, client_factory: ClientFactory | None = None) -> None:
        self._client_factory = client_factory or _default_client_factory

    async def run_debate(
        self,
        topic: str,
        mode: str,
        on_update: Callable[[DebateState], None] | None = None,
    ) -> DebateState:
        """Execute the full pipeline; always returns a final ``DebateState``."""
        agents = {
            role: agent_cls(AGENT_CONFIGS[role], self._client_factory(role))
            for role, agent_cls in _ROLE_AGENT_CLASSES.items()
        }
        state = DebateState(topic=topic, mode=mode)
        for role, cfg in AGENT_CONFIGS.items():
            state.results[role] = AgentResult(
                role=role, display_name=cfg.display_name, model_name=cfg.model
            )
        self._emit(state, on_update)

        # Stage 2: openings, concurrently; one failing must not abort the other.
        self._mark_thinking(state, AgentRole.STRATEGIST, on_update)
        self._mark_thinking(state, AgentRole.CHALLENGER, on_update)
        pro_outcome, con_outcome = await asyncio.gather(
            agents[AgentRole.STRATEGIST].argue(topic, mode),
            agents[AgentRole.CHALLENGER].argue(topic, mode),
            return_exceptions=True,
        )
        pro_result = self._as_result(AgentRole.STRATEGIST, pro_outcome)
        con_result = self._as_result(AgentRole.CHALLENGER, con_outcome)
        state.results[AgentRole.STRATEGIST] = pro_result
        self._emit(state, on_update)
        state.results[AgentRole.CHALLENGER] = con_result
        self._emit(state, on_update)

        pro_text = pro_result.content if pro_result.ok else ""
        con_text = con_result.content if con_result.ok else ""
        if not pro_result.ok and not con_result.ok:
            state.judge_error = (
                "Both opening agents failed, so the analysis and verdict stages "
                "were skipped. Check the agents' error messages and retry."
            )
            self._emit(state, on_update)
            return state

        # Stage 3: analysis of whatever openings succeeded, concurrently.
        self._mark_thinking(state, AgentRole.RESEARCHER, on_update)
        self._mark_thinking(state, AgentRole.DEVILS_ADVOCATE, on_update)
        audit_outcome, attack_outcome = await asyncio.gather(
            agents[AgentRole.RESEARCHER].argue(topic, mode, pro_text, con_text),
            agents[AgentRole.DEVILS_ADVOCATE].argue(topic, mode, pro_text, con_text),
            return_exceptions=True,
        )
        audit_result = self._as_result(AgentRole.RESEARCHER, audit_outcome)
        attack_result = self._as_result(AgentRole.DEVILS_ADVOCATE, attack_outcome)
        state.results[AgentRole.RESEARCHER] = audit_result
        self._emit(state, on_update)
        state.results[AgentRole.DEVILS_ADVOCATE] = attack_result
        self._emit(state, on_update)

        # Stage 4: verdict over the openings plus whatever analysis succeeded.
        self._mark_thinking(state, AgentRole.SUPREME_JUDGE, on_update)
        analysis = _ANALYSIS_SEPARATOR.join(
            section_result.content
            for section_result in (audit_result, attack_result)
            if section_result.ok and section_result.content.strip()
        )
        verdict: Verdict | None = None
        try:
            verdict, judge_result = await agents[AgentRole.SUPREME_JUDGE].judge(
                topic, mode, pro_text, con_text, analysis
            )
        except Exception as exc:  # judge stage must never kill the pipeline
            judge_cfg = AGENT_CONFIGS[AgentRole.SUPREME_JUDGE]
            judge_result = AgentResult(
                role=AgentRole.SUPREME_JUDGE,
                display_name=judge_cfg.display_name,
                model_name=judge_cfg.model,
                status=AgentStatus.FAILED,
                error=f"unexpected failure: {exc}",
            )
        state.results[AgentRole.SUPREME_JUDGE] = judge_result
        self._emit(state, on_update)
        if verdict is not None:
            state.verdict = verdict
        else:
            state.judge_error = (
                "The Supreme Judge could not deliver a verdict: "
                f"{judge_result.error or 'unknown failure'}"
            )
        self._emit(state, on_update)
        return state

    @staticmethod
    def _emit(state: DebateState, on_update: Callable[[DebateState], None] | None) -> None:
        """Push the current state to the UI; a callback glitch is swallowed."""
        if on_update is None:
            return
        with suppress(Exception):
            on_update(state)

    @staticmethod
    def _mark_thinking(
        state: DebateState, role: AgentRole, on_update: Callable[[DebateState], None] | None
    ) -> None:
        state.results[role].status = AgentStatus.THINKING
        DebateOrchestrator._emit(state, on_update)

    @staticmethod
    def _as_result(role: AgentRole, outcome: AgentResult | BaseException) -> AgentResult:
        """Pass agent results through; convert unexpected crashes to FAILED."""
        if isinstance(outcome, AgentResult):
            return outcome
        cfg = AGENT_CONFIGS[role]
        return AgentResult(
            role=role,
            display_name=cfg.display_name,
            model_name=cfg.model,
            status=AgentStatus.FAILED,
            error=f"unexpected failure: {outcome}",
        )
