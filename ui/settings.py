"""Sidebar settings: per-agent base URL + key, live connection test, model picker.

Each agent gets one expander in pipeline order containing a small form.
Submitting saves the override to ``.agent_settings.json`` (via
``core.settings``), then calls the provider's OpenAI-compatible
``GET {base_url}models`` (via ``core.api_client.fetch_models``); on success
the available models appear in a dropdown whose selection is persisted and
picked up by the next debate run.

Security posture: the API key is write-only from the UI's point of view. It
is typed into a password field that is never prefilled and is emptied on the
run after each save, and it can never appear in a status pill, error message,
or placeholder - those only ever carry env var names, URLs (no key: auth is
a header), and provider error text.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from core.api_client import fetch_models
from core.config import AGENT_CONFIGS, AgentConfig, get_api_key
from core.exceptions import AgentWarsError, ConfigError
from core.models import AgentRole
from core.settings import has_credentials, resolve_config, save_override

_ERROR_SNIPPET_CHARS = 120


def render_sidebar() -> None:
    """Render the SETTINGS section: one expander per agent, pipeline order."""
    with st.sidebar:
        st.markdown(
            '<div class="aw-micro aw-sidebar-title">SETTINGS</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="aw-sidebar-help">Base URL + key per agent. Test to list models. '
            "Stored in .agent_settings.json (gitignored).</div>",
            unsafe_allow_html=True,
        )
        for cfg in AGENT_CONFIGS.values():
            _render_agent_settings(cfg)


def _render_agent_settings(cfg: AgentConfig) -> None:
    """One agent expander: form (base URL + key), status pill, model dropdown."""
    role = cfg.role
    key_field = f"aw_key_{role.value}"
    clear_flag = f"aw_keyclear_{role.value}"

    # Consume the key-clear flag before the widget is instantiated this run,
    # so a typed key is wiped from session state right after being saved.
    if st.session_state.pop(clear_flag, False) and key_field in st.session_state:
        st.session_state[key_field] = ""

    resolved = resolve_config(role)
    with st.expander(f"{cfg.glyph} {cfg.display_name}"):
        with st.form(key=f"aw_form_{role.value}", border=False):
            base_url = st.text_input(
                "Base URL",
                value=resolved.base_url,
                key=f"aw_base_{role.value}",
            )
            st.text_input(
                "API key",
                value="",  # ALWAYS blank; never prefill or render a key
                key=key_field,
                type="password",
                placeholder="saved (session/env)" if has_credentials(resolved) else "not set",
            )
            submitted = st.form_submit_button("SAVE & TEST CONNECTION", use_container_width=True)
        if submitted:
            _handle_submit(role, base_url)

        _render_connection_result(role)


def _handle_submit(role: AgentRole, base_url: str) -> None:
    """Save overrides, run the live connection test, store the outcome.

    Always ends in one ``st.rerun()`` so the typed key is wiped from session
    state and the fresh result pill renders below the form.
    """
    conn_key = f"aw_conn_{role.value}"
    clear_flag = f"aw_keyclear_{role.value}"
    key_typed = bool(str(st.session_state.get(f"aw_key_{role.value}", "")).strip())
    new_base = str(base_url).strip()
    current = resolve_config(role)

    def fail(message: str) -> None:
        st.session_state[conn_key] = {"ok": False, "models": None, "error": _snippet(message)}
        st.session_state[clear_flag] = key_typed
        st.rerun()

    try:
        if new_base != current.base_url or key_typed:
            save_override(
                role,
                base_url=new_base if new_base != current.base_url else None,
                api_key=str(st.session_state.get(f"aw_key_{role.value}", "")) or None,
            )
    except ConfigError as exc:
        fail(str(exc))
        return

    resolved = resolve_config(role)
    try:
        api_key = get_api_key(resolved)
    except ConfigError as exc:
        fail(str(exc))
        return
    try:
        with st.spinner("Testing connection..."):
            models = fetch_models(resolved.base_url, api_key)
    except AgentWarsError as exc:  # ApiError / ResponseFormatError; never contains the key
        fail(str(exc))
        return
    st.session_state[conn_key] = {"ok": True, "models": models, "error": None}
    st.session_state[clear_flag] = key_typed
    st.rerun()


def _render_connection_result(role: AgentRole) -> None:
    """Status pill under the form; with a model dropdown on success."""
    conn = st.session_state.get(f"aw_conn_{role.value}")
    if conn is None:
        return
    if conn.get("ok"):
        models = conn.get("models") or []
        st.markdown(
            '<div class="aw-status is-ok">'
            f'<span class="aw-status-dot"></span>{len(models)} MODELS</div>',
            unsafe_allow_html=True,
        )
        _render_model_picker(role, models)
        return
    error = conn.get("error") or "connection failed"
    st.markdown(
        '<div class="aw-status is-err">'
        '<span class="aw-status-dot"></span>CONNECTION FAILED</div>'
        f'<div class="aw-status-err-text">{escape(error)}</div>',
        unsafe_allow_html=True,
    )


def _render_model_picker(role: AgentRole, models: list[str]) -> None:
    """Model dropdown fed by the last successful test; persists the selection."""
    if not models:
        return
    model_key = f"aw_model_{role.value}"
    # A previous test may have left a selection that is not in the new list;
    # drop it so the widget falls back to the computed index instead of erroring.
    if model_key in st.session_state and st.session_state[model_key] not in models:
        del st.session_state[model_key]
    resolved = resolve_config(role)
    index = models.index(resolved.model) if resolved.model in models else 0
    selected = st.selectbox("Model", models, key=model_key, index=index)
    if selected and selected != resolved.model:  # guard: save only on actual change
        try:
            save_override(role, model=selected)
        except ConfigError as exc:
            st.markdown(
                f'<div class="aw-status-err-text">{escape(_snippet(str(exc)))}</div>',
                unsafe_allow_html=True,
            )
            return
        st.rerun()


def _snippet(text: str) -> str:
    """Collapse whitespace and truncate; keeps provider errors single-line."""
    text = " ".join(str(text).split())
    if len(text) > _ERROR_SNIPPET_CHARS:
        return text[: _ERROR_SNIPPET_CHARS - 3] + "..."
    return text
