"""Tests for mcp_servers security-rejection log sanitization."""

from __future__ import annotations

import asyncio
import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def stubbed_mcp_servers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Load stata_mcp.mcp_servers with isolated dependency stubs."""
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    home_dir.mkdir()
    project_dir.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.chdir(project_dir)
    monkeypatch.delenv("STATA_MCP_CONFIG_FILE", raising=False)

    fastmcp_module = ModuleType("mcp.server.fastmcp")

    class _FastMCP:
        def __init__(self, *args, **kwargs) -> None:
            self._tools = []

        def tool(self, name: str, description: str):
            def _decorator(func):
                self._tools.append((name, func))
                return func

            return _decorator

        def resource(self, uri: str, name: str, description: str):
            def _decorator(func):
                return func

            return _decorator

        def run(self, transport: str) -> None:
            return None

    class _Icon:
        def __init__(self, *args, **kwargs) -> None:
            pass

    class _Context:
        pass

    fastmcp_module.FastMCP = _FastMCP
    fastmcp_module.Icon = _Icon
    fastmcp_module.Context = _Context

    mcp_module = ModuleType("mcp")
    mcp_server_module = ModuleType("mcp.server")
    mcp_server_module.fastmcp = fastmcp_module
    mcp_module.server = mcp_server_module

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", mcp_server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)

    monkeypatch.delitem(sys.modules, "stata_mcp.mcp_servers", raising=False)

    return importlib.import_module("stata_mcp.mcp_servers")


def test_prepare_stata_do_request_rejection_log_redacts_url_query(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    stubbed_mcp_servers,
    tmp_path: Path,
) -> None:
    """The security-rejection log must not leak URL query parameters or full paths."""
    work = tmp_path / "work"
    work.mkdir()

    fake_folder = SimpleNamespace(DO=work, TMP=tmp_path / "tmp")
    fake_config = SimpleNamespace(
        WORKING_DIR=work,
        STATA_MCP_FOLDER=fake_folder,
        IS_GUARD=True,
        ENABLE_DATA_COMMAND_PATH_GUARD=True,
        STRICT_DATA_INFO_LOCAL_BOUNDARY=True,
        ENABLE_DATA_INFO_URL_GUARD=True,
        DATA_INFO_ALLOWED_URL_DOMAINS=("example.com",),
        IS_MONITOR=False,
        MAX_RAM_MB=None,
        LOGGING_ON=True,
    )
    monkeypatch.setattr(stubbed_mcp_servers, "config", fake_config)

    dofile = work / "bad.do"
    dofile.write_text(
        'use "https://evil.com/data.dta?token=secret#anchor"\n',
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        result = stubbed_mcp_servers._prepare_stata_do_request(dofile.as_posix())

    assert result["action"] == "Security check, dofile not executed"
    # The caller-facing warning still contains the raw URL for diagnostics.
    assert "token=secret" in result["warning"]

    messages = "\n".join(caplog.messages)
    assert "[SECURITY VIOLATION]" in messages
    assert "token=secret" not in messages
    assert "#anchor" not in messages
    assert "evil.com/data.dta" in messages


def test_prepare_stata_do_request_rejection_log_redacts_local_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    stubbed_mcp_servers,
    tmp_path: Path,
) -> None:
    """The security-rejection log must not leak absolute local file paths."""
    work = tmp_path / "work"
    work.mkdir()
    outside = tmp_path / "secret.dta"
    outside.write_text("", encoding="utf-8")

    fake_folder = SimpleNamespace(DO=work, TMP=tmp_path / "tmp")
    fake_config = SimpleNamespace(
        WORKING_DIR=work,
        STATA_MCP_FOLDER=fake_folder,
        IS_GUARD=True,
        ENABLE_DATA_COMMAND_PATH_GUARD=True,
        STRICT_DATA_INFO_LOCAL_BOUNDARY=True,
        ENABLE_DATA_INFO_URL_GUARD=True,
        DATA_INFO_ALLOWED_URL_DOMAINS=(),
        IS_MONITOR=False,
        MAX_RAM_MB=None,
        LOGGING_ON=True,
    )
    monkeypatch.setattr(stubbed_mcp_servers, "config", fake_config)

    dofile = work / "bad.do"
    dofile.write_text(
        f'use "{outside.as_posix()}"\n',
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        result = stubbed_mcp_servers._prepare_stata_do_request(dofile.as_posix())

    assert result["action"] == "Security check, dofile not executed"
    # The caller-facing warning still contains the raw path for diagnostics.
    assert outside.as_posix() in result["warning"]

    messages = "\n".join(caplog.messages)
    assert "[SECURITY VIOLATION]" in messages
    assert outside.as_posix() not in messages


def test_read_log_rejection_log_redacts_local_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    stubbed_mcp_servers,
    tmp_path: Path,
) -> None:
    """The read_log boundary rejection log must not leak absolute paths."""
    statamcp_dir = tmp_path / "statamcp"
    statamcp_dir.mkdir()
    outside = tmp_path / "secret.log"
    outside.write_text("log content", encoding="utf-8")

    fake_folder = SimpleNamespace(path=statamcp_dir)
    fake_config = SimpleNamespace(STATA_MCP_FOLDER=fake_folder)
    monkeypatch.setattr(stubbed_mcp_servers, "config", fake_config)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(PermissionError):
            stubbed_mcp_servers.read_log(outside.as_posix())

    messages = "\n".join(caplog.messages)
    assert "[SECURITY VIOLATION]" in messages
    assert outside.as_posix() not in messages
    assert "requested_path" not in messages
    assert "resolved_path" not in messages
    assert "allowed_directory" not in messages


def test_read_log_structured_parsing_depends_only_on_config(
    monkeypatch: pytest.MonkeyPatch,
    stubbed_mcp_servers,
    tmp_path: Path,
) -> None:
    """Structured MCP log parsing must not depend on the operating system."""
    statamcp_dir = tmp_path / "statamcp"
    log_dir = statamcp_dir / "stata-mcp-log"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "test.log"
    log_file.write_text(
        "name: test\nlog: /path/to/test.log\n\n. sysuse auto\n. regress price mpg\n",
        encoding="utf-8",
    )

    fake_folder = SimpleNamespace(path=statamcp_dir)
    fake_config = SimpleNamespace(
        STATA_MCP_FOLDER=fake_folder,
        ENABLE_STRUCTURED_LOG=True,
    )
    monkeypatch.setattr(stubbed_mcp_servers, "config", fake_config)

    result = stubbed_mcp_servers.read_log(log_file.as_posix())

    assert "name: test" not in result
    assert ". sysuse auto" in result


def test_sync_stata_do_execution_failure_log_redacts_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    stubbed_mcp_servers,
    tmp_path: Path,
) -> None:
    """The sync execution-failure log must not leak absolute paths."""
    work = tmp_path / "work"
    work.mkdir()
    dofile = work / "analysis.do"
    dofile.write_text("di 1\n", encoding="utf-8")

    fake_folder = SimpleNamespace(DO=work, TMP=tmp_path / "tmp", LOG=tmp_path / "log")
    fake_config = SimpleNamespace(
        WORKING_DIR=work,
        STATA_MCP_FOLDER=fake_folder,
        IS_GUARD=False,
        IS_MONITOR=False,
        MAX_RAM_MB=None,
        LOGGING_ON=True,
        STATA_CLI=Path("stata"),
        IS_UNIX=True,
    )
    monkeypatch.setattr(stubbed_mcp_servers, "config", fake_config)

    class _FailingExecutor:
        def __init__(self, **kwargs) -> None:
            pass

        def execute_dofile(self, *args, **kwargs) -> None:
            raise RuntimeError(f"failed to run {dofile.as_posix()}")

    stata_module = importlib.import_module("stata_mcp.stata")
    monkeypatch.setattr(stata_module, "StataDo", _FailingExecutor)

    with caplog.at_level(logging.ERROR):
        result = stubbed_mcp_servers._sync_stata_do(dofile.as_posix())

    assert "error" in result
    messages = "\n".join(caplog.messages)
    assert "Failed to execute dofile." in messages
    assert dofile.as_posix() not in messages


def test_async_stata_do_execution_failure_log_redacts_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    stubbed_mcp_servers,
    tmp_path: Path,
) -> None:
    """The async execution-failure log must not leak absolute paths."""
    work = tmp_path / "work"
    work.mkdir()
    dofile = work / "analysis.do"
    dofile.write_text("di 1\n", encoding="utf-8")

    fake_folder = SimpleNamespace(DO=work, TMP=tmp_path / "tmp", LOG=tmp_path / "log")
    fake_config = SimpleNamespace(
        WORKING_DIR=work,
        STATA_MCP_FOLDER=fake_folder,
        IS_GUARD=False,
        IS_MONITOR=False,
        MAX_RAM_MB=None,
        LOGGING_ON=True,
        STATA_CLI=Path("stata"),
        IS_UNIX=True,
    )
    monkeypatch.setattr(stubbed_mcp_servers, "config", fake_config)

    class _FailingAsyncExecutor:
        def __init__(self, **kwargs) -> None:
            pass

        async def execute_dofile_async(self, *args, **kwargs) -> None:
            raise RuntimeError(f"failed to run {dofile.as_posix()}")

    async_do_module = importlib.import_module("stata_mcp.stata.stata_do.async_do")
    monkeypatch.setattr(async_do_module, "AsyncStataDo", _FailingAsyncExecutor)

    with caplog.at_level(logging.ERROR):
        result = asyncio.run(stubbed_mcp_servers._async_stata_do(dofile.as_posix()))

    assert "error" in result
    messages = "\n".join(caplog.messages)
    assert "Failed to execute dofile." in messages
    assert dofile.as_posix() not in messages
