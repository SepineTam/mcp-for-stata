"""Register downloaded LSP settings through Claude Code's native plugin manager."""

from __future__ import annotations

import json
import shutil
import subprocess

from .addon_source import AddonError, Bundle
from .addon_store import ManagedStore, json_bytes


def install_lsp(definitions: object, bundle: Bundle, client: str, store: ManagedStore) -> None:
    if not definitions:
        return
    if client != "claude-code":
        print(f"[SKIP]\t{client}: LSP configuration is not supported by this adapter")
        return
    claude = shutil.which("claude")
    if not claude:
        print("[SKIP]\tclaude-code: LSP requires the Claude CLI; skills and rules remain available")
        return
    if not isinstance(definitions, dict):
        raise AddonError("lspServers must be an object")
    available = {}
    for name, settings in definitions.items():
        if not isinstance(settings, dict) or not isinstance(settings.get("command"), str):
            raise AddonError(f"Invalid LSP definition: {name}")
        if not shutil.which(settings["command"]):
            print(f"[SKIP]\tclaude-code: LSP {name} needs {settings['command']} on PATH; install it separately")
        else:
            available[name] = settings
    if not available:
        return

    def run(arguments):
        try:
            result = subprocess.run([claude, "plugin", *arguments], capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired as error:
            raise AddonError("Claude plugin command timed out; retry installation") from error
        if result.returncode:
            raise AddonError(f"Claude plugin {' '.join(arguments[:2])} failed (exit {result.returncode})")
        return result.stdout

    # Leave an existing complete native toolbox responsible for its own LSP.
    listing = json.loads(run(["list", "--json"]))
    if not isinstance(listing, list):
        raise AddonError("Unsupported Claude plugin list response")
    for plugin in listing:
        if (
            bundle.group == "addon"
            and isinstance(plugin, dict)
            and plugin.get("enabled", False)
            and str(plugin.get("id", "")).startswith("stata-toolbox@")
        ):
            print("[SKIP]\tclaude-code: installed stata-toolbox already manages its LSP settings")
            return

    plugin_name = f"stata-mcp-{bundle.group}-lsp"
    marketplace_name = f"stata-mcp-{bundle.group}-managed"
    root = store.root / "addon-plugins" / bundle.group
    qualified = f"{plugin_name}@{marketplace_name}"
    installed_plugin = next((item for item in listing if isinstance(item, dict) and item.get("id") == qualified), None)
    if installed_plugin and installed_plugin.get("enabled") is False:
        print(f"[SKIP]\tclaude-code: {qualified} is disabled; leaving it disabled")
        return
    files = {
        ".claude-plugin/marketplace.json": json_bytes(
            {
                "name": marketplace_name,
                "owner": {"name": "MCP-for-Stata"},
                "plugins": [{"name": plugin_name, "source": "./plugin"}],
            }
        ),
        "plugin/.claude-plugin/plugin.json": json_bytes(
            {
                "name": plugin_name,
                "version": f"0.0.0-g{bundle.commit[:12]}",
                "description": "Stata-MCP managed LSP configuration",
                "lspServers": available,
            }
        ),
    }
    if not store.install_files(root, files, bundle, client, "lsp-plugin"):
        return
    # Refreshing a known local marketplace is handled by plugin update itself.
    if installed_plugin:
        run(["update", qualified, "--scope", "user"])
    else:
        run(["marketplace", "add", str(root)])
        run(["install", qualified, "--scope", "user"])
    print(f"[DONE]\tclaude-code: LSP plugin {qualified}; restart Claude Code to load changes")
