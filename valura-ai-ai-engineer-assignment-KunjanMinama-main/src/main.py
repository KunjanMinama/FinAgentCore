"""
Valura AI Agent Manager — FastAPI Application Entry Point.

Starts the microservice that handles user queries through the
safety → classifier → agent → SSE streaming pipeline.

Usage:
    uvicorn src.main:app --reload --port 8000
"""

from __future__ import annotations  

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env before anything else
load_dotenv()

from src.api.router import router
from src.core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("🚀 Valura AI Agent Manager starting up")
    yield
    logger.info("👋 Valura AI Agent Manager shutting down")


app = FastAPI(
    title="Valura AI Agent Manager",
    description=(
        "Intelligence layer for Valura's wealth management platform. "
        "Classifies user queries, routes to specialist agents, and "
        "streams responses via SSE."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
