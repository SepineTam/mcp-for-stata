"""Tests for dofile execution boundary validation."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from stata_mcp.stata.stata_do.do import StataDo


@pytest.fixture
def loaded_mcp_servers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Load mcp_servers with minimal external dependency stubs."""
    monkeypatch.setenv("HOME", (tmp_path / "home").as_posix())
    monkeypatch.setitem(sys.modules, "tomli_w", SimpleNamespace(dump=lambda *args, **kwargs: None))
    monkeypatch.setitem(sys.modules, "pexpect", ModuleType("pexpect"))

    fastmcp_module = ModuleType("mcp.server.fastmcp")

    class _FastMCP:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def tool(self, name: str, description: str):
            def _decorator(func):
                return func

            return _decorator

        def resource(self, uri: str, name: str, description: str):
            def _decorator(func):
                return func

            return _decorator

    class _Icon:
        def __init__(self, *args, **kwargs) -> None:
            pass

    fastmcp_module.FastMCP = _FastMCP
    fastmcp_module.Icon = _Icon

    mcp_module = ModuleType("mcp")
    mcp_server_module = ModuleType("mcp.server")
    mcp_server_module.fastmcp = fastmcp_module
    mcp_module.server = mcp_server_module

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", mcp_server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)

    monkeypatch.delitem(sys.modules, "stata_mcp.mcp_servers", raising=False)
    return importlib.import_module("stata_mcp.mcp_servers")


def _configure_base(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, do_dir: Path, work_dir: Path, root: Path) -> None:
    monkeypatch.setattr(
        loaded_mcp_servers,
        "config",
        SimpleNamespace(
            STATA_MCP_FOLDER=SimpleNamespace(DO=do_dir, LOG=root, path=root),
            WORKING_DIR=work_dir,
            IS_GUARD=False,
            IS_MONITOR=False,
            STATA_CLI="stata",
            IS_UNIX=True,
        ),
        raising=False,
    )


def _patch_stata_module(monkeypatch: pytest.MonkeyPatch, log_file: Path) -> None:
    fake_stata = ModuleType("stata_mcp.stata")

    class _FakeStataDo:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def execute_dofile(self, *args, **kwargs):
            return {"text": log_file}

    fake_stata.StataDo = _FakeStataDo
    monkeypatch.setitem(sys.modules, "stata_mcp.stata", fake_stata)


def test_is_within_allowed_directories_uses_input_path_directly(loaded_mcp_servers, tmp_path: Path):
    allowed = tmp_path / "allowed"
    dofile = allowed / "nested" / "sample.do"
    dofile.parent.mkdir(parents=True)
    dofile.write_text("display 1")

    assert loaded_mcp_servers._is_within_allowed_directories(dofile.resolve(), [allowed.resolve()]) is True
    assert loaded_mcp_servers._is_within_allowed_directories((tmp_path / "outside.do").resolve(), [allowed.resolve()]) is False


def test_stata_do_allows_dofile_in_working_dir(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, tmp_path: Path):
    do_dir = tmp_path / "do"
    do_dir.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    dofile = work_dir / "ok.do"
    dofile.write_text("display 1")

    log_file = tmp_path / "run.log"
    log_file.write_text("ok")

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)
    _patch_stata_module(monkeypatch, log_file)

    result = loaded_mcp_servers.stata_do(dofile.as_posix())

    assert "error" not in result
    assert result["log_file_path"]["text"] == log_file.as_posix()


def test_stata_do_rejects_dofile_outside_whitelist(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, tmp_path: Path):
    do_dir = tmp_path / "do"
    do_dir.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    dofile = outside / "blocked.do"
    dofile.write_text("display 1")

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)

    result = loaded_mcp_servers.stata_do(dofile.as_posix())

    assert result["error"].startswith("Access denied")
    assert do_dir.resolve().as_posix() in result["allowed_directories"]
    assert work_dir.resolve().as_posix() in result["allowed_directories"]


def test_stata_do_rejects_symlink_pointing_outside(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, tmp_path: Path):
    do_dir = tmp_path / "do"
    do_dir.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()
    real_file = outside / "real.do"
    real_file.write_text("display 1")
    symlink = work_dir / "link.do"
    symlink.symlink_to(real_file)

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)

    result = loaded_mcp_servers.stata_do(symlink.as_posix())

    assert result["error"].startswith("Access denied")


def test_stata_do_rejects_path_traversal(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, tmp_path: Path):
    do_dir = tmp_path / "do"
    do_dir.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()
    blocked = outside / "blocked.do"
    blocked.write_text("display 1")

    traversal_path = work_dir / ".." / "outside" / "blocked.do"

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)

    result = loaded_mcp_servers.stata_do(traversal_path.as_posix())

    assert result["error"].startswith("Access denied")


def test_stata_do_skips_missing_allowed_directories(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, tmp_path: Path):
    do_dir = tmp_path / "missing-do"
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    dofile = work_dir / "ok.do"
    dofile.write_text("display 1")

    log_file = tmp_path / "run.log"
    log_file.write_text("ok")

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)
    _patch_stata_module(monkeypatch, log_file)

    result = loaded_mcp_servers.stata_do(dofile.as_posix())

    assert "error" not in result
    assert result["log_file_path"]["text"] == log_file.as_posix()


def test_stata_do_allows_dofile_in_do_directory(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, tmp_path: Path):
    do_dir = tmp_path / "do"
    do_dir.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    dofile = do_dir / "ok.do"
    dofile.write_text("display 1")

    log_file = tmp_path / "run.log"
    log_file.write_text("ok")

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)
    _patch_stata_module(monkeypatch, log_file)

    result = loaded_mcp_servers.stata_do(dofile.as_posix())

    assert "error" not in result
    assert result["log_file_path"]["text"] == log_file.as_posix()


def test_stata_do_rejects_when_allowed_directories_are_empty(monkeypatch: pytest.MonkeyPatch, loaded_mcp_servers, tmp_path: Path):
    do_dir = tmp_path / "missing-do"
    work_dir = tmp_path / "missing-work"
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    dofile = outside_dir / "blocked.do"
    dofile.write_text("display 1")

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)

    result = loaded_mcp_servers.stata_do(dofile.as_posix())

    assert result["error"].startswith("Access denied")
    assert result["allowed_directories"] == []


def test_stata_do_logs_warning_when_guard_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    loaded_mcp_servers,
    tmp_path: Path,
):
    do_dir = tmp_path / "do"
    do_dir.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    dofile = work_dir / "ok.do"
    dofile.write_text("display 1")
    log_file = tmp_path / "run.log"
    log_file.write_text("ok")

    _configure_base(monkeypatch, loaded_mcp_servers, do_dir, work_dir, tmp_path)
    _patch_stata_module(monkeypatch, log_file)

    with caplog.at_level("WARNING"):
        loaded_mcp_servers.stata_do(dofile.as_posix())

    assert any("[SECURITY] Guard is disabled" in message for message in caplog.messages)


class TestValidateLogName:
    """Tests for StataDo._validate_log_name security validation."""

    def test_valid_log_names(self):
        valid_names = [
            "test",
            "test_123",
            "my.file",
            "my-file",
            "A" * 128,
        ]
        for name in valid_names:
            StataDo._validate_log_name(name)

    def test_invalid_characters(self):
        invalid_names = [
            'test"; shell echo pwn',
            "test`cmd'",
            "test\nshell",
            "test; shell",
            "test/name",
            "test\\name",
            "test name",
            "test<dir>",
        ]
        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid log_file_name"):
                StataDo._validate_log_name(name)

    def test_path_traversal(self):
        invalid_names = [
            "..",
            ".",
        ]
        for name in invalid_names:
            with pytest.raises(ValueError, match="Path traversal"):
                StataDo._validate_log_name(name)

    def test_path_traversal_with_slash(self):
        invalid_names = [
            "../etc/passwd",
            "foo/../../bar",
        ]
        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid log_file_name"):
                StataDo._validate_log_name(name)

    def test_length_boundary(self):
        StataDo._validate_log_name("a" * 128)
        with pytest.raises(ValueError, match="Invalid log_file_name"):
            StataDo._validate_log_name("a" * 129)


class TestValidateDofilePath:
    """Tests for StataDo._validate_dofile_path security validation."""

    def test_allows_do_file(self, tmp_path: Path):
        dofile = tmp_path / "ok.do"
        dofile.write_text("display 1")

        assert StataDo._validate_dofile_path(dofile) == dofile.resolve()

    def test_rejects_non_do_file(self, tmp_path: Path):
        dofile = tmp_path / "ok.txt"
        dofile.write_text("display 1")

        with pytest.raises(ValueError, match="Only .do files"):
            StataDo._validate_dofile_path(dofile)

    def test_rejects_control_characters_in_resolved_path(self, tmp_path: Path):
        for name in ['bad"name.do', "bad`name.do", "bad'name.do"]:
            dofile = tmp_path / name
            dofile.write_text("display 1")

            with pytest.raises(ValueError, match="Quotes, backticks, and newlines"):
                StataDo._validate_dofile_path(dofile)


class TestGenerateLogFile:
    """Tests for StataDo.generate_log_file boundary validation."""

    def test_rejects_resolved_path_outside_log_directory(self, tmp_path: Path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        stata_do = StataDo("stata", log_dir)

        with pytest.raises(ValueError, match="Path traversal"):
            stata_do.generate_log_file("../outside")
