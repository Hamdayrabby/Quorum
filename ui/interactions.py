"""Client-side behaviors for the arena: reveal, expand, copy.

Streamlit rebuilds the DOM on every pipeline update, so all behavior is
delegated (one listener on the parent document) and signature-gated: the
script remembers what each slot (agent role, stepper phase, verdict) last
showed and only plays entrance effects for genuinely new content. The script
is injected once per script run inside a zero-height iframe and reaches the
parent document — same origin, standard Streamlit pattern. Every effect is
progressive enhancement: without it the page renders complete and correct.

Effects:
- typewriter reveal of an agent's output the first time it completes;
- click-to-expand reading modal for any card with output (Esc/backdrop/× to
  close, closes itself when the underlying DOM is rebuilt);
- copy-to-clipboard buttons on cards and in the modal;
- ``.aw-enter`` class on cards/stepper/verdict when their signature is new,
  which gates the entrance animations declared in ``ui/theme.py``.
"""
from __future__ import annotations

from streamlit.components.v1 import html as component_html

# Plain string on purpose: the JS uses template literals, so no f-string.
_SCRIPT = """
<script>
(() => {
  if (window.parent === window) return; // no parent document: nothing to do
  const doc = window.parent.document;
  if (doc.getElementById('aw-ix-bound')) return; // already bound this page load
  const marker = doc.createElement('div');
  marker.id = 'aw-ix-bound';
  marker.style.display = 'none';
  doc.body.appendChild(marker);

  const reduceMotion =
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const seen = new Map();   // slot key -> last signature
  const typed = new Set();  // content hashes already revealed
  let openModal = null;

  const hash = (s) => {
    let h = 5381;
    for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
    return (h >>> 0).toString(36);
  };
  const fullText = (root) => {
    const el = root.querySelector('.aw-output, .aw-err');
    return el ? (el.dataset.full || el.textContent || '') : '';
  };

  // ---- typewriter reveal (real content only, shown progressively) ----
  const typewrite = (el, text) => {
    el.dataset.full = text;
    const dur = Math.min(1600, Math.max(350, text.length * 1.2));
    const caret = doc.createElement('span');
    caret.className = 'aw-caret';
    el.textContent = '';
    el.appendChild(caret);
    const t0 = performance.now();
    const step = (now) => {
      if (!caret.isConnected) return; // element was rebuilt mid-animation
      const p = Math.min(1, (now - t0) / dur);
      const eased = 1 - Math.pow(1 - p, 2.2);
      const n = Math.max(1, Math.floor(text.length * eased));
      while (el.childNodes.length > 1) el.removeChild(el.firstChild);
      el.insertBefore(doc.createTextNode(text.slice(0, n)), caret);
      if (p < 1) requestAnimationFrame(step);
      else caret.remove();
    };
    requestAnimationFrame(step);
  };

  // ---- expanded-reading modal ----
  const closeModal = () => {
    if (openModal) { openModal.remove(); openModal = null; }
  };
  const openModalFor = (card) => {
    closeModal();
    const pill = card.querySelector('.aw-pill');
    const latency = card.querySelector('.aw-latency');
    const accent = (getComputedStyle(card).getPropertyValue('--accent') || '#D4AF37').trim();
    const wrap = doc.createElement('div');
    wrap.className = 'aw-modal';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.innerHTML = `
      <div class="aw-modal-panel" style="--accent:${accent}">
        <div class="aw-modal-head">
          <span class="aw-glyph">${card.querySelector('.aw-glyph')?.textContent || ''}</span>
          <span class="aw-name">${card.dataset.name || 'Agent'}</span>
          <span class="aw-chip" title="${card.dataset.provider || ''}">${card.dataset.model || ''}</span>
          <span class="${pill ? pill.className : 'aw-pill'}">${pill ? pill.textContent : ''}</span>
          <button class="aw-modal-close" type="button" aria-label="Close">&#215;</button>
        </div>
        <div class="aw-modal-body"></div>
        <div class="aw-modal-foot">
          <span class="aw-latency">${latency ? latency.textContent : ''}</span>
          <button class="aw-copy" type="button">Copy</button>
        </div>
      </div>`;
    wrap.querySelector('.aw-modal-body').textContent = fullText(card);
    doc.body.appendChild(wrap);
    openModal = wrap;
  };

  // ---- clipboard with fallback ----
  const fallbackCopy = (text, done) => {
    const ta = doc.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    doc.body.appendChild(ta);
    ta.select();
    try { doc.execCommand('copy'); done(); } catch (e) { /* best effort */ }
    ta.remove();
  };
  const copyText = (text, btn) => {
    const done = () => {
      btn.classList.add('is-copied');
      btn.textContent = 'Copied';
      setTimeout(() => { btn.classList.remove('is-copied'); btn.textContent = 'Copy'; }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, () => fallbackCopy(text, done));
    } else {
      fallbackCopy(text, done);
    }
  };

  // ---- one delegated click handler (survives Streamlit rebuilds) ----
  doc.addEventListener('click', (e) => {
    if (openModal && e.target === openModal) { closeModal(); return; }
    const t = e.target.closest ? e.target.closest('.aw-expand, .aw-copy, .aw-modal-close') : null;
    if (!t) return;
    if (t.classList.contains('aw-modal-close')) { closeModal(); return; }
    if (t.classList.contains('aw-expand')) {
      const card = t.closest('.aw-card');
      if (card) openModalFor(card);
      return;
    }
    if (t.classList.contains('aw-copy')) {
      const root = t.closest('.aw-card, .aw-modal-panel');
      copyText(root ? fullText(root) : '', t);
    }
  });
  doc.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

  // ---- signature-gated entrance effects ----
  const process = (el) => {
    const cl = el.classList;
    if (!cl) return;
    if (cl.contains('aw-card')) {
      const role = el.dataset.role || 'card';
      const pill = el.querySelector('.aw-pill');
      const status = pill ? pill.textContent.trim() : '';
      const sig = role + '|' + status + '|' + hash(fullText(el));
      const fresh = seen.get(role) !== sig;
      seen.set(role, sig);
      if (fresh && !reduceMotion) {
        el.classList.add('aw-enter');
        const out = el.querySelector('.aw-output');
        if (out && out.textContent) {
          const h = hash(out.textContent);
          if (!typed.has(h)) { typed.add(h); typewrite(out, out.textContent); }
        }
      }
      return;
    }
    if (cl.contains('aw-stepper')) {
      const sig = 'phase|' + (el.dataset.phase || '');
      if (seen.get('_stepper') !== sig) { seen.set('_stepper', sig); if (!reduceMotion) el.classList.add('aw-enter'); }
      return;
    }
    if (cl.contains('aw-verdict')) {
      const sig = 'verdict|' + hash(el.innerText || '');
      if (seen.get('_verdict') !== sig) { seen.set('_verdict', sig); if (!reduceMotion) el.classList.add('aw-enter'); }
    }
  };

  const scan = (node) => {
    if (!node || node.nodeType !== 1) return;
    if (node.matches && node.matches('.aw-card, .aw-stepper, .aw-verdict')) process(node);
    if (node.querySelectorAll) {
      node.querySelectorAll('.aw-card, .aw-stepper, .aw-verdict').forEach(process);
    }
  };

  const obs = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const n of m.addedNodes) {
        if (n.nodeType !== 1) continue; // text nodes (typewriter) are never arena rebuilds
        const isArena =
          n.matches && (n.matches('.aw-card, .aw-stepper, .aw-verdict') ||
                        n.querySelector('.aw-card, .aw-stepper, .aw-verdict'));
        if (!isArena) continue; // the modal's own DOM must not close the modal
        if (openModal) closeModal(); // arena rebuilt underneath: drop the stale overlay
        scan(n);
      }
    }
  });
  obs.observe(doc.body, { childList: true, subtree: true });
  scan(doc.body); // first paint: stagger the initial arena into place
})();
</script>
"""


def inject() -> None:
    """Install the behavior layer once per browser page load.

    The zero-height iframe re-renders on every Streamlit rerun; the script
    re-executes but exits immediately once its marker exists in the parent
    document, so listeners and observers are never doubled.
    """
    component_html(_SCRIPT, height=0)
