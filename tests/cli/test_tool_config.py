"""Tests for CLI tool configuration plumbing."""

from __future__ import annotations

import importlib
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.api import get_data_info as api_get_data_info
from stata_mcp.cli._handlers import handle_tool
from stata_mcp.cli._parsers import add_tool_parser, create_root_parser


def _tool_parser():
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command")
    add_tool_parser(subparsers)
    return parser


def test_data_info_heads_parser_distinguishes_omitted_and_explicit_values() -> None:
    parser = _tool_parser()

    omitted_args = parser.parse_args(["tool", "data-info", "sample.csv"])
    positive_args = parser.parse_args(
        ["tool", "data-info", "sample.csv", "--heads", "8"]
    )
    disabled_args = parser.parse_args(
        ["tool", "data-info", "sample.csv", "--heads", "0"]
    )
    tail_args = parser.parse_args(
        ["tool", "data-info", "sample.csv", "--heads", "-3"]
    )

    assert omitted_args.heads is None
    assert positive_args.heads == 8
    assert disabled_args.heads == 0
    assert tail_args.heads == -3


def test_data_info_handler_forwards_cli_context_and_omitted_head(
    monkeypatch,
) -> None:
    get_data_info = Mock(return_value="data info")
    fake_api = SimpleNamespace(
        ado_package_install=Mock(),
        get_data_info=get_data_info,
        read_log=Mock(),
        stata_do=Mock(),
        stata_help=Mock(),
    )
    monkeypatch.setitem(sys.modules, "stata_mcp.api", fake_api)
    args = Namespace(
        tool_action="data-info",
        data_path="sample.csv",
        vars_list=None,
        encoding="utf-8",
        heads=None,
    )

    assert handle_tool(args) == 0
    get_data_info.assert_called_once_with(
        data_path="sample.csv",
        vars_list=None,
        encoding="utf-8",
        head=None,
        tool_context="cli",
    )


def test_data_info_handler_forwards_explicit_heads(monkeypatch) -> None:
    get_data_info = Mock(return_value="data info")
    fake_api = SimpleNamespace(
        ado_package_install=Mock(),
        get_data_info=get_data_info,
        read_log=Mock(),
        stata_do=Mock(),
        stata_help=Mock(),
    )
    monkeypatch.setitem(sys.modules, "stata_mcp.api", fake_api)
    args = Namespace(
        tool_action="data-info",
        data_path="sample.csv",
        vars_list=["price"],
        encoding="utf-8",
        heads=0,
    )

    assert handle_tool(args) == 0
    assert get_data_info.call_args.kwargs["head"] == 0
    assert get_data_info.call_args.kwargs["tool_context"] == "cli"


@pytest.mark.parametrize(
    ("tool_config", "expected_heads"),
    [
        ("", 5),
        ("\n[data_info]\nheads = 2", 2),
        (
            "\n[data_info]\nheads = 2\n\n"
            "[CLI.TOOLS.DATA_INFO]\nheads = 7",
            7,
        ),
    ],
)
def test_cli_api_resolves_heads_from_context_then_generic_then_default(
    monkeypatch,
    tmp_path: Path,
    tool_config: str,
    expected_heads: int,
) -> None:
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    data_path = working_dir / "sample.csv"
    data_path.write_text("x\n1\n", encoding="utf-8")
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'[PROJECT]\nWORKING_DIR = "{working_dir.as_posix()}"{tool_config}',
        encoding="utf-8",
    )
    calls = []

    class _FakeDataInfo:
        def __init__(self, *args, **kwargs):
            calls.append(kwargs)

        @property
        def info(self):
            return {"ok": True}

    get_data_info_module = importlib.import_module("stata_mcp.api.get_data_info")
    monkeypatch.setattr(
        get_data_info_module,
        "get_data_handler",
        lambda extension: _FakeDataInfo,
    )

    api_get_data_info(
        data_path.as_posix(),
        config_file=config_path,
        tool_context="cli",
    )

    assert calls[-1]["head"] == expected_heads
