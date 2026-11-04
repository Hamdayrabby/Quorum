"""Visual QA harness: every card/verdict state with fabricated data.

Run: ``.venv/Scripts/python.exe -m streamlit run tests/ui_preview.py``

All content below is locally fabricated purely to exercise styling and the
interaction layer (typewriter, expand modal, copy, entrance animations). The
real app renders only what ``DebateOrchestrator`` emits; nothing here is
shipped to it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from core.config import AGENT_CONFIGS
from core.models import AgentResult, AgentRole, AgentStatus, DebateState, Verdict
from ui import components as ui
from ui import interactions
from ui.theme import inject, page_config

_PRO_TEXT = (
    "Remote work is structurally superior for knowledge economies. First, it converts "
    "commute time — nationally averaging 55 minutes per day — back into either labor or "
    "rest, and both raise output. Second, it widens the hiring pool from a commute radius "
    "to the whole time zone, which is the single largest untapped labor arbitrage available "
    "to mid-size firms. Third, distributed teams force written, asynchronous communication, "
    "and written decisions are auditable decisions: fewer meetings, fewer misunderstandings, "
    "a paper trail for every call. The office-era firm optimized for supervision; the "
    "remote-era firm optimizes for throughput, and throughput is what compounds."
)

_CON_TEXT = (
    "The proposition confuses absence of an office with absence of structure. Junior "
    "staff in distributed settings report slower skill formation precisely because the "
    "hallway apprenticeship — watching a senior negotiate a call — disappears. Innovation "
    "research consistently ties serendipitous encounter to novel combination of ideas, and "
    "video calls schedule serendipity out of existence. Finally, the productivity gains "
    "cited accrue mostly to senior individual contributors, while the coordination tax "
    "lands on managers and new hires. A policy that advantages one cohort while taxing "
    "another is not structurally superior; it is selectively superior."
)

_VERDICT = Verdict(
    winner="PRO",
    pro_score=78,
    con_score=64,
    explanation=(
        "The proposition's case compounds three independent mechanisms (time reclamation, "
        "labor-pool breadth, auditable async decisions) while the opposition's strongest "
        "material targets onboarding and serendipity — real costs, but mitigable ones. "
        "The opposition's strongest move, the cohort-distribution argument, lands but does "
        "not reverse the aggregate."
    ),
    conclusion=(
        "Remote work wins on aggregate throughput for knowledge economies, with a marked "
        "caveat: firms must deliberately engineer the apprenticeship and encounter "
        "structures that offices provided for free."
    ),
    strongest_argument=(
        "Written, asynchronous communication makes decisions auditable — a governance "
        "upgrade the opposition never contests."
    ),
    weakest_argument=(
        "The commute-time reclamation figure assumes workers reallocate time toward "
        "productive or restful uses; the evidence for that reallocation is thin."
    ),
    key_disagreements=[
        "Whether hallway serendipity is a real innovation driver or nostalgia with a citation.",
        "Whether the coordination tax falls evenly across seniority levels.",
    ],
    fallacies=["survivorship bias", "composition fallacy"],
    raw_text="",
    parse_ok=True,
)

_RAW_VERDICT = Verdict(
    winner="",
    raw_text=(
        "After weighing both sides, I find the proposition narrowly ahead. "
        '{"winner": "PRO", "pro_score": 71, "con_score": 66} — note the reply drifted '
        "into prose and was not parseable as structured output."
    ),
    parse_ok=False,
)


def _result(
    role: AgentRole,
    status: AgentStatus,
    content: str = "",
    error: str | None = None,
    latency: float = 4.2,
) -> AgentResult:
    cfg = AGENT_CONFIGS[role]
    return AgentResult(
        role=role,
        display_name=cfg.display_name,
        model_name=cfg.model,
        status=status,
        content=content,
        error=error,
        latency_s=latency,
    )


def _row(label: str, results: list[AgentResult]) -> None:
    st.markdown(
        f'<div class="aw-micro" style="margin:18px 2px 8px">{label}</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(results), gap="small")
    for i, (col, res) in enumerate(zip(cols, results)):
        with col:
            ui.render_agent_card(AGENT_CONFIGS[res.role], res, index=i)


def main() -> None:
    page_config()
    inject()
    interactions.inject()
    ui.render_header()

    st.markdown(
        '<div class="aw-banner"><div class="aw-micro aw-micro-warn">UI preview</div>'
        '<div class="aw-banner-body">All content on this page is fabricated locally to '
        "exercise styling and interactions — it is not a live debate and never touches the "
        'orchestrator or providers.</div></div>',
        unsafe_allow_html=True,
    )

    idle = [
        AgentResult(
            role=r, display_name=AGENT_CONFIGS[r].display_name, model_name=AGENT_CONFIGS[r].model
        )
        for r in AGENT_CONFIGS
    ]
    _row("1 — idle arena (all waiting)", idle)

    _row(
        "2 — mid-run: one done, one thinking, three queued",
        [
            _result(AgentRole.STRATEGIST, AgentStatus.COMPLETED, _PRO_TEXT, latency=6.1),
            _result(AgentRole.CHALLENGER, AgentStatus.THINKING),
            _result(AgentRole.RESEARCHER, AgentStatus.WAITING),
            _result(AgentRole.DEVILS_ADVOCATE, AgentStatus.WAITING),
            _result(AgentRole.SUPREME_JUDGE, AgentStatus.WAITING),
        ],
    )

    _row(
        "3 — completed, failed, judge thinking",
        [
            _result(AgentRole.STRATEGIST, AgentStatus.COMPLETED, _PRO_TEXT, latency=6.1),
            _result(AgentRole.CHALLENGER, AgentStatus.COMPLETED, _CON_TEXT, latency=5.4),
            _result(
                AgentRole.RESEARCHER,
                AgentStatus.FAILED,
                error="MISTRAL_API_KEY not set — Researcher (Mistral AI) has no API key.",
                latency=0.0,
            ),
            _result(AgentRole.DEVILS_ADVOCATE, AgentStatus.COMPLETED, _CON_TEXT[:280] + "…", latency=7.9),
            _result(AgentRole.SUPREME_JUDGE, AgentStatus.THINKING),
        ],
    )

    st.markdown('<div class="aw-micro" style="margin:18px 2px 8px">4 — stepper, phase 3 of 5</div>', unsafe_allow_html=True)
    mid = DebateState(topic="Remote work is better than office work", mode="Society")
    mid.results = {
        AgentRole.STRATEGIST: _result(AgentRole.STRATEGIST, AgentStatus.COMPLETED, _PRO_TEXT),
        AgentRole.CHALLENGER: _result(AgentRole.CHALLENGER, AgentStatus.COMPLETED, _CON_TEXT),
        AgentRole.RESEARCHER: _result(AgentRole.RESEARCHER, AgentStatus.THINKING),
    }
    ui.render_stepper(mid)

    st.markdown('<div class="aw-micro" style="margin:18px 2px 8px">5 — verdict (parsed)</div>', unsafe_allow_html=True)
    state_ok = DebateState(topic="Remote work is better than office work", mode="Society")
    state_ok.results = {r: _result(r, AgentStatus.COMPLETED, _PRO_TEXT) for r in AGENT_CONFIGS}
    state_ok.verdict = _VERDICT
    ui.render_verdict(state_ok)

    st.markdown('<div class="aw-micro" style="margin:18px 2px 8px">6 — unparsed judge reply</div>', unsafe_allow_html=True)
    ui.render_verdict(DebateState(verdict=_RAW_VERDICT, topic="t", mode="m"))

    st.markdown('<div class="aw-micro" style="margin:18px 2px 8px">7 — judge failed (analyses survive)</div>', unsafe_allow_html=True)
    fail_state = DebateState(topic="t", mode="m", judge_error="NVIDIA NIM returned 503 after 3 attempts.")
    fail_state.results = {r: _result(r, AgentStatus.COMPLETED, _PRO_TEXT) for r in AGENT_CONFIGS}
    ui.render_verdict(fail_state)

    ui.render_footer()


if __name__ == "__main__":
    main()
