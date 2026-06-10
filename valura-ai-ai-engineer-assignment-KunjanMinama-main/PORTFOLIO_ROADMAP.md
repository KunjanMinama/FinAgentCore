# Valura AI — Portfolio Showcase Roadmap

To turn this assignment into a jaw-dropping portfolio piece that proves you are a senior AI Engineer, here is the exact roadmap of what remains to be built.

---

## Phase 1: Implement the Remaining Agents (The Intelligence)

Right now, 9 agents are currently stubs (`src/agents/stubs.py`). You need to build them out. 

1. **`market_research`**: 
   - **What it does:** Fetches real-time stock quotes, news, and fundamentals.
   - **How to build it:** Integrate an external API (like AlphaVantage, Yahoo Finance via `yfinance`, or an MCP server). Use the LLM to summarize the fetched data.
2. **`financial_calculator`**:
   - **What it does:** Calculates compound interest, loan amortizations, and retirement projections.
   - **How to build it:** Do **not** use an LLM for the math. Build pure Python calculation functions, and use the LLM only to format the final answer.
3. **`risk_assessment` & `investment_strategy`**:
   - **What it does:** Analyzes the user's KYC data and risk profile to suggest broad asset allocations.
4. **`product_recommendation`**:
   - **What it does:** Suggests specific ETFs or bonds based on the strategy.
5. **`predictive_analysis`**:
   - **What it does:** Basic technical analysis (moving averages, RSI) based on historical price data.
6. **`financial_planning`, `customer_support`, `general_query`**:
   - **What they do:** Conversational agents powered heavily by the LLM and specific system prompts.

---

## Phase 2: Production-Ready Engineering (The Infrastructure)

These are the "stretch goals" from the assignment that separate junior developers from senior engineers.

1. **Persistent Session Memory (Redis/Postgres)**
   - Swap out your in-memory dictionary in `SessionMemory`.
   - Connect it to a real Redis cache or Postgres database so sessions survive server restarts.
2. **LLM Deduplication Cache (Cost Savings)**
   - Hash incoming user queries. If a novice asks "What is an ETF?", check Redis first. If it exists, return the cached answer instantly instead of paying for another OpenAI call.
3. **Semantic Embedding Pre-Classifier (Latency Reduction)**
   - Instead of always calling `gpt-4o-mini` to classify intent, generate a fast local embedding of the user's query.
   - Do a cosine-similarity search against a database of known intents. If confidence is >95%, skip the LLM entirely and route directly to the agent.
4. **Multi-Tenant Rate Limiting**
   - Implement `slowapi` or a custom Redis rate limiter in FastAPI to prevent abuse.

---

## Phase 3: Deployment & Presentation (The Showcase)

To actually show this off to future employers, they need to be able to use it.

1. **Dockerization**
   - Create a `Dockerfile` for the FastAPI backend.
   - Create a `docker-compose.yml` that spins up the backend, a Redis container, and a Postgres container simultaneously.
2. **Build a Simple Frontend**
   - Evaluators don't want to use `curl`. Build a basic React (Vite) or plain HTML/JS chat interface.
   - It must support consuming Server-Sent Events (SSE) so the streaming text looks like ChatGPT.
3. **Cloud Deployment**
   - Deploy the backend and frontend to a platform like **Railway**, **Render**, or **AWS (ECS)**.
   - Ensure you securely inject your real `OPENAI_API_KEY` via cloud environment variables.
4. **Live Demo Link**
   - Update your `README.md` with a link to the live, working application.
