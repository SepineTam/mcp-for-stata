"""Install supported components from the addon and extra GitHub directories."""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

import tomli_w

from .addon_lsp import install_lsp
from .addon_source import BUNDLE_PATHS, AddonError, Bundle, GitHubSource
from .addon_store import ManagedStore, check_path, json_bytes

SKILL_ROOTS = {
    "claude-code": ".claude/skills",
    "codex": ".agents/skills",
    "gemini": ".gemini/skills",
    "opencode": ".config/opencode/skills",
    "cursor": ".cursor/skills",
    "copilot": ".copilot/skills",
    "openclaw": ".openclaw/skills",
    "pi": ".pi/agent/skills",
}
JSON_CLIENTS = {"claude", "claude-code", "cursor", "cline", "gemini", "workbuddy", "openclaw", "pi", "copilot"}


def load_object(data: bytes, name: str) -> dict:
    value = json.loads(data)
    if not isinstance(value, dict):
        raise AddonError(f"{name} must contain a JSON object")
    return value


def convert_server(client: str, entry: object) -> dict:
    """Translate the repository's stdio/HTTP definitions without running them."""
    if not isinstance(entry, dict):
        raise AddonError("MCP entry must be an object")
    kind = entry.get("type", "stdio" if "command" in entry else "http")
    if kind == "stdio":
        if set(entry) - {"type", "command", "args", "env"}:
            raise AddonError("Unsupported stdio MCP fields")
        command, args, env = entry.get("command"), entry.get("args", []), entry.get("env", {})
        if not isinstance(command, str) or not command.strip():
            raise AddonError("MCP command must be a nonempty string")
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise AddonError("MCP args must be strings")
        if not isinstance(env, dict) or not all(isinstance(value, str) for value in env.values()):
            raise AddonError("MCP environment must contain strings")
        if client == "opencode":
            return {"type": "local", "command": [command, *args], **({"environment": env} if env else {})}
        result = {"command": command, "args": args, **({"env": env} if env else {})}
        if client == "copilot":
            result.update(type="local", tools=["*"])
        return result
    if kind != "http" or set(entry) - {"type", "url", "headers"}:
        raise AddonError(f"Unsupported MCP transport/fields: {kind}")
    url = entry.get("url")
    if not isinstance(url, str):
        raise AddonError("MCP URL must be a string")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise AddonError("Remote MCP requires an HTTPS URL without embedded credentials")
    headers = entry.get("headers", {})
    if not isinstance(headers, dict) or not all(isinstance(value, str) for value in headers.values()):
        raise AddonError("MCP headers must contain strings")
    if client in {"claude", "pi"}:
        raise AddonError(f"HTTP MCP configuration is not supported by this {client} adapter")
    if client == "codex":
        return {"url": url, **({"http_headers": headers} if headers else {})}
    if client == "gemini":
        return {"httpUrl": url, **({"headers": headers} if headers else {})}
    result = {"url": url, **({"headers": headers} if headers else {})}
    if client == "opencode":
        result["type"] = "remote"
    elif client == "cline":
        result["type"] = "streamableHttp"
    elif client == "openclaw":
        result["transport"] = "streamable-http"
    elif client in {"claude-code", "copilot"}:
        result["type"] = "http"
    if client == "copilot":
        result["tools"] = ["*"]
    return result


def replace_toml_server(original: bytes, name: str, entry: dict, exists: bool) -> bytes:
    """Replace only our explicit server table, preserving all unrelated TOML text."""
    addition = tomli_w.dumps({"mcp_servers": {name: entry}})
    text = original.decode("utf-8")
    if not exists:
        return (text.rstrip("\n") + "\n\n" + addition).encode("utf-8")
    chunks = re.split(r"(?m)(?=^[ \t]*\[)", text)
    kept, removed = [], False
    for chunk in chunks:
        first_line = chunk.splitlines()[0] if chunk else ""
        try:
            header = tomllib.loads(first_line + "\n__statamcp_header__ = true\n")
        except tomllib.TOMLDecodeError:
            header = {}
        if name in header.get("mcp_servers", {}):
            removed = True
        else:
            kept.append(chunk)
    if not removed:
        raise AddonError("Existing TOML server uses an unsupported layout; left unchanged")
    updated = ("".join(kept).rstrip("\n") + "\n\n" + addition).encode("utf-8")
    before, after = tomllib.loads(text), tomllib.loads(updated.decode("utf-8"))
    before["mcp_servers"][name] = entry
    if before != after:
        raise AddonError("TOML update would change unrelated settings; left unchanged")
    return updated


class AddonInstaller:
    def __init__(self, installer, *, addon: bool = True, extra: bool = False, ref: str = "master") -> None:
        self.installer = installer
        self.groups = [name for name, enabled in (("addon", addon), ("extra", extra)) if enabled]
        self.source = GitHubSource(ref)

    def install(self, client: str | None, config_path=None, config_index=None) -> None:
        if not self.groups:
            return
        client = self.installer.CLIENT_ALIASES.get(client, client) if client else "custom-json"
        for group in self.groups:
            try:
                bundle = self.source.fetch(group)
                with ManagedStore().locked() as store:
                    self._files(bundle, client, store)
                    self._servers(bundle, client, store, config_path, config_index)
                print(f"[DONE]\t{client}: checked {BUNDLE_PATHS[group]} at {bundle.commit[:12]}")
            except (OSError, ValueError, TypeError) as error:
                print(f"[WARN]\t{client}: {group} incomplete: {error}. Base MCP configuration is retained.")

    def _files(self, bundle: Bundle, client: str, store: ManagedStore) -> None:
        roots = sorted({name.split("/")[1] for name in bundle.files if re.fullmatch(r"skills/[^/]+/SKILL\.md", name)})
        skill_root = SKILL_ROOTS.get(client)
        if roots and not skill_root:
            print(f"[SKIP]\t{client}: skill installation is not supported by this adapter")
        elif roots:
            base = Path.home() / skill_root
            if client == "claude-code":
                base = Path(os.getenv("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "skills"
            elif client == "opencode":
                base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "opencode" / "skills"
            for name in roots:
                prefix = f"skills/{name}/"
                files = {key[len(prefix) :]: data for key, data in bundle.files.items() if key.startswith(prefix)}
                store.install_files(base / name, files, bundle, client, "skill")
        for kind in ("rules", "commands", "agents"):
            prefix = kind + "/"
            files = {key[len(prefix) :]: data for key, data in bundle.files.items() if key.startswith(prefix)}
            if not files:
                continue
            if client != "claude-code":
                print(f"[SKIP]\t{client}: {kind} installation is not supported by this adapter")
                continue
            # Keep each bundle in its own namespace without editing CLAUDE.md.
            base = Path(os.getenv("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / kind / bundle.group
            store.install_files(base, files, bundle, client, kind)
        manifest = load_object(bundle.files.get("plugin.json", b"{}"), "plugin.json")
        try:
            install_lsp(manifest.get("lspServers"), bundle, client, store)
        except (OSError, ValueError) as error:
            print(f"[WARN]\t{client}: LSP setup incomplete: {error}")
        if manifest.get("hooks") or any(key.startswith("hooks/") for key in bundle.files):
            print(f"[SKIP]\t{client}: hooks require native plugin setup; not enabled by file installation")

    def _servers(self, bundle: Bundle, client: str, store: ManagedStore, config_path, config_index) -> None:
        if "mcp.json" in bundle.files:
            document = load_object(bundle.files["mcp.json"], "mcp.json")
            if set(document) - {"mcpServers"}:
                raise AddonError("All MCP entries in mcp.json must be inside mcpServers")
            servers = document.get("mcpServers", {})
        else:
            document = load_object(bundle.files.get("plugin.json", b"{}"), "plugin.json")
            servers = document.get("mcpServers", {})
        if not isinstance(servers, dict):
            raise AddonError("mcpServers must be an object")
        for name, entry in servers.items():
            # Base installation is authoritative for Stata detection and configuration.
            if name == "stata-mcp":
                continue
            try:
                if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
                    raise AddonError("Invalid MCP server name")
                self._server(bundle, client, store, name, entry, config_path, config_index)
            except (OSError, ValueError, TypeError) as error:
                print(f"[SKIP]\t{client}: MCP {name}: {error}")

    def _server(self, bundle, client, store, name, entry, config_path, config_index):
        if client not in JSON_CLIENTS | {"codex", "opencode", "custom-json"}:
            raise AddonError("Extra MCP installation is not supported by this adapter")
        path = Path(config_path) if config_path else self.installer.find_config_path(client)
        path = check_path(path)
        original = path.read_bytes() if path.exists() else None
        converted = convert_server(client, entry)
        if client == "codex":
            document = tomllib.loads((original or b"").decode("utf-8"))
            servers = document.get("mcp_servers", {})
            if not isinstance(servers, dict):
                raise AddonError("mcp_servers must be a table")
            current = servers.get(name)
            content = replace_toml_server(original or b"", name, converted, current is not None)
            key = f"mcp_servers/{name}"
        else:
            document = load_object(original or b"{}", str(path))
            index = config_index if config_index is not None else self.installer.find_default_index(client)
            keys = [index] if isinstance(index, str) else list(index)
            cursor = document
            for segment in keys:
                cursor = cursor.setdefault(segment, {})
                if not isinstance(cursor, dict):
                    raise AddonError(f"Configuration section {segment} must be an object")
            current = cursor.get(name)
            if name in cursor and not isinstance(current, dict):
                raise AddonError("Existing MCP entry is not an object; left unchanged")
            cursor[name] = converted
            content = json_bytes(document)
            key = "/".join([*keys, name])
        store.install_entry(path, key, current, converted, content, original, bundle, client)
