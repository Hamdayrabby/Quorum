"""Strategist agent: strongest opening case FOR the proposition."""

from __future__ import annotations

from agents.base import BaseAgent
from core.models import AgentResult
from prompts.agent_prompts import strategist_prompt


class StrategistAgent(BaseAgent):
    """Opens the debate with the strongest case FOR the proposition."""

    async def argue(
        self,
        topic: str,
        mode: str,
        pro_argument: str = "",
        con_argument: str = "",
    ) -> AgentResult:
        """Run the opening stage; openings take no prior arguments."""
        del pro_argument, con_argument  # uniform role interface, unused here
        system, user = strategist_prompt(topic, mode)
        return await self.run(system, user)
