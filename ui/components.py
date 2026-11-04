"""Pure render functions for the Agent Wars arena.

Every function turns typed input (``AgentConfig``, ``AgentResult``,
``DebateState``) into finished HTML via ``st.markdown`` and nothing else:
no orchestration, no session state, no provider knowledge. ``app.py``
decides when and where each function runs.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from core.config import AGENT_CONFIGS, DEBATE_MODES
from core.config import AgentConfig
from core.models import AgentResult, AgentRole, AgentStatus, DebateState, Verdict

# Stepper labels; each stage borrows the accent of the agent that anchors it
# (strategist, challenger, researcher, devil's advocate, judge).
_STAGES: list[tuple[str, str]] = [
    ("Setup", "#5B9DFF"),
    ("Openings", "#9B7BFF"),
    ("Analysis", "#FF8A4C"),
    ("Judgment", "#3ED6B5"),
    ("Verdict", "#D4AF37"),
]

_ANALYSIS_ROLES = ("STRATEGIST", "CHALLENGER", "RESEARCHER", "DEVILS_ADVOCATE")


def _stable_html(html: str) -> str:
    """Drop blank lines so st.markdown keeps the payload as one raw-HTML block.

    A blank line inside an ``unsafe_allow_html`` template terminates Streamlit's
    raw-HTML block and re-parses the remainder as Markdown — indented provider
    output (e.g. a pretty-printed API error) then leaks into the page as a
    stray code element. Agent and provider text may contain arbitrary bytes,
    so every multi-line template goes through this before rendering; line
    breaks inside pre-wrap bodies are preserved either way.
    """
    return "\n".join(line for line in html.splitlines() if line.strip())


def debate_phase(state: DebateState | None) -> int:
    """Map a ``DebateState`` onto the current stepper stage (1-5)."""
    if state is None:
        return 1
    if state.verdict is not None or state.judge_error is not None:
        return 5
    statuses = [
        state.results[role].status if role in state.results else AgentStatus.WAITING
        for role in AGENT_CONFIGS
    ]
    if AgentStatus.THINKING in statuses:
        # The pipeline marks agents thinking strictly stage by stage.
        thinking_idx = max(i for i, s in enumerate(statuses) if s is AgentStatus.THINKING)
        return {0: 2, 1: 2, 2: 3, 3: 3, 4: 4}[thinking_idx]
    terminal = all(s in (AgentStatus.COMPLETED, AgentStatus.FAILED) for s in statuses)
    return 5 if terminal else 1


def render_header() -> None:
    """Wordmark, tagline and the five quiet agent accent dots."""
    dots = "".join(
        f'<span class="aw-dot" style="background:{cfg.accent}"></span>'
        for cfg in AGENT_CONFIGS.values()
    )
    st.markdown(
        _stable_html(f"""
        <div class="aw-header">
          <div class="aw-brand">
            <span class="aw-wordmark">AGENT<span class="aw-gold">&#8202;WARS</span></span>
            <span class="aw-vdivider"></span>
            <span class="aw-micro aw-tagline">FIVE MINDS. ONE VERDICT.</span>
          </div>
          <div class="aw-dots">{dots}</div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_banner(missing_keys: list[str]) -> None:
    """Quiet amber banner naming the environment variables that are unset."""
    st.markdown(
        _stable_html(f"""
        <div class="aw-banner">
          <div class="aw-micro aw-micro-warn">Configuration</div>
          <div class="aw-banner-body">{escape(", ".join(missing_keys))} not set &#8212;
          those agents will fail. Add keys to .env.</div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_input_zone(
    *, running: bool, disabled_reason: str | None
) -> tuple[str, str] | None:
    """Topic input, mode pills and the primary button.

    Returns ``(topic, mode)`` when Start is clicked with a valid topic,
    otherwise ``None``. Never touches the orchestrator.
    """
    label = "DEBATE IN PROGRESS&#8230;" if running else "START DEBATE"
    disabled = running or disabled_reason is not None

    col_topic, col_mode = st.columns([0.62, 0.38], gap="medium")
    with col_topic:
        st.markdown('<div class="aw-micro">Topic</div>', unsafe_allow_html=True)
        topic = st.text_input(
            "Topic",
            key="aw_topic",
            label_visibility="collapsed",
            placeholder="State the proposition to debate, e.g. Remote work is better than office work",
        )
    with col_mode:
        st.markdown('<div class="aw-micro">Mode</div>', unsafe_allow_html=True)
        mode = st.pills(
            "Mode",
            DEBATE_MODES,
            selection_mode="single",
            default=DEBATE_MODES[0],
            label_visibility="collapsed",
        )

    clicked = st.button(
        label,
        type="primary",
        disabled=disabled,
        use_container_width=False,
    )
    if disabled_reason is not None and not running:
        st.markdown(
            f'<div class="aw-input-note">{escape(disabled_reason)}</div>',
            unsafe_allow_html=True,
        )
    if not clicked:
        return None
    if not topic.strip():
        st.markdown(
            '<div class="aw-input-note aw-input-note-err">Enter a topic to start the debate.</div>',
            unsafe_allow_html=True,
        )
        return None
    if not mode:
        st.markdown(
            '<div class="aw-input-note aw-input-note-err">Select a debate mode.</div>',
            unsafe_allow_html=True,
        )
        return None
    return topic.strip(), mode


def render_stepper(state: DebateState | None) -> None:
    """Five-stage stepper derived from the debate state."""
    phase = debate_phase(state)
    recap = ""
    if state is not None and state.topic:
        recap = (
            '<div class="aw-recap">'
            f"{escape((state.mode or '').upper())} &#8212; {escape(state.topic)}"
            "</div>"
        )
    steps: list[str] = []
    for i, (name, accent) in enumerate(_STAGES, start=1):
        if phase == 5 or i < phase:
            cls = "is-done"
        elif i == phase:
            cls = "is-active"
        else:
            cls = "is-todo"
        line = "" if i == len(_STAGES) else '<span class="aw-step-line"></span>'
        steps.append(
            f'<div class="aw-step {cls}" style="--step-accent:{accent}">'
            f'<span class="aw-step-dot">{i}</span>'
            f'<span class="aw-step-label">{name}</span>'
            f"{line}</div>"
        )
    st.markdown(
        f'{recap}<div class="aw-stepper">{"".join(steps)}</div>',
        unsafe_allow_html=True,
    )


def render_agent_card(cfg: AgentConfig, result: AgentResult | None) -> None:
    """One agent card: identity, live status pill and output or error."""
    status = result.status if result is not None else AgentStatus.WAITING
    pill_class = {
        AgentStatus.WAITING: "is-waiting",
        AgentStatus.THINKING: "is-thinking",
        AgentStatus.COMPLETED: "is-completed",
        AgentStatus.FAILED: "is-failed",
    }[status]

    if status is AgentStatus.FAILED and result is not None and result.error:
        body = f'<div class="aw-err">{escape(result.error)}</div>'
    elif status is AgentStatus.COMPLETED and result is not None:
        body = f'<div class="aw-output">{escape(result.content)}</div>'
    else:
        body = ""

    foot = ""
    if status is AgentStatus.COMPLETED and result is not None:
        foot = f'<div class="aw-card-foot"><span class="aw-latency">{result.latency_s:.1f}s</span></div>'

    st.markdown(
        _stable_html(f"""
        <div class="aw-card" style="--accent:{cfg.accent}">
          <div class="aw-card-line"></div>
          <div class="aw-card-head">
            <span class="aw-glyph">{cfg.glyph}</span>
            <span class="aw-name">{escape(cfg.display_name)}</span>
          </div>
          <span class="aw-chip" title="{escape(cfg.model)}">{escape(cfg.model)}</span>
          <div class="aw-card-tag aw-micro">{escape(cfg.tagline)}</div>
          <span class="aw-pill {pill_class}">
            <span class="aw-pill-dot"></span>{status.value.upper()}
          </span>
          {body}
          {foot}
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_verdict(state: DebateState) -> None:
    """Verdict panel on success, gold-bordered error panel on judge failure.

    Renders nothing while the debate has not reached the judgment stage.
    """
    if state.verdict is not None:
        _render_verdict_panel(state.verdict)
    elif state.judge_error is not None:
        _render_judge_failed(state)


def _render_verdict_panel(verdict: Verdict) -> None:
    if not verdict.parse_ok or verdict.winner not in ("PRO", "CON", "TIE"):
        _render_unparsed_verdict(verdict)
        return

    if verdict.winner == "PRO":
        winner_html = '<span class="aw-gold">PROPOSITION</span> WINS'
    elif verdict.winner == "CON":
        winner_html = '<span class="aw-gold">OPPOSITION</span> WINS'
    else:
        winner_html = "DEAD HEAT"

    pro_width = min(100, max(0, verdict.pro_score))
    con_width = min(100, max(0, verdict.con_score))

    cells: list[str] = []
    for title, text in (
        ("Explanation", verdict.explanation),
        ("Overall conclusion", verdict.conclusion),
        ("Strongest argument", verdict.strongest_argument),
        ("Weakest argument", verdict.weakest_argument),
    ):
        if text.strip():
            cells.append(
                f'<div class="aw-cell"><div class="aw-micro">{title}</div>'
                f'<div class="aw-cell-body">{escape(text)}</div></div>'
            )
    grid = f'<div class="aw-grid">{"".join(cells)}</div>' if cells else ""

    sections = ""
    if verdict.key_disagreements:
        items = "".join(f"<li>{escape(d)}</li>" for d in verdict.key_disagreements)
        sections += (
            '<div class="aw-section"><div class="aw-micro">Key disagreements</div>'
            f'<ul class="aw-list">{items}</ul></div>'
        )
    if verdict.fallacies:
        chips = "".join(f"<span>{escape(f)}</span>" for f in verdict.fallacies)
        sections += (
            '<div class="aw-section"><div class="aw-micro">Fallacies</div>'
            f'<div class="aw-chips">{chips}</div></div>'
        )

    st.markdown(
        _stable_html(f"""
        <div class="aw-verdict">
          <div class="aw-verdict-head">
            <span class="aw-micro aw-micro-gold">Verdict</span>
            <span class="aw-winner">{winner_html}</span>
          </div>
          <div class="aw-scores">
            <div class="aw-score-row">
              <span class="aw-score-label aw-micro">For</span>
              <div class="aw-score-track"><div class="aw-score-fill" style="width:{pro_width}%"></div></div>
              <span class="aw-score-num">{verdict.pro_score}</span>
            </div>
            <div class="aw-score-row">
              <span class="aw-score-label aw-micro">Against</span>
              <div class="aw-score-track"><div class="aw-score-fill aw-score-con" style="width:{con_width}%"></div></div>
              <span class="aw-score-num">{verdict.con_score}</span>
            </div>
          </div>
          {grid}
          {sections}
          <div class="aw-verdict-foot">
            <span class="aw-micro">Scores are model-generated qualitative assessments, not objective measurements.</span>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def _render_unparsed_verdict(verdict: Verdict) -> None:
    """The judge replied but the reply is not valid structured output."""
    st.markdown(
        _stable_html(f"""
        <div class="aw-verdict">
          <div class="aw-verdict-head">
            <span class="aw-micro aw-micro-gold">Verdict &#8212; unparsed judge reply</span>
          </div>
          <div class="aw-raw">{escape(verdict.raw_text)}</div>
          <div class="aw-verdict-foot">
            <span class="aw-micro">The judge's reply could not be parsed as structured output; the raw text is shown unmodified.</span>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def _render_judge_failed(state: DebateState) -> None:
    any_analysis = any(
        role in state.results and state.results[role].ok
        for role in (AgentRole.STRATEGIST, AgentRole.CHALLENGER, AgentRole.RESEARCHER, AgentRole.DEVILS_ADVOCATE)
    )
    note = (
        '<div class="aw-judge-note">The four analyses below remain available.</div>'
        if any_analysis
        else ""
    )
    st.markdown(
        _stable_html(f"""
        <div class="aw-verdict">
          <div class="aw-verdict-head">
            <span class="aw-micro aw-micro-gold">Verdict</span>
          </div>
          <div class="aw-err" style="margin-top:10px">{escape(state.judge_error or "")}</div>
          {note}
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        _stable_html("""
        <div class="aw-footer">
          <span class="aw-micro">AGENT WARS &#8212; Advanced AI course project</span>
          <span class="aw-micro">Five providers &#183; OpenAI-compatible endpoints</span>
        </div>
        """),
        unsafe_allow_html=True,
    )
