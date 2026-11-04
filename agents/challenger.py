"""Challenger agent: strongest case AGAINST the proposition."""

from __future__ import annotations

from agents.base import BaseAgent
from core.models import AgentResult
from prompts.agent_prompts import challenger_prompt


class ChallengerAgent(BaseAgent):
    """Answers with the strongest case AGAINST the proposition."""

    async def argue(
        self,
        topic: str,
        mode: str,
        pro_argument: str = "",
        con_argument: str = "",
    ) -> AgentResult:
        """Run the opening stage; it launches alongside the Strategist, so
        ``pro_argument`` is normally empty and ``con_argument`` is unused."""
        del con_argument
        system, user = challenger_prompt(topic, mode, pro_argument)
        return await self.run(system, user)
