"""Tests for shared diagnostic logging helpers."""

from __future__ import annotations

import io
import logging

from stata_mcp._diagnostic_logging import (
    DiagnosticWatchdog,
    log_event,
    process_log_path,
    safe_stack,
    utf8_size,
)


def test_safe_stack_redacts_absolute_source_paths_and_exception_messages() -> None:
    """Sanitized stacks should retain locations without usernames or messages."""
    try:
        exec(
            compile(
                'raise RuntimeError("dataset at /tmp/private/data.dta")',
                "/tmp/private/site-packages/reader.py",
                "exec",
            )
        )
    except RuntimeError as error:
        stack = safe_stack(error)
    else:
        raise AssertionError("Expected the compiled test code to fail")

    assert "reader.py:1:<module>" in stack
    assert "/tmp/private" not in stack
    assert "data.dta" not in stack


def test_safe_stack_remains_private_in_fully_formatted_log() -> None:
    """The final formatter output should not reintroduce absolute traceback paths."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger = logging.getLogger("test.diagnostic.safe-stack")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.ERROR)

    try:
        exec(
            compile(
                'raise ValueError("secret /tmp/private/data.dta")',
                "/tmp/private/site-packages/parser.py",
                "exec",
            )
        )
    except ValueError as error:
        log_event(
            logger,
            logging.ERROR,
            "get_data_info.test.failed",
            "abc123def456",
            error_type=type(error).__name__,
            stack=safe_stack(error),
        )

    output = stream.getvalue()
    assert "parser.py:1:<module>" in output
    assert "/tmp/private" not in output
    assert "data.dta" not in output


def test_watchdog_cancel_prevents_late_snapshot(caplog) -> None:
    """A completed request should not receive a late watchdog warning."""
    logger = logging.getLogger("test.diagnostic.watchdog")
    watchdog = DiagnosticWatchdog(logger, "abc123def456", delays=())

    watchdog.cancel()
    with caplog.at_level(logging.WARNING, logger=logger.name):
        watchdog._log_snapshot(30.0)

    assert not caplog.records


def test_process_log_path_adds_pid_before_suffix() -> None:
    """Debug log files should be isolated by process before rotation."""
    result = process_log_path("/tmp/logs/stata_mcp_debug.log", pid=4321)
    assert result.as_posix().endswith("/stata_mcp_debug.4321.log")


def test_utf8_size_handles_isolated_surrogates() -> None:
    """Diagnostic byte measurement should never reject a valid Python string."""
    assert utf8_size("ok\ud800") > 2
