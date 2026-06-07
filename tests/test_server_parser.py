"""Tests for server command parsing behavior."""

from __future__ import annotations

import pytest

from stata_mcp.cli._parsers import add_server_parser, create_root_parser


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
