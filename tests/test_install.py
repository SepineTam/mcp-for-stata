"""Tests for `stata-mcp install` parsing and handler decision tree."""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock

import pytest

from stata_mcp.cli._handlers import _parse_json_index, handle_install
from stata_mcp.cli._parsers import add_install_parser


# ---------- Parser tests ----------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_install_parser(subparsers)
    return parser


def test_install_client_default_is_none():
    parser = _build_parser()
    args = parser.parse_args(["install"])
    assert args.client is None
    assert args.all is False
    assert args.json_file is None
    assert args.json_index is None


def test_install_accepts_json_index_flag():
    parser = _build_parser()
    args = parser.parse_args(
        ["install", "--json-file", "/tmp/x.json", "--json-index", "mcp.servers"]
    )
    assert args.json_file == "/tmp/x.json"
    assert args.json_index == "mcp.servers"


def test_install_rejects_invalid_client():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["install", "-c", "nonexistent"])


# ---------- _parse_json_index ----------

def test_parse_json_index_single_segment():
    assert _parse_json_index("mcpServers") == ["mcpServers"]


def test_parse_json_index_dotted():
    assert _parse_json_index("mcp.servers") == ["mcp", "servers"]


def test_parse_json_index_skips_empty_segments():
    assert _parse_json_index("a..b") == ["a", "b"]


# ---------- handle_install decision tree ----------

def _make_args(**overrides) -> argparse.Namespace:
    base = dict(client=None, all=False, json_file=None, json_index=None)
    base.update(overrides)
    return argparse.Namespace(**base)


@pytest.fixture
def installer_stub(monkeypatch):
    """Stub Installer's side-effecting methods while keeping class attributes."""
    from stata_mcp.utils.installer import Installer as RealInstaller

    install_all = MagicMock()
    install = MagicMock()
    install_to_json_config = MagicMock()

    monkeypatch.setattr(RealInstaller, "install_all", install_all)
    monkeypatch.setattr(RealInstaller, "install", install)
    monkeypatch.setattr(RealInstaller, "install_to_json_config", install_to_json_config)
    # Skip heavy Stata CLI lookup during construction
    monkeypatch.setattr(RealInstaller, "_post_init", lambda self: None)

    stub = MagicMock()
    stub.install_all = install_all
    stub.install = install
    stub.install_to_json_config = install_to_json_config
    stub.CLIENT_DEFAULT_KEY = RealInstaller.CLIENT_DEFAULT_KEY
    return stub


def test_bare_install_routes_to_install_all(installer_stub):
    args = _make_args()
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install_all.assert_called_once()
    installer_stub.install.assert_not_called()
    installer_stub.install_to_json_config.assert_not_called()


def test_all_flag_wins_over_other_args(installer_stub):
    args = _make_args(all=True, client="openclaw", json_file="/tmp/x.json")
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install_all.assert_called_once()
    installer_stub.install.assert_not_called()
    installer_stub.install_to_json_config.assert_not_called()


def test_json_index_without_json_file_errors():
    args = _make_args(json_index="mcp.servers")
    rc = handle_install(args)
    assert rc == 1


def test_opencode_with_json_file_warns_and_uses_default(installer_stub, capsys):
    args = _make_args(client="opencode", json_file="/tmp/x.json")
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install.assert_called_once_with("opencode")
    installer_stub.install_to_json_config.assert_not_called()
    out = capsys.readouterr().out
    assert "warning" in out.lower()
    assert "opencode" in out


def test_codex_with_json_index_warns_and_uses_default(installer_stub, capsys):
    args = _make_args(client="codex", json_file="/tmp/x.toml", json_index="abc")
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install.assert_called_once_with("codex")
    installer_stub.install_to_json_config.assert_not_called()
    assert "warning" in capsys.readouterr().out.lower()


def test_openclaw_with_json_file_uses_nested_key(installer_stub):
    args = _make_args(client="openclaw", json_file="/tmp/o.json")
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install_to_json_config.assert_called_once_with(
        "/tmp/o.json", key=["mcp", "servers"]
    )


def test_client_with_json_index_overrides_default_key(installer_stub):
    args = _make_args(
        client="claude", json_file="/tmp/c.json", json_index="custom.path"
    )
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install_to_json_config.assert_called_once_with(
        "/tmp/c.json", key=["custom", "path"]
    )


def test_only_json_file_uses_default_mcp_servers(installer_stub):
    args = _make_args(json_file="/tmp/x.json")
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install_to_json_config.assert_called_once_with(
        "/tmp/x.json", key="mcpServers"
    )


def test_only_json_file_with_index_uses_parsed_key(installer_stub):
    args = _make_args(json_file="/tmp/x.json", json_index="abc")
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install_to_json_config.assert_called_once_with(
        "/tmp/x.json", key=["abc"]
    )


def test_client_only_routes_to_install(installer_stub):
    args = _make_args(client="claude")
    rc = handle_install(args)
    assert rc == 0
    installer_stub.install.assert_called_once_with("claude")
    installer_stub.install_to_json_config.assert_not_called()


def test_client_default_key_table_excludes_opencode_and_codex():
    """opencode/codex are intentionally not in CLIENT_DEFAULT_KEY."""
    from stata_mcp.utils.installer import Installer

    assert "opencode" not in Installer.CLIENT_DEFAULT_KEY
    assert "codex" not in Installer.CLIENT_DEFAULT_KEY
    assert Installer.CLIENT_DEFAULT_KEY["openclaw"] == ["mcp", "servers"]
    assert Installer.CLIENT_DEFAULT_KEY["claude"] == "mcpServers"
