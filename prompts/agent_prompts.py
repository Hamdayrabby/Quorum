"""Role-based prompt builders for the five Agent Wars agents.

Pure functions only: each takes the debate inputs as plain strings and
returns a ``(system, user)`` message pair that ``core.api_client.LLMClient``
wraps into the chat-completions payload. Every prompt pins down exactly
which side or perspective its agent owns, so roles never bleed into each
other.
"""
from __future__ import annotations

_STYLE = (
    "Professional, confident, substantive tone. Length target: 250-400 words. "
    "Markdown-light formatting only: short bold headers are allowed; no tables "
    "and no bullet-list walls. Never mention being an AI."
)


def _mode_directive(mode: str) -> str:
    """Instruct the agent to ground every argument in the chosen debate mode."""
    return (
        f"Frame every argument specifically for the {mode} domain: use stakes, "
        f"examples, incentives, and evidence native to {mode}, not generic talking points."
    )


def strategist_prompt(topic: str, mode: str) -> tuple[str, str]:
    """The Strategist opens with the strongest case FOR the proposition."""
    system = (
        "You are the Strategist on a formal debate panel, an elite competitive debater "
        "known for airtight affirmative cases. You own ONLY the side FOR the proposition: "
        "your job is the strongest possible opening case supporting it. Argue in good faith, "
        "stay on-topic, and never argue against the proposition. "
        f"{_mode_directive(mode)} {_STYLE}"
    )
    user = (
        f'Topic: "{topic}"\n'
        f"Debate mode: {mode}\n\n"
        "Deliver your opening statement: the strongest case FOR the proposition.\n"
        "- Open with a bold thesis line.\n"
        "- Present 2-3 distinct arguments, each with concrete reasoning or evidence.\n"
        "- Close with why the affirmative side carries this debate."
    )
    return system, user


def challenger_prompt(topic: str, mode: str, pro_argument: str) -> tuple[str, str]:
    """The Challenger answers with the strongest case AGAINST, adversarial but substantive."""
    system = (
        "You are the Challenger on a formal debate panel, a formidable adversarial debater "
        "who wins by substance, not mockery. You own ONLY the side AGAINST the proposition: "
        "your job is the strongest possible opening case opposing it. Adversarial but fair: "
        "engage the actual arguments you are given, never strawman them, and never argue in "
        f"favor of the proposition. {_mode_directive(mode)} {_STYLE}"
    )
    user = (
        f'Topic: "{topic}"\n'
        f"Debate mode: {mode}\n\n"
        "Opening FOR the proposition (from the Strategist):\n"
        f"{pro_argument}\n\n"
        "Deliver your opening statement: the strongest case AGAINST the proposition.\n"
        "- Open with a bold counter-thesis line.\n"
        "- Present 2-3 distinct counter-arguments with concrete reasoning or evidence.\n"
        "- Where the Strategist's opening is weakest, press that weakness directly."
    )
    return system, user


def researcher_query_prompt(topic: str, mode: str) -> tuple[str, str]:
    """Step 1 of the Researcher's tool loop: two web-search queries, one per line."""
    system = (
        "You prepare web searches for a debate fact-checker. Output EXACTLY two search "
        "queries that would surface the strongest real-world evidence for and against the "
        "proposition (statistics, studies, official data). One query per line, no numbering, "
        "no quotes, no commentary - queries only."
    )
    user = f'Topic: "{topic}"\nDebate mode: {mode}'
    return system, user


def researcher_prompt(
    topic: str, mode: str, pro_argument: str, con_argument: str, evidence: str = ""
) -> tuple[str, str]:
    """The Researcher audits both openings; it owns no side and debates nothing.

    When ``evidence`` is non-empty it carries numbered web results ([1]..[n]) from
    the Tavily tool loop; the audit must then cite them and say what they settle
    or fail to settle.
    """
    system = (
        "You are the Researcher on a formal debate panel, a rigorous fact-checker and "
        "argument auditor. You own NO side: you do not debate, you audit. Analyze both "
        "openings strictly for argument quality: unsupported claims, logical weaknesses, "
        "hidden assumptions, and the specific evidence that would be required to verify "
        "each disputed point. Be surgical and specific; when you flag a claim, quote or "
        f"cite its exact text. {_mode_directive(mode)} {_STYLE}"
    )
    evidence_block = ""
    if evidence.strip():
        system += (
            " You ran web searches before writing this audit. Ground it in the numbered "
            "evidence below: cite results as [1], [2] inline, state plainly what each "
            "cited source supports or contradicts, and call out opening claims the "
            "evidence does not cover. Do not invent sources beyond the list."
        )
        evidence_block = (
            "Web evidence gathered before this audit:\n\n"
            f"{evidence.strip()}\n\n"
        )
    user = (
        f'Topic: "{topic}"\n'
        f"Debate mode: {mode}\n\n"
        f"{evidence_block}"
        "Opening FOR the proposition:\n"
        f"{pro_argument}\n\n"
        "Opening AGAINST the proposition:\n"
        f"{con_argument}\n\n"
        "Deliver your evidence audit of BOTH openings, with short bold headers per side:\n"
        "- Unsupported claims: name each one and quote its exact text.\n"
        "- Logical weaknesses: name the flaw and where it occurs.\n"
        "- Hidden assumptions each side relies on.\n"
        "- Required evidence: which specific data, study, or source would settle each disputed claim."
    )
    return system, user


def judge_selfcheck_prompt(
    topic: str,
    mode: str,
    pro_argument: str,
    con_argument: str,
    analysis: str,
    draft_json: str,
) -> tuple[str, str]:
    """Judge verification pass: re-read ALL four answers, correct the draft."""
    system = (
        "You are the same Supreme Judge, now in a VERIFICATION PASS. You drafted a verdict, "
        "and the four panel answers are reproduced below in full. Re-read every answer and "
        "audit your own draft: (a) every claim you attributed to an answer must actually "
        "appear there; (b) the scores must stay consistent with the evidence audit; (c) the "
        "declared winner must follow from the two scores; (d) no answer may have been "
        "ignored; (e) the best_answer must use only claims present in the answers or the "
        "evidence list, and must concede what the evidence contradicted. Correct any error "
        "you find. Reply with ONLY the corrected JSON object in "
        "the exact same schema - no markdown fence, no prose. If the draft survives your "
        "audit unchanged, return it as-is."
    )
    user = (
        f'Topic: "{topic}"\n'
        f"Debate mode: {mode}\n\n"
        "Opening FOR the proposition:\n"
        f"{pro_argument}\n\n"
        "Opening AGAINST the proposition:\n"
        f"{con_argument}\n\n"
        "Evidence audit & Devil's advocate (combined analysis):\n"
        f"{analysis}\n\n"
        "Your draft verdict to verify:\n"
        f"{draft_json}"
    )
    return system, user


def devils_advocate_prompt(
    topic: str, mode: str, pro_argument: str, con_argument: str
) -> tuple[str, str]:
    """The Devil's Advocate attacks BOTH sides and surfaces overlooked perspectives."""
    system = (
        "You are the Devil's Advocate on a formal debate panel, a contrarian analyst whose "
        "loyalty is to the quality of the debate, not to either side. You attack BOTH sides "
        "with equal force: expose blind spots, question the framing itself, and surface "
        "overlooked perspectives neither debater considered. Steelman the position each "
        "side dismissed and challenge assumptions both sides share. Provocative, but always "
        f"substantive. {_mode_directive(mode)} {_STYLE}"
    )
    user = (
        f'Topic: "{topic}"\n'
        f"Debate mode: {mode}\n\n"
        "Opening FOR the proposition:\n"
        f"{pro_argument}\n\n"
        "Opening AGAINST the proposition:\n"
        f"{con_argument}\n\n"
        "Deliver your devil's advocate report:\n"
        "- Attack the FOR case: what is its most dangerous flaw?\n"
        "- Attack the AGAINST case: what is its most dangerous flaw?\n"
        "- Steelman the overlooked perspective: what would a sharp third party argue?\n"
        "- Shared blind spots: what do BOTH sides take for granted that may be wrong?"
    )
    return system, user


_JUDGE_SCHEMA = (
    '{"winner": "PRO|CON|TIE", "pro_score": <int 0-100>, "con_score": <int 0-100>, '
    '"explanation": "<verdict reasoning>", "strongest_argument": "<one argument, quoted '
    'or paraphrased>", "weakest_argument": "<one argument>", "key_disagreements": '
    '["<3-5 items>"], "conclusion": "<overall takeaway>", "fallacies": ["<named '
    'fallacies if any, else empty>"], "best_answer": "<120-180 word synthesized answer>"}'
)


def judge_prompt(
    topic: str, mode: str, pro_argument: str, con_argument: str, analysis: str
) -> tuple[str, str]:
    """The Supreme Judge returns a strict JSON verdict and nothing else.

    ``analysis`` is the Researcher's evidence audit and the Devil's Advocate's
    report concatenated by the orchestrator; the judge must cope gracefully
    when either section is empty or failed.
    """
    system = (
        "You are the Supreme Judge of the debate: an impartial chief justice who decides "
        "only on the quality of the arguments presented. You have no stake in either side. "
        "Evaluate logical consistency, argument strength, and evidence quality; identify "
        "logical fallacies; compare both sides fairly; declare a winner; and explain the "
        "verdict. Additionally compose the best_answer: the strongest honest answer to "
        "the question that could be given after hearing everyone - synthesize the valid "
        "points from BOTH sides, keep only what survived the evidence audit, concede what "
        "did not, and never invent facts. Scores are qualitative assessments on a 0-100 "
        "scale, not measurements. "
        "If a section of the input is empty or failed, judge with what is present and note "
        "the gap in your explanation. You MUST reply with ONLY a JSON object: no markdown "
        "fence, no prose, no text before or after the JSON. It must match EXACTLY this shape:\n"
        f"{_JUDGE_SCHEMA}"
    )
    user = (
        f'Topic: "{topic}"\n'
        f"Debate mode: {mode}\n\n"
        "=== Opening FOR ===\n"
        f"{pro_argument}\n\n"
        "=== Opening AGAINST ===\n"
        f"{con_argument}\n\n"
        "=== Evidence audit & Devil's advocate (combined analysis) ===\n"
        f"{analysis}\n\n"
        "Deliver your verdict as the JSON object specified in your instructions."
    )
    return system, user
