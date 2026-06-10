"""
Safety Guard — synchronous, pre-LLM filter.

Runs in <1ms. No network calls. No LLM calls.
Evaluates the user query against hardcoded rules and returns a verdict.

Design tradeoff: We accept a small risk of over-blocking on edge cases
(e.g. a query that contains both harmful keywords and educational phrasing
where the educational markers aren't captured by our whitelist). This is
documented in the README. Erring on the side of safety is correct for
a financial platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.safety.rules import SAFETY_RULES, SafetyRule, _is_educational


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of the safety guard evaluation."""
    blocked: bool
    category: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "blocked": self.blocked,
            "category": self.category,
            "message": self.message,
        }


# Re-usable "pass" verdict
_PASS = SafetyVerdict(blocked=False)


def evaluate(query: str) -> SafetyVerdict:
    """
    Evaluate a user query against all safety rules.

    Returns SafetyVerdict with blocked=True if the query matches a harmful
    pattern AND is not an educational query.

    Performance: O(n_rules * n_patterns) — all patterns are pre-compiled.
    Measured at <0.2ms on commodity hardware for the full rule set.
    """
    if not query or not query.strip():
        return _PASS

    query_lower = query.lower().strip()

    # Educational queries get a free pass — even if they mention harmful topics
    if _is_educational(query):
        return _PASS

    # Check each rule category
    for rule in SAFETY_RULES:
        if _matches_rule(query, query_lower, rule):
            return SafetyVerdict(
                blocked=True,
                category=rule.category,
                message=rule.message,
            )

    return _PASS


def _matches_rule(query: str, query_lower: str, rule: SafetyRule) -> bool:
    """Check if a query matches any pattern or keyword in a safety rule."""
    # Check regex patterns
    for pattern in rule.block_patterns:
        if pattern.search(query):
            return True

    # Check keyword phrases
    for keyword in rule.block_keywords:
        if keyword.lower() in query_lower:
            return True

    return False
