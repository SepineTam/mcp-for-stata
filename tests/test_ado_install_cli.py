"""Tests for explicit CLI acknowledgement of high-risk ado installation."""

from argparse import Namespace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.cli._handlers import handle_tool
from stata_mcp.cli._parsers import add_tool_parser, create_root_parser


def _build_parser():
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command")
    add_tool_parser(subparsers)
    return parser


def test_ado_install_cli_defaults_to_no_confirmation_or_replace() -> None:
    args = _build_parser().parse_args(["tool", "ado-install", "reghdfe"])

    assert args.yes is False
    assert args.is_replace is False


def test_ado_install_cli_accepts_explicit_confirmation() -> None:
    args = _build_parser().parse_args(
        ["tool", "ado-install", "reghdfe", "--yes", "--is-replace", "true"]
    )

    assert args.yes is True
    assert args.is_replace is True


def test_ado_install_cli_handler_forwards_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ado_package_install = Mock(return_value="Installation State: True")
    fake_api = SimpleNamespace(
        ado_package_install=ado_package_install,
        get_data_info=Mock(),
        read_log=Mock(),
        stata_do=Mock(),
        stata_help=Mock(),
    )
    monkeypatch.setitem(__import__("sys").modules, "stata_mcp.api", fake_api)
    args = Namespace(
        tool_action="ado-install",
        package_name="reghdfe",
        source="ssc",
        is_replace=False,
        package_source_from=None,
        yes=True,
    )

    assert handle_tool(args) == 0
    ado_package_install.assert_called_once_with(
        package="reghdfe",
        source="ssc",
        is_replace=False,
        package_source_from=None,
        confirm=True,
    )
