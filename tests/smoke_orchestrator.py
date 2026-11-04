"""Mock-based end-to-end proof of the debate pipeline (no network, no keys).

Run directly: ``.venv/Scripts/python.exe tests/smoke_orchestrator.py``.
A ``FakeClient`` stands in for ``LLMClient`` behind the orchestrator's
injected client factory, so the full staged pipeline runs deterministically
offline: happy path, opening failures, verdict tolerance, and stage-2
parallelism.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.exceptions import ApiError  # noqa: E402
from core.models import AgentRole, AgentStatus, DebateState  # noqa: E402
from core.orchestrator import DebateOrchestrator  # noqa: E402

_TOPIC = "Remote work is better than office work"
_MODE = "Business"

_STRATEGIST_REPLY = (
    "PRO: Remote work beats office work because it widens the talent pool, "
    "cuts fixed costs, and returns commuting hours to employees. Firms hiring "
    "without geographic limits fill roles 30 percent faster, and measured "
    "output rises when people work in environments they control."
)
_CHALLENGER_REPLY = (
    "CON: Office work builds the informal mentorship and shared context that "
    "remote schedules erode. Junior staff learn more slowly without hallway "
    "apprenticeship, and collaboration drops once coordination moves into "
    "calendars and chat threads."
)
_RESEARCHER_REPLY = (
    "AUDIT: Both sides cite numbers without sources. The strategist's "
    "30-percent faster-hiring claim needs the underlying study; the "
    "challenger's collaboration-drop claim needs a controlled comparison of "
    "team output before and after remote adoption."
)
_DEVILS_REPLY = (
    "PERSPECTIVES: Both sides assume work must happen in one mode. Hybrid "
    "schedules break the binary, and both ignore the worker-type split: "
    "career starters may need offices while seniors may not."
)
_JUDGE_VERDICT: dict = {
    "winner": "PRO",
    "pro_score": 87,
    "con_score": 72,
    "explanation": "The strategist's case carries better evidence density.",
    "strongest_argument": "A borderless talent pool fills roles faster.",
    "weakest_argument": "The challenger cites no data for slower mentorship.",
    "key_disagreements": ["productivity measurement", "mentorship quality", "cost savings"],
    "conclusion": "Remote work wins when outcomes are measured, not hours.",
    "fallacies": ["hasty generalization", "appeal to tradition", "false dichotomy"],
}
_JUDGE_REPLY = json.dumps(_JUDGE_VERDICT)

_FAILURES: list[str] = []


class FakeClient:
    """Duck-typed ``LLMClient`` stand-in: canned reply, optional delay or failure."""

    def __init__(self, reply: str, *, delay_s: float = 0.0, fail: bool = False) -> None:
        self.reply = reply
        self.delay_s = delay_s
        self.fail = fail
        self.calls = 0
        self.last_user = ""

    async def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        self.calls += 1
        self.last_user = user
        if self.delay_s > 0:
            await asyncio.sleep(self.delay_s)
        if self.fail:
            raise ApiError("FakeProvider", 500, "simulated provider outage")
        return self.reply


_BASE_REPLIES: dict[AgentRole, str] = {
    AgentRole.STRATEGIST: _STRATEGIST_REPLY,
    AgentRole.CHALLENGER: _CHALLENGER_REPLY,
    AgentRole.RESEARCHER: _RESEARCHER_REPLY,
    AgentRole.DEVILS_ADVOCATE: _DEVILS_REPLY,
    AgentRole.SUPREME_JUDGE: _JUDGE_REPLY,
}


def make_clients(
    *,
    delay_s: float = 0.0,
    failures: set[AgentRole] | None = None,
    judge_reply: str | None = None,
) -> dict[AgentRole, FakeClient]:
    failures = failures or set()
    clients: dict[AgentRole, FakeClient] = {}
    for role, reply in _BASE_REPLIES.items():
        if role is AgentRole.SUPREME_JUDGE and judge_reply is not None:
            reply = judge_reply
        clients[role] = FakeClient(reply, delay_s=delay_s, fail=role in failures)
    return clients


def scenario(name: str):
    def decorate(func):
        def run() -> None:
            try:
                asyncio.run(func())
                print(f"PASS: {name}")
            except AssertionError as exc:
                _FAILURES.append(name)
                print(f"FAIL: {name} - {exc}")
            except Exception as exc:  # noqa: BLE001 - report, keep running
                _FAILURES.append(name)
                print(f"FAIL: {name} - unexpected {type(exc).__name__}: {exc}")

        return run

    return decorate


@scenario("1. happy path: all five COMPLETED, verdict parsed, >= 8 updates, latency recorded")
async def scenario_happy_path() -> None:
    clients = make_clients()
    updates: list[DebateState] = []
    orchestrator = DebateOrchestrator(client_factory=lambda role: clients[role])
    state = await orchestrator.run_debate(_TOPIC, _MODE, on_update=updates.append)

    for role in AgentRole:
        result = state.get(role)
        assert result is not None, f"{role.value}: missing result"
        assert result.status is AgentStatus.COMPLETED, f"{role.value}: {result.status.value}"
        assert result.content, f"{role.value}: empty content"
        assert result.latency_s > 0, f"{role.value}: latency not recorded"
        assert clients[role].calls == 1, f"{role.value}: {clients[role].calls} client calls"
    assert state.completed_count() == 5
    assert state.judge_error is None

    verdict = state.verdict
    assert verdict is not None, "verdict missing"
    assert verdict.parse_ok is True
    assert verdict.winner == "PRO", verdict.winner
    assert verdict.pro_score == 87, verdict.pro_score
    assert verdict.con_score == 72, verdict.con_score
    assert len(verdict.key_disagreements) == 3
    assert len(verdict.fallacies) == 3
    assert len(updates) >= 8, f"only {len(updates)} on_update calls"


@scenario("2. one opening fails: strategist survives, judge still delivers")
async def scenario_one_opening_fails() -> None:
    clients = make_clients(failures={AgentRole.CHALLENGER})
    orchestrator = DebateOrchestrator(client_factory=lambda role: clients[role])
    state = await orchestrator.run_debate(_TOPIC, _MODE)

    strategist = state.get(AgentRole.STRATEGIST)
    challenger = state.get(AgentRole.CHALLENGER)
    judge = state.get(AgentRole.SUPREME_JUDGE)
    assert strategist is not None and strategist.ok
    assert challenger is not None and challenger.status is AgentStatus.FAILED
    assert challenger.error and "simulated provider outage" in challenger.error
    assert judge is not None and judge.ok
    assert state.verdict is not None and state.verdict.parse_ok is True
    assert state.judge_error is None
    assert "PRO:" in clients[AgentRole.RESEARCHER].last_user, "surviving opening not forwarded"


@scenario("3. both openings fail: stages 3-4 skipped, judge_error set, nothing escapes")
async def scenario_both_openings_fail() -> None:
    clients = make_clients(failures={AgentRole.STRATEGIST, AgentRole.CHALLENGER})
    orchestrator = DebateOrchestrator(client_factory=lambda role: clients[role])
    state = await orchestrator.run_debate(_TOPIC, _MODE)

    for role in (AgentRole.STRATEGIST, AgentRole.CHALLENGER):
        result = state.get(role)
        assert result is not None and result.status is AgentStatus.FAILED, role.value
    for role in (AgentRole.RESEARCHER, AgentRole.DEVILS_ADVOCATE, AgentRole.SUPREME_JUDGE):
        result = state.get(role)
        assert result is not None and result.status is AgentStatus.WAITING, role.value
    assert clients[AgentRole.RESEARCHER].calls == 0, "analysis stage must be skipped"
    assert clients[AgentRole.SUPREME_JUDGE].calls == 0, "verdict stage must be skipped"
    assert state.judge_error is not None
    assert state.verdict is None


@scenario("4. judge wraps JSON in prose and fences: still parsed")
async def scenario_prose_wrapped_verdict() -> None:
    wrapped = "Here is my verdict:\n\n```json\n" + _JUDGE_REPLY + "\n```\n\nGood debate."
    clients = make_clients(judge_reply=wrapped)
    orchestrator = DebateOrchestrator(client_factory=lambda role: clients[role])
    state = await orchestrator.run_debate(_TOPIC, _MODE)

    verdict = state.verdict
    assert verdict is not None, "verdict missing"
    assert verdict.parse_ok is True
    assert verdict.winner == "PRO"
    assert verdict.pro_score == 87


@scenario("5. judge returns garbage: parse_ok False, raw_text kept, judge_error None")
async def scenario_garbage_verdict() -> None:
    clients = make_clients(judge_reply="I cannot decide.")
    orchestrator = DebateOrchestrator(client_factory=lambda role: clients[role])
    state = await orchestrator.run_debate(_TOPIC, _MODE)

    verdict = state.verdict
    assert verdict is not None, "verdict missing"
    assert verdict.parse_ok is False
    assert verdict.raw_text == "I cannot decide.", verdict.raw_text
    assert state.judge_error is None
    judge = state.get(AgentRole.SUPREME_JUDGE)
    assert judge is not None and judge.ok


@scenario("6. stage-2 pair is parallel: < 0.35 s at 0.2 s per client call")
async def scenario_concurrency() -> None:
    clients = make_clients(delay_s=0.2)
    stamps: list[tuple[float, DebateState]] = []
    started = time.perf_counter()
    orchestrator = DebateOrchestrator(client_factory=lambda role: clients[role])
    state = await orchestrator.run_debate(
        _TOPIC, _MODE, on_update=lambda snapshot: stamps.append((time.perf_counter(), snapshot))
    )

    def both_openings_done(snapshot: DebateState) -> bool:
        strategist = snapshot.get(AgentRole.STRATEGIST)
        challenger = snapshot.get(AgentRole.CHALLENGER)
        return (
            strategist is not None
            and challenger is not None
            and strategist.ok
            and challenger.ok
        )

    assert state.completed_count() == 5
    stage2_end = next(
        (stamp for stamp, snapshot in stamps if both_openings_done(snapshot)), None
    )
    assert stage2_end is not None, "no update observed with both openings done"
    elapsed = stage2_end - started
    assert elapsed < 0.35, f"stage 2 took {elapsed:.3f}s - agents ran serially"


def main() -> None:
    scenario_happy_path()
    scenario_one_opening_fails()
    scenario_both_openings_fail()
    scenario_prose_wrapped_verdict()
    scenario_garbage_verdict()
    scenario_concurrency()
    if _FAILURES:
        print(f"PIPELINE SMOKE RED ({len(_FAILURES)} failing: {', '.join(_FAILURES)})")
        raise SystemExit(1)
    print("PIPELINE SMOKE GREEN")


if __name__ == "__main__":
    main()
