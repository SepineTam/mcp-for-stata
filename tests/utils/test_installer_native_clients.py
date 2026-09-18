"""Opt-in native configuration acceptance, always using disposable client homes.

Run with STATA_MCP_NATIVE_INSTALL_TESTS=1. No model request, Stata execution or
external MCP service is used. Client health checks may launch the inert probe.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest

from stata_mcp.utils.installer import Installer
from stata_mcp.utils.installer.addon_source import Bundle
from stata_mcp.utils.installer.addons import AddonInstaller

pytestmark = pytest.mark.skipif(
    os.getenv("STATA_MCP_NATIVE_INSTALL_TESTS") != "1",
    reason="Native client acceptance is opt-in and needs installed client CLIs",
)


@pytest.mark.parametrize("client,binary", [("codex", "codex"), ("claude-code", "claude")])
@pytest.mark.parametrize("custom_directory", [False, True])
def test_native_client_reads_base_and_extra(client, binary, custom_directory, monkeypatch, tmp_path):
    executable = shutil.which(binary)
    if executable is None:
        pytest.skip(f"{binary} is not installed")
    root = tmp_path.resolve()
    monkeypatch.chdir(root)
    for variable in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(variable, str(root))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(root / ".config"))
    for variable in ("CODEX_HOME", "CLAUDE_CONFIG_DIR"):
        monkeypatch.delenv(variable, raising=False)
    if custom_directory:
        custom = root / "custom-client"
        custom.mkdir()
        monkeypatch.setenv("CODEX_HOME" if binary == "codex" else "CLAUDE_CONFIG_DIR", str(custom))
    monkeypatch.setattr(Installer, "STATA_CLI", property(lambda self: "/test/stata"))
    files = {
        "mcp.json": json.dumps(
            {
                "mcpServers": {
                    "installation-probe": {"command": sys.executable, "args": ["-c", "pass"]},
                }
            }
        ).encode(),
    }
    installer = Installer(is_env=False)
    # Some clients health-check entries while reading them. Keep both entries inert.
    installer.command = sys.executable
    installer.args = ["-c", "pass"]
    installer.addons = AddonInstaller(installer, addon=False, extra=True)
    monkeypatch.setattr(installer.addons.source, "fetch", lambda group: Bundle(group, "a" * 40, files))
    installer.install(client)
    installer.install(client)
    for name in ("stata-mcp", "installation-probe"):
        command = [executable, "mcp", "get", name]
        if binary == "codex":
            command.append("--json")
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, cwd=root)
        assert result.returncode == 0, result.stderr
        assert name in result.stdout
    assert installer.find_config_path(client).is_relative_to(root)
    assert (root / ".statamcp/addons-v1.json").is_file()
