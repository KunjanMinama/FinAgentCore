"""
Intent Classifier — single LLM call per classification.

Architecture:
  1. Build context from session memory (follow-up resolution)
  2. Construct a structured prompt with the agent taxonomy
  3. Make ONE OpenAI API call with JSON response format
  4. Parse into ClassifierOutput
  5. On ANY failure → return FALLBACK_CLASSIFIER_OUTPUT (routes to customer_support)

The classifier is designed for the `gpt-4o-mini` model during development
and `gpt-4.1` during evaluation. Both support structured JSON output.
"""

from __future__ import annotations

import json
import asyncio
from typing import Any, Callable, Optional

from openai import AsyncOpenAI

from src.classifier.followup import build_context_prompt
from src.classifier.schema import (
    ClassifierOutput,
    ExtractedEntities,
    FALLBACK_CLASSIFIER_OUTPUT,
)
from src.core.config import get_settings
from src.core.logger import get_logger
from src.memory.session_memory import SessionMemory, get_session_memory

logger = get_logger(__name__)

# ────────────────────────────────────────────────────────────
# System prompt (the core of the classifier)
# ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the intent classifier for Valura.ai, a wealth management platform.
Your job is to classify user queries into the correct agent and extract all relevant entities.

AGENT TAXONOMY (you MUST use exactly one of these agent names):
- portfolio_health: structured assessment of the user's portfolio (concentration, performance, benchmarking, observations)
- market_research: factual/recent info about an instrument, sector, or market event
- investment_strategy: advice/strategy questions — should I buy/sell/rebalance, allocation guidance
- financial_planning: long-term planning — retirement, goals, savings rate
- financial_calculator: deterministic numerical computation — DCA returns, mortgage, tax, future value, FX conversion
- risk_assessment: risk metrics, exposure analysis, what-if scenarios
- product_recommendation: recommend specific products/funds matching user profile
- predictive_analysis: forward-looking analysis — forecasts, trend extrapolation
- customer_support: platform issues, account questions, how-to-use-app
- general_query: educational, conversational, definitions, greetings

ENTITY EXTRACTION RULES:
- tickers: uppercase, exchange-suffixed where relevant (AAPL, ASML.AS, 7203.T). Map company names to tickers (Apple→AAPL, Nvidia→NVDA, Microsoft→MSFT, Tesla→TSLA, Google→GOOGL, Amazon→AMZN, Meta→META, AMD→AMD, HSBC→HSBA.L, Barclays→BARC.L, Toyota→7203.T, ASML→ASML.AS). Gold→GOLD.
- amount: numeric value in the unit of currency
- currency: ISO 4217 (USD, EUR, GBP, JPY)
- rate: decimal (e.g. 0.08 for 8%)
- period_years: integer
- frequency: one of daily, weekly, monthly, yearly
- horizon: one of 6_months, 1_year, 5_years
- time_period: one of today, this_week, this_month, this_year
- topics: descriptive topic keywords — include FX for forex queries, DCA for dollar-cost averaging, LTCG for long-term capital gains
- sectors: industry sectors (e.g. technology)
- index: exact name — S&P 500, FTSE 100, NIKKEI 225, MSCI World
- action: one of buy, sell, hold, hedge, rebalance
- goal: one of retirement, education, house, FIRE, emergency_fund

SAFETY VERDICT:
Return one of: safe, uncertain, risky
- safe: normal financial query
- uncertain: borderline but probably fine
- risky: potentially harmful but not blocked (safety guard handles blocking)

MULTI-INTENT QUERIES:
When a query contains multiple intents (e.g. "how is my portfolio and what should I sell?"),
route to the PRIMARY intent (the first/most important one).

FOLLOW-UP HANDLING:
If conversation history is provided, use it to resolve pronouns and references.
But if the current query is clearly a NEW topic, do NOT carry forward stale entities.

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{
    "intent": "string",
    "entities": {
        "tickers": [],
        "topics": [],
        "sectors": [],
        "amount": null,
        "currency": null,
        "rate": null,
        "period_years": null,
        "index": null,
        "action": null,
        "goal": null,
        "frequency": null,
        "horizon": null,
        "time_period": null
    },
    "agent": "string (from taxonomy above)",
    "safety_verdict": "safe|uncertain|risky"
}"""


class IntentClassifier:
    """
    Single-LLM-call intent classifier.

    Can be initialized with a custom LLM callable for testing (mock_llm).
    """

    def __init__(
        self,
        llm_callable: Optional[Callable] = None,
        memory: Optional[SessionMemory] = None,
    ):
        self._llm_callable = llm_callable
        self._memory = memory or get_session_memory()
        self._settings = get_settings()

    async def classify(
        self,
        query: str,
        session_id: str = "default",
        prior_turns_override: list[str] | None = None,
    ) -> ClassifierOutput:
        """
        Classify a user query into an intent + entities + agent.

        Args:
            query: The user's current query.
            session_id: Session identifier for memory lookup.
            prior_turns_override: Override prior turns (for testing).

        Returns:
            ClassifierOutput with intent, entities, agent, safety_verdict.
        """
        try:
            # Build context from session memory or overrides
            context = build_context_prompt(
                session_id=session_id,
                current_query=query,
                memory=self._memory,
                prior_turns_override=prior_turns_override,
            )

            # Build user message
            if context:
                user_message = f"{context}\n\nClassify the CURRENT QUERY above."
            else:
                user_message = f"Classify this query: \"{query}\""

            # Call LLM (mock or real)
            if self._llm_callable is not None:
                raw_result = self._llm_callable(query, context)
                if isinstance(raw_result, ClassifierOutput):
                    return raw_result
                if isinstance(raw_result, dict):
                    return self._parse_response(raw_result)
                return FALLBACK_CLASSIFIER_OUTPUT
            else:
                return await self._call_openai(user_message)

        except Exception as e:
            logger.error(f"Classifier failed: {e}")
            return FALLBACK_CLASSIFIER_OUTPUT

    async def _call_openai(self, user_message: str) -> ClassifierOutput:
        """Make the actual OpenAI API call."""
        try:
            client = AsyncOpenAI(api_key=self._settings.openai_api_key)

            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self._settings.openai_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=500,
                ),
                timeout=self._settings.llm_timeout_seconds,
            )

            content = response.choices[0].message.content
            if not content:
                logger.warning("Empty LLM response — using fallback")
                return FALLBACK_CLASSIFIER_OUTPUT

            data = json.loads(content)
            return self._parse_response(data)

        except asyncio.TimeoutError:
            logger.error("LLM call timed out")
            return FALLBACK_CLASSIFIER_OUTPUT
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return FALLBACK_CLASSIFIER_OUTPUT

    def _parse_response(self, data: dict) -> ClassifierOutput:
        """Parse raw dict into ClassifierOutput, with defensive handling."""
        try:
            entities_data = data.get("entities", {})
            entities = ExtractedEntities(
                tickers=entities_data.get("tickers", []),
                topics=entities_data.get("topics", []),  
                sectors=entities_data.get("sectors", []),
                amount=entities_data.get("amount"),
                currency=entities_data.get("currency"),
                rate=entities_data.get("rate"),
                period_years=entities_data.get("period_years"),
                index=entities_data.get("index"),
                action=entities_data.get("action"),
                goal=entities_data.get("goal"),
                frequency=entities_data.get("frequency"),
                horizon=entities_data.get("horizon"),
                time_period=entities_data.get("time_period"),
            )

            return ClassifierOutput(
                intent=data.get("intent", "unknown"),
                entities=entities,
                agent=data.get("agent", "customer_support"),
                safety_verdict=data.get("safety_verdict", "safe"),
            )
        except Exception as e:
            logger.error(f"Failed to parse classifier response: {e}")
            return FALLBACK_CLASSIFIER_OUTPUT
