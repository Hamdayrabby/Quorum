"""Settings-layer verification (plain script, no pytest).

Run directly: ``.venv/Scripts/python.exe tests/test_settings.py``.
Every case runs against a temporary overrides file (``core.settings.OVERRIDES_FILE``
is swapped per case and restored after), so the real ``.agent_settings.json``
and ``.env`` are never touched.

Covers: save/load roundtrip + corrupt-file tolerance; resolve precedence
(base -> override, empty strings ignored); API-key resolution through the
override; and ``fetch_models`` at the HTTP boundary via ``httpx.MockTransport``.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

import core.settings as settings_module  # noqa: E402
from core.api_client import fetch_models  # noqa: E402
from core.config import AGENT_CONFIGS, get_api_key  # noqa: E402
from core.exceptions import ApiError, ConfigError, ResponseFormatError  # noqa: E402
from core.models import AgentRole  # noqa: E402
from core.settings import clear_override, has_credentials, load_overrides, resolve_config, save_override  # noqa: E402

_FAILURES: list[str] = []
_TEST_ENV_VAR = "AW_SETTINGS_TEST_KEY"  # never a real provider key name


def settings_case(name: str):
    """Run one case against a fresh temp overrides file; print PASS/FAIL."""

    def decorate(func):
        def run() -> None:
            original = settings_module.OVERRIDES_FILE
            tmp_dir = Path(tempfile.mkdtemp(prefix="aw_settings_test_"))
            settings_module.OVERRIDES_FILE = tmp_dir / "agent_settings.json"
            try:
                func()
                print(f"PASS: {name}")
            except AssertionError as exc:
                _FAILURES.append(name)
                print(f"FAIL: {name} - {exc}")
            except Exception as exc:  # noqa: BLE001 - report, keep running
                _FAILURES.append(name)
                print(f"FAIL: {name} - unexpected {type(exc).__name__}: {exc}")
            finally:
                settings_module.OVERRIDES_FILE = original

        return run

    return decorate


@settings_case("1. save/load roundtrip preserves all three fields; corrupt file -> {} without raising")
def case_roundtrip() -> None:
    role = AgentRole.CHALLENGER
    save_override(
        role,
        base_url="https://relay.example/v1/",
        api_key="  sk-test-123  ",
        model="model-b",
    )
    data = load_overrides()
    assert data == {
        role.value: {
            "base_url": "https://relay.example/v1/",
            "api_key": "sk-test-123",
            "model": "model-b",
        }
    }, data
    assert resolve_config(role).base_url == "https://relay.example/v1/"
    assert resolve_config(role).api_key == "sk-test-123"
    assert resolve_config(role).model == "model-b"
    # Saving one field preserves the others; key is stored only when non-empty.
    save_override(role, model="model-c")
    save_override(role, api_key="   ")
    data = load_overrides()
    assert data[role.value]["api_key"] == "sk-test-123", data
    assert data[role.value]["base_url"] == "https://relay.example/v1/", data
    assert data[role.value]["model"] == "model-c", data
    # clear_override removes one field, keeps the rest.
    clear_override(role, "model")
    data = load_overrides()
    assert "model" not in data[role.value], data
    assert data[role.value]["api_key"] == "sk-test-123", data
    # A corrupt file never kills the app: load returns {} and resolve falls back.
    settings_module.OVERRIDES_FILE.write_text("{not json", encoding="utf-8")
    assert load_overrides() == {}, "corrupt file must load as {}"
    assert resolve_config(role) == AGENT_CONFIGS[role]
    # A missing file behaves the same way.
    settings_module.OVERRIDES_FILE.unlink()
    assert load_overrides() == {}


@settings_case("2. resolve precedence: base -> override (base_url, model, api_key); empty strings ignored")
def case_precedence() -> None:
    role = AgentRole.RESEARCHER
    base = AGENT_CONFIGS[role]
    # Hand-written empty/whitespace overrides are ignored on resolve.
    settings_module.OVERRIDES_FILE.write_text(
        json.dumps({role.value: {"base_url": "", "model": "   ", "api_key": ""}}),
        encoding="utf-8",
    )
    cfg = resolve_config(role)
    assert cfg.base_url == base.base_url, cfg.base_url
    assert cfg.model == base.model, cfg.model
    assert cfg.api_key is None, cfg.api_key
    # Non-empty overrides win over base for each field.
    save_override(role, base_url="https://proxy.example/v1/", model="mistral-test")
    cfg = resolve_config(role)
    assert cfg.base_url == "https://proxy.example/v1/", cfg.base_url
    assert cfg.model == "mistral-test", cfg.model
    assert cfg.api_key is None
    # Untouched roles keep their base config.
    assert resolve_config(AgentRole.STRATEGIST) == AGENT_CONFIGS[AgentRole.STRATEGIST]


@settings_case("3. get_api_key: override wins, env fallback, has_credentials False when neither")
def case_api_key() -> None:
    os.environ.pop(_TEST_ENV_VAR, None)
    base = AGENT_CONFIGS[AgentRole.SUPREME_JUDGE]
    cfg_env = replace(base, api_key=None, api_key_env=_TEST_ENV_VAR)
    # Neither override nor env: has_credentials False, get_api_key raises.
    assert has_credentials(cfg_env) is False
    try:
        get_api_key(cfg_env)
    except ConfigError as exc:
        assert _TEST_ENV_VAR in str(exc), str(exc)
    else:
        raise AssertionError("expected ConfigError when no override and no env key")
    # Env key alone is enough.
    os.environ[_TEST_ENV_VAR] = "env-key"
    assert has_credentials(cfg_env) is True
    assert get_api_key(cfg_env) == "env-key"
    # Non-empty override beats the env.
    save_override(AgentRole.SUPREME_JUDGE, api_key="override-key")
    cfg = resolve_config(AgentRole.SUPREME_JUDGE)
    assert cfg.api_key == "override-key", cfg.api_key
    assert get_api_key(cfg) == "override-key"
    assert has_credentials(cfg) is True
    os.environ.pop(_TEST_ENV_VAR, None)


@settings_case("4. fetch_models: OpenAI shape -> sorted ids; bare list; 401 -> ApiError; empty -> ResponseFormatError")
def case_fetch_models() -> None:
    def handler_openai(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/models"), str(request.url)
        assert request.headers.get("Authorization") == "Bearer sk-test"
        return httpx.Response(
            200, json={"data": [{"id": "model-b"}, {"id": "model-a"}, {"id": "model-a"}]}
        )

    models = fetch_models(
        "https://relay.example/v1/", "sk-test", _transport=httpx.MockTransport(handler_openai)
    )
    assert models == ["model-a", "model-b"], models

    def handler_bare(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "y"}, {"id": "x"}])

    assert fetch_models(
        "https://relay.example/v1/", "sk-test", _transport=httpx.MockTransport(handler_bare)
    ) == ["x", "y"]

    def handler_401(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "invalid api key"}})

    try:
        fetch_models(
            "https://relay.example/v1/", "sk-test", _transport=httpx.MockTransport(handler_401)
        )
    except ApiError as exc:
        assert exc.status_code == 401, str(exc)
        assert "invalid api key" in str(exc), str(exc)
    else:
        raise AssertionError("expected ApiError on 401")

    def handler_empty(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    try:
        fetch_models(
            "https://relay.example/v1/", "sk-test", _transport=httpx.MockTransport(handler_empty)
        )
    except ResponseFormatError:
        pass
    else:
        raise AssertionError("expected ResponseFormatError for an empty model list")


def main() -> None:
    case_roundtrip()
    case_precedence()
    case_api_key()
    case_fetch_models()
    if _FAILURES:
        print(f"SETTINGS TESTS RED ({len(_FAILURES)} failing: {', '.join(_FAILURES)})")
        raise SystemExit(1)
    print("SETTINGS TESTS GREEN")


if __name__ == "__main__":
    main()
