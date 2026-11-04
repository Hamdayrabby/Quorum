# Agent Wars

Five LLM agents from five different providers argue a proposition, audit each other, and a judge agent delivers a scored verdict. Built as an Advanced AI course project to demonstrate a multi-provider, multi-agent pipeline with graceful failure handling.

```
                          topic + mode
                               |
        -----------------------+-----------------------
        |                      |                      |
  Strategist (Gemini)    Challenger (DeepSeek)          <- Stage 2: openings, concurrent
        PRO case               CON case
        -----------------------+-----------------------
                               |
              Researcher (Mistral) + Devil's Advocate (GLM)  <- Stage 3: analysis, concurrent
                               |
                     Supreme Judge (NVIDIA NIM)                <- Stage 4: verdict
                               |
                    Verdict: winner, scores, fallacies
```

## Architecture

```
app.py                    Streamlit wiring: layout, session state, one run flow
ui/
  theme.py                Design tokens + full stylesheet, injected once
  components.py           Pure render functions (header, stepper, cards, verdict, footer)
core/
  models.py               Shared data contracts: AgentResult, Verdict, DebateState
  config.py               The five agent/provider configs, debate modes, key resolution
  api_client.py           Async OpenAI-compatible client with retry/backoff
  orchestrator.py         Staged pipeline, concurrent agents inside a stage, never raises
  exceptions.py           ConfigError, ApiError, ResponseFormatError
agents/
  base.py                 BaseAgent runner + verdict parsing
  strategist.py           Opening case FOR the proposition
  challenger.py           Opening case AGAINST the proposition
  researcher.py           Audits both openings for unsupported claims
  devils_advocate.py      Attacks both sides, surfaces overlooked perspectives
  supreme_judge.py        Scores both sides, delivers structured verdict
prompts/
  agent_prompts.py        Role system/user prompts
tests/
  smoke_orchestrator.py   Offline end-to-end pipeline proof (mocked clients)
  test_core_errors.py     Error-path verification for the LLM client
```

## Setup

Prerequisites: Python 3.11+.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
copy .env.example .env                          # then fill in your keys
```

Each agent needs its own provider key in `.env`:

| Variable            | Provider  | Console                                        |
| ------------------- | --------- | ---------------------------------------------- |
| `GEMINI_API_KEY`    | Google    | https://aistudio.google.com/apikey             |
| `DEEPSEEK_API_KEY`  | DeepSeek  | https://platform.deepseek.com                  |
| `MISTRAL_API_KEY`   | Mistral   | https://console.mistral.ai                     |
| `GLM_API_KEY`       | Z.ai GLM  | https://z.ai                                   |
| `NVIDIA_API_KEY`    | NVIDIA    | https://build.nvidia.com                       |

The app starts with any subset of keys: missing keys are listed in a banner at the top of the page and only the affected agents fail. With all five missing, the start button is disabled.

## Run

```bash
.venv/Scripts/streamlit run app.py
```

## How a debate runs

The orchestrator runs four stages in order, with the agents inside each stage running concurrently: (1) setup, (2) the Strategist and Challenger write opposing openings at the same time, (3) the Researcher audits and the Devil's Advocate attacks both openings concurrently, (4) the Supreme Judge receives everything and returns a structured verdict. The UI subscribes to `on_update` and re-renders the stage stepper and agent cards at every status change. A failing provider never aborts the debate: it is contained in that agent's card, and the judge still runs over whatever succeeded. If the judge itself fails, the four analyses stay on screen with an explanatory panel.

## Design notes

Dark dashboard on a fixed token palette (`--bg #0A0E14`, surfaces `#10151E`/`#151C27`); typography is Space Grotesk for display, Inter for body, JetBrains Mono for micro-labels, model chips and scores. Each agent keeps a permanent accent used on its card top line, glyph and stepper state: Strategist `#5B9DFF`, Challenger `#9B7BFF`, Researcher `#FF8A4C`, Devil's Advocate `#3ED6B5`, Supreme Judge `#D4AF37` (gold doubles as the verdict accent). All component styling lives in `ui/theme.py` as CSS custom properties; `.streamlit/config.toml` only pins the base palette for native widgets.

## Testing

Both scripts are plain Python, no network and no API keys required:

```bash
.venv/Scripts/python.exe tests/smoke_orchestrator.py
.venv/Scripts/python.exe tests/test_core_errors.py
```

`smoke_orchestrator.py` runs the full staged pipeline behind an injected mock client factory and proves the happy path, opening-failure tolerance, verdict tolerance, and that stage-2 agents actually run in parallel. `test_core_errors.py` proves the client behavior at the HTTP boundary: missing key raises `ConfigError`, 429-then-200 retries successfully, exhausted retries raise `ApiError`, 401 fails fast with the status code, and empty content raises `ResponseFormatError`.

## Honest limitations

- Scores and verdicts are model-generated qualitative assessments, not objective measurements.
- Live provider calls have not been tested end-to-end without API keys; the pipeline is verified offline against mocked clients only.
- The GLM model id `glm-5.3-flash` is configurable in `core/config.py`; if your Z.ai account uses a different id (e.g. `glm-4.6`), change it there. Provider model ids change often - alternates are noted next to each config.
