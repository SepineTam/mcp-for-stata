"""Tests for server command parsing behavior."""

from __future__ import annotations

import pytest

from stata_mcp.cli._parsers import (
    add_install_parser,
    add_server_parser,
    add_tool_parser,
    create_root_parser,
)


def _build_parser():
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command")
    add_server_parser(subparsers)
    return parser


def test_root_transport_remains_available_without_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["-t", "http"])

    assert args.command is None
    assert args.transport == "http"


def test_server_defaults_to_all_profile():
    parser = _build_parser()
    args = parser.parse_args(["server"])

    assert args.command == "server"
    assert args.core_profile is False
    assert args.all_profile is False
    assert args.unsafe_profile is False
    assert args.transport == "stdio"


def test_server_core_profile_with_transport():
    parser = _build_parser()
    args = parser.parse_args(["server", "--core", "-t", "http"])

    assert args.command == "server"
    assert args.core_profile is True
    assert args.all_profile is False
    assert args.unsafe_profile is False
    assert args.transport == "http"


def test_server_unsafe_profile():
    parser = _build_parser()
    args = parser.parse_args(["server", "--unsafe"])

    assert args.unsafe_profile is True
    assert args.core_profile is False
    assert args.all_profile is False


def test_server_profile_flags_are_mutually_exclusive():
    parser = _build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["server", "--core", "--all"])

    with pytest.raises(SystemExit):
        parser.parse_args(["server", "--all", "--unsafe"])


def test_root_config_override_parses_before_subcommand(tmp_path):
    parser = _build_parser()
    config_file = tmp_path / "debug.toml"

    args = parser.parse_args(["-c", str(config_file), "server"])

    assert args.command == "server"
    assert args.config_file == config_file


def test_server_config_override_parses_after_subcommand(tmp_path):
    parser = _build_parser()
    config_file = tmp_path / "debug.toml"

    args = parser.parse_args(["server", "--config", str(config_file)])

    assert args.command == "server"
    assert args.config_file == config_file


def test_install_client_short_flag_is_not_config_override():
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command")
    add_install_parser(subparsers)

    args = parser.parse_args(["install", "-c", "codex"])

    assert args.command == "install"
    assert args.client == "codex"
    assert args.config_file is None


def test_nested_tool_config_override_parses_after_tool_action(tmp_path):
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command")
    add_tool_parser(subparsers)
    config_file = tmp_path / "debug.toml"

    args = parser.parse_args(["tool", "do", "analysis.do", "--config", str(config_file)])

    assert args.command == "tool"
    assert args.tool_action == "do"
    assert args.config_file == config_file
