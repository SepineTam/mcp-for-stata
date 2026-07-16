"""Tests for context-aware tool configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from stata_mcp.config import DEFAULT_DATA_INFO_METRICS, Config


def _write_config(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / "config.toml"
    config_path.write_text(content.strip(), encoding="utf-8")
    return config_path


def test_help_context_falls_back_per_key_to_generic_section(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
[HELP]
IS_CACHE = false
IS_SAVE = false

[MCP.TOOLS.HELP]
IS_CACHE = true
""",
    )

    config = Config(config_file=config_path)

    assert config.get_help_config("mcp").is_cache is True
    assert config.get_help_config("mcp").is_save is False
    assert config.get_help_config("cli").is_cache is False
    assert config.IS_CACHE_HELP is False


def test_context_environment_overrides_generic_environment_and_toml(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path,
        """
[HELP]
IS_CACHE = false

[MCP.TOOLS.HELP]
IS_CACHE = false
""",
    )
    monkeypatch.setenv("STATA_MCP__HELP__IS_CACHE", "false")
    monkeypatch.setenv("STATA_MCP__MCP__TOOLS__HELP__IS_CACHE", "true")

    assert Config(config_file=config_path).get_help_config("mcp").is_cache is True


def test_system_generic_value_overrides_context_environment_and_debug_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    system_config_path = tmp_path / "etc" / "statamcp" / "config.toml"
    system_config_path.parent.mkdir(parents=True)
    system_config_path.write_text("[HELP]\nIS_CACHE = false", encoding="utf-8")
    debug_config_path = _write_config(
        tmp_path,
        """
[MCP.TOOLS.HELP]
IS_CACHE = true
""",
    )
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(Config, "SYSTEM_CONFIG_FILE", system_config_path)
    monkeypatch.setenv("STATA_MCP__MCP__TOOLS__HELP__IS_CACHE", "true")

    settings = Config(config_file=debug_config_path).get_help_config("mcp")

    assert settings.is_cache is False


def test_project_generic_value_overrides_user_context_specific_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.chdir(project_dir)
    (user_config_dir / "config.toml").write_text(
        "[MCP.TOOLS.HELP]\nIS_CACHE = true",
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        "[HELP]\nIS_CACHE = false",
        encoding="utf-8",
    )

    settings = Config().get_help_config("mcp")

    assert settings.is_cache is False


def test_project_generic_data_info_value_overrides_user_context_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.chdir(project_dir)
    (user_config_dir / "config.toml").write_text(
        "[CLI.TOOLS.DATA_INFO]\nheads = 9",
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        "[data_info]\nheads = 2",
        encoding="utf-8",
    )

    settings = Config().get_data_info_config("cli")

    assert settings.heads == 2


def test_legacy_help_environment_alias_remains_supported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("STATA_MCP__CACHE_HELP", "false")

    config = Config(config_file=tmp_path / "missing.toml")

    assert config.get_help_config("mcp").is_cache is False
    assert config.IS_CACHE_HELP is False


def test_data_info_context_uses_canonical_then_legacy_generic_tables(
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path,
        """
[data_info]
is_cache = false
string_keep_number = 7
decimal_places = 2
hash_length = 8
heads = 1

[DATA_INFO]
decimal_places = 4

[MCP.TOOLS.DATA_INFO]
is_cache = true
metrics = ["obs", "med", "q1"]
hash_length = 16
""",
    )

    settings = Config(config_file=config_path).get_data_info_config("mcp")

    assert settings.is_cache is True
    assert settings.metrics == ("obs", "med", "q1")
    assert settings.string_keep_number == 7
    assert settings.decimal_places == 4
    assert settings.hash_length == 16
    assert settings.heads == 1


def test_data_info_context_defaults_distinguish_cli_from_mcp(tmp_path: Path) -> None:
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.get_data_info_config("cli").heads == 5
    assert config.get_data_info_config("mcp").heads == 0
    assert config.get_data_info_config("api").metrics == DEFAULT_DATA_INFO_METRICS


@pytest.mark.parametrize(
    ("key", "value", "attribute", "default"),
    [
        ("metrics", '["unknown"]', "metrics", DEFAULT_DATA_INFO_METRICS),
        ("string_keep_number", "-1", "string_keep_number", 10),
        ("decimal_places", "-1", "decimal_places", 3),
        ("hash_length", "0", "hash_length", 12),
        ("hash_length", "33", "hash_length", 12),
    ],
)
def test_invalid_data_info_values_fall_back_safely(
    tmp_path: Path,
    key: str,
    value: str,
    attribute: str,
    default,
) -> None:
    config_path = _write_config(
        tmp_path,
        f"""
[MCP.TOOLS.DATA_INFO]
{key} = {value}
""",
    )

    settings = Config(config_file=config_path).get_data_info_config("mcp")

    assert getattr(settings, attribute) == default


def test_legacy_data_info_environment_aliases_remain_supported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("STATA_MCP__DATA_INFO_IS_CACHE", "false")
    monkeypatch.setenv("STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER", "4")
    monkeypatch.setenv("STATA_MCP_DATA_INFO_DECIMAL_PLACES", "1")
    monkeypatch.setenv("STATA_MCP_DATA_INFO_HASH_LENGTH", "6")

    settings = Config(
        config_file=tmp_path / "missing.toml"
    ).get_data_info_config("mcp")

    assert settings.is_cache is False
    assert settings.string_keep_number == 4
    assert settings.decimal_places == 1
    assert settings.hash_length == 6


@pytest.mark.parametrize(
    ("tool_name", "expected"),
    [
        ("HELP", False),
        ("DATA_INFO", True),
        ("STATA_DO", True),
    ],
)
def test_mcp_tool_switches_default_to_enabled_and_read_explicit_values(
    tmp_path: Path,
    tool_name: str,
    expected: bool,
) -> None:
    config_path = _write_config(
        tmp_path,
        """
[MCP.TOOLS]
ENABLE_HELP = false
ENABLE_DATA_INFO = true
""",
    )
    config = Config(config_file=config_path)

    assert config.is_tool_enabled("mcp", tool_name) is expected


def test_tool_switch_rejects_unknown_context(tmp_path: Path) -> None:
    config = Config(config_file=tmp_path / "missing.toml")

    with pytest.raises(ValueError, match="Unsupported tool context"):
        config.is_tool_enabled("desktop", "HELP")  # type: ignore[arg-type]


def test_additional_allowed_dirs_expand_and_anchor_relative_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    home_dir = tmp_path / "home"
    working_dir = tmp_path / "work"
    home_dir.mkdir()
    working_dir.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setenv("HOME", home_dir.as_posix())
    config_path = _write_config(
        tmp_path,
        f"""
[PROJECT]
WORKING_DIR = "{working_dir.as_posix()}"

[SECURITY]
ADDITIONAL_ALLOWED_DIRS = ["~/shared", "project-data", "project-data"]
""",
    )

    config = Config(config_file=config_path)

    assert config.ADDITIONAL_ALLOWED_DIRS == (
        (home_dir / "shared").resolve(),
        (working_dir / "project-data").resolve(),
    )


def test_user_additional_allowed_dirs_override_project_security(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.chdir(project_dir)
    (user_config_dir / "config.toml").write_text(
        '[SECURITY]\nADDITIONAL_ALLOWED_DIRS = ["user-data"]',
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        '[SECURITY]\nADDITIONAL_ALLOWED_DIRS = ["project-data"]',
        encoding="utf-8",
    )

    config = Config()

    assert config.ADDITIONAL_ALLOWED_DIRS == (
        (project_dir / "user-data").resolve(),
    )
