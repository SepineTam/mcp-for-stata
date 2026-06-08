"""Tests for optional stata_do execution timeouts."""

from __future__ import annotations

import importlib
import subprocess
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.cli._handlers import handle_tool
from stata_mcp.cli._parsers import add_tool_parser, create_root_parser
from stata_mcp.stata.stata_do.do import StataDo


def _build_parser():
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command")
    add_tool_parser(subparsers)
    return parser


def _dofile(tmp_path: Path) -> Path:
    dofile = tmp_path / "analysis.do"
    dofile.write_text("display 1", encoding="utf-8")
    return dofile


def _completed_process() -> Mock:
    process = Mock()
    process.returncode = 0
    process.communicate.return_value = ("", "")
    process.poll.return_value = 0
    return process


def test_cli_do_timeout_defaults_to_none_and_accepts_seconds() -> None:
    parser = _build_parser()

    default_args = parser.parse_args(["tool", "do", "analysis.do"])
    timeout_args = parser.parse_args(["tool", "do", "analysis.do", "--timeout", "2.5"])

    assert default_args.timeout is None
    assert timeout_args.timeout == 2.5


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "invalid"])
def test_cli_do_timeout_rejects_invalid_values(value: str) -> None:
    with pytest.raises(SystemExit):
        _build_parser().parse_args(["tool", "do", "analysis.do", "--timeout", value])


def test_cli_do_handler_forwards_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    stata_do = Mock(return_value={"log_file_path": {"text": "/tmp/run.log"}})
    fake_api = SimpleNamespace(
        ado_package_install=Mock(),
        get_data_info=Mock(),
        read_log=Mock(),
        stata_do=stata_do,
        stata_help=Mock(),
    )
    monkeypatch.setitem(__import__("sys").modules, "stata_mcp.api", fake_api)
    args = Namespace(
        tool_action="do",
        dofile_path="analysis.do",
        log_file_name=None,
        is_read_log=True,
        is_replace_log=True,
        enable_smcl=True,
        timeout=15.0,
    )

    assert handle_tool(args) == 0
    stata_do.assert_called_once_with(
        dofile_path="analysis.do",
        log_file_name=None,
        read_log_when_error=True,
        is_replace_log=True,
        enable_smcl=True,
        timeout=15.0,
    )


@pytest.mark.parametrize(
    "timeout",
    [True, 0, -1, float("nan"), float("inf"), 10**400, "10"],
)
def test_stata_do_rejects_invalid_timeout(timeout) -> None:
    with pytest.raises(ValueError, match="Invalid timeout"):
        StataDo._validate_timeout(timeout)


def test_stata_do_accepts_none_as_no_timeout() -> None:
    assert StataDo._validate_timeout(None) is None
    assert StataDo._validate_timeout(2) == 2.0


@pytest.mark.parametrize("with_monitor", [False, True])
def test_unix_execution_forwards_timeout_and_cleans_up_after_expiry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    with_monitor: bool,
) -> None:
    process = _completed_process()
    process.communicate.side_effect = subprocess.TimeoutExpired("stata", 0.1)
    process.poll.return_value = None
    monitor = Mock()
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=process))
    executor = StataDo(
        "stata",
        tmp_path,
        is_unix=True,
        monitors=[monitor] if with_monitor else None,
    )

    with pytest.raises(RuntimeError, match="timed out after 0.1 seconds"):
        executor.execute_dofile(_dofile(tmp_path), timeout=0.1)

    assert process.communicate.call_args.kwargs["timeout"] == 0.1
    process.terminate.assert_called_once_with()
    process.wait.assert_called_once_with(timeout=5)
    if with_monitor:
        monitor.stop.assert_called_once_with()


def test_unix_execution_uses_no_timeout_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    process = _completed_process()
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=process))
    executor = StataDo("stata", tmp_path, is_unix=True)

    executor.execute_dofile(_dofile(tmp_path), enable_smcl=False)

    assert process.communicate.call_args.kwargs["timeout"] is None


def test_windows_execution_forwards_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run = Mock(return_value=SimpleNamespace(returncode=0, stderr=""))
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr("tempfile.gettempdir", lambda: tmp_path.as_posix())
    executor = StataDo("stata", tmp_path, is_unix=False)

    executor.execute_dofile(_dofile(tmp_path), timeout=4)

    assert run.call_args.kwargs["timeout"] == 4.0


def test_monitored_windows_execution_forwards_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    process = _completed_process()
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr("tempfile.gettempdir", lambda: tmp_path.as_posix())
    executor = StataDo("stata", tmp_path, is_unix=False, monitors=[Mock()])

    executor.execute_dofile(_dofile(tmp_path), timeout=4)

    assert process.communicate.call_args.kwargs["timeout"] == 4.0


def test_api_stata_do_forwards_optional_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stata_do_api = importlib.import_module("stata_mcp.api.stata_do")
    dofile = _dofile(tmp_path)
    executor = Mock()
    executor.execute_dofile.return_value = {"text": tmp_path / "run.log"}
    runtime = SimpleNamespace(
        config=SimpleNamespace(
            STATA_MCP_FOLDER=SimpleNamespace(DO=tmp_path),
            WORKING_DIR=tmp_path,
            IS_GUARD=False,
            IS_MONITOR=False,
        ),
        stata_cli="stata",
        log_base_path=tmp_path,
        is_unix=True,
        cwd=tmp_path,
    )
    monkeypatch.setattr(
        stata_do_api, "create_runtime_context", lambda **kwargs: runtime
    )
    monkeypatch.setattr(stata_do_api, "StataDo", Mock(return_value=executor))

    result = stata_do_api.stata_do(dofile.as_posix(), timeout=8)

    assert "error" not in result
    executor.execute_dofile.assert_called_once_with(
        dofile.resolve(),
        None,
        True,
        True,
        timeout=8,
    )
