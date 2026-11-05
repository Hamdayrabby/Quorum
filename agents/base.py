"""Reusable debate-agent runner and verdict parsing shared by all five roles.

``BaseAgent`` is the single place an agent's LLM call happens: it builds the
``AgentResult``, times the call, and converts every expected failure into a
FAILED result instead of an exception, so the orchestrator can treat agent
invocations as total functions. The verdict parser also lives here because
only the Supreme Judge consumes it, while the UI relies on its never-raise
contract.
"""
from __future__ import annotations

import json
import time

from core.api_client import LLMClient
from core.config import AgentConfig
from core.exceptions import AgentWarsError, ResponseFormatError
from core.models import AgentResult, AgentStatus, Verdict


class BaseAgent:
    """Runs one debate role: builds its prompt, calls its model, records timing/status."""

    def __init__(self, cfg: AgentConfig, client: LLMClient) -> None:
        self._cfg = cfg
        self._client = client

    async def run(self, system: str, user: str) -> AgentResult:
        """Execute one completion; never raises, always returns a terminal result."""
        return await self.run_sequence((system, user))

    async def run_sequence(self, *steps: tuple[str, str]) -> AgentResult:
        """Execute 1..N completions under one timing/error envelope.

        Each step is a ``(system, user)`` pair run in order; the LAST step's
        reply becomes ``result.content``. Tool-using agents (the Researcher's
        search loop) use this so multi-call work still gets the never-raise
        contract: any ``AgentWarsError`` becomes a FAILED result, an empty
        final reply counts as a failure too.
        """
        result = AgentResult(
            role=self._cfg.role,
            display_name=self._cfg.display_name,
            model_name=self._cfg.model,
        )
        start = time.perf_counter()
        try:
            content = ""
            for system, user in steps:
                content = await self._client.complete(system, user)
            if not content.strip():
                raise ResponseFormatError(f"{self._cfg.provider} returned empty content")
            result.status = AgentStatus.COMPLETED
            result.content = content
            used = getattr(self._client, "used_model", None)
            if used:
                result.model_name = used
        except AgentWarsError as exc:
            result.status = AgentStatus.FAILED
            result.error = str(exc)
            result.content = ""
        finally:
            result.latency_s = time.perf_counter() - start
        return result


def extract_json_object(text: str) -> dict | None:
    """Return the first ``{...}`` block in ``text`` parsed as a JSON dict.

    Tolerates markdown fences and prose around the JSON, and braces inside
    JSON strings. Unparseable candidates are skipped so prose braces do not
    hide a valid object further along the reply; None when nothing parses.
    """
    search_from = 0
    while True:
        start = text.find("{", search_from)
        if start == -1:
            return None
        block = _balanced_block(text, start)
        if block is not None:
            try:
                parsed = json.loads(block)
            except ValueError:
                parsed = None
            if isinstance(parsed, dict):
                return parsed
        search_from = start + 1


def _balanced_block(text: str, start: int) -> str | None:
    """Return the balanced brace block opening at ``start``, or None.

    Tracks JSON strings and escape sequences so braces quoted inside values
    cannot unbalance the count.
    """
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def parse_verdict(raw_text: str) -> Verdict:
    """Map a judge reply onto ``Verdict``; never raises.

    Missing keys fall back to dataclass defaults with sensible coercion
    (winner uppercased, ints via ``int()``, lists stay lists). When no JSON
    object can be extracted, the verdict carries ``parse_ok=False`` and the
    full raw text so the UI can still show the judgment.
    """
    data = extract_json_object(raw_text)
    if data is None:
        return Verdict(winner="", raw_text=raw_text, parse_ok=False)
    return Verdict(
        winner=_coerce_winner(data.get("winner")),
        pro_score=_coerce_int(data.get("pro_score")),
        con_score=_coerce_int(data.get("con_score")),
        explanation=_coerce_str(data.get("explanation")),
        strongest_argument=_coerce_str(data.get("strongest_argument")),
        weakest_argument=_coerce_str(data.get("weakest_argument")),
        key_disagreements=_coerce_str_list(data.get("key_disagreements")),
        conclusion=_coerce_str(data.get("conclusion")),
        best_answer=_coerce_str(data.get("best_answer")),
        fallacies=_coerce_str_list(data.get("fallacies")),
        raw_text=raw_text,
        parse_ok=True,
    )


def _coerce_winner(value: object) -> str:
    return _coerce_str(value).strip().upper()


def _coerce_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _coerce_str(value: object) -> str:
    if isinstance(value, str):
        return value
    return "" if value is None else str(value)


def _coerce_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value]
    return []
