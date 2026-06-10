"""
API Router — FastAPI endpoint for the query pipeline.

Exposes:
  POST /query — accepts user query, runs full pipeline, streams SSE response.

Pipeline flow:
  1. Safety Guard (sync, <1ms)
  2. Intent Classifier (async, single LLM call)
  3. Agent Manager (async, routes + executes)
  4. Stream response via SSE

All errors are returned as structured SSE events — never raw stack traces.
Pipeline enforces a 10-second timeout.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.agents.agent_manager import AgentManager
from src.api.sse import sse_data, sse_end, sse_error, sse_safety_block
from src.classifier.classifier_model import IntentClassifier
from src.classifier.schema import QueryRequest
from src.core.config import get_settings
from src.core.logger import get_logger
from src.memory.session_memory import get_session_memory
from src.safety.guard import evaluate as safety_evaluate

logger = get_logger(__name__)

router = APIRouter()

# Module-level singletons (created on first use)
_classifier: IntentClassifier | None = None
_agent_manager: AgentManager | None = None


def get_classifier() -> IntentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier


def get_agent_manager() -> AgentManager:
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager


async def _pipeline_stream(
    request: QueryRequest,
) -> AsyncGenerator[str, None]:
    """
    Full query pipeline as an SSE stream generator.

    Yields SSE events: safety_block | data | error | end
    """
    settings = get_settings()

    try:
        # ── Step 1: Safety Guard ──
        safety_verdict = safety_evaluate(request.query)

        if safety_verdict.blocked:
            logger.info(
                f"Safety blocked: category={safety_verdict.category} "
                f"query=\"{request.query[:80]}\""
            )
            yield sse_safety_block(
                category=safety_verdict.category or "unknown",
                message=safety_verdict.message or "This query has been blocked.",
            )
            yield sse_end()
            return

        # ── Step 2: Intent Classifier ──
        classifier = get_classifier()
        classifier_output = await asyncio.wait_for(
            classifier.classify(
                query=request.query,
                session_id=request.session_id,
            ),
            timeout=settings.pipeline_timeout_seconds,
        )

        logger.info(
            f"Classified: agent={classifier_output.agent} "
            f"intent={classifier_output.intent} "
            f"entities={classifier_output.entities.to_dict()}"
        )

        # ── Step 3: Agent Manager ──
        manager = get_agent_manager()
        result = await asyncio.wait_for(
            manager.handle(
                classifier_output=classifier_output,
                user_id=request.user_id,
            ),
            timeout=settings.pipeline_timeout_seconds,
        )

        # ── Step 4: Record turn in session memory ──
        memory = get_session_memory()
        memory.add_turn(
            session_id=request.session_id,
            user_query=request.query,
            entities=classifier_output.entities.to_dict(),
            agent=classifier_output.agent,
            intent=classifier_output.intent,
        )

        # ── Step 5: Stream response ──
        yield sse_data(result)
        yield sse_end()

    except asyncio.TimeoutError:
        logger.error(f"Pipeline timeout for query: {request.query[:80]}")
        yield sse_error(
            message="Request timed out. Please try again.",
            detail=f"Pipeline exceeded {settings.pipeline_timeout_seconds}s timeout.",
        )
        yield sse_end()

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        yield sse_error(
            message="An unexpected error occurred. Please try again.",
            detail=str(e),
        )
        yield sse_end()


@router.post("/query")
async def query_endpoint(request: QueryRequest):
    """
    POST /query — Main query endpoint.

    Accepts a JSON body with query, user_id, and optional session_id.
    Returns an SSE stream with the pipeline results.
    """
    return StreamingResponse(
        _pipeline_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "valura-ai-agent-manager"}
