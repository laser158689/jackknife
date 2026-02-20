"""Tests for the logging configuration."""

from __future__ import annotations

from jackknife.core.logging import configure_logging, get_logger


def test_get_logger_returns_logger() -> None:
    configure_logging()
    log = get_logger(__name__)
    assert log is not None


def test_configure_logging_json_mode() -> None:
    """JSON mode should not raise."""
    configure_logging(level="WARNING", json_output=True)


def test_configure_logging_console_mode() -> None:
    """Console mode should not raise."""
    configure_logging(level="INFO", json_output=False)


def test_logger_can_log(capsys: object) -> None:
    configure_logging(level="DEBUG", json_output=False)
    log = get_logger("test.module")
    # Should not raise
    log.info("test_event", key="value")
