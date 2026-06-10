"""
SSE (Server-Sent Events) streaming utilities.

Provides a generator that yields SSE-formatted strings for the response stream.

Event types:
  - data: normal response payload
  - error: structured error event
  - safety_block: safety guard blocked the query
  - end: stream termination signal
"""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Generator


def sse_event(event_type: str, data: Any) -> str:
    """
    Format a single SSE event string.

    Args:
        event_type: Event name (data, error, safety_block, end).
        data: Payload to serialize as JSON.

    Returns:
        SSE-formatted string: "event: {type}\\ndata: {json}\\n\\n"
    """
    payload = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {payload}\n\n"


def sse_data(data: Any) -> str:
    """Emit a 'data' event."""
    return sse_event("data", data)


def sse_error(message: str, detail: str | None = None) -> str:
    """Emit an 'error' event."""
    payload = {"error": True, "message": message}
    if detail:
        payload["detail"] = detail
    return sse_event("error", payload)


def sse_safety_block(category: str, message: str) -> str:
    """Emit a 'safety_block' event."""
    return sse_event("safety_block", {
        "blocked": True,
        "category": category,
        "message": message,
    })


def sse_end() -> str:
    """Emit an 'end' event to signal stream termination."""
    return sse_event("end", {"status": "complete"})
