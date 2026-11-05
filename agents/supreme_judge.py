"""Supreme Judge agent: structured verdict over both sides and the analysis.

Two-phase by design: draft the verdict, then a VERIFICATION PASS re-reads all
four panel answers against the draft and returns the corrected JSON. If the
verification call or its parse fails, the draft verdict still ships (marked
unverified) — the judge never blocks the pipeline on its own second opinion.
"""

from __future__ import annotations

import asyncio

from agents.base import BaseAgent, parse_verdict
from core.models import AgentResult, Verdict
from prompts.agent_prompts import judge_prompt, judge_selfcheck_prompt


_CHECK_TIMEOUT_S = 120.0


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
        draft = await self.run(system, user)
        if not draft.ok:
            return None, draft
        verdict = parse_verdict(draft.content)
        if not verdict.parse_ok:
            return verdict, draft

        # Verification pass: the judge re-reads all four answers with its own
        # draft in hand and corrects any misattribution or score inconsistency.
        check_system, check_user = judge_selfcheck_prompt(
            topic, mode, pro_argument, con_argument, analysis, draft.content
        )
        try:
            # The check is quality assurance, not the deliverable: bound its
            # latency so a slow reasoning model cannot stall the verdict.
            final = await asyncio.wait_for(
                self.run(check_system, check_user), timeout=_CHECK_TIMEOUT_S
            )
        except asyncio.TimeoutError:
            return verdict, draft
        final_verdict = parse_verdict(final.content)
        if final.ok and final_verdict.parse_ok:
            final_verdict.verified = True
            return final_verdict, final
        return verdict, draft
