"""Tests for StataController prompt and error handling."""

from types import SimpleNamespace
from unittest.mock import Mock

import pexpect
import pytest

from stata_mcp.stata.stata_controller import StataController


def _controller_with_child(child: SimpleNamespace) -> StataController:
    controller = StataController.__new__(StataController)
    controller.child = child
    controller.timeout = 30
    controller._last_error_code = None
    controller._last_error_output = None
    return controller


def test_run_raises_with_stata_error_code_matched_by_expect() -> None:
    child = SimpleNamespace(
        before="package not found",
        after="r(601);",
        expect=Mock(side_effect=[3, 0]),
        sendline=Mock(),
    )
    controller = _controller_with_child(child)

    with pytest.raises(RuntimeError, match=r"Stata error r\(601\): package not found"):
        controller.run("github install owner/repository")

    child.sendline.assert_called_once_with("github install owner/repository")


def test_run_raises_when_error_prompt_has_no_parseable_code() -> None:
    child = SimpleNamespace(
        before="unknown Stata failure",
        after="error",
        expect=Mock(side_effect=[3, 0]),
        sendline=Mock(),
    )
    controller = _controller_with_child(child)

    with pytest.raises(RuntimeError, match="Stata command failed: unknown Stata failure"):
        controller.run("bad command")


def test_run_returns_output_after_standard_prompt() -> None:
    child = SimpleNamespace(
        before="command output",
        after=". ",
        expect=Mock(return_value=0),
        sendline=Mock(),
    )
    controller = _controller_with_child(child)

    assert controller.run("display 1") == "command output"


def test_run_raises_after_timeout() -> None:
    child = SimpleNamespace(
        before="partial output",
        after=pexpect.TIMEOUT,
        expect=Mock(side_effect=[4, 1]),
        sendline=Mock(),
    )
    controller = _controller_with_child(child)

    with pytest.raises(RuntimeError, match="Command timed out"):
        controller.run("sleep 1000", timeout=1)


def test_run_raises_after_stata_session_ends() -> None:
    child = SimpleNamespace(
        before="session ended",
        after=pexpect.EOF,
        expect=Mock(return_value=5),
        sendline=Mock(),
    )
    controller = _controller_with_child(child)

    with pytest.raises(RuntimeError, match="Stata session terminated unexpectedly"):
        controller.run("display 1")
