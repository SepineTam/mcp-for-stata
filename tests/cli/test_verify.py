"""Tests for the `verify` CLI subcommand and the Installer read-only helpers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from stata_mcp.cli._handlers import handle_verify
from stata_mcp.cli._parsers import add_verify_parser
from stata_mcp.utils.installer import Installer
from stata_mcp.utils.installer import (
    Verifier,
    VerifyOutcome,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _make_verifier() -> Verifier:
    return Verifier(sys_os="darwin")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_verify_parser(subparsers)
    return parser


def _make_args(**overrides) -> argparse.Namespace:
    base = dict(client=None, file=None, index=None, key="stata-mcp")
    base.update(overrides)
    return argparse.Namespace(**base)


class TestFindConfigPath:
    @pytest.mark.parametrize(
        "client,expected_suffix",
        [
            ("cc", ".claude.json"),
            ("claude-code", ".claude.json"),
            ("gemini", ".gemini/settings.json"),
            ("cursor", ".cursor/mcp.json"),
            ("opencode", ".config/opencode/opencode.json"),
            ("codex", ".codex/config.toml"),
            ("openclaw", ".openclaw/openclaw.json"),
            ("hermes", ".hermes/config.yaml"),
            ("hermes-agent", ".hermes/config.yaml"),
        ],
    )
    def test_returns_expected_path(
        self, monkeypatch, tmp_path, client, expected_suffix
    ):
        monkeypatch.setenv("HOME", tmp_path.as_posix())
        path = Installer(sys_os="darwin").find_config_path(client)
        assert str(path).endswith(expected_suffix)

    def test_claude_darwin_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOME", tmp_path.as_posix())
        path = Installer(sys_os="darwin").find_config_path("claude")
        assert "Library/Application Support/Claude/claude_desktop_config.json" in str(path)

    def test_claude_linux_unsupported(self):
        with pytest.raises(ValueError):
            Installer(sys_os="linux").find_config_path("claude")

    def test_claude_windows_uses_appdata(self, monkeypatch, tmp_path):
        appdata = tmp_path / "AppData/Roaming"
        appdata.mkdir(parents=True)
        monkeypatch.setenv("APPDATA", str(appdata))
        path = Installer(sys_os="windows").find_config_path("claude")
        assert str(path).replace("\\", "/").endswith("Claude/claude_desktop_config.json")

    def test_cline_darwin_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOME", tmp_path.as_posix())
        path = Installer(sys_os="darwin").find_config_path("cline")
        assert "saoudrizwan.claude-dev/settings/cline_mcp_settings.json" in str(path)

    def test_unknown_client_raises(self):
        with pytest.raises(ValueError, match="unknown client"):
            Installer(sys_os="darwin").find_config_path("vscode")


class TestFindDefaultIndex:
    @pytest.mark.parametrize(
        "client,expected",
        [
            ("claude", "mcpServers"),
            ("cc", "mcpServers"),
            ("claude-code", "mcpServers"),
            ("gemini", "mcpServers"),
            ("cursor", "mcpServers"),
            ("cline", "mcpServers"),
            ("opencode", "mcp"),
            ("codex", "mcp_servers"),
            ("hermes", "mcp_servers"),
            ("hermes-agent", "mcp_servers"),
            ("openclaw", ["mcp", "servers"]),
        ],
    )
    def test_returns_expected_key(self, client, expected):
        result = Installer(sys_os="darwin").find_default_index(client)
        assert result == expected

    def test_unknown_client_raises(self):
        with pytest.raises(ValueError, match="unknown client"):
            Installer(sys_os="darwin").find_default_index("vscode")


class TestVerifyFileSuccess:
    def test_valid_json_with_stata_mcp_entry(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": "uvx", "args": ["stata-mcp"]}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.VERIFIED
        assert result.exit_code == 0
        assert result.location == path.as_posix()

    def test_valid_toml_with_stata_mcp_entry(self, tmp_path):
        path = tmp_path / "config.toml"
        path.write_text(
            '[mcp_servers.stata-mcp]\n'
            'command = "uvx"\n'
            'args = ["stata-mcp"]\n',
            encoding="utf-8",
        )
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.VERIFIED
        assert result.exit_code == 0

    def test_custom_key(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"my-alias": {"command": "uvx"}},
        })
        result = _make_verifier().verify_file(path, key="my-alias")
        assert result.outcome == VerifyOutcome.VERIFIED
        assert result.exit_code == 0

    def test_index_navigates_nested_dict(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcp": {"servers": {"stata-mcp": {"command": "uvx"}}},
        })
        result = _make_verifier().verify_file(path, index="mcp.servers")
        assert result.outcome == VerifyOutcome.VERIFIED
        assert result.exit_code == 0
        assert result.location is not None
        assert "mcp.servers" in result.location
        assert path.as_posix() in result.location


class TestVerifyFileFailure:
    def test_empty_mcp_servers_dict(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {"mcpServers": {}})
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 2
        assert result.reason is not None
        assert "is empty" in result.reason

    def test_missing_stata_mcp_entry(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"other": {"command": "uvx"}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 2
        assert result.reason is not None
        assert "entry 'stata-mcp' not found" in result.reason

    def test_malformed_json(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("{not valid json", encoding="utf-8")
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 3
        assert result.reason is not None
        assert "failed to parse" in result.reason

    def test_missing_command_field(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"args": ["stata-mcp"]}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 4
        assert result.reason is not None
        assert "missing required field 'command'" in result.reason

    def test_command_is_list(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": ["uvx", "stata-mcp"]}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 4
        assert result.reason is not None
        assert "must be a string" in result.reason

    def test_command_is_int(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": 42}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 4
        assert result.reason is not None
        assert "must be a string" in result.reason

    def test_toml_missing_command(self, tmp_path):
        path = tmp_path / "config.toml"
        path.write_text(
            '[mcp_servers.stata-mcp]\n'
            'args = ["stata-mcp"]\n',
            encoding="utf-8",
        )
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 4
        assert result.reason is not None
        assert "missing required field 'command'" in result.reason

    def test_unsupported_yaml_extension(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("stata-mcp: {command: uvx}", encoding="utf-8")
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 1
        assert result.reason is not None
        assert "unsupported file extension" in result.reason

    def test_path_is_directory(self, tmp_path):
        result = _make_verifier().verify_file(tmp_path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 1
        assert result.reason is not None
        assert "is a directory" in result.reason

    def test_path_does_not_exist(self, tmp_path):
        missing = tmp_path / "nope.json"
        result = _make_verifier().verify_file(missing)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 1
        assert result.reason is not None
        assert "file not found" in result.reason

    def test_permission_denied_yields_cannot_read(self, tmp_path, monkeypatch):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": "uvx"}},
        })

        def _raise_oserror(*_args, **_kwargs):
            raise OSError(13, "Permission denied")  # noqa: ARG001

        monkeypatch.setattr(Verifier, "_load", _raise_oserror)
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 1
        assert result.reason is not None
        assert "cannot read file" in result.reason

    def test_index_missing_intermediate_key(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "other": {"stata-mcp": {"command": "uvx"}},
        })
        result = _make_verifier().verify_file(path, index="mcp.servers")
        assert result.outcome == VerifyOutcome.FAILED
        assert result.exit_code == 2


class TestVerifyFileWarnings:
    @pytest.mark.parametrize("addr", ["127.0.0.1", "0.0.0.0"])
    def test_ip_address_in_command_warns(self, tmp_path, addr):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": f"uvx --host {addr}"}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.WARNING
        assert result.exit_code == 0
        assert result.warnings

    def test_localhost_lowercase_warns(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": "uvx localhost"}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.WARNING
        assert result.exit_code == 0
        assert result.warnings

    def test_localhost_mixed_case_warns(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": "uvx LocalHost"}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.WARNING
        assert result.exit_code == 0
        assert result.warnings

    @pytest.mark.parametrize("scheme", ["http://", "https://"])
    def test_command_starts_with_url_warns(self, tmp_path, scheme):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": f"{scheme}example.com"}},
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.WARNING
        assert result.exit_code == 0
        assert result.warnings

    def test_http_type_with_url_no_stdio_warning(self, tmp_path):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {
                "stata-mcp": {
                    "type": "http",
                    "url": "http://localhost:8000",
                    "command": "uvx 127.0.0.1",
                }
            },
        })
        result = _make_verifier().verify_file(path)
        assert result.outcome == VerifyOutcome.VERIFIED
        assert result.exit_code == 0
        assert result.warnings == []


class TestHandleVerify:
    def test_no_args_returns_5(self, capsys):
        rc = handle_verify(_make_args())
        captured = capsys.readouterr()
        assert rc == 5
        assert "must specify" in captured.err

    def test_client_with_file_conflict(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HOME", tmp_path.as_posix())
        rc = handle_verify(_make_args(client="codex", file=tmp_path / "x.json"))
        captured = capsys.readouterr()
        assert "-c takes precedence; -f is ignored" in captured.err
        assert rc == 1
        assert "file not found" in captured.out

    def test_client_with_index_conflict(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HOME", tmp_path.as_posix())
        rc = handle_verify(_make_args(client="codex", index="mcp.servers"))
        captured = capsys.readouterr()
        assert "-c takes precedence; --index is ignored" in captured.err
        assert rc == 1

    def test_invalid_client_rejected_by_argparse(self):
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["verify", "-c", "vscode"])
        assert exc_info.value.code == 5

    def test_successful_verify_prints_verified_line(self, tmp_path, capsys):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": "uvx"}},
        })
        rc = handle_verify(_make_args(file=path))
        captured = capsys.readouterr()
        assert rc == 0
        assert f"Verified: stata-mcp is installed at {path.as_posix()}." in captured.out

    def test_failed_verify_prints_failed_line(self, tmp_path, capsys):
        path = tmp_path / "missing.json"
        rc = handle_verify(_make_args(file=path))
        captured = capsys.readouterr()
        assert rc == 1
        assert "Failed:" in captured.out
        assert "file not found" in captured.out

    def test_warning_then_verified_line(self, tmp_path, capsys):
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": "uvx localhost"}},
        })
        rc = handle_verify(_make_args(file=path))
        captured = capsys.readouterr()
        assert rc == 0
        out_lines = [line for line in captured.out.splitlines() if line]
        assert out_lines[0].startswith("warning:")
        assert out_lines[-1].startswith("Verified:")

    def test_no_color_disables_ansi(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        path = _write_json(tmp_path / "config.json", {
            "mcpServers": {"stata-mcp": {"command": "uvx localhost"}},
        })
        rc = handle_verify(_make_args(file=path))
        captured = capsys.readouterr()
        assert rc == 0
        assert "\033[" not in captured.out

    def test_codex_client_routes_via_install_helper(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("HOME", tmp_path.as_posix())
        codex_path = tmp_path / ".codex" / "config.toml"
        codex_path.parent.mkdir(parents=True)
        codex_path.write_text(
            '[mcp_servers.stata-mcp]\ncommand = "uvx"\n',
            encoding="utf-8",
        )
        rc = handle_verify(_make_args(client="codex"))
        captured = capsys.readouterr()
        assert rc == 0
        assert "Verified: stata-mcp is installed at codex." in captured.out
