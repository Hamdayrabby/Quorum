"""Async OpenAI-compatible LLM client shared by all five providers.

Every provider configured in ``core.config`` exposes a chat-completions
endpoint that speaks the OpenAI wire format, so one client class serves the
whole pipeline. Retry policy: exponential backoff (1s, 2s + jitter) only on
HTTP 429, 5xx, and transport-level failures; other 4xx fail fast with the
provider's error message.

``fetch_models`` is the sync companion used by the settings UI for the live
connection test (the debate pipeline itself stays async).
"""
from __future__ import annotations

import asyncio
import random

import httpx

from core.config import MAX_RETRIES, TIMEOUT_S, AgentConfig, get_api_key
from core.exceptions import ApiError, ResponseFormatError

_BACKOFF_BASE_S = 1.0
_BACKOFF_JITTER_S = 0.5
_ERROR_SNIPPET_CHARS = 300
_DISCOVERY_PROVIDER = "model discovery"


class LLMClient:
    """Posts chat-completions requests for one agent configuration.

    The client is created per call inside ``async with`` so connections are
    always closed cleanly. ``_transport`` is a test seam (e.g. an
    ``httpx.MockTransport``); when omitted, a real network client is used.
    """

    def __init__(
        self,
        cfg: AgentConfig,
        timeout_s: float = TIMEOUT_S,
        max_retries: int = MAX_RETRIES,
        _transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._cfg = cfg
        self._timeout_s = timeout_s
        self._max_retries = max_retries
        self._transport = _transport

    async def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        """Send one chat completion and return the assistant content string.

        Raises ConfigError when the provider API key is missing, ApiError on
        provider/network failures after retries are exhausted, and
        ResponseFormatError when the reply is missing or empty.
        """
        api_key = get_api_key(self._cfg)
        url = self._cfg.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self._cfg.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self._cfg.temperature if temperature is None else temperature,
            "max_tokens": self._cfg.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout_s), transport=self._transport
        ) as client:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.post(url, headers=headers, json=payload)
                except httpx.TransportError as exc:  # includes TimeoutException
                    if attempt < self._max_retries:
                        await asyncio.sleep(self._backoff(attempt))
                        continue
                    raise ApiError(
                        self._cfg.provider, None, f"transport failure: {exc}"
                    ) from exc
                if response.is_success:
                    return self._extract_content(response)
                if self._retryable(response.status_code) and attempt < self._max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                raise ApiError(
                    self._cfg.provider, response.status_code, _provider_error_message(response)
                )

    def _backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter: ~1s after the first attempt, ~2s after the second."""
        return _BACKOFF_BASE_S * (2**attempt) + random.uniform(0.0, _BACKOFF_JITTER_S)

    @staticmethod
    def _retryable(status_code: int) -> bool:
        """Only rate limits and server-side failures are worth retrying."""
        return status_code == 429 or 500 <= status_code <= 599

    def _extract_content(self, response: httpx.Response) -> str:
        """Pull choices[0].message.content; never fabricate or pad missing text."""
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (ValueError, IndexError, KeyError, TypeError):
            raise ResponseFormatError(
                f"{self._cfg.provider} returned an unexpected response shape"
            ) from None
        if not isinstance(content, str) or not content.strip():
            raise ResponseFormatError(f"{self._cfg.provider} returned empty content")
        return content

    def _error_message(self, response: httpx.Response) -> str:
        return _provider_error_message(response)


def _provider_error_message(response: httpx.Response) -> str:
    """Best-effort provider error message from the response body."""
    try:
        data = response.json()
    except ValueError:
        return response.text[:_ERROR_SNIPPET_CHARS] or "no response body"
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        for field in ("message", "detail"):
            if isinstance(data.get(field), str):
                return data[field]
    return response.text[:_ERROR_SNIPPET_CHARS] or "no response body"


def fetch_models(
    base_url: str,
    api_key: str,
    timeout_s: float = 15.0,
    *,
    _transport: httpx.AsyncBaseTransport | httpx.BaseTransport | None = None,
) -> list[str]:
    """Sync ``GET {base_url}models`` with Bearer auth; returns sorted model ids.

    Used by the settings UI for the live connection test. No retries and a
    short timeout so the UI stays snappy. Raises ApiError on transport/HTTP
    failures and ResponseFormatError when the response carries no usable
    model list. ``_transport`` is a test seam (``httpx.MockTransport``).
    """
    url = base_url.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_s), transport=_transport) as client:
            response = client.get(url, headers=headers)
    except httpx.TransportError as exc:  # includes TimeoutException
        raise ApiError(_DISCOVERY_PROVIDER, None, f"transport failure: {exc}") from exc
    if not response.is_success:
        raise ApiError(
            _DISCOVERY_PROVIDER, response.status_code, _provider_error_message(response)
        )
    try:
        data = response.json()
    except ValueError:
        raise ResponseFormatError(
            f"{_DISCOVERY_PROVIDER} returned an unexpected response shape"
        ) from None
    if isinstance(data, dict):
        entries = data.get("data")
    elif isinstance(data, list):  # tolerate a bare JSON list of model objects
        entries = data
    else:
        entries = None
    ids: list[str] = []
    if isinstance(entries, list):
        ids = sorted(
            {
                item["id"]
                for item in entries
                if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()
            }
        )
    if not ids:
        raise ResponseFormatError(f"{_DISCOVERY_PROVIDER} returned no models")
    return ids


def tavily_check(
    api_key: str,
    timeout_s: float = 15.0,
    *,
    _transport: httpx.BaseTransport | None = None,
) -> str:
    """Verify a Tavily key and return a short human status string.

    Tries the free ``GET /usage`` endpoint first; when that route is not
    available (older API surface), falls back to a minimal
    ``POST /search`` (costs one credit). Raises ApiError on auth/transport
    failures; the message never contains the key (auth is a header).
    ``_transport`` is a test seam.
    """
    if not api_key.strip():
        raise ApiError("Tavily", None, "no API key configured")
    headers = {"Authorization": f"Bearer {api_key}"}
    base = "https://api.tavily.com"
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_s), transport=_transport) as client:
            response = client.get(f"{base}/usage", headers=headers)
            if response.status_code in (404, 405):
                response = client.post(
                    f"{base}/search",
                    headers=headers,
                    json={"query": "connectivity check", "max_results": 1, "search_depth": "basic"},
                )
                response.raise_for_status()
                return "connected - search API reachable"
            if not response.is_success:
                raise ApiError("Tavily", response.status_code, _provider_error_message(response))
            data = response.json()
    except httpx.TransportError as exc:  # includes TimeoutException
        raise ApiError("Tavily", None, f"transport failure: {exc}") from exc
    except ValueError:
        raise ResponseFormatError("Tavily returned an unexpected response shape") from None

    # Build a status from whatever usage fields the account reports.
    key_info = data.get("key") if isinstance(data, dict) else None
    account = data.get("account") if isinstance(data, dict) else None
    used = limit = None
    if isinstance(key_info, dict):
        used = key_info.get("usage")
        limit = key_info.get("limit")
    if used is None and isinstance(account, dict):
        used = account.get("plan_usage")
        limit = account.get("plan_limit")
    if isinstance(used, int) and isinstance(limit, int):
        return f"connected - {used}/{limit} credits used"
    return "connected"
