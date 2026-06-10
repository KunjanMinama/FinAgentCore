"""
Portfolio math utilities — pure computation, no side effects.

All functions take portfolio data as input and return computed metrics.
No data fetching happens here — prices come from market_data service.
"""

from __future__ import annotations

from typing import Optional


def compute_position_weights(
    positions: list[dict],
    current_prices: dict[str, float],
) -> list[dict]:
    """
    Compute the current market value and weight of each position.

    Args:
        positions: List of position dicts from user profile.
        current_prices: Map of ticker → current price.

    Returns:
        List of dicts with ticker, quantity, avg_cost, current_price,
        market_value, cost_basis, gain_loss, gain_loss_pct, weight.
    """
    # Calculate market values
    enriched = []
    total_value = 0.0

    for pos in positions:
        ticker = pos["ticker"]
        quantity = pos["quantity"]
        avg_cost = pos["avg_cost"]
        current_price = current_prices.get(ticker, avg_cost)

        market_value = quantity * current_price
        cost_basis = quantity * avg_cost
        gain_loss = market_value - cost_basis
        gain_loss_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0

        total_value += market_value
        enriched.append({
            "ticker": ticker,
            "quantity": quantity,
            "avg_cost": round(avg_cost, 2),
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "cost_basis": round(cost_basis, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
            "weight": 0.0,  # filled below
        })

    # Calculate weights
    if total_value > 0:
        for item in enriched:
            item["weight"] = round((item["market_value"] / total_value) * 100, 2)

    # Sort by weight descending
    enriched.sort(key=lambda x: x["weight"], reverse=True)
    return enriched


def compute_concentration_risk(
    weighted_positions: list[dict],
) -> dict:
    """
    Assess concentration risk from position weights.

    Returns:
        {
            "top_position_pct": float,
            "top_3_positions_pct": float,
            "flag": "high" | "medium" | "low",
            "top_position_ticker": str
        }
    """
    if not weighted_positions:
        return {
            "top_position_pct": 0.0,
            "top_3_positions_pct": 0.0,
            "flag": "low",
            "top_position_ticker": None,
        }

    top_pct = weighted_positions[0]["weight"]
    top_3_pct = sum(p["weight"] for p in weighted_positions[:3])
    top_ticker = weighted_positions[0]["ticker"]

    # Thresholds based on common portfolio management guidelines
    if top_pct >= 40:
        flag = "high"
    elif top_pct >= 25 or top_3_pct >= 60:
        flag = "medium"
    else:
        flag = "low"

    return {
        "top_position_pct": round(top_pct, 1),
        "top_3_positions_pct": round(top_3_pct, 1),
        "flag": flag,
        "top_position_ticker": top_ticker,
    }


def compute_portfolio_return(
    positions: list[dict],
    current_prices: dict[str, float],
) -> dict:
    """
    Compute total portfolio return and annualized return.

    Uses cost basis vs current value for total return.
    Approximates annualized return using the earliest purchase date.

    Returns:
        {
            "total_value": float,
            "total_cost": float,
            "total_return_pct": float,
            "annualized_return_pct": float
        }
    """
    import datetime

    total_value = 0.0
    total_cost = 0.0
    earliest_date = None

    for pos in positions:
        ticker = pos["ticker"]
        quantity = pos["quantity"]
        avg_cost = pos["avg_cost"]
        current_price = current_prices.get(ticker, avg_cost)

        total_value += quantity * current_price
        total_cost += quantity * avg_cost

        # Track earliest purchase date
        purchased_at = pos.get("purchased_at")
        if purchased_at:
            try:
                dt = datetime.date.fromisoformat(purchased_at)
                if earliest_date is None or dt < earliest_date:
                    earliest_date = dt
            except ValueError:
                pass

    if total_cost <= 0:
        return {
            "total_value": 0.0,
            "total_cost": 0.0,
            "total_return_pct": 0.0,
            "annualized_return_pct": 0.0,
        }

    total_return_pct = ((total_value - total_cost) / total_cost) * 100

    # Annualized return
    years = 1.0
    if earliest_date:
        days = (datetime.date.today() - earliest_date).days
        years = max(days / 365.25, 0.1)  # minimum 0.1 to avoid division by 0

    if total_cost > 0 and total_value > 0:
        annualized = ((total_value / total_cost) ** (1 / years) - 1) * 100
    else:
        annualized = 0.0

    return {
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_return_pct": round(total_return_pct, 2),
        "annualized_return_pct": round(annualized, 2),
    }


def compute_benchmark_comparison(
    portfolio_return_pct: float,
    benchmark_return_pct: float,
    benchmark_name: str,
) -> dict:
    """
    Compare portfolio performance against a benchmark.

    Returns:
        {
            "benchmark": str,
            "portfolio_return_pct": float,
            "benchmark_return_pct": float,
            "alpha_pct": float
        }
    """
    alpha = portfolio_return_pct - benchmark_return_pct

    return {
        "benchmark": benchmark_name,
        "portfolio_return_pct": round(portfolio_return_pct, 2),
        "benchmark_return_pct": round(benchmark_return_pct, 2),
        "alpha_pct": round(alpha, 2),
    }


def generate_observations(
    concentration: dict,
    performance: dict,
    benchmark_comparison: Optional[dict],
    weighted_positions: list[dict],
    user_profile: dict,
) -> list[dict]:
    """
    Generate human-readable observations about the portfolio.

    Targets novice investors — plain language, surface the 1-2 things
    that matter most.

    Returns:
        List of {"severity": "warning|info|positive", "text": str}
    """
    observations = []

    # Concentration warnings
    if concentration["flag"] == "high":
        ticker = concentration.get("top_position_ticker", "one position")
        pct = concentration["top_position_pct"]
        observations.append({
            "severity": "warning",
            "text": (
                f"{pct}% of your portfolio is in {ticker} — that's highly concentrated. "
                f"If {ticker} drops significantly, your whole portfolio feels it. "
                f"Consider spreading into other sectors or an index fund."
            ),
        })
    elif concentration["flag"] == "medium":
        pct = concentration["top_3_positions_pct"]
        observations.append({
            "severity": "warning",
            "text": (
                f"Your top 3 positions make up {pct}% of your portfolio. "
                f"That's moderately concentrated — not alarming, but worth monitoring."
            ),
        })
    else:
        observations.append({
            "severity": "positive",
            "text": "Your portfolio is reasonably well diversified across positions.",
        })

    # Performance observations
    total_return = performance.get("total_return_pct", 0)
    if total_return > 0:
        observations.append({
            "severity": "positive",
            "text": f"Your portfolio is up {total_return:.1f}% overall. Nice work.",
        })
    elif total_return < -10:
        observations.append({
            "severity": "warning",
            "text": (
                f"Your portfolio is down {abs(total_return):.1f}% overall. "
                f"This could reflect market conditions or specific holdings. "
                f"Check if any single position is dragging things down."
            ),
        })

    # Benchmark comparison
    if benchmark_comparison:
        alpha = benchmark_comparison.get("alpha_pct", 0)
        benchmark = benchmark_comparison.get("benchmark", "the benchmark")
        if alpha > 2:
            observations.append({
                "severity": "info",
                "text": f"Outperforming {benchmark} by {alpha:.1f}% — your picks are beating the market.",
            })
        elif alpha < -5:
            observations.append({
                "severity": "warning",
                "text": (
                    f"Underperforming {benchmark} by {abs(alpha):.1f}%. "
                    f"You might consider whether active picks are worth the effort vs. an index fund."
                ),
            })

    # Sector concentration (if all positions are tech-like)
    risk_profile = user_profile.get("risk_profile", "moderate")
    if risk_profile == "conservative":
        observations.append({
            "severity": "info",
            "text": (
                "With a conservative risk profile, focus on capital preservation. "
                "Review your bond allocation and ensure adequate income-producing holdings."
            ),
        })

    # Check for income focus (retiree)
    if user_profile.get("preferences", {}).get("income_focus"):
        observations.append({
            "severity": "info",
            "text": (
                "As an income-focused investor, review dividend yields across holdings. "
                "Bond and dividend ETF positions can help maintain steady income streams."
            ),
        })

    return observations
