# Valura AI Agent Manager — Build Summary

## ✅ All 52 Tests Passing

```text
tests/test_agent_manager.py     — 8 passed  (routing, stubs, error isolation)
tests/test_classifier.py        — 10 passed (mock LLM, schemas, fallback)
tests/test_routing.py           — 10 passed (gold accuracy, entity normalization)
tests/test_safety.py            — 8 passed  (recall ≥95%, passthrough ≥90%)
tests/test_portfolio_health.py  — 16 passed (all 5 user profiles + edge cases + skeleton tests)
```
 
## 📂 Files Generated

### Source (`src/`)
| File | Purpose |
|---|---|
| [main.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/main.py) | FastAPI app entry point |
| [api/router.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/api/router.py) | POST /query pipeline endpoint |
| [api/sse.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/api/sse.py) | SSE event formatting |
| [core/config.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/core/config.py) | Pydantic settings from .env |
| [core/logger.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/core/logger.py) | Structured logging |
| [safety/guard.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/safety/guard.py) | Pre-LLM safety filter (<1ms) |
| [safety/rules.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/safety/rules.py) | 7-category regex/keyword matchers |
| [classifier/classifier_model.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/classifier/classifier_model.py) | Single-LLM-call classifier |
| [classifier/schema.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/classifier/schema.py) | Pydantic models (ClassifierOutput, ExtractedEntities) |
| [classifier/followup.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/classifier/followup.py) | Follow-up resolution via context injection |
| [memory/session_memory.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/memory/session_memory.py) | Thread-safe in-memory session store |
| [agents/base.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/agents/base.py) | Abstract agent interface + error isolation |
| [agents/agent_manager.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/agents/agent_manager.py) | Central orchestrator |
| [agents/portfolio_health.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/agents/portfolio_health.py) | Fully implemented health check agent |
| [agents/stubs.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/agents/stubs.py) | Stub agents for 9 unimplemented types |
| [services/market_data.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/services/market_data.py) | yfinance + mock fallback |
| [services/portfolio_math.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/src/services/portfolio_math.py) | Pure portfolio computation |

### Tests (`tests/`)
| File | Purpose |
|---|---|
| [conftest.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/tests/conftest.py) | Fixtures, mocks, entity matchers |
| [test_safety.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/tests/test_safety.py) | Safety recall/passthrough/performance |
| [test_classifier.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/tests/test_classifier.py) | Classifier with mock LLM |
| [test_agent_manager.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/tests/test_agent_manager.py) | Routing + error isolation |
| [test_routing.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/tests/test_routing.py) | Gold-standard routing accuracy |
| [test_portfolio_health.py](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/tests/test_portfolio_health.py) | All 5 user profiles + edge cases |

### Root
| File | Purpose |
|---|---|
| [README.md](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/README.md) | Architecture, setup, decisions, test strategy |
| [requirements.txt](file:///c:/Users/ASUS/Downloads/valura-ai-ai-engineer-assignment-KunjanMinama-main/valura-ai-ai-engineer-assignment-KunjanMinama-main/requirements.txt) | Updated with pydantic-settings + yfinance |

## 🏗️ Architecture Highlights

1. **Safety Guard** — 7 categories, <0.2ms, educational whitelist, distinct refusal messages
2. **Intent Classifier** — Single LLM call, 10-agent taxonomy, structured JSON output
3. **Follow-up Resolution** — Context injection into prompt (not a separate LLM call)
4. **Agent Manager** — Deterministic routing, error isolation per agent, extensible registry
5. **Portfolio Health** — Full implementation: concentration risk, performance, benchmark comparison, observations, empty portfolio handling
6. **SSE Streaming** — Typed events: `data`, `error`, `safety_block`, `end`
7. **Session Memory** — Thread-safe in-memory dict, last 3 turns, entity/agent history
