"""Tests for help refresh behavior exposed through API and CLI interfaces."""

import importlib
from argparse import Namespace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.cli._handlers import handle_tool
from stata_mcp.cli._parsers import add_tool_parser, create_root_parser

stata_help_api = importlib.import_module("stata_mcp.api.stata_help")


def test_api_forwards_replace_to_help_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    help_reader = Mock()
    runtime = SimpleNamespace(
        stata_cli="stata",
        tmp_base_path="/tmp/project",
        config=SimpleNamespace(HELP_CACHE_DIR="/tmp/cache"),
    )
    monkeypatch.setattr(stata_help_api, "create_runtime_context", lambda **kwargs: runtime)
    monkeypatch.setattr(stata_help_api, "StataHelp", lambda **kwargs: help_reader)

    stata_help_api.stata_help("regress", replace=True)

    help_reader.help.assert_called_once_with("regress", replace=True)


def test_cli_help_parser_exposes_replace_flag() -> None:
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command")
    add_tool_parser(subparsers)

    default_args = parser.parse_args(["tool", "help", "regress"])
    replace_args = parser.parse_args(["tool", "help", "regress", "--replace", "true"])

    assert default_args.replace is False
    assert replace_args.replace is True


def test_cli_help_handler_forwards_replace(monkeypatch: pytest.MonkeyPatch) -> None:
    stata_help = Mock(return_value="help content")
    fake_api = SimpleNamespace(
        ado_package_install=Mock(),
        get_data_info=Mock(),
        read_log=Mock(),
        stata_do=Mock(),
        stata_help=stata_help,
    )
    monkeypatch.setitem(__import__("sys").modules, "stata_mcp.api", fake_api)
    args = Namespace(
        tool_action="help",
        stata_command="regress",
        replace=True,
    )

    assert handle_tool(args) == 0
    stata_help.assert_called_once_with(cmd="regress", replace=True)
