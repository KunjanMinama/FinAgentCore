"""
Session memory — in-memory storage for conversation context.

Design decision: In-memory dict keyed by session_id.
Justified because:
  1. Assignment explicitly allows in-memory persistence
  2. Zero infrastructure dependency
  3. Sufficient for demo / evaluation runs
  4. Easy to swap for Redis/Postgres via the same interface

Stores:
  - Last N user turns (configurable, default 3)
  - Last extracted entities per turn
  - Last classifier outputs per turn
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from src.core.config import get_settings


@dataclass
class TurnRecord:
    """A single conversational turn."""
    user_query: str  
    entities: dict = field(default_factory=dict)
    agent: str = ""
    intent: str = ""


class SessionMemory:
    """Thread-safe in-memory session store."""

    def __init__(self, max_turns: int | None = None):
        self._max_turns = max_turns or get_settings().session_max_turns
        self._store: dict[str, list[TurnRecord]] = defaultdict(list)
        self._lock = threading.Lock()

    def get_history(self, session_id: str) -> list[TurnRecord]:
        """Return the last N turns for a session (most recent last)."""
        with self._lock:
            return list(self._store.get(session_id, []))

    def get_prior_user_turns(self, session_id: str) -> list[str]:
        """Return just the user query strings for prior turns."""
        return [t.user_query for t in self.get_history(session_id)]

    def get_last_entities(self, session_id: str) -> dict:
        """Return the entities from the most recent turn, or empty dict."""
        history = self.get_history(session_id)
        if history:
            return history[-1].entities
        return {}

    def get_last_agent(self, session_id: str) -> Optional[str]:
        """Return the agent from the most recent turn."""
        history = self.get_history(session_id)
        if history:
            return history[-1].agent
        return None

    def add_turn(
        self,
        session_id: str,
        user_query: str,
        entities: dict | None = None,
        agent: str = "",
        intent: str = "",
    ) -> None:
        """Record a new turn, keeping only the last N turns."""
        record = TurnRecord(
            user_query=user_query,
            entities=entities or {},
            agent=agent,
            intent=intent,
        )
        with self._lock:
            self._store[session_id].append(record)
            # Trim to max_turns
            if len(self._store[session_id]) > self._max_turns:
                self._store[session_id] = self._store[session_id][-self._max_turns:]

    def clear_session(self, session_id: str) -> None:
        """Clear all history for a session."""
        with self._lock:
            self._store.pop(session_id, None)

    def clear_all(self) -> None:
        """Clear all sessions (used in tests)."""
        with self._lock:
            self._store.clear()


# Module-level singleton — import and use directly
_session_memory: SessionMemory | None = None


def get_session_memory() -> SessionMemory:
    """Return the global SessionMemory singleton."""
    global _session_memory
    if _session_memory is None:
        _session_memory = SessionMemory()
    return _session_memory
