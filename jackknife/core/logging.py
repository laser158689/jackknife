"""
Structured logging configuration for jackknife using structlog.

Why structlog over stdlib logging:
- Log entries are key=value pairs, not free-form strings
- Machine-readable JSON in production (Datadog, CloudWatch, etc.)
- Human-readable colored output in development
- Context variables (request_id, agent_id, etc.) attach to all log lines

Usage:
    from jackknife.core.logging import configure_logging, get_logger

    # Call once at startup (cli.py or __init__.py)
    configure_logging()

    # In any module:
    log = get_logger(__name__)
    log.info("memory_write", key="my-key", tokens=256)
    log.error("llm_error", provider="openai", error=str(exc))
"""

from __future__ import annotations

import logging
import sys
from typing import cast

import structlog
from structlog.stdlib import BoundLogger as BoundLogger  # noqa: PLC0414


def configure_logging(level: str = "INFO", json_output: bool = False) -> None:
    """
    Configure structlog for the process. Call once at startup.

    Args:
        level: Log level — DEBUG, INFO, WARNING, ERROR
        json_output: True for JSON lines (production); False for colored console (dev)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Use stdlib LoggerFactory so add_logger_name can read logger.name.
    # basicConfig routes everything through the same stream.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> BoundLogger:
    """
    Get a structlog bound logger for the given module name.

    Example:
        log = get_logger(__name__)
        log.info("blade_initialized", blade="memory", collection="project_memory")
    """
    return cast(BoundLogger, structlog.get_logger(name))
