# Valura AI — Build Log

This file is updated every time a new file or feature is added.
Read this to know exactly what has been built and what is next.

---

## Legend
- ✅ Done and tested
- 🔨 In progress
- ⏳ Planned next
- 💤 Planned later

---

## STEP 1 — Pure Python Financial Calculations ✅
**Date:** 2026-06-10
**Files changed:**
- `requirements.txt` — added `numpy`, `pandas`, `groq`, `jinja2`
- `src/services/financial_calc.py` — [NEW] Pure Python math engine

**What it does:**
Handles ALL deterministic financial calculations with zero LLM calls:
- `compound_interest(principal, rate, years, n)` — standard compound formula
- `dca_projection(monthly, rate, years)` — dollar-cost averaging future value
- `fire_number(annual_expenses, swr)` — FIRE retirement target (default 4% rule)
- `loan_payment(principal, rate, years)` — monthly mortgage/loan payment
- `loan_amortization(principal, rate, years)` — full amortization schedule (first 12 months)
- `savings_to_goal(target, rate, years)` — how much to save monthly to hit a goal
- `inflation_adjusted(amount, inflation_rate, years)` — real purchasing power

**Why no LLM:** Math is exact. LLMs get arithmetic wrong. These functions are deterministic and testable.

**How to verify it works:**
```python
from src.services.financial_calc import compound_interest
result = compound_interest(10000, 0.08, 10)
# Returns: {'final_amount': 21589.25, 'total_interest': 11589.25, ...}
```

---

## STEP 2 — Technical Indicators (RSI, MACD, SMA) ⏳
**Planned files:**
- `src/services/tech_analysis.py` — RSI, MACD, SMA20/50/200, Bollinger Bands

---

## STEP 3 — Risk Math (VaR, Sharpe, Beta) ⏳
**Planned files:**
- `src/services/risk_math.py` — VaR, Sharpe ratio, Beta, max drawdown

---

## STEP 4 — ETF Database (Product Recommendation data) ⏳
**Planned files:**
- `src/services/etf_database.py` — Curated ETF lookup by risk profile + goal

---

## STEP 5 — LLM Provider Abstraction (Groq + Gemini fallback) ⏳
**Planned files:**
- `src/services/llm_provider.py` — Multi-provider: Groq → Gemini → OpenAI

---

## STEP 6 — financial_calculator Agent ⏳
**Planned files:**
- `src/agents/financial_calculator.py` — Tier 1 agent using financial_calc.py

---

## STEP 7 — risk_assessment Agent ⏳
**Planned files:**
- `src/agents/risk_assessment.py` — Tier 1 agent using risk_math.py

---

## STEP 8 — predictive_analysis Agent ⏳
**Planned files:**
- `src/agents/predictive_analysis.py` — Tier 1 agent using tech_analysis.py

---

## STEP 9 — market_research Agent ⏳
**Planned files:**
- `src/agents/market_research.py` — Tier 2: yfinance data + Jinja2 template

---

## STEP 10 — investment_strategy Agent ⏳
**Planned files:**
- `src/agents/investment_strategy.py` — Tier 2: rule engine + optional Groq

---

## STEP 11 — product_recommendation Agent ⏳
**Planned files:**
- `src/agents/product_recommendation.py` — Tier 2: ETF database lookup

---

## STEP 12 — financial_planning Agent ⏳
**Planned files:**
- `src/agents/financial_planning.py` — Tier 3: math + Groq narrative

---

## STEP 13 — customer_support Agent ⏳
**Planned files:**
- `src/services/faq_store.py` — FAQ dictionary
- `src/agents/customer_support.py` — Tier 3: FAQ first, Groq fallback

---

## STEP 14 — general_query Agent ⏳
**Planned files:**
- `src/agents/general_query.py` — Tier 3: Groq educational Q&A

---

## STEP 15 — Register All Agents in AgentManager ⏳
**Files changed:**
- `src/agents/agent_manager.py` — wire in all new agents

---

## STEP 16 — Chat Frontend ⏳
**Planned files:**
- `src/static/index.html` — streaming chat UI
- `src/static/style.css`
- `src/static/app.js`
- `src/api/router.py` — add static file serving

---

## STEP 17 — Docker ⏳
**Planned files:**
- `Dockerfile`
- `docker-compose.yml`

---

*This log is updated after every completed step.*
