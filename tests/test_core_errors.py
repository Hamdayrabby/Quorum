"""Error-path verification for the core layer (plain script, no pytest).

Covers: missing API key -> ConfigError; 429-then-200 -> retry succeeds;
repeated 429/5xx -> ApiError after retries are exhausted; 401 -> immediate
ApiError carrying the status code; empty content -> ResponseFormatError.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from core.api_client import LLMClient  # noqa: E402
from core.config import AGENT_CONFIGS  # noqa: E402
from core.exceptions import ApiError, ConfigError, ResponseFormatError  # noqa: E402
from core.models import AgentRole  # noqa: E402


def _ok_response(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def test_missing_key_raises_config_error() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    client = LLMClient(AGENT_CONFIGS[AgentRole.STRATEGIST])
    try:
        asyncio.run(client.complete("system", "user"))
    except ConfigError as exc:
        assert "GEMINI_API_KEY" in str(exc), str(exc)
    else:
        raise AssertionError("expected ConfigError for missing GEMINI_API_KEY")


def test_retry_on_429_then_success() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, json={"error": {"message": "rate limited"}})
        return _ok_response("recovered")

    client = LLMClient(
        AGENT_CONFIGS[AgentRole.STRATEGIST],
        max_retries=2,
        _transport=httpx.MockTransport(handler),
    )
    content = asyncio.run(client.complete("system", "user"))
    assert content == "recovered"
    assert len(calls) == 2


def test_retries_exhausted_raise_api_error() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503, json={"error": {"message": "overloaded"}})

    client = LLMClient(
        AGENT_CONFIGS[AgentRole.STRATEGIST],
        max_retries=2,
        _transport=httpx.MockTransport(handler),
    )
    try:
        asyncio.run(client.complete("system", "user"))
    except ApiError as exc:
        assert exc.status_code == 503, str(exc)
        assert len(calls) == 3, f"expected 3 attempts (1 + 2 retries), got {len(calls)}"
    else:
        raise AssertionError("expected ApiError after retries are exhausted")


def test_401_fails_fast_with_status() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, json={"error": {"message": "invalid api key"}})

    client = LLMClient(
        AGENT_CONFIGS[AgentRole.STRATEGIST],
        max_retries=2,
        _transport=httpx.MockTransport(handler),
    )
    try:
        asyncio.run(client.complete("system", "user"))
    except ApiError as exc:
        assert exc.status_code == 401, str(exc)
        assert "invalid api key" in str(exc), str(exc)
        assert len(calls) == 1, f"401 must not retry, got {len(calls)} calls"
    else:
        raise AssertionError("expected ApiError on 401")


def test_empty_content_raises_response_format_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "  "}}]})

    client = LLMClient(
        AGENT_CONFIGS[AgentRole.STRATEGIST],
        max_retries=0,
        _transport=httpx.MockTransport(handler),
    )
    try:
        asyncio.run(client.complete("system", "user"))
    except ResponseFormatError as exc:
        assert "empty" in str(exc), str(exc)
    else:
        raise AssertionError("expected ResponseFormatError for empty content")


def main() -> None:
    test_missing_key_raises_config_error()
    # Mock-transport tests exercise HTTP behavior, not auth: install a dummy key.
    os.environ["GEMINI_API_KEY"] = "test-key"
    test_retry_on_429_then_success()
    test_retries_exhausted_raise_api_error()
    test_401_fails_fast_with_status()
    test_empty_content_raises_response_format_error()
    print("ERROR-PATH TESTS GREEN")


if __name__ == "__main__":
    main()
