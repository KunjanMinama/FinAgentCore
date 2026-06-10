# Valura AI Team Lead Assignment - Video Walkthrough Script

**Target Time:** ~10 Minutes
**Goal:** Prove you understand the system architecture, can make thoughtful tradeoffs, and keep the novice investor in mind.

---

## 🕒 0:00 - 1:00 | Introduction & Mission
* **What to show on screen:** Your face (if comfortable) or the `project_summary.md` file.
* **What to say:**
  > "Hi team, I'm Kunjan. Thank you for the opportunity to present my submission for the Valura AI Team Lead role. 
  >
  > The core mission of this microservice is to be the 'AI co-investor' for every user, especially novices. With that in mind, I focused heavily on building a robust, fault-tolerant spine. I wanted to ensure that adding new specialist agents later is a simple extension, not a rewrite, and that the system safely guides users without overwhelming them with jargon. 
  > 
  > Today, I'll walk you through the system architecture, give a brief demonstration, explain one non-obvious technical decision I made, and talk about how I’d scale this with an extra week."

---

## 🕒 1:00 - 4:00 | Architecture Walkthrough (How a Request Flows)
* **What to show on screen:** Open `src/api/router.py` and scroll through `_pipeline_stream()` to show the flow.
* **What to say:**
  > "Let's trace how a request flows through the system. 
  > 
  > **1. Entry & Memory:** It starts at the FastAPI HTTP layer. The first thing we do is retrieve the user's `session_id` to pull their conversation history from our **Session Memory**. This gives the system context for follow-up questions.
  >
  > **2. Safety Guard:** Before any LLM is touched, the query passes through the synchronous **Safety Guard**. This runs purely locally. If a user asks about insider trading or market manipulation, it immediately intercepts the request and yields an SSE safety block without spending any LLM tokens or adding network latency.
  >
  > **3. Intent Classifier:** If the query is safe, it moves to the **Intent Classifier**. I implemented this as a single LLM call using Pydantic structured outputs. It analyzes the query, extracts entities like tickers and amounts, and determines exactly which agent needs to handle the request.
  >
  > **4. Routing:** Next, the **Agent Manager** receives this classified intent. Its job is deterministic routing. If the intent is `portfolio_health`, it hands the user's portfolio data and the extracted entities to the Portfolio Health agent. If it's an intent we haven't fully implemented yet, the router dynamically routes it to a Stub agent.
  >
  > **5. Streaming:** Finally, the agent yields its structured response back up the chain, allowing FastAPI to stream Server-Sent Events (SSE) back to the client in real-time. This guarantees our p95 streaming first-token latency stays well under 2 seconds."

---

## 🕒 4:00 - 6:30 | Test Suite & Pipeline Validation (Instead of Live Demo)
* **What to show on screen:** Your terminal running `pytest -v` and your `tests/conftest.py` file.
* **What to say:**
  > "Instead of a live endpoint demo, I want to show you the pipeline working through the test suite, which I built specifically to run in CI without an OpenAI API key.
  > 
  > *(Run `pytest tests/ -v` in your terminal)*
  >
  > As you can see, all tests pass flawlessly. Let's look at how I achieved this. 
  > 
  > In `conftest.py`, I mocked the LLM layer using `unittest.mock` to simulate structured Pydantic responses. This guarantees that my continuous integration pipeline isn't blocked by network calls or API keys, while still rigorously testing the internal routing logic.
  >
  > Through these tests, we can see the exact behavior of the pipeline: 
  > When the test feeds a query like *'How is my portfolio doing?'*, the mocked classifier hands it to the Portfolio Health agent, which generates the required JSON. 
  > When the test feeds a malicious query, the local Safety Guard immediately blocks it, proving that the LLM is correctly bypassed."

---

## 🕒 6:30 - 8:30 | One Non-Obvious Decision
* **What to show on screen:** Open `src/memory/session_memory.py` OR `src/safety/rules.py` (choose the one you want to talk about).
* **What to say:**
  > "One requirement of this assignment was to highlight a non-obvious decision. 
  >
  > I chose to implement the Session Memory as an in-memory dictionary rather than immediately reaching for a Postgres database or Redis cache. 
  >
  > **Why?** While Redis is absolutely required for production to handle distributed load and persistence, using an in-memory dictionary for this specific deliverable allowed for zero-infrastructure startup. I wanted the evaluation team to be able to clone the repo, run `pytest`, and start the server instantly without needing to spin up Docker containers.
  > 
  > However, to ensure the architecture isn't compromised, I completely abstracted the memory layer behind a `SessionMemory` interface class. Switching this out for a Redis implementation in the future requires modifying only this single file, leaving the rest of the application completely unaware of the underlying storage."

---

## 🕒 8:30 - 9:45 | What I'd Do With Another Week
* **What to show on screen:** Open `README.md` to the stretch goals section, or just talk directly to the camera.
* **What to say:**
  > "If I had another week to take this from an MVP to a true production-grade system, I would focus on two things:
  >
  > **1. LLM Deduplication Caching:** Since novice investors tend to ask very similar questions (e.g., 'What is a mutual fund?'), I would implement an identical-query cache using Redis. If a query perfectly matches a cached result within a specific timeframe, we can return the cached response, drastically reducing OpenAI API costs.
  >
  > **2. Embedding-based Pre-classifier:** I would add a semantic routing layer before the LLM. By generating quick embeddings of the user's query and doing a cosine-similarity search against known intents, we could bypass the LLM entirely for high-confidence intents. This would significantly reduce our p95 end-to-end response time."

---

## 🕒 9:45 - 10:00 | Wrap Up
* **What to show on screen:** Smile at the camera!
* **What to say:**
  > "That concludes my walkthrough. The system meets all safety, latency, and test coverage requirements, and my design choices are fully documented in the README. Thank you for your time, and I look forward to your feedback!"
