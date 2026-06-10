"""
Financial Calculator — Pure Python math engine.

ZERO LLM calls. ZERO API calls. ZERO cost.

All calculations are deterministic and exact.
LLMs get arithmetic wrong — this module never will.

Functions:
    compound_interest    — A = P(1 + r/n)^(nt)
    dca_projection       — Dollar-cost averaging future value
    fire_number          — FIRE retirement target
    loan_payment         — Monthly mortgage / loan payment
    loan_amortization    — First 12 months amortization schedule
    savings_to_goal      — Monthly savings needed to hit a target
    inflation_adjusted   — Real purchasing power after inflation
"""

from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# 1. Compound Interest
# ---------------------------------------------------------------------------

def compound_interest(
    principal: float,
    rate: float,          # annual rate, e.g. 0.08 for 8%
    years: float,
    n: int = 12,          # compounding frequency per year (12 = monthly)
) -> dict[str, Any]:
    """
    Calculate compound interest.

    Formula: A = P * (1 + r/n)^(n*t)

    Args:
        principal: Starting amount (e.g. 10000)
        rate:      Annual interest rate as decimal (e.g. 0.08 for 8%)
        years:     Investment period in years
        n:         Compounding frequency per year (default 12 = monthly)

    Returns:
        dict with final_amount, total_interest, principal, rate_pct, years

    Example:
        >>> compound_interest(10000, 0.08, 10)
        {'final_amount': 22196.4, 'total_interest': 12196.4, ...}
    """
    if principal <= 0 or years <= 0:
        raise ValueError("principal and years must be positive")
    if rate < 0:
        raise ValueError("rate cannot be negative")

    final_amount = principal * (1 + rate / n) ** (n * years)
    total_interest = final_amount - principal

    return {
        "principal": round(principal, 2),
        "rate_pct": round(rate * 100, 2),
        "years": years,
        "compounding_frequency": n,
        "final_amount": round(final_amount, 2),
        "total_interest": round(total_interest, 2),
        "growth_multiplier": round(final_amount / principal, 2),
    }


# ---------------------------------------------------------------------------
# 2. Dollar-Cost Averaging (DCA) Projection
# ---------------------------------------------------------------------------

def dca_projection(
    monthly_amount: float,
    annual_rate: float,    # e.g. 0.08 for 8%
    years: float,
    initial_investment: float = 0.0,
) -> dict[str, Any]:
    """
    Project the future value of regular monthly investments (DCA).

    Uses the future value of annuity formula:
        FV = PMT * [((1 + r)^n - 1) / r]

    where r = monthly rate, n = total months.

    Args:
        monthly_amount:      Fixed amount invested each month
        annual_rate:         Expected annual return (e.g. 0.08)
        years:               Investment horizon in years
        initial_investment:  Lump sum invested at the start (default 0)

    Returns:
        dict with final_value, total_invested, total_gain, monthly_amount, etc.
    """
    if monthly_amount < 0 or years <= 0:
        raise ValueError("monthly_amount must be >= 0 and years must be positive")

    monthly_rate = annual_rate / 12
    n_months = int(years * 12)

    # Future value of periodic payments
    if monthly_rate == 0:
        fv_payments = monthly_amount * n_months
    else:
        fv_payments = monthly_amount * (((1 + monthly_rate) ** n_months - 1) / monthly_rate)

    # Future value of any initial lump sum
    fv_initial = initial_investment * (1 + monthly_rate) ** n_months

    final_value = fv_payments + fv_initial
    total_invested = monthly_amount * n_months + initial_investment
    total_gain = final_value - total_invested

    return {
        "monthly_amount": round(monthly_amount, 2),
        "initial_investment": round(initial_investment, 2),
        "annual_rate_pct": round(annual_rate * 100, 2),
        "years": years,
        "total_months": n_months,
        "total_invested": round(total_invested, 2),
        "final_value": round(final_value, 2),
        "total_gain": round(total_gain, 2),
        "gain_pct": round((total_gain / total_invested) * 100, 2) if total_invested > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# 3. FIRE Number
# ---------------------------------------------------------------------------

def fire_number(
    annual_expenses: float,
    swr: float = 0.04,     # Safe Withdrawal Rate, default 4% rule
) -> dict[str, Any]:
    """
    Calculate the FIRE (Financial Independence, Retire Early) target.

    Formula: FIRE Number = Annual Expenses / SWR

    The 4% rule (Bengen 1994) states: if you withdraw 4% annually from a
    diversified portfolio, it will last 30+ years historically.

    Args:
        annual_expenses: Current yearly spending
        swr:             Safe Withdrawal Rate (default 0.04 = 4%)

    Returns:
        dict with fire_target, annual_expenses, swr_pct, and interpretation
    """
    if annual_expenses <= 0:
        raise ValueError("annual_expenses must be positive")
    if not (0.01 <= swr <= 0.10):
        raise ValueError("swr should be between 1% and 10%")

    fire_target = annual_expenses / swr

    # How much you need to save monthly to hit FIRE in common timeframes
    scenarios = {}
    for years in [10, 15, 20, 25, 30]:
        monthly = savings_to_goal(fire_target, 0.07, years)["monthly_savings"]
        scenarios[f"{years}_years"] = monthly

    return {
        "annual_expenses": round(annual_expenses, 2),
        "swr_pct": round(swr * 100, 2),
        "fire_target": round(fire_target, 2),
        "monthly_expenses": round(annual_expenses / 12, 2),
        "monthly_savings_scenarios": scenarios,
        "rule": f"{round(swr * 100, 0):.0f}% safe withdrawal rate ({round(1/swr, 0):.0f}x annual expenses)",
    }


# ---------------------------------------------------------------------------
# 4. Loan / Mortgage Monthly Payment
# ---------------------------------------------------------------------------

def loan_payment(
    principal: float,
    annual_rate: float,    # e.g. 0.065 for 6.5%
    years: float,
) -> dict[str, Any]:
    """
    Calculate the fixed monthly payment for a loan or mortgage.

    Formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]

    Args:
        principal:    Loan amount
        annual_rate:  Annual interest rate as decimal
        years:        Loan term in years

    Returns:
        dict with monthly_payment, total_paid, total_interest, etc.
    """
    if principal <= 0 or years <= 0:
        raise ValueError("principal and years must be positive")
    if annual_rate < 0:
        raise ValueError("annual_rate cannot be negative")

    monthly_rate = annual_rate / 12
    n_months = int(years * 12)

    if monthly_rate == 0:
        monthly_payment = principal / n_months
    else:
        monthly_payment = principal * (
            monthly_rate * (1 + monthly_rate) ** n_months
        ) / ((1 + monthly_rate) ** n_months - 1)

    total_paid = monthly_payment * n_months
    total_interest = total_paid - principal

    return {
        "principal": round(principal, 2),
        "annual_rate_pct": round(annual_rate * 100, 2),
        "years": years,
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "interest_to_principal_ratio": round(total_interest / principal, 2),
    }


# ---------------------------------------------------------------------------
# 5. Loan Amortization Schedule (first 12 months)
# ---------------------------------------------------------------------------

def loan_amortization(
    principal: float,
    annual_rate: float,
    years: float,
    n_months_shown: int = 12,
) -> dict[str, Any]:
    """
    Generate a loan amortization schedule (first n months).

    Args:
        principal:       Loan amount
        annual_rate:     Annual interest rate as decimal
        years:           Loan term in years
        n_months_shown:  How many months to include in the schedule (default 12)

    Returns:
        dict with monthly_payment and schedule list
    """
    base = loan_payment(principal, annual_rate, years)
    monthly_payment = base["monthly_payment"]
    monthly_rate = annual_rate / 12

    schedule = []
    balance = principal

    for month in range(1, min(n_months_shown + 1, int(years * 12) + 1)):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance = max(0.0, balance - principal_payment)

        schedule.append({
            "month": month,
            "payment": round(monthly_payment, 2),
            "principal": round(principal_payment, 2),
            "interest": round(interest_payment, 2),
            "remaining_balance": round(balance, 2),
        })

    return {
        "monthly_payment": round(monthly_payment, 2),
        "annual_rate_pct": round(annual_rate * 100, 2),
        "total_months": int(years * 12),
        "schedule": schedule,
    }


# ---------------------------------------------------------------------------
# 6. Savings Needed to Reach a Goal
# ---------------------------------------------------------------------------

def savings_to_goal(
    target: float,
    annual_rate: float,
    years: float,
    initial_savings: float = 0.0,
) -> dict[str, Any]:
    """
    Calculate how much to save monthly to reach a financial goal.

    Solves DCA formula for monthly_payment:
        PMT = (FV - PV*(1+r)^n) * r / ((1+r)^n - 1)

    Args:
        target:          The target amount to reach
        annual_rate:     Expected annual return (e.g. 0.07 for 7%)
        years:           Time horizon in years
        initial_savings: Already saved amount (default 0)

    Returns:
        dict with monthly_savings and projection details
    """
    if target <= 0 or years <= 0:
        raise ValueError("target and years must be positive")

    monthly_rate = annual_rate / 12
    n_months = int(years * 12)

    # Future value of existing savings
    fv_existing = initial_savings * (1 + monthly_rate) ** n_months

    # Gap to fill with monthly savings
    gap = target - fv_existing

    if gap <= 0:
        return {
            "target": round(target, 2),
            "annual_rate_pct": round(annual_rate * 100, 2),
            "years": years,
            "initial_savings": round(initial_savings, 2),
            "monthly_savings": 0.0,
            "note": "Your existing savings already cover the target at the given return rate.",
        }

    if monthly_rate == 0:
        monthly_savings = gap / n_months
    else:
        monthly_savings = gap * monthly_rate / ((1 + monthly_rate) ** n_months - 1)

    return {
        "target": round(target, 2),
        "annual_rate_pct": round(annual_rate * 100, 2),
        "years": years,
        "initial_savings": round(initial_savings, 2),
        "monthly_savings": round(monthly_savings, 2),
        "total_contributions": round(monthly_savings * n_months + initial_savings, 2),
        "growth_from_returns": round(target - (monthly_savings * n_months + initial_savings), 2),
    }


# ---------------------------------------------------------------------------
# 7. Inflation-Adjusted Future Value
# ---------------------------------------------------------------------------

def inflation_adjusted(
    amount: float,
    inflation_rate: float = 0.03,   # 3% default annual inflation
    years: float = 10,
) -> dict[str, Any]:
    """
    Calculate the real purchasing power of an amount after inflation.

    Formula: Real Value = Amount / (1 + inflation_rate)^years

    Args:
        amount:         Current amount
        inflation_rate: Annual inflation rate (default 0.03 = 3%)
        years:          Number of years into the future

    Returns:
        dict with real_value, purchasing_power_loss, and interpretation
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    real_value = amount / (1 + inflation_rate) ** years
    purchasing_power_loss = amount - real_value
    loss_pct = (purchasing_power_loss / amount) * 100

    return {
        "current_amount": round(amount, 2),
        "inflation_rate_pct": round(inflation_rate * 100, 2),
        "years": years,
        "real_value_in_todays_dollars": round(real_value, 2),
        "purchasing_power_loss": round(purchasing_power_loss, 2),
        "loss_pct": round(loss_pct, 2),
        "interpretation": (
            f"${amount:,.0f} today will only buy ${real_value:,.0f} worth "
            f"of goods in {years:.0f} years at {inflation_rate*100:.1f}% inflation."
        ),
    }
