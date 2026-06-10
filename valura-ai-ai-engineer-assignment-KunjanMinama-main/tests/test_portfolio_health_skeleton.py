"""
Skeleton test for the Portfolio Health agent.

Wired up to use the actual PortfolioHealthAgent implementation.
"""
import pytest

from src.agents.portfolio_health import PortfolioHealthAgent
from src.classifier.schema import ClassifierOutput, ExtractedEntities


@pytest.fixture
def agent():
    return PortfolioHealthAgent()


@pytest.fixture
def default_classifier_output():
    return ClassifierOutput(
        intent="portfolio_health",
        entities=ExtractedEntities(),
        agent="portfolio_health",
        safety_verdict="safe",
    )


@pytest.mark.asyncio
async def test_portfolio_health_does_not_crash_on_empty_portfolio(
    load_user, agent, default_classifier_output
):
    """
    user_004 has no positions. Agent must not crash.
    """
    user = load_user("usr_004")
    response = await agent.execute(default_classifier_output, user)

    assert response is not None
    assert "disclaimer" in response


@pytest.mark.asyncio
async def test_portfolio_health_flags_concentration(
    load_user, agent, default_classifier_output
):
    """
    user_003 has ~60% in NVDA. Agent must surface this.
    """
    user = load_user("usr_003")
    response = await agent.execute(default_classifier_output, user)

    assert response["concentration_risk"]["flag"] in {"high", "warning"}


@pytest.mark.asyncio
async def test_portfolio_health_includes_disclaimer(
    load_user, agent, default_classifier_output
):
    user = load_user("usr_001")
    response = await agent.execute(default_classifier_output, user)
    assert response["disclaimer"]
    assert "not investment advice" in response["disclaimer"].lower()
