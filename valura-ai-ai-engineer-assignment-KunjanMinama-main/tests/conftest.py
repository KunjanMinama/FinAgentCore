"""
Shared pytest fixtures for the Valura AI assignment.

The most important fixture here is `mock_llm` — every test that touches the
classifier or any LLM-using code must use it. CI runs without OPENAI_API_KEY
and unmocked LLM calls will fail.
"""
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure we don't hit real OpenAI in tests
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("APP_ENV", "test")

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixture loaders
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def load_user():
    """Load a user fixture by id, e.g. load_user('usr_001')."""
    def _load(user_id: str) -> dict:
        for path in (FIXTURES_DIR / "users").glob("*.json"):
            with open(path, encoding="utf-8") as f:
                user = json.load(f)
            if user["user_id"] == user_id:
                return user
        raise FileNotFoundError(f"No fixture for user {user_id}")
    return _load


@pytest.fixture
def gold_classifier_queries() -> list[dict]:
    with open(FIXTURES_DIR / "test_queries" / "intent_classification.json", encoding="utf-8") as f:
        return json.load(f)["queries"]


@pytest.fixture
def gold_safety_queries() -> list[dict]:
    with open(FIXTURES_DIR / "test_queries" / "safety_pairs.json", encoding="utf-8") as f:
        return json.load(f)["queries"]


@pytest.fixture
def conversation_test_cases():
    """Returns a callable: conversation_test_cases('follow_up_session')."""
    def _load(name: str) -> list[dict]:
        path = FIXTURES_DIR / "conversations" / f"{name}.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)["test_cases"]
    return _load


# ---------------------------------------------------------------------------
# LLM mocking
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm():
    """
    Returns a MagicMock that you should configure per-test to return whatever
    structured output your classifier expects.

    Usage:
        def test_something(mock_llm):
            mock_llm.return_value = {"agent": "portfolio_health", "entities": {}}
            ...
    """
    return MagicMock()


# ---------------------------------------------------------------------------
# Entity matching utilities (used across test modules)
# ---------------------------------------------------------------------------

def normalize_ticker(ticker: str) -> str:
    """Normalize ticker for comparison: case-fold, strip exchange suffix."""
    t = ticker.lower().strip()
    # Strip common exchange suffixes
    for suffix in [".us", ".l", ".as", ".t", ".hk", ".si"]:
        if t.endswith(suffix):
            t = t[: -len(suffix)]
            break
    return t


def entities_match(expected: dict, actual: dict) -> tuple[bool, list[str]]:
    """
    Check if actual entities satisfy expected (subset match + normalization).

    Returns:
        (match_ok: bool, failures: list[str])
    """
    failures = []

    for key, expected_val in expected.items():
        actual_val = actual.get(key)

        if key == "tickers":
            # Case-folded, exchange-suffix optional
            expected_tickers = {normalize_ticker(t) for t in expected_val}
            actual_tickers = {normalize_ticker(t) for t in (actual_val or [])}
            missing = expected_tickers - actual_tickers
            if missing:
                failures.append(f"tickers: missing {missing} (got {actual_tickers})")

        elif key in ("topics", "sectors"):
            # Case-folded substring match
            expected_items = [item.lower() for item in expected_val]
            actual_items = [item.lower() for item in (actual_val or [])]
            for item in expected_items:
                if not any(item in a for a in actual_items):
                    failures.append(f"{key}: missing '{item}' (got {actual_items})")

        elif key in ("amount", "rate"):
            # Numeric ±5%
            if actual_val is None:
                failures.append(f"{key}: expected {expected_val}, got None")
            elif abs(actual_val - expected_val) / max(abs(expected_val), 1e-9) > 0.05:
                failures.append(f"{key}: expected {expected_val} ±5%, got {actual_val}")

        elif key == "period_years":
            # Exact match
            if actual_val != expected_val:
                failures.append(f"period_years: expected {expected_val}, got {actual_val}")

        elif key in ("currency", "index", "action", "goal", "frequency", "horizon", "time_period"):
            # Exact string match
            if actual_val is None:
                failures.append(f"{key}: expected '{expected_val}', got None")
            elif str(actual_val).lower() != str(expected_val).lower():
                failures.append(f"{key}: expected '{expected_val}', got '{actual_val}'")

    return (len(failures) == 0, failures)


# ---------------------------------------------------------------------------
# Session memory fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_memory():
    """Return a fresh SessionMemory instance for isolated tests."""
    from src.memory.session_memory import SessionMemory
    return SessionMemory(max_turns=10)
