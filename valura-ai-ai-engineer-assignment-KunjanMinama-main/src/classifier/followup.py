"""
Follow-up resolution — enriches the current user query with session context.

Handles:
  - Pronoun resolution ("how much do I own?" → carry ticker from prior turn)
  - Referent resolution ("what about Apple?" → switch ticker, keep intent)
  - Topic switch detection (new topic → don't carry stale context)
  - Comparison references ("compare them" → carry multiple tickers)

This module builds the context string that is injected into the classifier prompt,
allowing a single LLM call to handle follow-ups naturally.
"""

from __future__ import annotations

from typing import Optional

from src.memory.session_memory import SessionMemory, TurnRecord


def build_context_prompt(
    session_id: str,
    current_query: str,
    memory: SessionMemory,
    prior_turns_override: list[str] | None = None,
) -> str:
    """
    Build the conversation context string for the classifier prompt.

    Args:
        session_id: Current session identifier.
        current_query: The user's current query.
        memory: SessionMemory instance.
        prior_turns_override: If provided, use these instead of memory
                              (used during testing with fixture data).

    Returns:
        A formatted context string to prepend to the classifier prompt.
    """
    if prior_turns_override is not None:
        prior_turns = prior_turns_override
        # Build synthetic history for entity context
        history = [TurnRecord(user_query=t) for t in prior_turns_override]
    else:
        prior_turns = memory.get_prior_user_turns(session_id)
        history = memory.get_history(session_id)

    if not prior_turns:
        return ""

    # Build context block
    lines = ["CONVERSATION HISTORY (most recent last):"]
    for i, turn in enumerate(prior_turns, 1):
        lines.append(f"  Turn {i}: \"{turn}\"")

    # Add entity context from memory if available
    if history:
        last = history[-1]
        if last.entities:
            entity_parts = []
            for k, v in last.entities.items():
                if v:
                    entity_parts.append(f"{k}={v}")
            if entity_parts:
                lines.append(f"  Previous entities: {', '.join(entity_parts)}")
        if last.agent:
            lines.append(f"  Previous agent: {last.agent}")

    lines.append(f"\nCURRENT QUERY: \"{current_query}\"")
    lines.append(
        "\nINSTRUCTIONS FOR FOLLOW-UP RESOLUTION:"
        "\n- If the current query references something from prior turns (pronouns, "
        "'it', 'them', 'that stock'), carry forward the relevant entities."
        "\n- If the user introduces a NEW entity (e.g., 'what about AMD?' after "
        "discussing NVDA), use the NEW entity but you may carry forward the intent type."
        "\n- If the user says 'compare them', carry forward ALL mentioned tickers."
        "\n- If the query is a complete topic switch (e.g., from portfolio health to "
        "a calculator question), do NOT carry forward previous entities."
        "\n- If the query is a conversational closer (thanks, bye, thx), route to general_query."
    )

    return "\n".join(lines)
