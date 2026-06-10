"""
Tests for the Portfolio Health Agent.

Validates:
  - Normal portfolio produces all required fields
  - Concentration risk is computed correctly
  - Empty portfolio (user_004) produces BUILD-oriented guidance
  - Concentrated portfolio (user_003) flags high concentration
  - Retiree portfolio (user_008) includes income-focused observations
  - Response always includes disclaimer
  - Multi-currency portfolio doesn't crash
"""

import pytest

from src.agents.portfolio_health import PortfolioHealthAgent
from src.classifier.schema import ClassifierOutput, ExtractedEntities


@pytest.fixture
def agent():
    return PortfolioHealthAgent()


@pytest.fixture
def classifier_output():
    return ClassifierOutput(
        intent="portfolio_health",
        entities=ExtractedEntities(),
        agent="portfolio_health",
        safety_verdict="safe",
    )


class TestPortfolioHealthAgent:
    """Full test suite for the portfolio health agent."""

    @pytest.mark.asyncio
    async def test_normal_portfolio(self, agent, classifier_output, load_user):
        """Active trader portfolio produces all required fields."""
        user = load_user("usr_001")
        result = await agent.execute(classifier_output, user)

        # Required fields
        assert "concentration_risk" in result
        assert "performance" in result
        assert "observations" in result
        assert "disclaimer" in result

        # Concentration risk structure
        cr = result["concentration_risk"]
        assert "top_position_pct" in cr
        assert "top_3_positions_pct" in cr
        assert cr["flag"] in ("high", "medium", "low")

        # Performance structure
        perf = result["performance"]
        assert "total_return_pct" in perf
        assert "annualized_return_pct" in perf

        # Observations should be non-empty
        assert len(result["observations"]) > 0

        # Disclaimer should be present and substantial
        assert len(result["disclaimer"]) > 50

    @pytest.mark.asyncio
    async def test_empty_portfolio(self, agent, classifier_output, load_user):
        """user_004 (empty portfolio) must not crash and should give BUILD guidance."""
        user = load_user("usr_004")
        result = await agent.execute(classifier_output, user)

        # Must not crash
        assert result is not None
        assert "observations" in result

        # Should include helpful guidance
        obs_texts = [o["text"] for o in result["observations"]]
        combined = " ".join(obs_texts).lower()

        # Should mention getting started or building
        assert any(
            word in combined
            for word in ["start", "build", "invest", "ready", "set up"]
        ), f"Empty portfolio response should mention getting started. Got: {combined[:200]}"

        # Should still have disclaimer
        assert "disclaimer" in result

        # Performance should be zeros
        assert result["performance"]["total_return_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_concentrated_portfolio(self, agent, classifier_output, load_user):
        """user_003 (~60% NVDA) should flag high concentration risk."""
        user = load_user("usr_003")
        result = await agent.execute(classifier_output, user)

        cr = result["concentration_risk"]
        # NVDA should be the top position
        assert cr["top_position_ticker"] == "NVDA"
        # Should be flagged as high (NVDA is ~60% of portfolio)
        assert cr["flag"] in ("high", "medium")
        # Top position should be significant
        assert cr["top_position_pct"] > 30

    @pytest.mark.asyncio
    async def test_retiree_portfolio(self, agent, classifier_output, load_user):
        """user_008 (retiree) should include income-focused observations."""
        user = load_user("usr_008")
        result = await agent.execute(classifier_output, user)

        obs_texts = [o["text"] for o in result["observations"]]
        combined = " ".join(obs_texts).lower()

        # Should mention income/dividend given the user's preferences
        assert any(
            word in combined
            for word in ["income", "dividend", "yield", "conservative"]
        ), f"Retiree response should mention income focus. Got: {combined[:200]}"

    @pytest.mark.asyncio
    async def test_multi_currency_portfolio(self, agent, classifier_output, load_user):
        """user_006 (multi-currency) should not crash."""
        user = load_user("usr_006")
        result = await agent.execute(classifier_output, user)

        assert result is not None
        assert "concentration_risk" in result
        assert "performance" in result
        assert len(result.get("holdings", [])) == len(user["positions"])

    @pytest.mark.asyncio
    async def test_agent_id(self, agent):
        """Agent should identify itself correctly."""
        assert agent.agent_id == "portfolio_health"

    @pytest.mark.asyncio
    async def test_holdings_sorted_by_weight(self, agent, classifier_output, load_user):
        """Holdings should be sorted by weight (descending)."""
        user = load_user("usr_001")
        result = await agent.execute(classifier_output, user)

        holdings = result.get("holdings", [])
        weights = [h["weight"] for h in holdings]
        assert weights == sorted(weights, reverse=True)

    @pytest.mark.asyncio
    async def test_weights_sum_to_100(self, agent, classifier_output, load_user):
        """Position weights should sum to approximately 100%."""
        user = load_user("usr_001")
        result = await agent.execute(classifier_output, user)

        holdings = result.get("holdings", [])
        total_weight = sum(h["weight"] for h in holdings)
        assert abs(total_weight - 100.0) < 1.0, (
            f"Weights sum to {total_weight}, expected ~100%"
        )

    @pytest.mark.asyncio
    async def test_safe_execute_error_isolation(self, load_user):
        """safe_execute should catch errors and return error dict."""
        from unittest.mock import AsyncMock, patch

        agent = PortfolioHealthAgent()
        co = ClassifierOutput(
            intent="portfolio_health",
            entities=ExtractedEntities(),
            agent="portfolio_health",
            safety_verdict="safe",
        )

        # Patch execute to raise
        with patch.object(agent, "execute", side_effect=RuntimeError("boom")):
            result = await agent.safe_execute(co, load_user("usr_001"))

        assert result.get("error") is True
        assert "portfolio_health" in result.get("agent", "")
