"""Exception hierarchy for Agent Wars.

The orchestrator catches these at the agent boundary so a single provider
failure never crashes the debate; the UI renders them as per-agent errors.
"""


class AgentWarsError(Exception):
    """Base class for all Agent Wars errors."""


class ConfigError(AgentWarsError):
    """Raised when an API key or configuration value is missing/invalid."""


class ApiError(AgentWarsError):
    """Raised when a provider call fails after retries (network, 4xx, 5xx)."""

    def __init__(self, provider: str, status_code: int | None, message: str):
        self.provider = provider
        self.status_code = status_code
        self.message = message
        label = f"{provider} API error"
        if status_code is not None:
            label += f" (HTTP {status_code})"
        super().__init__(f"{label}: {message}")


class ResponseFormatError(AgentWarsError):
    """Raised when a provider response cannot be parsed into usable output."""
