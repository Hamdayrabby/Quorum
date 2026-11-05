"""Pure render functions for the Quorum arena.

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

# Per-agent glyph motion while the card is THINKING; applied as a class on
# the avatar glyph and animated only inside ``.is-thinking`` (see theme.py).
_GLYPH_MOTION: dict[str, str] = {
    "STRATEGIST": "gm-rotate",
    "CHALLENGER": "gm-lunge",
    "RESEARCHER": "gm-orbit",
    "DEVILS_ADVOCATE": "gm-wobble",
    "SUPREME_JUDGE": "gm-gleam",
}

# Claude-Code-style working verbs, cycled by a CSS ticker while THINKING.
# Each role gets its own vocabulary so the arena reads as five distinct minds.
_THINKING_VERBS: dict[str, tuple[str, ...]] = {
    "STRATEGIST": ("BUILDING CASE", "MARSHALLING EVIDENCE", "STEELMANNING"),
    "CHALLENGER": ("PROBING WEAKNESSES", "FORGING COUNTERS", "ATTACKING ASSUMPTIONS"),
    "RESEARCHER": ("SEARCHING THE WEB", "AUDITING CLAIMS", "TRACING SOURCES", "WEIGHING EVIDENCE"),
    "DEVILS_ADVOCATE": ("HUNTING BLIND SPOTS", "FLIPPING THE BOARD", "BENDING PERSPECTIVES"),
    "SUPREME_JUDGE": ("WEIGHING ARGUMENTS", "CROSS-CHECKING LOGIC", "DELIBERATING"),
}


def _avatar_html(cfg: AgentConfig, status: AgentStatus) -> str:
    """Avatar tile for one agent: glyph + status ring/orbit/check/animation.

    Status behavior is pure CSS keyed off the card's state class:
    waiting floats dimmed, thinking spins an orbit ring, completed pops a
    check badge (gated by the JS-added ``.aw-enter``), failed shakes once.
    """
    motion = _GLYPH_MOTION.get(cfg.role.name, "")
    return (
        f'<span class="aw-avatar {motion}" aria-hidden="true">'
        f'<span class="aw-avatar-glyph">{_agent_icon(cfg.role.name)}</span>'
        '<span class="aw-avatar-ring"></span>'
        '<span class="aw-avatar-orbit"><i></i></span>'
        '<span class="aw-avatar-check">&#10003;</span>'
        "</span>"
    )


def _status_tail(role_value: str, status: AgentStatus) -> str:
    """Status text area: a cycling verb ticker while working, else the label."""
    if status is not AgentStatus.THINKING:
        return status.value.upper()
    verbs = _THINKING_VERBS.get(role_value, ("THINKING",))
    items = "".join(f'<b class="aw-verb">{escape(v)}</b>' for v in verbs)
    return (
        f'<span class="aw-verbs" style="--verbs:{len(verbs)}">'
        f'<span class="aw-verbs-track">{items}</span></span>'
    )



_ICON_ATTRS = (
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round"'
)

# Brand mark: recreation of the Framer "Autonomous Loop" icon (24x24 line art —
# centre dot, looping arcs, corner brackets). Same visual language as the
# per-agent icons below: stroke-only, currentColor, rounded caps.
_BRAND_ICON = (
    f'<svg class="aw-brand-svg" {_ICON_ATTRS} aria-hidden="true">'
    '<circle cx="12" cy="12" r="2.6"/>'
    '<path d="M20 8.99C18.94 6.08 16.39 3.99 13.33 3.51C10.27 3.03 7.2 4.24 5.3 6.69"/>'
    '<path d="M4 15C5.06 17.91 7.61 20 10.67 20.48C13.73 20.96 16.8 19.76 18.7 17.31"/>'
    '<path d="M5.3 3.5v3.2h3.2M18.7 20.5v-3.2h-3.2"/>'
    '</svg>'
)

# Per-agent icons (24x24, stroke-only) in the same language as the brand mark.
_AGENT_ICONS: dict[str, str] = {
    "STRATEGIST": (
        '<path d="M12 3.5 20 12l-8 8.5L4 12z"/>'
        '<circle cx="12" cy="12" r="1.4"/>'
    ),
    "CHALLENGER": (
        '<path d="M3.5 7.5h13M16.5 7.5l-4-4M16.5 7.5l-4 4"/>'
        '<path d="M20.5 16.5h-13M7.5 16.5l4-4M7.5 16.5l4 4"/>'
    ),
    "RESEARCHER": (
        '<circle cx="10.5" cy="10.5" r="6"/>'
        '<path d="M15 15l5.5 5.5"/>'
        '<path d="M7.5 10.5a3 3 0 0 1 6 0"/>'
    ),
    "DEVILS_ADVOCATE": (
        '<path d="M4.5 12a7.5 7.5 0 0 1 12.8-5.3"/>'
        '<path d="M17.3 3.5v3.2h-3.2"/>'
        '<path d="M19.5 12a7.5 7.5 0 0 1-12.8 5.3"/>'
        '<path d="M6.7 20.5v-3.2h3.2"/>'
    ),
    "SUPREME_JUDGE": (
        '<path d="M12 4v15M7.5 19h9M12 6.5l-6 1.5M12 6.5l6 1.5"/>'
        '<path d="M3 13.5a3 3 0 0 0 6 0L6 8l-3 5.5z"/>'
        '<path d="M15 13.5a3 3 0 0 0 6 0L18 8l-3 5.5z"/>'
    ),
}


def _agent_icon(role_name: str) -> str:
    """Inline stroke-only SVG for one agent, matching the brand mark style."""
    paths = _AGENT_ICONS.get(role_name, '<circle cx="12" cy="12" r="4"/>')
    return f'<svg {_ICON_ATTRS} aria-hidden="true">{paths}</svg>'


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
            <span class="aw-brand-mark">{_BRAND_ICON}</span>
            <span class="aw-wordmark">QUO<span class="aw-gold">RUM</span></span>
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
          <div class="aw-banner-body">{escape(", ".join(missing_keys))} no API key &#8212;
          those agents will fail. Add keys to .env or the sidebar Settings.</div>
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
        f'{recap}<div class="aw-stepper" data-phase="{phase}">{"".join(steps)}</div>',
        unsafe_allow_html=True,
    )


def render_agent_card(cfg: AgentConfig, result: AgentResult | None, index: int = 0) -> None:
    """One agent card: identity, live status pill and output or error.

    ``index`` staggers the entrance animation (0-4). The card root carries
    the status class plus data attributes consumed by ``ui/interactions.py``
    (expand modal, copy, typewriter reveal); rendering stays declarative.
    """
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

    # Researcher sources: quiet clickable chips (host label) under the output.
    sources_html = ""
    if status is AgentStatus.COMPLETED and result is not None and result.sources:
        chips = []
        for title, url in result.sources[:5]:
            host = url.split("//")[-1].split("/")[0].replace("www.", "")
            chips.append(
                f'<a class="aw-src" href="{escape(url, quote=True)}" target="_blank" '
                f'rel="noopener noreferrer" title="{escape(title)}">{escape(host)}</a>'
            )
        sources_html = (
            '<div class="aw-sources"><span class="aw-micro aw-sources-label">Sources</span>'
            f'{"".join(chips)}</div>'
        )

    has_content = bool(body)
    eq = (
        '<span class="aw-eq" title="Reasoning"><span></span><span></span><span></span></span>'
        if status is AgentStatus.THINKING
        else ""
    )
    expand = (
        '<button class="aw-expand" type="button" title="Read full output" '
        'aria-label="Read full output">&#x2922;</button>'
        if has_content
        else ""
    )
    foot = ""
    if status is AgentStatus.COMPLETED and result is not None:
        copy_btn = '<button class="aw-copy" type="button">Copy</button>'
        foot = (
            '<div class="aw-card-foot">'
            f'<span class="aw-latency">{result.latency_s:.1f}s</span>{copy_btn}</div>'
        )

    avatar = _avatar_html(cfg, status)
    st.markdown(
        _stable_html(f"""
        <div class="aw-card {pill_class}" data-role="{escape(cfg.role.value)}" data-name="{escape(cfg.display_name)}" data-model="{escape(cfg.model)}" data-provider="{escape(cfg.provider)}" style="--accent:{cfg.accent};--i:{index}">
          <div class="aw-card-line"></div>
          <div class="aw-card-head">
            {avatar}
            <span class="aw-name">{escape(cfg.display_name)}</span>
            {eq}{expand}
          </div>
          <span class="aw-chip" title="{escape(cfg.provider)}">{escape(cfg.model)}</span>
          <div class="aw-card-tag aw-micro">{escape(cfg.tagline)}</div>
          <span class="aw-pill {pill_class}">
            <span class="aw-pill-dot"></span>{_status_tail(cfg.role.name, status)}
          </span>
          {body}
          {sources_html}
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
        _render_verdict_panel(state)
    elif state.judge_error is not None:
        _render_judge_failed(state)


def _render_verdict_panel(state: DebateState) -> None:
    verdict = state.verdict
    if verdict is None:  # render_verdict only calls us when a verdict exists
        return
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

    def side_model(role: AgentRole) -> str:
        result = state.get(role)
        return result.model_name if result is not None and result.ok else ""

    pro_model = escape(side_model(AgentRole.STRATEGIST))
    con_model = escape(side_model(AgentRole.CHALLENGER))
    pro_chip = f'<span class="aw-score-model" title="{pro_model}">{pro_model}</span>' if pro_model else ""
    con_chip = f'<span class="aw-score-model" title="{con_model}">{con_model}</span>' if con_model else ""
    verified_chip = (
        '<span class="aw-verified">SELF-CHECKED</span>' if verdict.verified else ""
    )

    cells: list[str] = []
    for i, (title, text) in enumerate(
        (
            ("Explanation", verdict.explanation),
            ("Overall conclusion", verdict.conclusion),
            ("Strongest argument", verdict.strongest_argument),
            ("Weakest argument", verdict.weakest_argument),
        )
    ):
        if text.strip():
            cells.append(
                f'<div class="aw-cell" style="--i:{i}"><div class="aw-micro">{title}</div>'
                f'<div class="aw-cell-body">{escape(text)}</div></div>'
            )
    best_answer = (
        '<div class="aw-best">'
        '<div class="aw-micro aw-micro-gold">Best answer after all four analyses</div>'
        f'<div class="aw-best-text">{escape(verdict.best_answer)}</div>'
        "</div>"
        if verdict.best_answer.strip()
        else ""
    )
    grid = f'<div class="aw-grid">{"".join(cells)}</div>' if cells else ""

    sections = ""
    section_i = 0
    if verdict.key_disagreements:
        items = "".join(f"<li>{escape(d)}</li>" for d in verdict.key_disagreements)
        sections += (
            f'<div class="aw-section" style="--i:{section_i}"><div class="aw-micro">Key disagreements</div>'
            f'<ul class="aw-list">{items}</ul></div>'
        )
        section_i += 1
    if verdict.fallacies:
        chips = "".join(f"<span>{escape(f)}</span>" for f in verdict.fallacies)
        sections += (
            f'<div class="aw-section" style="--i:{section_i}"><div class="aw-micro">Fallacies</div>'
            f'<div class="aw-chips">{chips}</div></div>'
        )

    st.markdown(
        _stable_html(f"""
        <div class="aw-verdict">
          <div class="aw-verdict-head">
            <span class="aw-micro aw-micro-gold">Verdict</span>
            <span class="aw-winner">{winner_html}</span>
            {verified_chip}
          </div>
          <div class="aw-scores">
            <div class="aw-score-row">
              <span class="aw-score-label aw-micro">For</span>
              {pro_chip}
              <div class="aw-score-track"><div class="aw-score-fill" style="width:{pro_width}%"></div></div>
              <span class="aw-score-num">{verdict.pro_score}</span>
            </div>
            <div class="aw-score-row">
              <span class="aw-score-label aw-micro">Against</span>
              {con_chip}
              <div class="aw-score-track"><div class="aw-score-fill aw-score-con" style="width:{con_width}%"></div></div>
              <span class="aw-score-num">{verdict.con_score}</span>
            </div>
          </div>
          {best_answer}
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
          <span class="aw-micro">Five providers &#183; OpenAI-compatible endpoints</span>
        </div>
        """),
        unsafe_allow_html=True,
    )
