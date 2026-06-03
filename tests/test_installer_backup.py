"""Tests for installer config backup behavior."""

from __future__ import annotations

from datetime import datetime as real_datetime

import pytest

import stata_mcp.utils.installer.installer as installer_module
from stata_mcp.utils.installer import Installer


class FixedDatetime(real_datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 5, 18, 14, 30, tzinfo=tz)


@pytest.fixture(autouse=True)
def fixed_backup_timestamp(monkeypatch):
    monkeypatch.setattr(installer_module, "datetime", FixedDatetime)


@pytest.fixture
def installer():
    return Installer(is_env=False)


def test_existing_json_file_triggers_backup(installer, tmp_path, capsys):
    config_path = tmp_path / "settings.json"
    original = b'{"mcpServers":{"other":{"command":"old"}}}\n'
    config_path.write_bytes(original)

    installer.install_to_json_config(config_path)

    backup_path = tmp_path / "settings.backup-202605181430.json"
    assert backup_path.read_bytes() == original
    assert '"stata-mcp"' in config_path.read_text(encoding="utf-8")
    assert (
        f"[BACKUP]\tOriginal config backed up to: {backup_path}"
        in capsys.readouterr().out
    )


def test_missing_json_file_skips_backup(installer, tmp_path):
    config_path = tmp_path / "settings.json"

    installer.install_to_json_config(config_path)

    assert config_path.exists()
    assert not list(tmp_path.glob("*.backup-*.json"))


def test_backup_failure_aborts_without_writing(installer, tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "settings.json"
    original = b'{"mcpServers":{}}\n'
    config_path.write_bytes(original)

    def fail_copy(_source, _destination):
        raise OSError("disk full")

    monkeypatch.setattr(installer_module.shutil, "copy2", fail_copy)

    with pytest.raises(SystemExit) as exc_info:
        installer.install_to_json_config(config_path)

    assert exc_info.value.code == 1
    assert config_path.read_bytes() == original
    assert "[ERROR]\tFailed to backup" in capsys.readouterr().out


def test_same_minute_backup_is_idempotent(installer, tmp_path):
    config_path = tmp_path / "settings.json"
    original = b'{"mcpServers":{"other":{"command":"old"}}}\n'
    config_path.write_bytes(original)
    installer.install_to_json_config(config_path)

    config_path.write_bytes(original)
    installer.install_to_json_config(config_path)

    backups = list(tmp_path.glob("settings.backup-*.json"))
    assert backups == [tmp_path / "settings.backup-202605181430.json"]
    assert backups[0].read_bytes() == original


def test_toml_config_backup_before_write(installer, tmp_path):
    config_path = tmp_path / "config.toml"
    original = b'[other]\nvalue = "x"\n'
    config_path.write_bytes(original)

    installer.install_to_toml_config(config_path, key="mcp_servers")

    backup_path = tmp_path / "config.backup-202605181430.toml"
    assert backup_path.read_bytes() == original
    assert "[mcp_servers.stata-mcp]" in config_path.read_text(encoding="utf-8")


def test_yaml_config_backup_before_write(installer, tmp_path):
    config_path = tmp_path / "config.yaml"
    original = b"other: true\n"
    config_path.write_bytes(original)

    installer.install_to_yaml_config(config_path, key="mcp_servers")

    backup_path = tmp_path / "config.backup-202605181430.yaml"
    updated = config_path.read_text(encoding="utf-8")
    assert backup_path.read_bytes() == original
    assert "mcp_servers:" in updated
    assert "stata-mcp:" in updated


def test_hidden_json_file_uses_expected_backup_name(installer, tmp_path):
    config_path = tmp_path / ".claude.json"
    original = b'{"mcpServers":{"stata-mcp":{"command":"uvx"}}}'
    config_path.write_bytes(original)

    with pytest.raises(SystemExit) as exc_info:
        installer.install_to_json_config(config_path)

    assert exc_info.value.code == 0
    backup_path = tmp_path / ".claude.backup-202605181430.json"
    assert backup_path.read_bytes() == original
    assert config_path.read_bytes() == original


def test_invalid_json_is_backed_up_before_overwrite_prompt(
    installer, tmp_path, monkeypatch
):
    config_path = tmp_path / "settings.json"
    original = b"{not valid json"
    config_path.write_bytes(original)
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")

    installer.install_to_json_config(config_path)

    backup_path = tmp_path / "settings.backup-202605181430.json"
    assert backup_path.read_bytes() == original
    assert '"stata-mcp"' in config_path.read_text(encoding="utf-8")
