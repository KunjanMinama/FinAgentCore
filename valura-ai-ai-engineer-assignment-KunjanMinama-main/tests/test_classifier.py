"""
Tests for the Intent Classifier.

Uses a mock LLM to test:
  - Classifier output structure
  - Fallback behavior on LLM failure
  - Entity parsing
  - Agent routing with mocked responses
"""

import pytest
from unittest.mock import MagicMock

from src.classifier.classifier_model import IntentClassifier
from src.classifier.schema import (
    ClassifierOutput,
    ExtractedEntities,
    FALLBACK_CLASSIFIER_OUTPUT,
)
from src.memory.session_memory import SessionMemory


class TestClassifierWithMock:
    """Tests using a mock LLM (no real API calls)."""

    @pytest.fixture
    def memory(self):
        return SessionMemory(max_turns=10)

    def _make_mock_llm(self, response: dict):
        """Create a mock callable that returns a dict."""
        return MagicMock(return_value=response)

    @pytest.mark.asyncio
    async def test_basic_classification(self, memory):
        """Mock LLM returns a valid classification."""
        mock = self._make_mock_llm({
            "intent": "portfolio_health",
            "entities": {},
            "agent": "portfolio_health",
            "safety_verdict": "safe",
        })
        classifier = IntentClassifier(llm_callable=mock, memory=memory)
        result = await classifier.classify("how is my portfolio doing?")

        assert result.agent == "portfolio_health"
        assert result.intent == "portfolio_health"
        assert result.safety_verdict == "safe"

    @pytest.mark.asyncio
    async def test_entity_extraction(self, memory):
        """Mock LLM extracts entities correctly."""
        mock = self._make_mock_llm({
            "intent": "market_research",
            "entities": {"tickers": ["AAPL"], "time_period": "this_month"},
            "agent": "market_research",
            "safety_verdict": "safe",
        })
        classifier = IntentClassifier(llm_callable=mock, memory=memory)
        result = await classifier.classify("how is Apple doing this month?")

        assert result.agent == "market_research"
        assert "AAPL" in result.entities.tickers
        assert result.entities.time_period == "this_month"

    @pytest.mark.asyncio
    async def test_fallback_on_none(self, memory):
        """If mock returns None, classifier falls back."""
        mock = MagicMock(return_value=None)
        classifier = IntentClassifier(llm_callable=mock, memory=memory)
        result = await classifier.classify("some query")

        assert result.agent == "customer_support"
        assert result.intent == "fallback"

    @pytest.mark.asyncio
    async def test_fallback_on_exception(self, memory):
        """If mock raises exception, classifier falls back."""
        mock = MagicMock(side_effect=Exception("LLM failed"))
        classifier = IntentClassifier(llm_callable=mock, memory=memory)
        result = await classifier.classify("some query")

        assert result.agent == "customer_support"
        assert result.intent == "fallback"

    @pytest.mark.asyncio
    async def test_classifier_output_returns_directly(self, memory):
        """If mock returns a ClassifierOutput, it should be used directly."""
        expected = ClassifierOutput(
            intent="market_research",
            entities=ExtractedEntities(tickers=["NVDA"]),
            agent="market_research",
            safety_verdict="safe",
        )
        mock = MagicMock(return_value=expected)
        classifier = IntentClassifier(llm_callable=mock, memory=memory)
        result = await classifier.classify("tell me about NVIDIA")

        assert result is expected

    @pytest.mark.asyncio
    async def test_numeric_entities(self, memory):
        """Test parsing of numeric entities."""
        mock = self._make_mock_llm({
            "intent": "financial_calculator",
            "entities": {
                "amount": 2500,
                "frequency": "monthly",
                "period_years": 20,
                "rate": 0.08,
            },
            "agent": "financial_calculator",
            "safety_verdict": "safe",
        })
        classifier = IntentClassifier(llm_callable=mock, memory=memory)
        result = await classifier.classify(
            "if i invest 2500 monthly for 20 years at 8%"
        )

        assert result.entities.amount == 2500
        assert result.entities.frequency == "monthly"
        assert result.entities.period_years == 20
        assert result.entities.rate == 0.08


class TestClassifierSchema:
    """Tests for the schema models themselves."""

    def test_extracted_entities_to_dict_empty(self):
        """Empty entities should produce empty dict."""
        e = ExtractedEntities()
        assert e.to_dict() == {}

    def test_extracted_entities_to_dict_with_values(self):
        """Non-None/non-empty values should appear in dict."""
        e = ExtractedEntities(
            tickers=["AAPL", "MSFT"],
            amount=1000.0,
            currency="USD",
        )
        d = e.to_dict()
        assert d["tickers"] == ["AAPL", "MSFT"]
        assert d["amount"] == 1000.0
        assert d["currency"] == "USD"
        assert "topics" not in d  # empty list excluded
        assert "rate" not in d    # None excluded

    def test_classifier_output_to_dict(self):
        """ClassifierOutput.to_dict produces correct structure."""
        out = ClassifierOutput(
            intent="market_research",
            entities=ExtractedEntities(tickers=["AAPL"]),
            agent="market_research",
            safety_verdict="safe",
        )
        d = out.to_dict()
        assert d["intent"] == "market_research"
        assert d["agent"] == "market_research"
        assert d["safety_verdict"] == "safe"
        assert "AAPL" in d["entities"]["tickers"]

    def test_fallback_output(self):
        """Fallback output should route to customer_support."""
        assert FALLBACK_CLASSIFIER_OUTPUT.agent == "customer_support"
        assert FALLBACK_CLASSIFIER_OUTPUT.intent == "fallback"
        assert FALLBACK_CLASSIFIER_OUTPUT.safety_verdict == "uncertain"
