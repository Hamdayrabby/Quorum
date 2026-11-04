"""Centralized configuration for Agent Wars.

Single source of truth for the five agent/provider pairings, debate modes,
and API key resolution. ``.env`` is loaded once at import time so every layer
(agents, orchestrator, UI) sees identical settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from core.exceptions import ConfigError
from core.models import AgentRole

load_dotenv()


@dataclass(frozen=True)
class AgentConfig:
    """Static settings for one pipeline agent and its LLM provider."""

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


AGENT_CONFIGS: dict[AgentRole, AgentConfig] = {
    AgentRole.STRATEGIST: AgentConfig(
        role=AgentRole.STRATEGIST,
        display_name="Strategist",
        provider="Google Gemini",
        # Alternates: "gemini-2.5-pro", "gemini-2.5-flash-lite", "gemini-2.0-flash"
        model="gemini-2.5-flash",
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
        provider="DeepSeek",
        # Alternates: "deepseek-reasoner" (model ids change often)
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
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
        # Alternates: "mistral-medium-latest", "mistral-small-latest"
        model="mistral-large-latest",
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        temperature=0.4,
        max_tokens=1500,
        accent="#FF8A4C",
        glyph="\u25ce",
        tagline="Audits both openings for unsupported claims and weak logic.",
    ),
    AgentRole.DEVILS_ADVOCATE: AgentConfig(
        role=AgentRole.DEVILS_ADVOCATE,
        display_name="Devil's Advocate",
        provider="Z.ai (GLM)",
        # Alternates: "glm-4.6", "glm-4-flash" (model ids change often)
        model="glm-5.3-flash",
        base_url="https://api.z.ai/api/paas/v4/",
        api_key_env="GLM_API_KEY",
        temperature=0.8,
        max_tokens=1500,
        accent="#3ED6B5",
        glyph="\u2b21",
        tagline="Attacks both sides and surfaces overlooked perspectives.",
    ),
    AgentRole.SUPREME_JUDGE: AgentConfig(
        role=AgentRole.SUPREME_JUDGE,
        display_name="Supreme Judge",
        provider="NVIDIA NIM",
        # Alternates: "nvidia/llama-3.3-nemotron-super-49b-v1.5"
        model="nvidia/llama-3.3-nemotron-super-49b-v1",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY",
        temperature=0.3,
        max_tokens=3000,
        accent="#D4AF37",
        glyph="\u00a7",
        tagline="Scores both sides and delivers the final verdict.",
    ),
}

DEBATE_MODES: list[str] = ["Technology", "Science", "Education", "Business", "Society"]

TIMEOUT_S: float = 90.0
MAX_RETRIES: int = 2


def get_api_key(cfg: AgentConfig) -> str:
    """Return the provider API key for ``cfg`` from the environment.

    Raises ConfigError naming the missing environment variable when the key
    is absent or blank.
    """
    key = os.environ.get(cfg.api_key_env, "").strip()
    if not key:
        raise ConfigError(
            f"{cfg.display_name} ({cfg.provider}) has no API key: "
            f"set the {cfg.api_key_env} environment variable in .env"
        )
    return key
