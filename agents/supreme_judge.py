"""Supreme Judge agent: structured verdict over both sides and the analysis."""

from __future__ import annotations

from agents.base import BaseAgent, parse_verdict
from core.models import AgentResult, Verdict
from prompts.agent_prompts import judge_prompt


class SupremeJudgeAgent(BaseAgent):
    """Scores both sides and delivers the final verdict as structured JSON."""

    async def judge(
        self,
        topic: str,
        mode: str,
        pro_argument: str,
        con_argument: str,
        analysis: str,
    ) -> tuple[Verdict | None, AgentResult]:
        """Run the verdict stage; returns ``(verdict_or_none, result)``.

        On a completed call the reply is parsed into ``Verdict`` (with
        ``parse_ok=False`` and the raw text preserved when no JSON object can
        be extracted). A ``None`` verdict means the call itself failed; the
        companion result carries the error.
        """
        system, user = judge_prompt(topic, mode, pro_argument, con_argument, analysis)
        result = await self.run(system, user)
        if not result.ok:
            return None, result
        return parse_verdict(result.content), result
