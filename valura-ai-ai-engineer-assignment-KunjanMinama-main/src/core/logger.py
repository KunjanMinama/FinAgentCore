"""
Structured logging setup for the Valura AI microservice.

Usage:
    from src.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Classified query", extra={"agent": "portfolio_health"})
"""

from __future__ import annotations

import logging
import sys

from src.core.config import get_settings


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with structured formatting."""
    settings = get_settings()
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger
