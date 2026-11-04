"""Live model diagnostics: why a provider returns empty content or 404.

Run:  .venv/Scripts/python.exe tests/probe_models.py
Prints raw message shapes for reasoning-model diagnosis and probes candidate
ids with a short prompt. Read-only; uses the keys already in the environment.
"""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import replace
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from core.api_client import LLMClient  # noqa: E402
from core.config import AGENT_CONFIGS  # noqa: E402
from core.exceptions import AgentWarsError  # noqa: E402
from core.models import AgentRole  # noqa: E402
from prompts.agent_prompts import devils_advocate_prompt  # noqa: E402


async def raw_shape(base_url: str, key: str, model: str, max_tokens: int) -> None:
    """Print the raw first-choice message shape (keys + content length)."""
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base_url}chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say hello."}],
                "max_tokens": max_tokens,
            },
        )
        try:
            data = resp.json()
            msg = data["choices"][0]["message"]
            print(f"    raw[{model}, max_tokens={max_tokens}] http={resp.status_code} "
                  f"message keys={sorted(msg.keys())} "
                  f"content_len={len(msg.get('content') or '')} "
                  f"finish={data['choices'][0].get('finish_reason')!r}")
        except Exception:
            print(f"    raw[{model}] http={resp.status_code} body={resp.text[:150]!r}")


async def try_client(role: AgentRole, model: str, max_tokens: int, *, debate_prompt: bool = False) -> None:
    cfg = AGENT_CONFIGS[role]
    cfg = replace(cfg, model=model, max_tokens=max_tokens)
    client = LLMClient(cfg)
    system, user = "Reply with exactly one short sentence.", "Say hello."
    if debate_prompt:
        system, user = devils_advocate_prompt(
            "Social media does more harm than good to democratic societies", "Society", "pro side text", "con side text"
        )
    try:
        out = await client.complete(system, user)
        print(f"OK   {role.value:16} {model:42} max_tokens={max_tokens} -> {out[:80]!r}")
    except AgentWarsError as e:
        print(f"FAIL {role.value:16} {model:42} max_tokens={max_tokens} -> {str(e)[:120]}")


async def main() -> None:
    gem_key = os.environ["GEMINI_API_KEY"]
    mis_key = os.environ["MISTRAL_API_KEY"]
    river_key = os.environ["RIVER_API_KEY"]

    print("== empty-content diagnosis ==")
    await raw_shape("https://api.mistral.ai/v1/", mis_key, "mistral-large-4", 200)
    await raw_shape("https://api.river.ai/v1/", river_key, "zai-org/GLM-5.3-Flash", 200)

    print("== gemini candidates ==")
    for m in ("models/gemini-3.5-flash", "models/gemini-3.6-flash", "models/gemini-2.5-flash-lite", "models/gemini-flash-lite-latest"):
        await try_client(AgentRole.STRATEGIST, m, 100)

    print("== mistral candidates (larger budget) ==")
    await try_client(AgentRole.RESEARCHER, "mistral-large-4", 4000)

    print("== river GLM with debate-sized prompt + large budget ==")
    await try_client(AgentRole.DEVILS_ADVOCATE, "zai-org/GLM-5.3-Flash", 6000, debate_prompt=True)

    print("== nvidia candidates ==")
    for m in (
        "nvidia/llama-3.3-nemotron-super-49b-v1",
        "nvidia/nemotron-4-340b-instruct",
        "nvidia/llama-3.1-nemotron-51b-instruct",
        "meta/llama-3.3-70b-instruct",
    ):
        await try_client(AgentRole.SUPREME_JUDGE, m, 200)


if __name__ == "__main__":
    asyncio.run(main())
