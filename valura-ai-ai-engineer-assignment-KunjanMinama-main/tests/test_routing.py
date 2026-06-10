"""
Tests for routing accuracy against the gold-standard fixture.

Uses a mock LLM that returns the expected classification for each query,
validating that the pipeline wiring (classifier → entity parsing → routing)
works correctly end-to-end.

Also tests entity matching with the normalization rules from fixtures/README.md.
"""

import pytest
from unittest.mock import MagicMock

from src.classifier.classifier_model import IntentClassifier
from src.classifier.schema import ClassifierOutput, ExtractedEntities
from src.memory.session_memory import SessionMemory
from tests.conftest import entities_match, normalize_ticker


class TestRoutingAccuracy:
    """Validate routing against fixtures/test_queries/intent_classification.json."""

    @pytest.fixture
    def memory(self):
        return SessionMemory(max_turns=10)

    @pytest.mark.asyncio
    async def test_routing_accuracy_with_mock(
        self, gold_classifier_queries, memory
    ):
        """
        Simulate classifier routing by feeding expected results through mock.

        This validates the pipeline wiring, not the LLM itself.
        The ≥85% threshold is for real LLM testing; with mocks we expect 100%.
        """
        correct = 0
        total = len(gold_classifier_queries)

        for q in gold_classifier_queries:
            # Mock returns the expected output
            expected_agent = q["expected_agent"]
            expected_entities = q.get("expected_entities", {})

            mock = MagicMock(return_value={
                "intent": expected_agent,
                "entities": expected_entities,
                "agent": expected_agent,
                "safety_verdict": "safe",
            })

            classifier = IntentClassifier(llm_callable=mock, memory=memory)
            result = await classifier.classify(q["query"])

            if result.agent == expected_agent:
                correct += 1

        accuracy = correct / total if total > 0 else 0
        print(f"\nRouting accuracy (mocked): {correct}/{total} = {accuracy:.1%}")
        assert accuracy >= 0.85, f"Routing accuracy {accuracy:.1%} < 85%"

    @pytest.mark.asyncio
    async def test_entity_matching_accuracy(
        self, gold_classifier_queries, memory
    ):
        """Validate entity subset matching with normalization rules."""
        entity_pass = 0
        entity_total = 0
        failures = []

        for q in gold_classifier_queries:
            expected_entities = q.get("expected_entities", {})
            if not expected_entities:
                continue  # Skip queries with no expected entities

            entity_total += 1

            # Mock returns the expected entities
            mock = MagicMock(return_value={
                "intent": q["expected_agent"],
                "entities": expected_entities,
                "agent": q["expected_agent"],
                "safety_verdict": "safe",
            })

            classifier = IntentClassifier(llm_callable=mock, memory=memory)
            result = await classifier.classify(q["query"])

            matched, fails = entities_match(
                expected_entities, result.entities.to_dict()
            )
            if matched:
                entity_pass += 1
            else:
                failures.append(
                    f"  Query: {q['query'][:60]}\n"
                    f"  Failures: {fails}"
                )

        if entity_total > 0:
            accuracy = entity_pass / entity_total
            print(f"\nEntity matching accuracy: {entity_pass}/{entity_total} = {accuracy:.1%}")
            if failures:
                print("Failures:")
                for f in failures:
                    print(f)
            assert accuracy >= 0.85, f"Entity matching {accuracy:.1%} < 85%"


class TestEntityNormalization:
    """Test the entity matching normalization utilities."""

    def test_ticker_normalization(self):
        """Tickers should be case-insensitive and suffix-optional."""
        assert normalize_ticker("AAPL") == "aapl"
        assert normalize_ticker("aapl") == "aapl"
        assert normalize_ticker("ASML.AS") == "asml"
        assert normalize_ticker("HSBA.L") == "hsba"
        assert normalize_ticker("7203.T") == "7203"

    def test_entity_match_tickers(self):
        """Ticker subset match with normalization."""
        ok, fails = entities_match(
            {"tickers": ["AAPL"]},
            {"tickers": ["AAPL", "MSFT"]},
        )
        assert ok, f"Should match: {fails}"

    def test_entity_match_tickers_missing(self):
        """Missing tickers should fail."""
        ok, fails = entities_match(
            {"tickers": ["AAPL", "MSFT"]},
            {"tickers": ["AAPL"]},
        )
        assert not ok

    def test_entity_match_amount_within_threshold(self):
        """Amount within ±5% should pass."""
        ok, _ = entities_match({"amount": 2500}, {"amount": 2600})
        assert ok  # 2600 is within 5% of 2500

    def test_entity_match_amount_outside_threshold(self):
        """Amount outside ±5% should fail."""
        ok, _ = entities_match({"amount": 2500}, {"amount": 3000})
        assert not ok

    def test_entity_match_topics_substring(self):
        """Topics should match via substring."""
        ok, _ = entities_match(
            {"topics": ["ETF"]},
            {"topics": ["ETF", "large cap"]},
        )
        assert ok

    def test_entity_match_exact_fields(self):
        """Currency, action, etc. should match exactly."""
        ok, _ = entities_match(
            {"currency": "USD", "action": "buy"},
            {"currency": "USD", "action": "buy"},
        )
        assert ok

        ok, _ = entities_match(
            {"currency": "USD"},
            {"currency": "EUR"},
        )
        assert not ok

    def test_entity_match_period_years_exact(self):
        """period_years must be exact."""
        ok, _ = entities_match({"period_years": 20}, {"period_years": 20})
        assert ok

        ok, _ = entities_match({"period_years": 20}, {"period_years": 21})
        assert not ok
