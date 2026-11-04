"""Devil's Advocate agent: attacks both sides, surfaces overlooked perspectives."""

from __future__ import annotations

from agents.base import BaseAgent
from core.models import AgentResult
from prompts.agent_prompts import devils_advocate_prompt


class DevilsAdvocateAgent(BaseAgent):
    """Attacks both openings with equal force and steelmans the overlooked view."""

    async def argue(
        self,
        topic: str,
        mode: str,
        pro_argument: str = "",
        con_argument: str = "",
    ) -> AgentResult:
        """Report on both openings; failed ones arrive as empty strings."""
        system, user = devils_advocate_prompt(topic, mode, pro_argument, con_argument)
        return await self.run(system, user)
