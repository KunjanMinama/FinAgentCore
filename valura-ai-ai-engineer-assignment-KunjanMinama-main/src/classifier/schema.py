"""
Pydantic schemas for the intent classifier output.

These models define the structured output that the LLM must produce.
They also serve as the contract between the classifier and the agent manager.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ExtractedEntities(BaseModel):
    """All entities that can be extracted from a user query."""
    tickers: list[str] = Field(default_factory=list, description="Stock tickers (e.g. AAPL, NVDA, ASML.AS)")
    topics: list[str] = Field(default_factory=list, description="Topic keywords")
    sectors: list[str] = Field(default_factory=list, description="Industry sectors")
    amount: Optional[float] = Field(default=None, description="Monetary amount")
    currency: Optional[str] = Field(default=None, description="ISO 4217 currency code")
    rate: Optional[float] = Field(default=None, description="Rate as decimal (e.g. 0.08 for 8%)")
    period_years: Optional[int] = Field(default=None, description="Time period in years")
    index: Optional[str] = Field(default=None, description="Market index name")
    action: Optional[str] = Field(default=None, description="User intent action: buy, sell, hold, hedge, rebalance")
    goal: Optional[str] = Field(default=None, description="Financial goal: retirement, education, house, FIRE, emergency_fund")
    frequency: Optional[str] = Field(default=None, description="Frequency: daily, weekly, monthly, yearly")
    horizon: Optional[str] = Field(default=None, description="Time horizon: 6_months, 1_year, 5_years")
    time_period: Optional[str] = Field(default=None, description="Time period: today, this_week, this_month, this_year")

    def to_dict(self) -> dict:
        """Return non-None, non-empty fields as a dictionary."""
        result = {}
        for field_name, value in self:
            if value is not None:
                if isinstance(value, list):
                    if value:  # skip empty lists
                        result[field_name] = value
                else:
                    result[field_name] = value
        return result


class ClassifierOutput(BaseModel):
    """Structured output from the intent classifier."""
    intent: str = Field(description="Classified intent label")
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    agent: str = Field(description="Target agent to handle this query")
    safety_verdict: str = Field(
        default="safe",
        description="Informational safety verdict: safe, uncertain, or risky",
    )

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "entities": self.entities.to_dict(),
            "agent": self.agent,
            "safety_verdict": self.safety_verdict,
        }


class QueryRequest(BaseModel):
    """Incoming query from the HTTP layer."""
    query: str = Field(description="User query text")
    user_id: str = Field(description="User identifier for loading profile")
    session_id: str = Field(default="default", description="Conversation session identifier")


# Default fallback when LLM fails
FALLBACK_CLASSIFIER_OUTPUT = ClassifierOutput(
    intent="fallback",
    entities=ExtractedEntities(),
    agent="customer_support",
    safety_verdict="uncertain",
)
