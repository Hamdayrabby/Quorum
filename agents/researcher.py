"""Researcher agent: a genuine tool-using agent.

Flow (one ``argue`` call, all failures contained):
1. Ask its model for two web-search queries (tolerant: any failure falls
   back to the raw topic as a single query).
2. Run both Tavily searches concurrently; each failure is swallowed so a
   dead search API degrades to a reasoning-only audit instead of failing.
3. Feed the numbered evidence into the audit prompt, cite it inline, and
   attach the deduplicated ``(title, url)`` list to the result for the UI.

The search function is injected so tests can fake the web; the default
reads the Tavily key from settings/.env and returns no results when the
key is missing (reasoning-only mode, never a crash).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from agents.base import BaseAgent
from core.api_client import tavily_search
from core.models import AgentResult
from core.settings import get_tavily_key
from prompts.agent_prompts import researcher_prompt, researcher_query_prompt

SearchFn = Callable[[str], Awaitable[list[dict]]]

_MAX_SOURCES = 5
_SNIPPET_CHARS = 320


async def _default_search(query: str) -> list[dict]:
    """Real Tavily search; no key configured means zero results, not a crash."""
    key = get_tavily_key()
    if not key:
        return []
    return await tavily_search(key, query, max_results=3)


def _parse_queries(reply: str, topic: str) -> list[str]:
    """Extract up to two queries from the model reply; tolerant by design."""
    lines = [line.strip(" \t-*0123456789.\"" ) for line in reply.splitlines()]
    queries = [line for line in lines if 8 <= len(line) <= 120]
    return queries[:2] if queries else [topic.strip()[:120] or "debate evidence"]


class ResearcherAgent(BaseAgent):
    """Audits both openings for unsupported claims and weak logic; owns no side."""

    def __init__(
        self,
        cfg,
        client,
        search: SearchFn | None = None,
    ) -> None:
        super().__init__(cfg, client)
        self._search = search or _default_search

    async def argue(
        self,
        topic: str,
        mode: str,
        pro_argument: str = "",
        con_argument: str = "",
    ) -> AgentResult:
        """Search the web for evidence, then audit the two openings against it."""
        query_system, query_user = researcher_query_prompt(topic, mode)
        query_result = await self.run(query_system, query_user)
        queries = (
            _parse_queries(query_result.content, topic)
            if query_result.ok
            else [topic.strip()[:120] or "debate evidence"]
        )

        search_outcomes = await asyncio.gather(
            *(self._search(query) for query in queries),
            return_exceptions=True,
        )
        sources: list[tuple[str, str]] = []
        evidence_blocks: list[str] = []
        for outcome in search_outcomes:
            if isinstance(outcome, BaseException) or not isinstance(outcome, list):
                continue  # a failed search must not fail the audit
            for item in outcome:
                if len(sources) >= _MAX_SOURCES:
                    break
                title, url = str(item.get("title", "")).strip(), str(item.get("url", "")).strip()
                if not url:
                    continue
                sources.append((title or url, url))
                evidence_blocks.append(
                    f"[{len(sources)}] {title or url}\n{url}\n"
                    f"{str(item.get('content', '')).strip()[:_SNIPPET_CHARS]}"
                )

        evidence = "\n\n".join(evidence_blocks)
        if not evidence:
            evidence = (
                "(Web search returned no usable evidence - audit from reasoning "
                "alone and note which claims could not be checked.)"
            )
        system, user = researcher_prompt(topic, mode, pro_argument, con_argument, evidence)
        result = await self.run(system, user)
        # Attach sources even on failure: the searches really ran, and the UI
        # can decide what to show with them.
        result.sources = sources
        return result
