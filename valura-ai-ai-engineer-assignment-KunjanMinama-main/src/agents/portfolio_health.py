"""
Portfolio Health Agent — fully implemented specialist agent.

Speaks to the MONITOR and PROTECT halves of Valura's mission.
Produces a structured health check covering concentration risk,
performance metrics, benchmark comparison, and actionable observations.

Key design decisions:
  - Receives portfolio data as input (never fetches it)
  - Handles empty portfolios gracefully (BUILD-oriented guidance)
  - All observations target novice investors (plain language)
  - Includes regulatory disclaimer on every response
"""

from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.classifier.schema import ClassifierOutput
from src.core.logger import get_logger
from src.services import market_data, portfolio_math

logger = get_logger(__name__)

DISCLAIMER = (
    "This is not investment advice. The information provided is for "
    "educational purposes only and should not be construed as a recommendation "
    "to buy, sell, or hold any security. Past performance does not guarantee "
    "future results. Please consult a qualified financial advisor before making "
    "investment decisions."
)


class PortfolioHealthAgent(BaseAgent):
    """Portfolio health check — concentration, performance, benchmarking."""

    @property
    def agent_id(self) -> str:
        return "portfolio_health"

    async def execute(
        self,
        classifier_output: ClassifierOutput,
        user_profile: dict,
    ) -> dict:
        """
        Produce a full portfolio health assessment.

        Handles:
          - Normal portfolios (full analysis)
          - Empty portfolios (BUILD-oriented guidance)
          - Failed price lookups (graceful degradation)
        """
        positions = user_profile.get("positions", [])

        # ── Empty portfolio path ──
        if not positions:
            return self._empty_portfolio_response(user_profile)

        # ── Fetch current prices ──
        current_prices = {}
        for pos in positions:
            ticker = pos["ticker"]
            price = market_data.get_current_price(ticker)
            if price is not None:
                current_prices[ticker] = price
            else:
                # Fallback to avg_cost if price unavailable
                current_prices[ticker] = pos["avg_cost"]
                logger.warning(f"Using avg_cost as fallback for {ticker}")

        # ── Compute metrics ──
        weighted_positions = portfolio_math.compute_position_weights(
            positions, current_prices
        )
        concentration = portfolio_math.compute_concentration_risk(
            weighted_positions
        )
        performance = portfolio_math.compute_portfolio_return(
            positions, current_prices
        )

        # ── Benchmark comparison ──
        benchmark_name = user_profile.get("preferences", {}).get(
            "preferred_benchmark", "S&P 500"
        )
        benchmark_return = market_data.get_benchmark_return(benchmark_name)

        benchmark_comparison = None
        if benchmark_return is not None:
            benchmark_comparison = portfolio_math.compute_benchmark_comparison(
                performance["total_return_pct"],
                benchmark_return,
                benchmark_name,
            )

        # ── Generate observations ──
        observations = portfolio_math.generate_observations(
            concentration=concentration,
            performance=performance,
            benchmark_comparison=benchmark_comparison,
            weighted_positions=weighted_positions,
            user_profile=user_profile,
        )

        return {
            "agent": self.agent_id,
            "concentration_risk": concentration,
            "performance": {
                "total_return_pct": performance["total_return_pct"],
                "annualized_return_pct": performance["annualized_return_pct"],
                "total_value": performance["total_value"],
                "total_cost": performance["total_cost"],
            },
            "benchmark_comparison": benchmark_comparison,
            "holdings": weighted_positions,
            "observations": observations,
            "disclaimer": DISCLAIMER,
        }

    def _empty_portfolio_response(self, user_profile: dict) -> dict:
        """
        BUILD-oriented response for users with no positions.

        Instead of an error, we guide the user toward getting started.
        """
        name = user_profile.get("name", "there")
        risk_profile = user_profile.get("risk_profile", "moderate")
        country = user_profile.get("country", "US")

        # Tailor guidance based on risk profile
        if risk_profile == "aggressive":
            suggestion = (
                "With your aggressive risk profile, you might start with a "
                "broad market ETF like QQQ (tech-heavy) or VTI (total market) "
                "and layer in individual growth stocks as you learn."
            )
        elif risk_profile == "conservative":
            suggestion = (
                "With your conservative risk profile, consider starting with "
                "a balanced approach — perhaps a mix of a bond ETF (BND) and "
                "a dividend ETF (VYM or SCHD) for steady income."
            )
        else:
            suggestion = (
                "With a moderate risk profile, a core index fund like VOO "
                "(S&P 500) is a solid foundation. You can diversify from there "
                "as you get comfortable."
            )

        observations = [
            {
                "severity": "info",
                "text": (
                    f"Hi {name}! You're all set up and ready to start investing. "
                    f"Your KYC is verified and your account is active."
                ),
            },
            {
                "severity": "info",
                "text": suggestion,
            },
            {
                "severity": "info",
                "text": (
                    "Start small, invest regularly (dollar-cost averaging), "
                    "and focus on learning. There's no rush — consistency "
                    "matters more than timing."
                ),
            },
        ]

        return {
            "agent": self.agent_id,
            "concentration_risk": {
                "top_position_pct": 0.0,
                "top_3_positions_pct": 0.0,
                "flag": "low",
                "top_position_ticker": None,
            },
            "performance": {
                "total_return_pct": 0.0,
                "annualized_return_pct": 0.0,
                "total_value": 0.0,
                "total_cost": 0.0,
            },
            "benchmark_comparison": None,
            "holdings": [],
            "observations": observations,
            "disclaimer": DISCLAIMER,
        }
