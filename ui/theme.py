"""Design tokens and stylesheet for the Agent Wars arena.

This module owns the single source of truth for the dark dashboard look:
design tokens as CSS custom properties, the component classes referenced by
``ui/components.py``, and minimal overrides for the native Streamlit widgets
(text input, pills, primary button). No HTML structure lives here.
"""
from __future__ import annotations

import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg: #0A0E14;
  --surface: #10151E;
  --surface-2: #151C27;
  --border: #1D2634;
  --border-strong: #2A3648;
  --text: #E8EDF5;
  --text-2: #97A3B6;
  --text-3: #5F6C80;
  --gold: #D4AF37;
  --ok: #4ADE80;
  --warn: #F5B94A;
  --err: #F87171;
  --info: #5B9DFF;
  --font-display: "Space Grotesk", "Segoe UI", system-ui, sans-serif;
  --font-body: "Inter", "Segoe UI", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "Cascadia Code", Consolas, monospace;
}

/* ---------- Streamlit chrome ---------- */
.stApp {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
}
header[data-testid="stHeader"] { background: transparent; }
header[data-testid="stHeader"] [data-testid="stToolbar"] { display: none; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2.2rem 1.4rem 2.5rem; max-width: 1280px; }
.stMarkdown, .stMarkdown p { font-family: var(--font-body); color: var(--text-2); }

/* ---------- Micro-label (shared) ---------- */
.aw-micro {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
  line-height: 1.4;
}
.aw-micro-gold { color: var(--gold); }
.aw-micro-warn { color: var(--warn); }

/* ---------- Header bar ---------- */
.aw-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 6px 2px 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 22px;
}
.aw-brand { display: flex; align-items: center; gap: 16px; min-width: 0; }
.aw-wordmark {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 34px;
  letter-spacing: 0.06em;
  line-height: 1;
  color: var(--text);
  white-space: nowrap;
}
.aw-wordmark .aw-gold { color: var(--gold); }
.aw-vdivider { width: 1px; height: 24px; background: var(--border-strong); flex: 0 0 auto; }
.aw-tagline { white-space: nowrap; }
.aw-dots { display: flex; align-items: center; gap: 8px; }
.aw-dot { width: 8px; height: 8px; border-radius: 4px; }

/* ---------- Missing-keys banner ---------- */
.aw-banner {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--warn);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 18px;
}
.aw-banner-body { font-size: 13px; line-height: 1.55; color: var(--text-2); margin-top: 4px; }

/* ---------- Stage stepper ---------- */
.aw-stepper { display: flex; align-items: center; margin: 6px 0 22px; }
.aw-step { display: flex; align-items: center; flex: 1 1 0; min-width: 0; }
.aw-step:last-child { flex: 0 0 auto; }
.aw-step-dot {
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  border-radius: 11px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-3);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}
.aw-step.is-done .aw-step-dot {
  background: var(--step-accent);
  border-color: var(--step-accent);
  color: #0A0E14;
}
.aw-step.is-active .aw-step-dot {
  border-color: var(--step-accent);
  color: var(--text);
  animation: aw-pulse 1.2s ease-in-out infinite;
}
.aw-step-line { flex: 1 1 0; height: 1px; background: var(--border); margin: 0 10px; min-width: 20px; }
.aw-step.is-done .aw-step-line { background: var(--border-strong); }
.aw-step-label {
  margin-left: 8px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
  white-space: nowrap;
}
.aw-step.is-active .aw-step-label { color: var(--text); }
.aw-step.is-done .aw-step-label { color: var(--text-2); }
@keyframes aw-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.55; } }
.aw-recap {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

/* ---------- Agent card ---------- */
.aw-card {
  position: relative;
  box-sizing: border-box;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 14px 12px;
  min-height: 340px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.aw-card-line {
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  height: 2px;
  border-radius: 12px 12px 0 0;
  background: var(--accent);
}
.aw-card-head { display: flex; align-items: center; gap: 8px; min-width: 0; }
.aw-glyph { color: var(--accent); font-size: 18px; line-height: 1; flex: 0 0 auto; }
.aw-name {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.aw-chip {
  display: inline-block;
  align-self: flex-start;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-2);
  background: var(--surface-2);
  border-radius: 6px;
  padding: 4px 8px;
}
.aw-card-tag { min-height: 26px; }
.aw-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  align-self: flex-start;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
}
.aw-pill-dot { width: 6px; height: 6px; border-radius: 3px; background: var(--text-3); flex: 0 0 auto; }
.aw-pill.is-thinking { color: var(--warn); }
.aw-pill.is-thinking .aw-pill-dot { background: var(--warn); animation: aw-pulse 1.2s ease-in-out infinite; }
.aw-pill.is-completed { color: var(--ok); }
.aw-pill.is-completed .aw-pill-dot { background: var(--ok); }
.aw-pill.is-failed { color: var(--err); }
.aw-pill.is-failed .aw-pill-dot { background: var(--err); }
.aw-output {
  flex: 1 1 auto;
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-2);
  white-space: pre-wrap;
  padding-right: 6px;
}
.aw-err { font-size: 12px; line-height: 1.55; color: var(--err); white-space: pre-wrap; }
.aw-card-foot { margin-top: auto; display: flex; justify-content: flex-end; min-height: 14px; }
.aw-latency { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.12em; color: var(--text-3); }
.aw-output::-webkit-scrollbar { width: 6px; }
.aw-output::-webkit-scrollbar-track { background: transparent; }
.aw-output::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 3px; }
.aw-output { scrollbar-width: thin; scrollbar-color: var(--border-strong) transparent; }

/* ---------- Verdict panel ---------- */
.aw-verdict {
  position: relative;
  box-sizing: border-box;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  padding: 20px 22px 16px;
  margin-top: 6px;
}
.aw-verdict::before {
  content: "";
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  height: 2px;
  border-radius: 12px 12px 0 0;
  background: var(--gold);
}
.aw-verdict-head { display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap; }
.aw-winner {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 24px;
  line-height: 1.2;
  color: #FFFFFF;
  letter-spacing: 0.02em;
}
.aw-winner .aw-gold { color: var(--gold); }
.aw-scores { display: flex; flex-direction: column; gap: 10px; margin: 16px 0 4px; max-width: 560px; }
.aw-score-row { display: flex; align-items: center; gap: 12px; }
.aw-score-label { width: 72px; flex: 0 0 auto; }
.aw-score-track { flex: 1 1 auto; height: 8px; border-radius: 4px; background: var(--surface-2); overflow: hidden; }
.aw-score-fill { height: 100%; border-radius: 4px; background: var(--gold); }
.aw-score-fill.aw-score-con { background: rgba(248, 113, 113, 0.55); }
.aw-score-num { width: 44px; text-align: right; font-family: var(--font-mono); font-size: 18px; color: var(--text); }
.aw-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 24px; margin-top: 18px; }
.aw-cell { min-width: 0; }
.aw-cell .aw-micro { margin-bottom: 6px; }
.aw-cell-body { font-size: 13px; line-height: 1.6; color: var(--text-2); }
.aw-section { margin-top: 18px; }
.aw-list { list-style: none; margin: 2px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.aw-list li {
  border-left: 3px solid var(--gold);
  padding: 1px 0 1px 12px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-2);
}
.aw-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 2px; }
.aw-chips span {
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  padding: 3px 10px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-2);
}
.aw-raw {
  margin-top: 14px;
  max-height: 320px;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-2);
  white-space: pre-wrap;
}
.aw-verdict-foot { margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--border); }
.aw-judge-note { margin-top: 10px; font-size: 13px; line-height: 1.55; color: var(--text-2); }

/* ---------- Input zone ---------- */
.stTextInput input {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
  padding: 12px 14px !important;
  font-size: 14px !important;
}
.stTextInput input:focus {
  border-color: var(--border-strong) !important;
  box-shadow: none !important;
}
.stTextInput input::placeholder { color: var(--text-3) !important; }
[data-testid="stPills"] button,
div[data-testid="stPills"] button {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  color: var(--text-2) !important;
  font-size: 12px !important;
  padding: 5px 12px !important;
  min-height: 0 !important;
}
[data-testid="stPills"] button:hover {
  border-color: var(--border-strong) !important;
  color: var(--text) !important;
}
[data-testid="stPills"] button[aria-pressed="true"],
[data-testid="stPills"] button[aria-checked="true"] {
  border-color: var(--info) !important;
  color: var(--text) !important;
}
.stButton > button {
  background: var(--text) !important;
  color: #0A0E14 !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 12px 24px !important;
  font-family: var(--font-display) !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.stButton > button:hover {
  background: rgba(232, 237, 245, 0.88) !important;
  color: #0A0E14 !important;
  border: none !important;
}
.stButton > button:disabled {
  background: var(--text) !important;
  color: #0A0E14 !important;
  opacity: 0.4;
}
.aw-input-note { margin-top: 10px; font-size: 12px; line-height: 1.5; color: var(--text-3); }
.aw-input-note-err { color: var(--err); }

/* ---------- Footer ---------- */
.aw-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid var(--border);
  padding: 14px 2px 4px;
  margin-top: 26px;
}
"""


def inject() -> None:
    """Apply the stylesheet exactly once per script run."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def page_config() -> None:
    """Streamlit page settings; must run before any other st command."""
    st.set_page_config(
        page_title="Agent Wars",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
