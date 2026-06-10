"""
Stub agents for all unimplemented agent types.

These stubs:
  - Route correctly (no crashes, no errors)
  - Return the classified intent and extracted entities
  - Clearly indicate the agent is not implemented in this build
  - Follow the exact contract specified in the assignment

Agent list derived from fixtures/test_queries/intent_classification.json:
  market_research, investment_strategy, financial_planning,
  financial_calculator, risk_assessment, product_recommendation,
  predictive_analysis, customer_support, general_query
"""

from __future__ import annotations

from src.agents.base import BaseAgent
from src.classifier.schema import ClassifierOutput


class StubAgent(BaseAgent):
    """
    Generic stub for any unimplemented agent.

    Instantiated with a specific agent_id to match the classifier taxonomy.
    """

    def __init__(self, agent_name: str):
        self._agent_name = agent_name

    @property
    def agent_id(self) -> str:
        return self._agent_name

    async def execute(
        self,
        classifier_output: ClassifierOutput,
        user_profile: dict,
    ) -> dict:
        return {
            "implemented": False,
            "agent": self._agent_name,
            "intent": classifier_output.intent,
            "entities": classifier_output.entities.to_dict(),
            "message": (
                f"The {self._agent_name} agent is not implemented in this build. "
                f"Your query was correctly classified and would be handled by "
                f"this agent in production."
            ),
        }


# Pre-instantiated stubs for all known agent types (except portfolio_health)
STUB_AGENTS: dict[str, StubAgent] = {
    name: StubAgent(name)
    for name in [
        "market_research",
        "investment_strategy",
        "financial_planning",
        "financial_calculator",
        "risk_assessment",
        "product_recommendation",
        "predictive_analysis",
        "customer_support",
        "general_query",
        "portfolio_query",  # from follow_up_session fixture
    ]
}


def get_stub_agent(agent_name: str) -> StubAgent:
    """Get or create a stub agent for the given name."""
    if agent_name not in STUB_AGENTS:
        STUB_AGENTS[agent_name] = StubAgent(agent_name)
    return STUB_AGENTS[agent_name]
