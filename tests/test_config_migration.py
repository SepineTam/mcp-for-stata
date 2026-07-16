"""Tests for automatic data-info table-name migration."""

from __future__ import annotations

import logging
import stat
from pathlib import Path

import pytest

from stata_mcp.config import Config


def _write_config(tmp_path: Path, content: str) -> Path:
    config_file = tmp_path / "config.toml"
    config_file.write_bytes(content.encode("utf-8"))
    return config_file


def test_legacy_data_info_header_is_renamed_without_reformatting(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    original_content = (
        "# Keep this comment and formatting.\r\n"
        "[data_info] # legacy table\r\n"
        "is_cache = false\r\n"
        "metrics = [\"obs\", \"med\"]\r\n"
    )
    config_file = _write_config(tmp_path, original_content)
    config_file.chmod(0o640)

    with caplog.at_level(logging.INFO):
        config = Config(config_file=config_file)

    migrated_content = config_file.read_bytes().decode("utf-8")
    assert migrated_content == original_content.replace(
        "[data_info]",
        "[DATA_INFO]",
        1,
    )
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o640
    assert config.get_data_info_config("api").is_cache is False
    assert config.get_data_info_config("api").metrics == ("obs", "med")
    assert "Migrated legacy [data_info] to [DATA_INFO]" in caplog.text


def test_quoted_legacy_header_is_renamed(tmp_path: Path) -> None:
    config_file = _write_config(
        tmp_path,
        '["data_info"]\nis_cache = false\n',
    )

    Config(config_file=config_file)

    assert '["DATA_INFO"]' in config_file.read_text(encoding="utf-8")


def test_existing_uppercase_and_lowercase_sections_are_not_overwritten(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    original_content = """
[data_info]
is_cache = false
hash_length = 8

[DATA_INFO]
hash_length = 16
""".strip()
    config_file = _write_config(tmp_path, original_content)

    with caplog.at_level(logging.WARNING):
        config = Config(config_file=config_file)

    assert config_file.read_text(encoding="utf-8") == original_content
    assert config.get_data_info_config("api").is_cache is False
    assert config.get_data_info_config("api").hash_length == 16
    assert "both [data_info] and [DATA_INFO] exist" in caplog.text


def test_permission_failure_is_logged_and_legacy_config_still_works(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        "[data_info]\nis_cache = false\n",
    )

    def deny_write(config_file: Path, content: str) -> None:
        raise PermissionError("read-only config")

    monkeypatch.setattr(Config, "_replace_config_text", staticmethod(deny_write))

    with caplog.at_level(logging.WARNING):
        config = Config(config_file=config_file)

    assert "[data_info]" in config_file.read_text(encoding="utf-8")
    assert config.get_data_info_config("api").is_cache is False
    assert "permission denied" in caplog.text
    assert "read-only config" in caplog.text


def test_other_filesystem_failure_is_logged_and_does_not_stop_loading(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        "[data_info]\ndecimal_places = 2\n",
    )

    def fail_write(config_file: Path, content: str) -> None:
        raise OSError("read-only file system")

    monkeypatch.setattr(Config, "_replace_config_text", staticmethod(fail_write))

    with caplog.at_level(logging.WARNING):
        config = Config(config_file=config_file)

    assert config.get_data_info_config("api").decimal_places == 2
    assert "filesystem error" in caplog.text
    assert "read-only file system" in caplog.text


def test_unexpected_write_failure_is_logged_and_does_not_stop_loading(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        "[data_info]\nhash_length = 8\n",
    )

    def fail_write(config_file: Path, content: str) -> None:
        raise RuntimeError("unexpected storage adapter failure")

    monkeypatch.setattr(Config, "_replace_config_text", staticmethod(fail_write))

    with caplog.at_level(logging.WARNING):
        config = Config(config_file=config_file)

    assert config.get_data_info_config("api").hash_length == 8
    assert "unexpected error RuntimeError" in caplog.text
    assert "unexpected storage adapter failure" in caplog.text


def test_inline_legacy_table_logs_safe_fallback(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    original_content = "data_info = { is_cache = false }\n"
    config_file = _write_config(tmp_path, original_content)

    with caplog.at_level(logging.WARNING):
        config = Config(config_file=config_file)

    assert config_file.read_text(encoding="utf-8") == original_content
    assert config.get_data_info_config("api").is_cache is False
    assert "not represented by a standalone TOML table header" in caplog.text


def test_uppercase_only_config_does_not_attempt_a_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        "[DATA_INFO]\nis_cache = false\n",
    )

    def unexpected_write(config_file: Path, content: str) -> None:
        raise AssertionError("uppercase config must not be rewritten")

    monkeypatch.setattr(
        Config,
        "_replace_config_text",
        staticmethod(unexpected_write),
    )

    config = Config(config_file=config_file)

    assert config.get_data_info_config("api").is_cache is False
