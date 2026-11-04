"""Researcher agent: evidence audit of both openings."""

from __future__ import annotations

from agents.base import BaseAgent
from core.models import AgentResult
from prompts.agent_prompts import researcher_prompt


class ResearcherAgent(BaseAgent):
    """Audits both openings for unsupported claims and weak logic; owns no side."""

    async def argue(
        self,
        topic: str,
        mode: str,
        pro_argument: str = "",
        con_argument: str = "",
    ) -> AgentResult:
        """Audit the two openings; failed ones arrive as empty strings."""
        system, user = researcher_prompt(topic, mode, pro_argument, con_argument)
        return await self.run(system, user)
