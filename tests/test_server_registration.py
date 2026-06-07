"""Tests for tool registration and server handler profile behavior."""

from __future__ import annotations

import importlib
import logging
import sys
import asyncio
from argparse import Namespace
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def loaded_modules(monkeypatch: pytest.MonkeyPatch):
    """Load target modules with isolated dependency stubs."""
    monkeypatch.setitem(sys.modules, "tomli_w", SimpleNamespace(dump=lambda *args, **kwargs: None))
    monkeypatch.setitem(sys.modules, "pexpect", ModuleType("pexpect"))

    fastmcp_module = ModuleType("mcp.server.fastmcp")

    class _FastMCP:
        def __init__(self, *args, **kwargs) -> None:
            self._tools = []
            self._resources = []

        def tool(self, name: str, description: str):
            def _decorator(func):
                self._tools.append((name, func))
                return func

            return _decorator

        def resource(self, uri: str, name: str, description: str):
            def _decorator(func):
                self._resources.append((name, func))
                return func

            return _decorator

        def run(self, transport: str) -> None:
            return None

    class _Icon:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

    class _Context:
        pass

    fastmcp_module.FastMCP = _FastMCP
    fastmcp_module.Icon = _Icon
    fastmcp_module.Context = _Context

    mcp_module = ModuleType("mcp")
    mcp_server_module = ModuleType("mcp.server")
    mcp_server_module.fastmcp = fastmcp_module
    mcp_module.server = mcp_server_module

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", mcp_server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)

    monkeypatch.delitem(sys.modules, "stata_mcp.mcp_servers", raising=False)
    monkeypatch.delitem(sys.modules, "stata_mcp.cli._handlers", raising=False)

    mcp_servers = importlib.import_module("stata_mcp.mcp_servers")
    handlers = importlib.import_module("stata_mcp.cli._handlers")
    return mcp_servers, handlers


class _DummyServer:
    def __init__(self) -> None:
        self.tools: list[str] = []
        self.resources: list[str] = []

    def tool(self, name: str, description: str):
        def _decorator(func):
            self.tools.append(name)
            return func

        return _decorator

    def resource(self, uri: str, name: str, description: str):
        def _decorator(func):
            self.resources.append(name)
            return func

        return _decorator


def _set_registry(
    monkeypatch: pytest.MonkeyPatch,
    mcp_servers,
    *,
    unix: bool,
    enable_write: bool,
) -> None:
    registry = {
        "stata_do": {"description": "d", "func": lambda: None, "profiles": {"core", "all"}},
        "get_data_info": {"description": "d", "func": lambda: None, "profiles": {"core", "all"}},
        "help": {"description": "d", "func": lambda: None, "profiles": {"core", "all"}, "unix_only": True},
        "read_log": {"description": "d", "func": lambda: None, "profiles": {"all"}},
        "ado_package_install": {
            "description": "d",
            "func": lambda: None,
            "profiles": {"unsafe"},
        },
        "write_dofile": {
            "description": "d",
            "func": lambda: None,
            "profiles": {"all"},
            "deprecated": True,
        },
        "broken_tool": {"description": "d", "profiles": {"all"}},
    }
    monkeypatch.setattr(mcp_servers, "_TOOL_REGISTRY", registry)
    monkeypatch.setattr(mcp_servers, "_registered_profile", None)
    monkeypatch.setattr(
        mcp_servers,
        "config",
        SimpleNamespace(
            IS_UNIX=unix,
            ENABLE_WRITE_DOFILE=enable_write,
        ),
        raising=False,
    )


def test_register_tools_core_only_registers_core(monkeypatch: pytest.MonkeyPatch, loaded_modules):
    mcp_servers, _ = loaded_modules
    _set_registry(monkeypatch, mcp_servers, unix=True, enable_write=False)
    server = _DummyServer()

    mcp_servers.register_tools(server, profile="core")

    assert set(server.tools) == {"stata_do", "get_data_info", "help"}
    assert server.resources == []  # resource registration temporarily disabled


def test_register_tools_all_applies_platform_and_deprecated_filters(
    monkeypatch: pytest.MonkeyPatch,
    loaded_modules,
):
    mcp_servers, _ = loaded_modules
    _set_registry(monkeypatch, mcp_servers, unix=False, enable_write=False)
    server = _DummyServer()

    mcp_servers.register_tools(server, profile="all")

    assert set(server.tools) == {"stata_do", "get_data_info", "read_log"}
    assert server.resources == []


def test_register_tools_unsafe_includes_standard_and_high_risk_tools(
    monkeypatch: pytest.MonkeyPatch,
    loaded_modules,
):
    mcp_servers, _ = loaded_modules
    server = _DummyServer()
    _set_registry(
        monkeypatch,
        mcp_servers,
        unix=True,
        enable_write=False,
    )
    mcp_servers.register_tools(server, profile="unsafe")

    assert set(server.tools) == {
        "stata_do",
        "get_data_info",
        "help",
        "read_log",
        "ado_package_install",
    }


def test_register_tools_prevents_profile_switch(monkeypatch: pytest.MonkeyPatch, loaded_modules):
    mcp_servers, _ = loaded_modules
    _set_registry(monkeypatch, mcp_servers, unix=True, enable_write=True)
    server = _DummyServer()

    mcp_servers.register_tools(server, profile="core")
    with pytest.raises(RuntimeError):
        mcp_servers.register_tools(server, profile="all")


def test_register_tools_logs_warning_for_missing_func(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    loaded_modules,
):
    mcp_servers, _ = loaded_modules
    _set_registry(monkeypatch, mcp_servers, unix=True, enable_write=True)
    server = _DummyServer()

    with caplog.at_level(logging.WARNING):
        mcp_servers.register_tools(server, profile="all")

    assert any("broken_tool" in message for message in caplog.messages)


def test_handle_server_defaults_to_all_when_profile_flags_are_missing(
    monkeypatch: pytest.MonkeyPatch,
    loaded_modules,
):
    _, handlers = loaded_modules
    calls: dict[str, str] = {}

    class _McpRun:
        def run(self, transport: str) -> None:
            calls["transport"] = transport

    fake_module = SimpleNamespace(
        register_tools=lambda server, profile: calls.setdefault("profile", profile),
        stata_mcp=_McpRun(),
    )
    monkeypatch.setitem(sys.modules, "stata_mcp.mcp_servers", fake_module)

    handlers.handle_server(Namespace(transport="http"))

    assert calls["profile"] == "all"
    assert calls["transport"] == "streamable-http"


def test_handle_server_respects_core_profile_flag(monkeypatch: pytest.MonkeyPatch, loaded_modules):
    _, handlers = loaded_modules
    calls: dict[str, str] = {}

    class _McpRun:
        def run(self, transport: str) -> None:
            calls["transport"] = transport

    fake_module = SimpleNamespace(
        register_tools=lambda server, profile: calls.setdefault("profile", profile),
        stata_mcp=_McpRun(),
    )
    monkeypatch.setitem(sys.modules, "stata_mcp.mcp_servers", fake_module)

    handlers.handle_server(Namespace(transport="stdio", core_profile=True, all_profile=False))

    assert calls["profile"] == "core"
    assert calls["transport"] == "stdio"


def test_handle_server_respects_unsafe_profile_flag(
    monkeypatch: pytest.MonkeyPatch,
    loaded_modules,
):
    _, handlers = loaded_modules
    calls: dict[str, str] = {}

    class _McpRun:
        def run(self, transport: str) -> None:
            calls["transport"] = transport

    fake_module = SimpleNamespace(
        register_tools=lambda server, profile: calls.setdefault("profile", profile),
        stata_mcp=_McpRun(),
    )
    monkeypatch.setitem(sys.modules, "stata_mcp.mcp_servers", fake_module)

    handlers.handle_server(
        Namespace(
            transport="stdio",
            core_profile=False,
            all_profile=False,
            unsafe_profile=True,
        )
    )

    assert calls["profile"] == "unsafe"
    assert calls["transport"] == "stdio"


def test_mcp_ado_install_delegates_to_api(
    monkeypatch: pytest.MonkeyPatch,
    loaded_modules,
):
    mcp_servers, _ = loaded_modules
    api_install = Mock(return_value="Installation State: True")
    fake_api_module = ModuleType("stata_mcp.api.ado_install")
    fake_api_module.ado_package_install = api_install
    monkeypatch.setitem(sys.modules, "stata_mcp.api.ado_install", fake_api_module)
    monkeypatch.setattr(
        mcp_servers,
        "config",
        SimpleNamespace(config_file="/tmp/config.toml"),
    )

    context = SimpleNamespace(
        elicit=AsyncMock(
            return_value=SimpleNamespace(
                action="accept",
                data=SimpleNamespace(approved=True),
            )
        )
    )

    result = asyncio.run(
        mcp_servers.ado_package_install(
            "reghdfe",
            is_replace=True,
            ctx=context,
        )
    )

    assert result == "Installation State: True"
    api_install.assert_called_once_with(
        package="reghdfe",
        source="ssc",
        is_replace=True,
        package_source_from=None,
        config_file="/tmp/config.toml",
    )
    context.elicit.assert_awaited_once()


def test_mcp_ado_install_fails_closed_without_user_approval(
    monkeypatch: pytest.MonkeyPatch,
    loaded_modules,
):
    mcp_servers, _ = loaded_modules
    api_install = Mock()
    fake_api_module = ModuleType("stata_mcp.api.ado_install")
    fake_api_module.ado_package_install = api_install
    monkeypatch.setitem(sys.modules, "stata_mcp.api.ado_install", fake_api_module)
    context = SimpleNamespace(
        elicit=AsyncMock(
            return_value=SimpleNamespace(
                action="decline",
                data=None,
            )
        )
    )

    with pytest.raises(PermissionError, match="not approved"):
        asyncio.run(mcp_servers.ado_package_install("reghdfe", ctx=context))

    api_install.assert_not_called()
