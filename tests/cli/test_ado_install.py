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


@pytest.mark.parametrize("flag", ["-y", "--yes"])
def test_ado_install_cli_accepts_confirmation_skip_flag(flag: str) -> None:
    args = _build_parser().parse_args(
        ["tool", "ado-install", "reghdfe", flag, "--is-replace", "true"]
    )

    assert args.yes is True
    assert args.is_replace is True


def test_ado_install_cli_handler_skips_prompt_with_yes(
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
    prompt = Mock()
    monkeypatch.setattr("builtins.input", prompt)
    args = Namespace(
        tool_action="ado-install",
        package_name="reghdfe",
        source="ssc",
        is_replace=False,
        package_source_from=None,
        yes=True,
    )

    assert handle_tool(args) == 0
    prompt.assert_not_called()
    ado_package_install.assert_called_once_with(
        package="reghdfe",
        source="ssc",
        is_replace=False,
        package_source_from=None,
    )


@pytest.mark.parametrize("response", ["y", "Y", "yes", " YES "])
def test_ado_install_cli_prompts_and_installs_after_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    response: str,
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
    monkeypatch.setattr("builtins.input", lambda prompt: response)
    args = Namespace(
        tool_action="ado-install",
        package_name="custompkg",
        source="net",
        is_replace=True,
        package_source_from="https://example.com/stata",
        yes=False,
    )

    assert handle_tool(args) == 0
    ado_package_install.assert_called_once_with(
        package="custompkg",
        source="net",
        is_replace=True,
        package_source_from="https://example.com/stata",
    )


@pytest.mark.parametrize("response", ["", "n", "no", "anything"])
def test_ado_install_cli_cancels_without_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    response: str,
) -> None:
    ado_package_install = Mock()
    fake_api = SimpleNamespace(
        ado_package_install=ado_package_install,
        get_data_info=Mock(),
        read_log=Mock(),
        stata_do=Mock(),
        stata_help=Mock(),
    )
    monkeypatch.setitem(__import__("sys").modules, "stata_mcp.api", fake_api)
    monkeypatch.setattr("builtins.input", lambda prompt: response)
    args = Namespace(
        tool_action="ado-install",
        package_name="reghdfe",
        source="ssc",
        is_replace=False,
        package_source_from=None,
        yes=False,
    )

    assert handle_tool(args) == 1
    ado_package_install.assert_not_called()


@pytest.mark.parametrize("error", [EOFError(), KeyboardInterrupt()])
def test_ado_install_cli_cancels_when_prompt_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    error: BaseException,
) -> None:
    ado_package_install = Mock()
    fake_api = SimpleNamespace(
        ado_package_install=ado_package_install,
        get_data_info=Mock(),
        read_log=Mock(),
        stata_do=Mock(),
        stata_help=Mock(),
    )
    monkeypatch.setitem(__import__("sys").modules, "stata_mcp.api", fake_api)

    def raise_prompt_error(prompt: str) -> str:
        raise error

    monkeypatch.setattr("builtins.input", raise_prompt_error)
    args = Namespace(
        tool_action="ado-install",
        package_name="reghdfe",
        source="ssc",
        is_replace=False,
        package_source_from=None,
        yes=False,
    )

    assert handle_tool(args) == 1
    ado_package_install.assert_not_called()
