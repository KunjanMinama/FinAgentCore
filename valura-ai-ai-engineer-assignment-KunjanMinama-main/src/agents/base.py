"""
Base agent interface — all specialist agents inherit from this.

Provides:
  - Standard interface (execute method)
  - Common response envelope
  - Error isolation wrapper
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.classifier.schema import ClassifierOutput


class BaseAgent(ABC):
    """Abstract base class for all specialist agents."""

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier matching the classifier taxonomy."""
        ...

    @abstractmethod
    async def execute(
        self,
        classifier_output: ClassifierOutput,
        user_profile: dict,
    ) -> dict:
        """
        Execute the agent logic.

        Args:
            classifier_output: The full classifier output.
            user_profile: The user's profile data (including positions).

        Returns:
            A dict with the agent's structured response.
        """
        ...

    async def safe_execute(
        self,
        classifier_output: ClassifierOutput,
        user_profile: dict,
    ) -> dict:
        """
        Error-isolated execution wrapper.

        If the agent raises any exception, this catches it and returns
        a safe error stub instead of crashing the pipeline.
        """
        try:
            return await self.execute(classifier_output, user_profile)
        except Exception as e:
            from src.core.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Agent {self.agent_id} failed: {e}")
            return {
                "agent": self.agent_id,
                "error": True,
                "message": (
                    f"The {self.agent_id} agent encountered an error processing "
                    f"your request. Please try again or contact support."
                ),
                "detail": str(e),
            }
