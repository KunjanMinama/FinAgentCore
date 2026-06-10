# Valura AI — Agent Manager Microservice

> AI co-investor for every user — helping investors BUILD, MONITOR, GROW, and PROTECT their wealth.

---

## 🎥 Submission Video

> [!IMPORTANT]
>
> [!WATCH THE VIDEO HERE](https://www.youtube.com/watch?v=7t_drgTytd4)
>


---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     POST /query                               │
│                   (FastAPI + SSE)                              │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│      Safety Guard        │  ◀── Pure Python, <1ms, no LLM
│   (regex + keywords)     │      Blocks harmful intent
└──────────────┬───────────┘
               │ (if safe)
               ▼
┌──────────────────────────┐
│   Intent Classifier      │  ◀── Single LLM call (gpt-4o-mini)
│   (structured output)    │      Returns intent + entities + agent
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│     Agent Manager        │  ◀── Routes to specialist agent
│   (orchestrator)         │      Error isolation per agent
└──────────────┬───────────┘
               │
      ┌────────┼────────┐
      ▼        ▼        ▼
┌──────────┐ ┌────────┐ ┌──────────┐
│Portfolio │ │ Stub   │ │  Stub    │
│Health ✅ │ │Agents  │ │ Agents   │
│(full)    │ │(9 more)│ │          │
└──────────┘ └────────┘ └──────────┘
               │
               ▼
┌──────────────────────────┐
│    SSE Stream Response   │  ◀── data | error | safety_block | end
└──────────────────────────┘
```

### Request Flow

1. **Safety Guard** — Synchronous, <1ms. Regex/keyword matching against 7 harmful categories. Educational queries whitelisted. If blocked → immediate `safety_block` SSE event.
2. **Intent Classifier** — One OpenAI API call. Returns structured JSON: intent, entities, target agent, safety verdict. Follow-up resolution via session context injection.
3. **Agent Manager** — Deterministic routing. Portfolio Health → full implementation. All others → structured stub. Error isolation: agent failures convert to safe messages.
4. **SSE Stream** — Response streamed as Server-Sent Events with typed event names.

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key

### Setup

```bash
# 1. Clone and enter
git clone <repo-url>
cd valura-ai-agent-manager

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Run tests (no API key needed — LLM is mocked)
pytest tests/ -v

# 6. Start the server
uvicorn src.main:app --reload --port 8000
```

### Test the API

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "how is my portfolio doing?", "user_id": "usr_001", "session_id": "test-1"}'
```

---

## 📁 Project Structure

```
src/
├── main.py                      # FastAPI app entry point
├── api/
│   ├── router.py                # POST /query endpoint + pipeline
│   └── sse.py                   # SSE event formatting utilities
├── core/
│   ├── config.py                # Pydantic settings from .env
│   └── logger.py                # Structured logging setup
├── safety/
│   ├── guard.py                 # Pre-LLM safety filter
│   └── rules.py                 # Hardcoded category matchers
├── classifier/
│   ├── classifier_model.py      # Single-LLM-call intent classifier
│   ├── schema.py                # Pydantic models for classifier I/O
│   └── followup.py              # Follow-up resolution logic
├── memory/
│   └── session_memory.py        # In-memory session store
├── agents/
│   ├── base.py                  # Abstract agent interface
│   ├── agent_manager.py         # Central orchestrator
│   ├── portfolio_health.py      # Fully implemented agent
│   └── stubs.py                 # Stub agents for unimplemented types
└── services/
    ├── market_data.py           # yfinance + mock fallback
    └── portfolio_math.py        # Pure computation functions

tests/
├── conftest.py                  # Fixtures, LLM mocking, entity matchers
├── test_safety.py               # Safety guard recall/passthrough
├── test_classifier.py           # Classifier with mock LLM
├── test_agent_manager.py        # Routing + error isolation
├── test_routing.py              # Gold-standard routing accuracy
└── test_portfolio_health.py     # All user profiles + edge cases
```

---

## 🔧 Dependency Justification

| Dependency | Why |
|---|---|
| **FastAPI** | Assignment requirement. Async, fast, built-in validation. |
| **sse-starlette** | SSE streaming required by assignment. Minimal, well-maintained. |
| **pydantic / pydantic-settings** | Typed config and schema validation. Catches bugs at parse time. |
| **openai** | Official SDK for structured outputs. Supports JSON mode natively. |
| **yfinance** | Assignment says "do not hardcode market data". Free, no API key, covers all fixture exchanges (NASDAQ, NYSE, EURONEXT, LSE, TSE). |
| **python-dotenv** | Load .env files. Standard practice. |
| **httpx** | Async HTTP client for testing. Ships with FastAPI TestClient. |
| **pytest / pytest-asyncio** | Assignment requirement. Industry standard. |

---

## 🔐 Safety Guard

### How It Works

Pure Python. No network calls. No LLM calls. Pre-compiled regex patterns + keyword sets.

**Categories covered:**
- `insider_trading` — MNPI, tipping, front-running
- `market_manipulation` — pump & dump, wash trading, spoofing
- `money_laundering` — structuring, source obscuring, reporting evasion
- `guaranteed_returns` — impossible promises, Ponzi-style claims
- `reckless_advice` — all-in crypto at 70, margin on single stocks
- `sanctions_evasion` — OFAC circumvention, shell companies
- `fraud` — fake documents, fabricated losses

**Educational whitelist:** Queries containing educational markers (`what is`, `explain`, `how does`, `penalty for`, `risks of`, etc.) pass through even if they mention harmful topics.

### Tradeoff

We accept a small risk of over-blocking on edge cases where harmful keywords overlap with legitimate educational phrasing that our whitelist doesn't capture. For a financial platform, erring on the side of safety is the correct default. The README and code document this explicitly.

**Performance:** <0.2ms per query on commodity hardware.

---

## 🧠 Intent Classifier

### Single LLM Call

One call to `gpt-4o-mini` (dev) / `gpt-4.1` (eval) returns:
- **Intent** — classified label
- **Entities** — tickers, amounts, currencies, rates, periods, etc.
- **Agent** — target specialist from the 10-agent taxonomy
- **Safety verdict** — informational only (safe/uncertain/risky)

### Follow-up Resolution

Session memory (last 3 turns) is injected into the classifier prompt as conversation context. The LLM handles:
- **Pronoun resolution**: "how much do I own?" → carries NVDA from prior turn
- **Entity switching**: "what about AMD?" → new ticker, same intent type
- **Comparison**: "compare them" → carries all mentioned tickers
- **Topic switching**: calculator question after portfolio check → no carryover
- **Conversational closers**: "thx" → general_query, no specialist

### Failure Fallback

If the LLM call fails (timeout, API error, malformed response), the classifier returns a default output routing to `customer_support` with `safety_verdict: "uncertain"`. The pipeline never crashes.

---

## 📊 Portfolio Health Agent

The first (and only fully implemented) specialist agent.

### Output Structure

```json
{
  "concentration_risk": {
    "top_position_pct": 60.4,
    "top_3_positions_pct": 78.2,
    "flag": "high",
    "top_position_ticker": "NVDA"
  },
  "performance": {
    "total_return_pct": 18.4,
    "annualized_return_pct": 12.1,
    "total_value": 125000.00,
    "total_cost": 105600.00
  },
  "benchmark_comparison": {
    "benchmark": "S&P 500",
    "portfolio_return_pct": 18.4,
    "benchmark_return_pct": 14.2,
    "alpha_pct": 4.2
  },
  "holdings": [...],
  "observations": [
    {"severity": "warning", "text": "60.4% of portfolio in NVDA — highly concentrated..."},
    {"severity": "info", "text": "Outperforming S&P 500 by 4.2%..."}
  ],
  "disclaimer": "This is not investment advice..."
}
```

### Edge Cases

| User | Scenario | Behavior |
|---|---|---|
| `usr_001` | Active trader, 9 holdings | Full analysis with benchmark |
| `usr_003` | ~60% NVDA | High concentration warning |
| `usr_004` | Empty portfolio | BUILD-oriented guidance, no crash |
| `usr_006` | Multi-currency | All currencies handled, no crash |
| `usr_008` | Retiree | Income-focused observations |

---

## 💰 Cost & Performance

### Cost Analysis

| Component | Tokens (est.) | Cost at gpt-4o-mini | Cost at gpt-4.1 |
|---|---|---|---|
| System prompt | ~800 tokens | — | — |
| User query + context | ~200 tokens | — | — |
| Response | ~200 tokens | — | — |
| **Total per query** | ~1,200 tokens | **~$0.001** | **~$0.02** |

Well under the $0.05/query target.

### Performance

| Metric | Target | Achieved |
|---|---|---|
| Safety guard latency | <10ms | <0.2ms |
| p95 first-token latency | <2s | ~1.2s (gpt-4o-mini) |
| p95 end-to-end | <6s | ~2.5s (with market data) |

**Measurement method:** `time.perf_counter()` around each pipeline stage. Safety guard measured in test suite (see `test_safety.py::test_safety_performance`).

---

## 🧪 Test Strategy

### Running Tests

```bash
# All tests — no API key needed
pytest tests/ -v

# Specific modules
pytest tests/test_safety.py -v
pytest tests/test_portfolio_health.py -v
```

### What's Tested

| Module | What | Threshold |
|---|---|---|
| `test_safety.py` | Guard recall on harmful queries | ≥95% |
| `test_safety.py` | Guard passthrough on educational | ≥90% |
| `test_classifier.py` | Classifier with mock LLM | Structure + fallback |
| `test_routing.py` | Routing accuracy (gold queries) | ≥85% |
| `test_routing.py` | Entity matching normalization | Subset + ±5% |
| `test_agent_manager.py` | Agent routing + error isolation | All agents |
| `test_portfolio_health.py` | All 5 user profiles | Including empty |

### LLM Mocking

All tests use `MagicMock` for the LLM callable. The `IntentClassifier` accepts an optional `llm_callable` parameter — in tests, we inject a mock that returns expected classifications. This means:
- Tests run without `OPENAI_API_KEY`
- Tests are deterministic
- Tests are fast (<2s total)

---

## 🔌 How to Extend with More Agents

Adding a new specialist agent requires exactly 3 steps:

### 1. Create the Agent

```python
# src/agents/my_new_agent.py
from src.agents.base import BaseAgent

class MyNewAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "market_research"  # matches classifier taxonomy

    async def execute(self, classifier_output, user_profile):
        # Your logic here
        return {"agent": self.agent_id, "data": "..."}
```

### 2. Register It

```python
# src/agents/agent_manager.py — in __init__
self._agents = {
    "portfolio_health": PortfolioHealthAgent(),
    "market_research": MyNewAgent(),  # ← add here
}
```

### 3. Add Tests

```python
# tests/test_my_new_agent.py
@pytest.mark.asyncio
async def test_my_agent(load_user):
    agent = MyNewAgent()
    result = await agent.execute(classifier_output, load_user("usr_001"))
    assert "data" in result
```

No changes to the classifier, safety guard, or HTTP layer. The router handles it automatically.

---

## 🎥 Video Walkthrough (Defence)

Here is the link to my 10-minute video walkthrough covering the architecture, technical tradeoffs, and future improvements: 
[Watch the Video Here](https://www.youtube.com/watch?v=7t_drgTytd4)

---

## 📋 Environment Variables

See `.env.example` for all variables. Required:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | Model to use (default: `gpt-4o-mini`) |

Optional:

| Variable | Description |
|---|---|
| `APP_ENV` | `development` / `production` / `test` |
| `LOG_LEVEL` | Logging level (default: `INFO`) |

---

## 🛡️ Session Memory

**Backend:** In-memory dictionary keyed by `session_id`.

**Why in-memory?** The assignment explicitly allows it. For this evaluation context:
- Zero infrastructure dependency
- Instant startup
- Sufficient for demo runs
- The interface (`SessionMemory`) is designed for easy swap to Redis/Postgres

**What's stored per session:**
- Last 3 user turns (configurable)
- Extracted entities per turn
- Classified agent per turn
- Intent per turn

**Thread safety:** Protected by `threading.Lock` for concurrent requests.

---

*Built for the Valura AI Team Lead assignment. All code in `src/`, all tests in `tests/`, all tests pass with `pytest tests/ -v`.*
