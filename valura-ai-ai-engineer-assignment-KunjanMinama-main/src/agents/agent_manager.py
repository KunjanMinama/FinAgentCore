"""
Agent Manager — central orchestrator for the query pipeline.

Responsibilities:
  1. Receives classifier output
  2. Loads user profile data from fixtures
  3. Routes to the correct agent (portfolio_health or stub)
  4. Executes agent logic with error isolation
  5. Returns structured response for SSE streaming


Architecture:
  - Deterministic routing based on classifier output
  - Error isolation: agent failures → safe error message, never crashes
  - Extensible: add a new agent by registering it in the agent registry
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from src.agents.base import BaseAgent
from src.agents.portfolio_health import PortfolioHealthAgent
from src.agents.stubs import get_stub_agent
from src.classifier.schema import ClassifierOutput
from src.core.config import FIXTURES_DIR
from src.core.logger import get_logger

logger = get_logger(__name__)


class AgentManager:
    """
    Routes classifier output to the appropriate agent and executes it.

    Usage:
        manager = AgentManager()
        result = await manager.handle(classifier_output, user_id="usr_001")
    """

    def __init__(self):
        # Agent registry — add new agents here
        self._agents: dict[str, BaseAgent] = {
            "portfolio_health": PortfolioHealthAgent(),
        }
        # Cache for loaded user profiles
        self._user_cache: dict[str, dict] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new specialist agent."""
        self._agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id}")

    async def handle(
        self,
        classifier_output: ClassifierOutput,
        user_id: str,
        user_profile: dict | None = None,
    ) -> dict:
        """
        Route to the correct agent and execute.

        Args:
            classifier_output: Output from the intent classifier.
            user_id: User identifier for loading profile.
            user_profile: Optional pre-loaded profile (skips file loading).

        Returns:
            Structured agent response dict.
        """
        agent_name = classifier_output.agent

        # Load user profile
        if user_profile is None:
            user_profile = self._load_user_profile(user_id)

        # Get the agent (registered or stub)
        agent = self._agents.get(agent_name)
        if agent is None:
            agent = get_stub_agent(agent_name)
            logger.info(f"Using stub agent for: {agent_name}")

        # Execute with error isolation
        logger.info(
            f"Routing to {agent_name} | intent={classifier_output.intent} | "
            f"entities={classifier_output.entities.to_dict()}"
        )

        result = await agent.safe_execute(classifier_output, user_profile)

        # Attach metadata
        result["_metadata"] = {
            "classified_agent": agent_name,
            "classified_intent": classifier_output.intent,
            "safety_verdict": classifier_output.safety_verdict,
        }

        return result

    def _load_user_profile(self, user_id: str) -> dict:
        """
        Load user profile from fixtures.

        Cached after first load for the session.
        """
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        users_dir = FIXTURES_DIR / "users"
        if not users_dir.exists():
            logger.warning(f"Users directory not found: {users_dir}")
            return self._default_user_profile(user_id)

        for path in users_dir.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    profile = json.load(f)
                if profile.get("user_id") == user_id:
                    self._user_cache[user_id] = profile
                    return profile
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load {path}: {e}")

        logger.warning(f"No fixture found for user {user_id}")
        return self._default_user_profile(user_id)

    def _default_user_profile(self, user_id: str) -> dict:
        """Return a minimal default profile for unknown users."""
        return {
            "user_id": user_id,
            "name": "User",
            "age": 30,
            "country": "US",
            "base_currency": "USD",
            "kyc": {"status": "pending"},
            "risk_profile": "moderate",
            "positions": [],
            "preferences": {"preferred_benchmark": "S&P 500"},
        }
