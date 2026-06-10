"""
Tests for the Agent Manager routing.

Validates:
  - Classifier output is routed to the correct agent
  - Stub agents return correct structure
  - Portfolio health agent is properly invoked
  - Error isolation works (agent errors → safe response)
  - Unknown agents get stub treatment
"""

import pytest
from unittest.mock import MagicMock 

from src.agents.agent_manager import AgentManager
from src.agents.base import BaseAgent
from src.classifier.schema import ClassifierOutput, ExtractedEntities


class TestAgentManager:
    """Tests for the agent manager orchestration."""

    @pytest.fixture
    def manager(self):
        return AgentManager()

    def _classifier_output(
        self, agent: str, intent: str = "", **entity_kwargs
    ) -> ClassifierOutput:
        """Helper to create classifier output."""
        return ClassifierOutput(
            intent=intent or agent,
            entities=ExtractedEntities(**entity_kwargs),
            agent=agent,
            safety_verdict="safe",
        )

    @pytest.mark.asyncio
    async def test_routes_to_portfolio_health(self, manager, load_user):
        """Portfolio health agent should be invoked for portfolio_health routing."""
        output = self._classifier_output("portfolio_health")
        user = load_user("usr_001")

        result = await manager.handle(output, user_id="usr_001", user_profile=user)

        assert "concentration_risk" in result
        assert "performance" in result
        assert "observations" in result
        assert "disclaimer" in result

    @pytest.mark.asyncio
    async def test_routes_to_stub(self, manager):
        """Unimplemented agents should get stub response."""
        output = self._classifier_output("market_research", tickers=["AAPL"])

        result = await manager.handle(output, user_id="usr_001")

        assert result["implemented"] is False
        assert result["agent"] == "market_research"
        assert "not implemented" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_stub_includes_entities(self, manager):
        """Stub responses should include the classified entities."""
        output = self._classifier_output(
            "financial_calculator",
            intent="calculate_returns",
            amount=2500.0,
            frequency="monthly",
        )

        result = await manager.handle(output, user_id="usr_001")

        assert result["implemented"] is False
        assert result["entities"]["amount"] == 2500.0

    @pytest.mark.asyncio
    async def test_unknown_agent_gets_stub(self, manager):
        """Completely unknown agent names should get stub treatment."""
        output = self._classifier_output("totally_unknown_agent")

        result = await manager.handle(output, user_id="usr_001")

        assert result["implemented"] is False
        assert result["agent"] == "totally_unknown_agent"

    @pytest.mark.asyncio
    async def test_error_isolation(self, manager):
        """Agent errors should be caught and converted to safe response."""
        # Register a deliberately failing agent
        class FailingAgent(BaseAgent):
            @property
            def agent_id(self):
                return "failing_agent"

            async def execute(self, classifier_output, user_profile):
                raise RuntimeError("Agent exploded!")

        manager.register_agent(FailingAgent())
        output = self._classifier_output("failing_agent")

        result = await manager.handle(output, user_id="usr_001")

        assert result.get("error") is True
        assert "error" in result.get("message", "").lower() or "try again" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_metadata_attached(self, manager):
        """Response should include routing metadata."""
        output = self._classifier_output("general_query", intent="greeting")

        result = await manager.handle(output, user_id="usr_001")

        assert "_metadata" in result
        assert result["_metadata"]["classified_agent"] == "general_query"
        assert result["_metadata"]["classified_intent"] == "greeting"

    @pytest.mark.asyncio
    async def test_all_stub_agents(self, manager):
        """All known agent types from taxonomy should work without crashing."""
        agent_names = [
            "market_research",
            "investment_strategy",
            "financial_planning",
            "financial_calculator",
            "risk_assessment",
            "product_recommendation",
            "predictive_analysis",
            "customer_support",
            "general_query",
        ]

        for name in agent_names:
            output = self._classifier_output(name)
            result = await manager.handle(output, user_id="usr_001")
            assert result["agent"] == name
            assert result["implemented"] is False

    @pytest.mark.asyncio
    async def test_register_custom_agent(self, manager):
        """Custom agents can be registered and invoked."""
        class CustomAgent(BaseAgent):
            @property
            def agent_id(self):
                return "custom_agent"

            async def execute(self, classifier_output, user_profile):
                return {"custom": True, "answer": "42"}

        manager.register_agent(CustomAgent())
        output = self._classifier_output("custom_agent")
        result = await manager.handle(output, user_id="usr_001")

        assert result.get("custom") is True
        assert result.get("answer") == "42"
