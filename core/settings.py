"""Runtime per-agent overrides stored in ``.agent_settings.json``.

The sidebar settings write base URL / API key / model overrides here; the
pipeline reads them back through ``resolve_config`` so a debate run picks up
whatever the user configured in the UI. The file lives next to the project
root (cwd) and is gitignored. Storage only: no HTTP happens in this module
(model discovery lives in ``core.api_client.fetch_models``).

File shape: ``{"<role_value>": {"base_url": "...", "api_key": "...",
"model": "..."}, "integrations": {"tavily": {"api_key": "..."}}}``.
Non-agent sections are preserved verbatim when agent overrides are written.
Load failures return ``{}`` so a corrupt file can never kill the app; write
failures raise ``ConfigError`` with short messages.
"""
from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

from core.config import AGENT_CONFIGS, AgentConfig, get_api_key
from core.exceptions import ConfigError
from core.models import AgentRole

OVERRIDES_FILE = Path(".agent_settings.json")  # relative to project root / cwd

_FIELDS = ("base_url", "api_key", "model")
_INTEGRATIONS = "integrations"
_TAVILY_ENV = "TAVILY_API_KEY"


def _load_raw() -> dict:
    """Whole settings document; ``{}`` when missing, unreadable, or corrupt."""
    try:
        raw = OVERRIDES_FILE.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, ValueError):
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def load_overrides() -> dict[str, dict[str, str]]:
    """Read the agent role overrides; ``{}`` when missing, unreadable, or corrupt.

    Only the three known fields are kept and only for string values, so a
    hand-edited file cannot inject unexpected keys into ``resolve_config``.
    Non-agent sections (e.g. ``integrations``) are ignored here.
    """
    result: dict[str, dict[str, str]] = {}
    for role_value, entry in _load_raw().items():
        if not isinstance(role_value, str) or not isinstance(entry, dict):
            continue
        clean = {
            field: value
            for field in _FIELDS
            if isinstance((value := entry.get(field)), str) and value.strip()
        }
        if clean:
            result[role_value] = clean
    return result


def save_override(
    role: AgentRole, *, base_url: str | None = None, api_key: str | None = None, model: str | None = None
) -> None:
    """Persist field overrides for ``role``; ``None`` leaves a field untouched.

    The API key is stored only when a non-empty value is given (a blank value
    never overwrites or clears a stored key - use ``clear_override`` for that).
    Raises ConfigError when the file cannot be written.
    """
    data = _load_raw()
    entry = dict(data.get(role.value, {}))
    if base_url is not None:
        entry["base_url"] = base_url.strip()
    if model is not None:
        entry["model"] = model.strip()
    if isinstance(api_key, str) and api_key.strip():
        entry["api_key"] = api_key.strip()
    entry = {field: value for field, value in entry.items() if value}
    if entry:
        data[role.value] = entry
    else:
        data.pop(role.value, None)
    _write(data)


def clear_override(role: AgentRole, field: str) -> None:
    """Remove one stored override field for ``role`` (and the entry when empty)."""
    if field not in _FIELDS:
        raise ConfigError(f"unknown settings field: {field}")
    data = _load_raw()
    entry = data.get(role.value)
    if entry is None:
        return
    entry.pop(field, None)
    if entry:
        data[role.value] = entry
    else:
        data.pop(role.value, None)
    _write(data)


def resolve_config(role: AgentRole) -> AgentConfig:
    """Merge ``AGENT_CONFIGS[role]`` with stored overrides (empty strings ignored)."""
    base = AGENT_CONFIGS[role]
    entry = load_overrides().get(role.value, {})
    updates: dict[str, str] = {}
    for field in _FIELDS:
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            updates[field] = value.strip()
    return replace(base, **updates) if updates else base


def has_credentials(cfg: AgentConfig) -> bool:
    """True when a usable API key exists (override or env); never raises."""
    try:
        return bool(get_api_key(cfg))
    except ConfigError:
        return False


def get_tavily_key() -> str:
    """Tavily key: settings override first, then ``TAVILY_API_KEY``; ``""`` if neither."""
    entry = _load_raw().get(_INTEGRATIONS, {})
    stored = entry.get("tavily", {}) if isinstance(entry, dict) else {}
    key = stored.get("api_key") if isinstance(stored, dict) else None
    if isinstance(key, str) and key.strip():
        return key.strip()
    return os.environ.get(_TAVILY_ENV, "").strip()


def save_tavily_key(api_key: str) -> None:
    """Persist a Tavily key in the settings file (blank is ignored, like agents)."""
    if not api_key.strip():
        return
    data = _load_raw()
    section = data.get(_INTEGRATIONS)
    section = dict(section) if isinstance(section, dict) else {}
    section["tavily"] = {"api_key": api_key.strip()}
    data[_INTEGRATIONS] = section
    _write(data)


def _write(data: dict[str, dict[str, str]]) -> None:
    """Write the overrides file human-readable, via a temp file then replace."""
    target = OVERRIDES_FILE
    tmp = target.with_suffix(target.suffix + ".tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        tmp.replace(target)
    except OSError as exc:
        raise ConfigError(f"could not save settings: {exc}") from exc
