"""Centralized configuration for Agent Wars.

Single source of truth for the five agent/provider pairings, debate modes,
and API key resolution. ``.env`` is loaded once at import time so every layer
(agents, orchestrator, UI) sees identical settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace as dataclass_replace

from dotenv import load_dotenv

from core.exceptions import ConfigError
from core.models import AgentRole

load_dotenv()


@dataclass(frozen=True)
class AgentConfig:
    """Static settings for one pipeline agent and its LLM provider.

    ``api_key`` is the runtime override entered in the sidebar settings;
    ``None``/empty means "fall back to the ``api_key_env`` environment
    variable" (see ``get_api_key``).
    """

    role: AgentRole
    display_name: str  # e.g. "Strategist"
    provider: str  # e.g. "Google Gemini"
    model: str  # exact provider model id
    base_url: str  # OpenAI-compatible chat-completions base
    api_key_env: str  # env var name, e.g. "GEMINI_API_KEY"
    temperature: float
    max_tokens: int
    accent: str  # hex color, used by the UI
    glyph: str  # single unicode symbol for the UI card
    tagline: str  # one-line responsibility, shown on the UI card
    api_key: str | None = None  # runtime override; None -> env lookup


RIVER_DEFAULT_BASE_URL = "https://api.river.ai/v1/"
# River AI routes the challenger-side agents through one OpenAI-compatible
# base; the deployment can redirect it via the RIVER_BASE_URL env var.
_RIVER_BASE_URL = os.environ.get("RIVER_BASE_URL", "").strip() or RIVER_DEFAULT_BASE_URL


AGENT_CONFIGS: dict[AgentRole, AgentConfig] = {
    AgentRole.STRATEGIST: AgentConfig(
        role=AgentRole.STRATEGIST,
        display_name="Strategist",
        provider="Google Gemini",
        # Live-verified 2026-11-05. Alternates: "models/gemini-flash-latest",
        # "models/gemini-3.8-flash" (google's catalog moves fast; confirm via
        # the settings model list).
        model="models/gemini-3.6-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key_env="GEMINI_API_KEY",
        temperature=0.7,
        max_tokens=1500,
        accent="#5B9DFF",
        glyph="\u25c6",
        tagline="Builds the strongest opening case FOR the proposition.",
    ),
    AgentRole.CHALLENGER: AgentConfig(
        role=AgentRole.CHALLENGER,
        display_name="Challenger",
        provider="River AI · DeepSeek",
        # Live-verified on River AI 2026-11-05; confirm via the settings
        # model list (SAVE & TEST CONNECTION). Direct-provider fallback:
        # base_url="https://api.deepseek.com/v1", api_key_env="DEEPSEEK_API_KEY".
        model="deepseek-ai/DeepSeek-V4.1-Flash",
        base_url=_RIVER_BASE_URL,
        api_key_env="RIVER_API_KEY",
        temperature=0.7,
        max_tokens=1500,
        accent="#9B7BFF",
        glyph="\u25b2",
        tagline="Builds the strongest case AGAINST the proposition.",
    ),
    AgentRole.RESEARCHER: AgentConfig(
        role=AgentRole.RESEARCHER,
        display_name="Researcher",
        provider="Mistral AI",
        # Note: "mistral-large-4" (free tier, 2026-11) answers with empty
        # content over the OpenAI-compat endpoint; medium works but is
        # rate-limited on free keys. Confirm via the settings model list.
        model="mistral-medium-latest",
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        temperature=0.4,
        # The seat often carries a reasoning model (nemotron-lightning via the
        # settings override, GLM on River) whose hidden thinking shares this
        # budget — a full audit can reason for thousands of tokens before the
        # first visible word, so this cap stays generous (a cap is not a cost).
        max_tokens=12000,
        accent="#FF8A4C",
        glyph="\u25ce",
        tagline="Audits both openings for unsupported claims and weak logic.",
    ),
    AgentRole.DEVILS_ADVOCATE: AgentConfig(
        role=AgentRole.DEVILS_ADVOCATE,
        display_name="Devil's Advocate",
        provider="River AI · GLM",
        # Live-verified on River AI 2026-11-05; a reasoning model — keep the
        # generous max_tokens below. Direct-provider fallback:
        # base_url="https://api.z.ai/api/paas/v4/", api_key_env="GLM_API_KEY".
        model="zai-org/GLM-5.3-Flash",
        base_url=_RIVER_BASE_URL,
        api_key_env="RIVER_API_KEY",
        temperature=0.8,
        # GLM-5.3-Flash (and other reasoning models) spend tokens on hidden
        # reasoning before the visible answer; a small budget yields empty
        # content, so reasoning-model roles get generous headroom.
        max_tokens=6000,
        accent="#3ED6B5",
        glyph="\u2b21",
        tagline="Attacks both sides and surfaces overlooked perspectives.",
    ),
    AgentRole.SUPREME_JUDGE: AgentConfig(
        role=AgentRole.SUPREME_JUDGE,
        display_name="Supreme Judge",
        provider="NVIDIA NIM",
        # Live-verified 2026-11-05 (llama-3.3-nemotron-super-49b-v1 reached
        # end of life; nemotron-3-super-120b-a12b is not entitled on free
        # keys). Alternates: "nvidia/nemotron-3.5-lightning-30b-a3b",
        # "nvidia/nemotron-3.5-super-vl-120b-a12b".
        model="nvidia/nemotron-3-ultra-550b-a55b",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY",
        temperature=0.3,
        # The judge parses into a strict JSON verdict; reasoning models on
        # this seat need headroom for hidden reasoning plus the JSON payload.
        max_tokens=8000,
        accent="#D4AF37",
        glyph="\u00a7",
        tagline="Scores both sides and delivers the final verdict.",
    ),
}

DEBATE_MODES: list[str] = ["Technology", "Science", "Education", "Business", "Society"]

# Per-seat model fallback for TRANSIENT provider failures (429/5xx after the
# client's own retries). Every entry is a live-verified model, so a seat that
# gets throttled re-asks a different model instead of failing the debate.
# Permanent errors (bad key, malformed request) never trigger a fallback.
_FALLBACKS: dict[AgentRole, dict] = {
    # GLM models reason before answering; the primary's small budget would
    # starve them into empty content, so fallbacks carry reasoning headroom.
    AgentRole.STRATEGIST: {"provider": "River AI · GLM", "model": "GLM-5.3",
                           "base_url": _RIVER_BASE_URL, "api_key_env": "RIVER_API_KEY",
                           "max_tokens": 6000},
    AgentRole.CHALLENGER: {"provider": "River AI · GLM", "model": "zai-org/GLM-5.3-Flash",
                           "base_url": _RIVER_BASE_URL, "api_key_env": "RIVER_API_KEY",
                           "max_tokens": 6000},
    AgentRole.RESEARCHER: {"provider": "NVIDIA NIM", "model": "nvidia/nemotron-3.5-bolt-e4b",
                           "base_url": "https://integrate.api.nvidia.com/v1", "api_key_env": "NVIDIA_API_KEY"},
    AgentRole.DEVILS_ADVOCATE: {"provider": "River AI · DeepSeek", "model": "deepseek-ai/DeepSeek-V4.1-Flash",
                                "base_url": _RIVER_BASE_URL, "api_key_env": "RIVER_API_KEY"},
    AgentRole.SUPREME_JUDGE: {"provider": "NVIDIA NIM", "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
                              "base_url": "https://integrate.api.nvidia.com/v1", "api_key_env": "NVIDIA_API_KEY",
                              "max_tokens": 8000},
}
FALLBACK_CONFIGS: dict[AgentRole, AgentConfig] = {
    role: dataclass_replace(AGENT_CONFIGS[role], **overrides) for role, overrides in _FALLBACKS.items()
}

TIMEOUT_S: float = 150.0  # reasoning models can think well past 90s per call
MAX_RETRIES: int = 2


def get_api_key(cfg: AgentConfig) -> str:
    """Return the API key for ``cfg``: the runtime override when set, else the environment.

    A non-empty ``cfg.api_key`` (sidebar settings override) wins over the
    environment. Raises ConfigError naming the missing environment variable
    when neither source provides a usable key.
    """
    if isinstance(cfg.api_key, str) and cfg.api_key.strip():
        return cfg.api_key.strip()
    key = os.environ.get(cfg.api_key_env, "").strip()
    if not key:
        raise ConfigError(
            f"{cfg.display_name} ({cfg.provider}) has no API key: "
            f"set the {cfg.api_key_env} environment variable in .env"
        )
    return key
