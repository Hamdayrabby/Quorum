"""Design tokens and stylesheet for the Quorum arena.

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
/* Keep the header toolbar rendered: it hosts the expand-sidebar arrow that
   the Settings panel depends on when Streamlit restores a collapsed sidebar
   from the browser's stored preference. Hide only the chrome we do not want. */
header[data-testid="stHeader"] [data-testid="stToolbar"] { display: flex; }
header[data-testid="stHeader"] [data-testid="stStatusWidget"],
header[data-testid="stHeader"] [data-testid="stAppDeployButton"],
header[data-testid="stHeader"] [data-testid="stMainMenuButton"] { display: none !important; }
footer { visibility: hidden; }
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
  padding: 4px 2px 14px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 18px;
}
.aw-brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.aw-brand-mark { display: inline-flex; color: var(--gold); flex: 0 0 auto; }
.aw-brand-mark svg { width: 26px; height: 26px; display: block; transition: transform 0.4s ease; }
.aw-brand-mark:hover svg { transform: rotate(180deg); }
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
.aw-stepper { display: flex; align-items: center; margin: 10px 0 20px; }
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
  min-height: 300px;
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
.aw-card-head { display: flex; align-items: center; gap: 10px; min-width: 0; }
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
.aw-card-tag { min-height: 26px; margin: 2px 0 4px; }
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
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-2);
  white-space: pre-wrap;
  padding-right: 6px;
  /* Condensed card view: long audits clamp to five lines; the expand modal
     copies textContent (ui/interactions.py), so it still shows the full text. */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
  overflow: hidden;
}
/* Agent sources: quiet clickable host chips under the Researcher output. */
.aw-sources {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: -2px;
}
.aw-sources-label { margin-right: 2px; }
.aw-src {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 3px 8px;
  text-decoration: none;
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.aw-src:hover { color: var(--accent); border-color: color-mix(in srgb, var(--accent) 45%, var(--border)); }
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
.aw-best {
  margin-top: 16px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--border));
  border-left: 3px solid var(--gold);
  border-radius: 10px;
  background: color-mix(in srgb, var(--gold) 5%, var(--surface));
}
.aw-best .aw-micro { margin-bottom: 8px; }
.aw-best-text { font-size: 14px; line-height: 1.7; color: var(--text); }

.aw-verified {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.14em;
  color: var(--gold);
  border: 1px solid color-mix(in srgb, var(--gold) 45%, transparent);
  border-radius: 6px;
  padding: 3px 8px;
  white-space: nowrap;
}
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

/* ---------- Motion & interaction layer ----------
   Entrance animations (rise, settle, shake, fill, winner reveal) play only
   under ``.aw-enter``, which ``ui/interactions.py`` adds when a rendered
   element's signature is new for its slot — Streamlit rebuilds the DOM on
   every pipeline update and replaying entrances on every rebuild would read
   as flicker. Continuous state animations (thinking border, equalizer,
   pulses, header dots) are unconditional. Without the injected script the
   arena is fully static but correct: progressive enhancement only. */

@property --aw-angle { syntax: "<angle>"; initial-value: 0deg; inherits: false; }

@keyframes aw-rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes aw-settle {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent) 32%, transparent); }
  100% { box-shadow: 0 0 0 16px transparent; }
}
@keyframes aw-shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-5px); } 40% { transform: translateX(4px); }
  60% { transform: translateX(-3px); } 80% { transform: translateX(2px); }
}
@keyframes aw-fill { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes aw-winner-in { from { opacity: 0; letter-spacing: 0.16em; } to { opacity: 1; letter-spacing: 0.02em; } }
@keyframes aw-fade { from { opacity: 0; } to { opacity: 1; } }
@keyframes aw-panel-in { from { opacity: 0; transform: translateY(12px) scale(0.975); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes aw-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-2px); } }
@keyframes aw-breathe { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.78); } }
@keyframes aw-eq { 0%, 100% { transform: scaleY(0.3); } 50% { transform: scaleY(1); } }
@keyframes aw-line-slide { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@keyframes aw-spin-border { to { --aw-angle: 360deg; } }
@keyframes aw-caret { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes aw-ping { from { box-shadow: 0 0 0 0 color-mix(in srgb, var(--step-accent) 45%, transparent); } to { box-shadow: 0 0 0 9px transparent; } }
@keyframes aw-pop { 0% { transform: scale(0.4); } 70% { transform: scale(1.18); } 100% { transform: scale(1); } }
@keyframes aw-gm-rotate { to { transform: rotate(360deg); } }
@keyframes aw-gm-lunge { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }
@keyframes aw-gm-orbit { to { transform: rotate(-360deg); } }
@keyframes aw-gm-wobble { 0%, 100% { transform: rotate(-9deg); } 50% { transform: rotate(9deg); } }
@keyframes aw-gm-gleam {
  0%, 100% { opacity: 1; text-shadow: 0 0 0 transparent; }
  50% { opacity: 0.8; text-shadow: 0 0 14px color-mix(in srgb, var(--accent) 65%, transparent); }
}

/* --- header: five minds breathing, staggered --- */
.aw-dots .aw-dot { animation: aw-breathe 3.6s ease-in-out infinite; }
.aw-dots .aw-dot:nth-child(2) { animation-delay: 0.25s; }
.aw-dots .aw-dot:nth-child(3) { animation-delay: 0.5s; }
.aw-dots .aw-dot:nth-child(4) { animation-delay: 0.75s; }
.aw-dots .aw-dot:nth-child(5) { animation-delay: 1s; }

/* --- card: hover lift + focus --- */
.aw-card { transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease; }
.aw-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--accent) 42%, var(--border));
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5), 0 0 22px color-mix(in srgb, var(--accent) 12%, transparent);
}
.aw-glyph { transition: transform 0.18s ease; }
.aw-card:hover .aw-glyph { transform: scale(1.14); }

/* --- card: waiting (queued agents stay faintly alive) --- */
.aw-card.is-waiting { opacity: 0.88; min-height: 232px; }
.aw-card.is-waiting .aw-glyph { opacity: 0.55; animation: aw-float 3.6s ease-in-out infinite; }
.aw-card.is-waiting .aw-card-line { opacity: 0.45; }

/* --- card: thinking (the showpiece) --- */
.aw-card.is-thinking { border-color: transparent; }
.aw-card.is-thinking::before {
  content: "";
  position: absolute;
  inset: -1px;
  border-radius: 13px;
  padding: 1px;
  background: conic-gradient(from var(--aw-angle), transparent 0deg, transparent 230deg, var(--accent) 310deg, transparent 360deg);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
  animation: aw-spin-border 2.6s linear infinite;
  pointer-events: none;
}
.aw-card.is-thinking::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 12px;
  pointer-events: none;
  background: linear-gradient(105deg, transparent 42%, color-mix(in srgb, var(--accent) 9%, transparent) 50%, transparent 58%);
  background-size: 220% 100%;
  animation: aw-line-slide 2.4s ease-in-out infinite;
}
.aw-card.is-thinking .aw-card-line {
  background: linear-gradient(90deg, transparent 0%, var(--accent) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: aw-line-slide 1.8s linear infinite;
}

/* per-agent glyph motion while thinking (class comes from components.py) */
.aw-card.is-thinking .gm-rotate { animation: aw-gm-rotate 1.6s linear infinite; }
.aw-card.is-thinking .gm-lunge { animation: aw-gm-lunge 0.9s ease-in-out infinite; }
.aw-card.is-thinking .gm-orbit { animation: aw-gm-orbit 2.2s linear infinite; }
.aw-card.is-thinking .gm-wobble { animation: aw-gm-wobble 1.1s ease-in-out infinite; }
.aw-card.is-thinking .gm-gleam { animation: aw-gm-gleam 1.4s ease-in-out infinite; }

/* --- agent avatar: identity tile with per-status behavior ---
   waiting: dimmed + floating glyph · thinking: orbit ring + travelling dot
   completed: check badge pops (JS-gated via .aw-enter) · failed: red tile */
.aw-card-head .aw-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--accent) 34%, var(--border));
  background:
    radial-gradient(120% 120% at 25% 20%, color-mix(in srgb, var(--accent) 16%, transparent), transparent 60%),
    var(--surface-2);
  color: var(--accent);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}
.aw-card:hover .aw-avatar {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--accent) 55%, var(--border));
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35), 0 0 14px color-mix(in srgb, var(--accent) 18%, transparent);
}
.aw-avatar-glyph { display: inline-flex; transform-origin: center; transition: transform 0.18s ease; }
.aw-avatar-glyph svg { width: 20px; height: 20px; display: block; }
.aw-card:hover .aw-avatar-glyph { transform: scale(1.12); }

.aw-avatar-ring,
.aw-avatar-orbit {
  position: absolute;
  inset: -4px;
  border-radius: 14px;
  opacity: 0;
  pointer-events: none;
}
.aw-avatar-ring { border: 1px dashed color-mix(in srgb, var(--accent) 45%, transparent); }
.aw-avatar-orbit i {
  position: absolute;
  top: -2px;
  left: 50%;
  width: 5px;
  height: 5px;
  margin-left: -2.5px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
}

.aw-card.is-waiting .aw-avatar { opacity: 0.6; }
.aw-card.is-waiting .aw-avatar-glyph { animation: aw-float 3.6s ease-in-out infinite; }

.aw-card.is-thinking .aw-avatar {
  border-color: color-mix(in srgb, var(--accent) 70%, transparent);
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--accent) 22%, transparent),
    0 0 22px color-mix(in srgb, var(--accent) 22%, transparent);
}
.aw-card.is-thinking .aw-avatar-ring { opacity: 1; animation: aw-avatar-rotate 6s linear infinite; }
.aw-card.is-thinking .aw-avatar-orbit { opacity: 1; animation: aw-avatar-rotate 2.4s linear infinite; }
@keyframes aw-avatar-rotate { to { transform: rotate(360deg); } }

.aw-avatar-check {
  position: absolute;
  right: -4px;
  bottom: -4px;
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 9px;
  font-weight: 700;
  color: #0a0e14;
  background: var(--ok);
  opacity: 0;
  transform: scale(0.4);
}
.aw-card.is-completed .aw-avatar-check { opacity: 1; transform: scale(1); }
.aw-card.aw-enter.is-completed .aw-avatar-check {
  animation: aw-pop 0.45s cubic-bezier(0.2, 0.8, 0.3, 1.2) both;
  animation-delay: 0.2s;
}
.aw-card.is-failed .aw-avatar {
  border-color: color-mix(in srgb, var(--err) 55%, var(--border));
  color: var(--err);
  background: color-mix(in srgb, var(--err) 8%, var(--surface-2));
}
.aw-card.aw-enter.is-failed .aw-avatar { animation: aw-shake 0.5s ease-in-out both; animation-delay: 0.25s; }

/* Claude-Code-style verb ticker in the thinking pill: a static 1-line
   window with an inner track that rolls through this agent's working
   verbs, one step per ~1.6s. The animation lives on the track — animating
   the window itself would drag content outside the clip. */
.aw-pill .aw-verbs {
  display: inline-flex;
  height: 14px;
  overflow: hidden;
}
.aw-pill .aw-verbs-track {
  display: flex;
  flex-direction: column;
}
.aw-pill .aw-verb {
  display: block;
  height: 14px;
  line-height: 14px;
  font-weight: 500;
  white-space: nowrap;
}
.aw-pill.is-thinking .aw-verbs-track {
  animation: aw-verbs-roll calc(var(--verbs) * 1.6s) steps(var(--verbs)) infinite;
}
@keyframes aw-verbs-roll { to { transform: translateY(calc(var(--verbs) * -14px)); } }

/* thinking equalizer: three accent bars beside the agent name */
.aw-eq { display: inline-flex; align-items: flex-end; gap: 3px; height: 14px; margin-left: auto; }
.aw-eq span {
  width: 3px;
  height: 100%;
  border-radius: 2px;
  background: var(--accent);
  transform-origin: bottom;
  animation: aw-eq 1s ease-in-out infinite;
}
.aw-eq span:nth-child(2) { animation-delay: 0.18s; }
.aw-eq span:nth-child(3) { animation-delay: 0.36s; }

/* --- card: entrance / settle / shake (JS-gated via .aw-enter) --- */
.aw-card.aw-enter { animation: aw-rise 0.5s cubic-bezier(0.16, 0.84, 0.3, 1) both; animation-delay: calc(var(--i, 0) * 70ms); }
.aw-card.aw-enter.is-completed {
  animation: aw-rise 0.5s cubic-bezier(0.16, 0.84, 0.3, 1) both, aw-settle 1s ease-out both;
  animation-delay: calc(var(--i, 0) * 70ms), calc(var(--i, 0) * 70ms + 0.25s);
}
.aw-card.aw-enter.is-failed {
  animation: aw-rise 0.5s cubic-bezier(0.16, 0.84, 0.3, 1) both, aw-shake 0.45s ease-in-out both;
  animation-delay: calc(var(--i, 0) * 70ms), calc(var(--i, 0) * 70ms + 0.4s);
}

/* --- typewriter caret --- */
.aw-caret {
  display: inline-block;
  width: 7px;
  height: 1em;
  margin-left: 2px;
  vertical-align: -2px;
  background: var(--accent);
  animation: aw-caret 0.8s steps(1) infinite;
}

/* --- card: expand + copy affordances --- */
.aw-expand, .aw-copy {
  font-family: var(--font-mono);
  cursor: pointer;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text-3);
  border-radius: 6px;
  transition: color 0.15s ease, border-color 0.15s ease, opacity 0.15s ease;
}
.aw-expand { margin-left: auto; width: 22px; height: 22px; font-size: 11px; line-height: 1; opacity: 0; flex: 0 0 auto; }
.aw-card:hover .aw-expand, .aw-expand:focus-visible { opacity: 1; }
.aw-expand:hover { color: var(--text); border-color: var(--border-strong); }
.aw-copy { font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; padding: 4px 9px; line-height: 1.2; }
.aw-copy:hover { color: var(--text); border-color: color-mix(in srgb, var(--accent) 45%, var(--border)); }
.aw-copy.is-copied { color: var(--ok); border-color: color-mix(in srgb, var(--ok) 45%, var(--border)); }
.aw-expand:focus-visible, .aw-copy:focus-visible { outline: 1px solid var(--accent); outline-offset: 2px; }
.aw-card-foot { gap: 8px; align-items: center; }

/* --- stepper: entrance pop + active ping (JS-gated) --- */
.aw-stepper.aw-enter .aw-step.is-done .aw-step-dot { animation: aw-pop 0.45s cubic-bezier(0.2, 0.9, 0.3, 1.4) both; }
.aw-stepper.aw-enter .aw-step.is-active .aw-step-dot { animation: aw-pulse 1.2s ease-in-out infinite, aw-ping 1.6s ease-out infinite; }

/* --- verdict: entrance choreography (JS-gated) --- */
.aw-verdict.aw-enter { animation: aw-rise 0.55s cubic-bezier(0.16, 0.84, 0.3, 1) both; }
.aw-verdict.aw-enter::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  border-radius: 12px 12px 0 0;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  background-size: 200% 100%;
  animation: aw-line-slide 1.3s ease-out both;
}
.aw-verdict.aw-enter .aw-winner { animation: aw-winner-in 0.8s 0.25s cubic-bezier(0.16, 0.84, 0.3, 1) both; }
.aw-verdict.aw-enter .aw-score-fill { transform-origin: left; animation: aw-fill 1s 0.3s cubic-bezier(0.2, 0.75, 0.25, 1) both; }
.aw-verdict.aw-enter .aw-cell { animation: aw-rise 0.5s both; animation-delay: calc(0.35s + var(--i, 0) * 80ms); }
.aw-verdict.aw-enter .aw-section { animation: aw-rise 0.5s both; animation-delay: calc(0.55s + var(--i, 0) * 80ms); }

/* --- expanded-reading modal (built by ui/interactions.py) --- */
.aw-modal {
  position: fixed;
  inset: 0;
  z-index: 1000000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 34px;
  background: rgba(5, 8, 13, 0.72);
  backdrop-filter: blur(7px);
  animation: aw-fade 0.16s ease both;
}
.aw-modal-panel {
  position: relative;
  width: min(840px, 94vw);
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: 14px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6);
  animation: aw-panel-in 0.24s cubic-bezier(0.18, 0.9, 0.28, 1.04) both;
  overflow: hidden;
}
.aw-modal-panel::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--accent, var(--gold)); }
.aw-modal-head { display: flex; align-items: center; gap: 10px; padding: 14px 18px; border-bottom: 1px solid var(--border); flex: 0 0 auto; }
.aw-modal-head .aw-glyph { font-size: 16px; }
.aw-modal-head .aw-name { font-size: 15px; }
.aw-modal-head .aw-pill { margin-left: 4px; }
.aw-modal-close {
  margin-left: auto;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-3);
  font-size: 13px;
  cursor: pointer;
  line-height: 1;
  flex: 0 0 auto;
}
.aw-modal-close:hover { color: var(--text); border-color: var(--border-strong); }
.aw-modal-body {
  padding: 16px 18px;
  overflow-y: auto;
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--text-2);
  white-space: pre-wrap;
}
.aw-modal-body::-webkit-scrollbar { width: 6px; }
.aw-modal-body::-webkit-scrollbar-track { background: transparent; }
.aw-modal-body::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 3px; }
.aw-modal-foot { display: flex; align-items: center; gap: 10px; padding: 10px 18px; border-top: 1px solid var(--border); flex: 0 0 auto; }
.aw-modal-foot .aw-copy { margin-left: auto; }

/* ---------- Sidebar settings ----------
   Same tokens as the main arena, scoped to the sidebar so the arena is
   untouched: surface-2 fields, 1px borders, mono micro-labels, ok/err pills. */
.aw-sidebar-title { margin-bottom: 2px; }
.aw-sidebar-help { font-size: 11px; line-height: 1.55; color: var(--text-3); margin-bottom: 14px; }
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 6px;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
}
[data-testid="stSidebar"] .stTextInput input {
  padding: 8px 10px !important;
  font-size: 12px !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-size: 12px !important;
  min-height: 0 !important;
}
[data-testid="stSidebar"] [data-baseweb="popover"] [role="listbox"] {
  background: var(--surface);
  border: 1px solid var(--border-strong);
}
[data-testid="stSidebar"] [data-baseweb="popover"] [role="listbox"] li {
  color: var(--text-2);
  font-size: 12px;
}

/* --- form polish: Streamlit shows a "Press Enter to submit form" hint inside
   form widgets after typing; it overlaps the field in the dark theme, and the
   SAVE button already communicates submission. Hide it and keep fields
   single-line, with a clear focus ring and readable placeholders. --- */
[data-testid="stSidebar"] [data-testid="stForm"] small,
[data-testid="stSidebar"] [data-testid="stForm"] [data-testid="stFormWidgetHelp"],
[data-testid="stSidebar"] [data-testid="stForm"] [class*="FormWidgetHelp"],
[data-testid="stSidebar"] [data-testid="stForm"] .stFormSubmitHint { display: none !important; }
[data-testid="stSidebar"] [data-testid="stForm"] [data-testid="stTextInput"] { margin-bottom: 3px; }
[data-testid="stSidebar"] .stTextInput input::placeholder {
  color: var(--text-3);
  opacity: 1;
  font-size: 10.5px;
  letter-spacing: 0.03em;
}
[data-testid="stSidebar"] input[type="password"] { font-family: var(--font-mono); }
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] .stTextInput input:focus-visible {
  border-color: var(--info) !important;
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--info) 45%, transparent) !important;
  outline: none !important;
}

/* --- key-active chip: a visible confirmation that a key exists (env or
   saved), since the write-only field intentionally never echoes it --- */
.aw-key-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 2px 0 2px;
  padding: 3px 9px;
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 8.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.aw-key-chip.is-ok { color: var(--ok); border: 1px solid color-mix(in srgb, var(--ok) 45%, transparent); background: color-mix(in srgb, var(--ok) 10%, transparent); }
.aw-key-chip.is-missing { color: var(--err); border: 1px solid color-mix(in srgb, var(--err) 45%, transparent); background: color-mix(in srgb, var(--err) 10%, transparent); }

/* Scroll insurance for the settings sidebar. The content can grow very tall
   (six agents x forms + an 85-model picker), and the model picker is a
   React Aria combobox whose virtual dropdown renders as a fixed overlay.
   Keep the content container the scroll owner, and cap the dropdown so it
   stays inside short viewports with its own explicit internal scroll. */
[data-testid="stSidebar"] { height: 100dvh; }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  overflow-y: auto;
  height: 100%;
}
[data-testid="stSidebar"] [role="listbox"] {
  max-height: 220px;
  overflow-y: auto;
}
.aw-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.aw-status-dot { width: 6px; height: 6px; border-radius: 3px; flex: 0 0 auto; }
.aw-status.is-ok { color: var(--ok); }
.aw-status.is-ok .aw-status-dot { background: var(--ok); }
.aw-status.is-err { color: var(--err); }
.aw-status.is-err .aw-status-dot { background: var(--err); }
.aw-status-err-text {
  font-size: 11px;
  line-height: 1.5;
  color: var(--err);
  margin-top: 2px;
  word-break: break-word;
}

/* ---------- Responsive layout ----------
   Streamlit rows wrap by default but columns keep squeezing; giving them a
   min-width under a breakpoint makes the five-card arena, the input zone and
   the sidebar forms reflow instead of shrinking into unreadable slivers.
   Streamlit 1.66 column testid is stColumn (not column). */

@media (max-width: 1200px) {
  .block-container { padding: 1.9rem 1.1rem 2.2rem; }
  main [data-testid="stHorizontalBlock"] { row-gap: 16px; }
  main [data-testid="stColumn"] { flex: 1 1 220px !important; min-width: 220px !important; }
  .aw-wordmark { font-size: 30px; }
}

@media (max-width: 900px) {
  .block-container { padding: 1.5rem 0.9rem 2rem; }
  main [data-testid="stColumn"] { flex: 1 1 210px !important; min-width: 210px !important; }
  .aw-header { padding-bottom: 12px; margin-bottom: 16px; }
  .aw-vdivider, .aw-tagline { display: none; }
  .aw-card { min-height: 240px; }
  .aw-card.is-waiting { min-height: 190px; }
  .aw-output { max-height: 240px; }
  .aw-grid { grid-template-columns: 1fr; gap: 14px; }
  .aw-stepper { margin: 8px 0 16px; }
  .aw-step-label { font-size: 9px; letter-spacing: 0.1em; }
  .aw-step-line { margin: 0 8px; min-width: 10px; }
  .aw-winner { font-size: 20px; }
  .aw-scores { max-width: 100%; }
  /* Mode pills: Streamlit keeps them on one line with overflow-x auto,
     which clips the last option below ~800px; let them wrap instead. */
  [data-testid="stButtonGroup"] [role="radiogroup"] { flex-wrap: wrap; row-gap: 8px; overflow-x: visible; }
}

@media (max-width: 640px) {
  /* Stepper collapses to numbered dots only once labels no longer fit. */
  .aw-step-label { display: none; }
  .aw-step-line { margin: 0 6px; min-width: 8px; }
}

@media (max-width: 560px) {
  .block-container { padding: 1.2rem 0.8rem 1.8rem; }
  main [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; }
  .aw-header { flex-wrap: wrap; gap: 10px; }
  .aw-wordmark { font-size: 25px; }
  .aw-brand-mark svg { width: 21px; height: 21px; }
  .aw-dots { display: none; }
  .aw-brand { gap: 10px; }
  .aw-card { min-height: 0; padding: 12px 12px 10px; }
  .aw-card:hover { transform: none; }  /* no hover lift on touch layouts */
  .aw-output { max-height: 300px; }
  .aw-card-head .aw-avatar { width: 34px; height: 34px; }
  .aw-verdict-head { gap: 8px; }
  .aw-winner { font-size: 18px; letter-spacing: 0.02em; }
  .aw-score-num { font-size: 15px; }
  .aw-modal { padding: 10px; }
  .aw-modal-panel { width: 100%; max-height: 92vh; border-radius: 12px; }
  .aw-footer { flex-direction: column; align-items: flex-start; gap: 4px; }
  .aw-pill { flex-wrap: wrap; }
}

/* --- accessibility: honor reduced-motion --- */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
"""


def inject() -> None:
    """Apply the stylesheet exactly once per script run."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def page_config() -> None:
    """Streamlit page settings; must run before any other st command.

    ``initial_sidebar_state`` is intentionally not set here: the settings
    panel lives in the sidebar, and ``.streamlit/config.toml`` expands it.
    Setting it here would override that config with a collapsed default.
    """
    st.set_page_config(
        page_title="Quorum",
        page_icon=None,
        layout="wide",
    )
