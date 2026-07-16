"""Tests for automatic data-info table-name migration."""

from __future__ import annotations

import logging
import os
import stat
import sys
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
        'metrics = ["obs", "med"]\r\n'
    )
    config_file = _write_config(tmp_path, original_content)
    config_file.chmod(0o640)
    original_inode = config_file.stat().st_ino

    with caplog.at_level(logging.INFO):
        config = Config(config_file=config_file)

    migrated_content = config_file.read_bytes().decode("utf-8")
    assert migrated_content == original_content.replace(
        "[data_info]",
        "[DATA_INFO]",
        1,
    )
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o640
    assert config_file.stat().st_ino == original_inode
    assert config.get_data_info_config("api").is_cache is False
    assert config.get_data_info_config("api").metrics == ("obs", "med")
    assert "Migrated legacy [data_info] to [DATA_INFO]" in caplog.text


@pytest.mark.skipif(not hasattr(os, "chown"), reason="Ownership is not POSIX metadata")
def test_legacy_header_migration_reapplies_owner_and_group(
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        "[data_info]\nis_cache = false\n",
    )
    current_group_id = config_file.stat().st_gid
    target_group_id = next(
        (group_id for group_id in os.getgroups() if group_id != current_group_id),
        None,
    )
    if target_group_id is None:
        pytest.skip("No secondary group is available for an ownership test")
    try:
        os.chown(config_file, -1, target_group_id)
    except OSError as error:
        pytest.skip(f"Could not assign a secondary test group: {error}")
    original_stat = config_file.stat()

    Config(config_file=config_file)

    migrated_stat = config_file.stat()
    assert migrated_stat.st_ino == original_stat.st_ino
    assert migrated_stat.st_uid == original_stat.st_uid
    assert migrated_stat.st_gid == original_stat.st_gid


@pytest.mark.skipif(
    not all(hasattr(os, name) for name in ("setxattr", "getxattr")),
    reason="Extended attributes are not supported",
)
def test_legacy_header_migration_preserves_extended_attributes(
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        "[data_info]\nis_cache = false\n",
    )
    attribute_name = (
        "com.stata_mcp.test"
        if sys.platform == "darwin"
        else "user.stata_mcp_test"
    )
    try:
        os.setxattr(config_file, attribute_name, b"preserve-me")
    except OSError as error:
        pytest.skip(f"Filesystem does not support test extended attributes: {error}")

    Config(config_file=config_file)

    assert os.getxattr(config_file, attribute_name) == b"preserve-me"


def test_quoted_legacy_header_is_renamed(tmp_path: Path) -> None:
    config_file = _write_config(
        tmp_path,
        '["data_info"]\nis_cache = false\n',
    )

    Config(config_file=config_file)

    assert '["DATA_INFO"]' in config_file.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("legacy_header", "canonical_header"),
    [
        ("[ data_info ]", "[ DATA_INFO ]"),
        ("[ 'data_info' ] # keep", "[ 'DATA_INFO' ] # keep"),
    ],
)
def test_legacy_header_with_inner_whitespace_is_renamed(
    legacy_header: str,
    canonical_header: str,
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        f"{legacy_header}\nis_cache = false\n",
    )

    config = Config(config_file=config_file)

    assert canonical_header in config_file.read_text(encoding="utf-8")
    assert config.get_data_info_config("api").is_cache is False


@pytest.mark.parametrize("delimiter", ['"""', "'''"])
def test_legacy_header_migration_ignores_multiline_string_content(
    delimiter: str,
    tmp_path: Path,
) -> None:
    original_content = (
        f"note = {delimiter}\n"
        "[data_info]\n"
        "This is documentation, not a table header.\n"
        f"{delimiter}\n"
        "\n"
        "[data_info]\n"
        "is_cache = false\n"
    )
    config_file = _write_config(tmp_path, original_content)

    config = Config(config_file=config_file)

    migrated_content = config_file.read_text(encoding="utf-8")
    assert migrated_content == original_content.replace(
        "\n[data_info]\nis_cache",
        "\n[DATA_INFO]\nis_cache",
        1,
    )
    assert config.get_data_info_config("api").is_cache is False


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

    def deny_write(config_file: Path, content: str, **kwargs) -> None:
        raise PermissionError("read-only config")

    monkeypatch.setattr(Config, "_replace_config_text", staticmethod(deny_write))

    with caplog.at_level(logging.WARNING):
        config = Config(config_file=config_file)

    assert "[data_info]" in config_file.read_text(encoding="utf-8")
    assert config.get_data_info_config("api").is_cache is False
    assert "permission denied" in caplog.text
    assert "read-only config" in caplog.text


def test_concurrent_config_change_is_not_overwritten(
    tmp_path: Path,
) -> None:
    original_content = "[data_info]\nis_cache = false\n"
    config_file = _write_config(tmp_path, original_content)
    external_content = original_content + "# edited by another process\n"
    config_file.write_text(external_content, encoding="utf-8")

    with pytest.raises(OSError, match="changed while migration"):
        Config._replace_config_text(
            config_file,
            original_content.replace("[data_info]", "[DATA_INFO]"),
            expected_content=original_content,
        )

    assert config_file.read_text(encoding="utf-8") == external_content


def test_fsync_failure_rolls_back_in_place_and_keeps_original(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    original_content = "[data_info]\nis_cache = false\n"
    config_file = _write_config(tmp_path, original_content)

    def fail_fsync(file_descriptor: int) -> None:
        raise OSError("disk flush failed")

    monkeypatch.setattr("stata_mcp.config.os.fsync", fail_fsync)

    with caplog.at_level(logging.WARNING):
        config = Config(config_file=config_file)

    assert config_file.read_text(encoding="utf-8") == original_content
    assert config.get_data_info_config("api").is_cache is False
    assert "filesystem error" in caplog.text
    assert "disk flush failed" in caplog.text
    assert list(tmp_path.glob(".config.toml.*.tmp")) == []


def test_other_filesystem_failure_is_logged_and_does_not_stop_loading(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_file = _write_config(
        tmp_path,
        "[data_info]\ndecimal_places = 2\n",
    )

    def fail_write(config_file: Path, content: str, **kwargs) -> None:
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

    def fail_write(config_file: Path, content: str, **kwargs) -> None:
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
