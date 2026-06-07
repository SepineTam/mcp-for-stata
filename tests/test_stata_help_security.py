"""Security tests for Stata help command-name validation."""

import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.stata.builtin_tools.help.stata_help import StataHelp


@pytest.fixture
def stata_help(tmp_path: Path) -> StataHelp:
    """Create a StataHelp instance without starting a real Stata process."""
    help_reader = StataHelp.__new__(StataHelp)
    help_reader._config = None
    help_reader.help_cache_dir = tmp_path / "cache"
    help_reader.help_cache_dir.mkdir()
    help_reader.project_tmp_dir = tmp_path / "project"
    help_reader.project_tmp_dir.mkdir()
    help_reader.controller = Mock()
    return help_reader


@pytest.mark.parametrize(
    ("raw_command", "normalized_command"),
    [
        ("regress", "regress"),
        ("ivreg2", "ivreg2"),
        ("_xtreg", "_xtreg"),
        ("  regress\t", "regress"),
    ],
)
def test_validate_command_name_accepts_single_command_names(
    raw_command: str,
    normalized_command: str,
) -> None:
    assert StataHelp._validate_command_name(raw_command) == normalized_command


@pytest.mark.parametrize(
    "unsafe_command",
    [
        "",
        "   ",
        "regress shell",
        "regress\tshell",
        "regress\nshell",
        "regress.do",
        "../regress",
        "`cmd'",
        "$cmd",
        "${cmd}",
        'regress"',
        "regress;",
    ],
)
def test_validate_command_name_rejects_unsafe_input(unsafe_command: str) -> None:
    with pytest.raises(ValueError, match="Invalid Stata command name"):
        StataHelp._validate_command_name(unsafe_command)


def test_validate_command_name_rejects_non_string() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        StataHelp._validate_command_name(None)  # type: ignore[arg-type]


def test_help_rejects_unsafe_input_before_cache_or_stata_access(
    stata_help: StataHelp,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_from_project = Mock()
    load_from_cache = Mock()
    load_from_stata = Mock()
    cache_and_save = Mock()
    monkeypatch.setattr(stata_help, "load_from_project", load_from_project)
    monkeypatch.setattr(stata_help, "load_from_cache", load_from_cache)
    monkeypatch.setattr(stata_help, "load_from_stata", load_from_stata)
    monkeypatch.setattr(stata_help, "_cache_and_save", cache_and_save)

    with pytest.raises(ValueError, match="Invalid Stata command name"):
        stata_help.help("regress\nshell echo pwn")

    load_from_project.assert_not_called()
    load_from_cache.assert_not_called()
    load_from_stata.assert_not_called()
    cache_and_save.assert_not_called()
    stata_help.controller.run.assert_not_called()


def test_help_uses_normalized_command_for_cache_lookup(stata_help: StataHelp) -> None:
    saved_help = stata_help.project_tmp_dir / "help__regress.txt"
    saved_help.write_text("saved help content", encoding="utf-8")

    result = stata_help.help("  regress  ")

    assert result == "Saved result for regress\nsaved help content"
    stata_help.controller.run.assert_not_called()


def test_help_uses_newest_enabled_cache(stata_help: StataHelp) -> None:
    stata_help._config = SimpleNamespace(IS_SAVE_HELP=True, IS_CACHE_HELP=True)
    project_help = stata_help.project_tmp_dir / "help__regress.txt"
    global_help = stata_help.help_cache_dir / "help__regress.txt"
    project_help.write_text("old project help", encoding="utf-8")
    global_help.write_text("new global help", encoding="utf-8")
    os.utime(project_help, ns=(100, 100))
    os.utime(global_help, ns=(200, 200))

    result = stata_help.help("regress")

    assert result == "Cached result for regress\nnew global help"
    stata_help.controller.run.assert_not_called()


def test_help_prefers_project_cache_when_timestamps_match(stata_help: StataHelp) -> None:
    stata_help._config = SimpleNamespace(IS_SAVE_HELP=True, IS_CACHE_HELP=True)
    project_help = stata_help.project_tmp_dir / "help__regress.txt"
    global_help = stata_help.help_cache_dir / "help__regress.txt"
    project_help.write_text("project help", encoding="utf-8")
    global_help.write_text("global help", encoding="utf-8")
    os.utime(project_help, ns=(100, 100))
    os.utime(global_help, ns=(100, 100))

    result = stata_help.help("regress")

    assert result == "Saved result for regress\nproject help"


def test_help_does_not_read_disabled_cache(stata_help: StataHelp) -> None:
    stata_help._config = SimpleNamespace(IS_SAVE_HELP=False, IS_CACHE_HELP=True)
    project_help = stata_help.project_tmp_dir / "help__regress.txt"
    global_help = stata_help.help_cache_dir / "help__regress.txt"
    project_help.write_bytes(b"\xff")
    global_help.write_text("global help", encoding="utf-8")

    result = stata_help.help("regress")

    assert result == "Cached result for regress\nglobal help"


def test_help_replace_bypasses_and_refreshes_caches(stata_help: StataHelp) -> None:
    stata_help._config = SimpleNamespace(IS_SAVE_HELP=True, IS_CACHE_HELP=True)
    project_help = stata_help.project_tmp_dir / "help__regress.txt"
    global_help = stata_help.help_cache_dir / "help__regress.txt"
    project_help.write_text("old project help", encoding="utf-8")
    global_help.write_text("old global help", encoding="utf-8")
    stata_help.controller.run.return_value = "live help"

    result = stata_help.help("regress", replace=True)

    assert result == "live help"
    stata_help.controller.run.assert_called_once_with("help regress")
    assert project_help.read_text(encoding="utf-8") == "live help"
    assert global_help.read_text(encoding="utf-8") == "live help"


def test_check_command_exist_rejects_unsafe_input_before_stata_access(
    stata_help: StataHelp,
) -> None:
    with pytest.raises(ValueError, match="Invalid Stata command name"):
        stata_help.check_command_exist_with_help("github\nshell echo pwn")

    stata_help.controller.run.assert_not_called()


def test_check_command_exist_uses_normalized_command(stata_help: StataHelp) -> None:
    stata_help.controller.run.return_value = "github help content"

    assert stata_help.check_command_exist_with_help("  github  ") is True
    stata_help.controller.run.assert_called_once_with("help github")
