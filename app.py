"""Agent Wars - Streamlit front end.

Slim wiring only: page setup, theme injection, sidebar settings, missing-key
banner, and the single run flow. All rendering lives in ``ui/components.py``
and ``ui/settings.py``; all styling in ``ui/theme.py``. The view renders
exactly what ``DebateOrchestrator`` emits and never fabricates a response.
"""
from __future__ import annotations

import asyncio

import streamlit as st

from core.config import AGENT_CONFIGS
from core.models import DebateState
from core.orchestrator import DebateOrchestrator
from core.settings import has_credentials, resolve_config
from ui import components as ui
from ui import interactions
from ui import settings as ui_settings
from ui.theme import inject, page_config

_ROLES = list(AGENT_CONFIGS)  # pipeline execution order


def _missing_keys() -> list[str]:
    """Env var names for agents with no usable key (settings override or env)."""
    missing: list[str] = []
    for role in _ROLES:
        cfg = resolve_config(role)
        if not has_credentials(cfg):
            missing.append(cfg.api_key_env)
    return missing


def _refresh(
    state: DebateState,
    stepper_ph: st.DeltaGenerator,
    card_phs: list[st.DeltaGenerator],
    verdict_ph: st.DeltaGenerator,
) -> None:
    """Re-render stepper, five agent cards and the verdict from one state."""
    with stepper_ph.container():
        ui.render_stepper(state)
    for i, (ph, role) in enumerate(zip(card_phs, _ROLES)):
        with ph.container():
            ui.render_agent_card(resolve_config(role), state.get(role), index=i)
    with verdict_ph.container():
        ui.render_verdict(state)


def _run_debate(
    topic: str,
    mode: str,
    stepper_ph: st.DeltaGenerator,
    card_phs: list[st.DeltaGenerator],
    verdict_ph: st.DeltaGenerator,
) -> None:
    """Blocking run: stream every pipeline update into the placeholders."""
    st.session_state["topic"] = topic
    st.session_state["mode"] = mode
    st.session_state["running"] = True
    try:
        orchestrator = DebateOrchestrator()

        def on_update(state: DebateState) -> None:
            _refresh(state, stepper_ph, card_phs, verdict_ph)

        final_state = asyncio.run(orchestrator.run_debate(topic, mode, on_update=on_update))
    finally:
        st.session_state["running"] = False
    st.session_state["debate"] = final_state
    st.rerun()


def main() -> None:
    page_config()
    inject()
    ui_settings.render_sidebar()
    interactions.inject()

    state: DebateState | None = st.session_state.get("debate")
    ui.render_header()

    missing = _missing_keys()
    if missing:
        ui.render_banner(missing)
    all_missing = len(missing) == len(_ROLES)
    disabled_reason = (
        "No API keys are configured - add at least one key in .env or the sidebar "
        "settings to enable a debate."
        if all_missing
        else None
    )
    running = bool(st.session_state.get("running"))

    picked = ui.render_input_zone(running=running, disabled_reason=disabled_reason)

    stepper_ph = st.empty()
    card_phs = [col.empty() for col in st.columns(len(_ROLES), gap="small")]
    verdict_ph = st.empty()

    if state is not None:
        _refresh(state, stepper_ph, card_phs, verdict_ph)
    else:
        # Idle arena: show the five waiting cards (and the Setup step) so the
        # layout is visible before the first debate, without any fake state.
        _refresh(DebateState(), stepper_ph, card_phs, verdict_ph)

    ui.render_footer()

    if picked is not None and not running:
        topic, mode = picked
        _run_debate(topic, mode, stepper_ph, card_phs, verdict_ph)


if __name__ == "__main__":
    main()
