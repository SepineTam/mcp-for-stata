#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : utils/installer/installer.py

import json
import logging
import os
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from ...stata import StataFinder

logger = logging.getLogger(__name__)


class Installer:
    PI_MCP_ADAPTER = "pi-mcp-adapter"
    PI_MCP_ADAPTER_SOURCE = "npm:pi-mcp-adapter"
    INSTALL_ALL_EXCLUDED_CLIENTS = frozenset({"pi"})

    CLIENT_ALIASES = {
        "cc": "claude-code",
        "hermes": "hermes-agent",
        "deepseek-harness": "dsh",
        "wb": "workbuddy",
    }

    def __init__(self, sys_os: str = None, is_env: bool = True):
        self.sys_os = sys_os or sys.platform
        self.is_env = is_env
        self.addons = None

        self._post_init()

    def _post_init(self):
        self.command = "uvx"
        self.args = ["stata-mcp"]
        self.env = {"STATA_CLI": self.STATA_CLI} if self.is_env else {}

    @property
    def STATA_CLI(self) -> str:
        return StataFinder().STATA_CLI

    @property
    def STATA_MCP_COMMON_CONFIG(self):
        return {
            "stata-mcp": {
                "command": self.command,
                "args": self.args,
                "env": self.env
            }
        }

    @property
    def client_function_mapping(self) -> Dict[str, Callable]:
        return {
            "claude": self.install_to_claude_desktop,
            "cc": self.install_to_claude_code,
            "claude-code": self.install_to_claude_code,
            "gemini": self.install_to_gemini,
            "cursor": self.install_to_cursor,
            "cline": self.install_to_cline,
            "codex": self.install_to_codex,
            "copilot": self.install_to_copilot,
            "opencode": self.install_to_opencode,
            "openclaw": self.install_to_openclaw,
            "hermes": self.install_to_hermes_agent,
            "hermes-agent": self.install_to_hermes_agent,
            "dsh": self.install_to_deepseek_harness,
            "workbuddy": self.install_to_workbuddy,
            "pi": self.install_to_pi,
        }

    # Default JSON key path each generic-JSON client expects.
    # opencode/codex are intentionally excluded: they have client-specific
    # schemas and do not participate in the --json-file/--json-index flow.
    CLIENT_DEFAULT_KEY: Dict[str, "str | list[str]"] = {
        "claude": "mcpServers",
        "cc": "mcpServers",
        "claude-code": "mcpServers",
        "gemini": "mcpServers",
        "cursor": "mcpServers",
        "cline": "mcpServers",
        "openclaw": ["mcp", "servers"],
        "workbuddy": "mcpServers",
        "wb": "mcpServers",
        "pi": "mcpServers",
        "copilot": "mcpServers",
    }

    def install_all(self):
        seen = set()
        success = True
        for target in self.client_function_mapping:
            client = self.CLIENT_ALIASES.get(target, target)
            if client in seen:
                continue
            seen.add(client)
            if client in self.INSTALL_ALL_EXCLUDED_CLIENTS:
                continue
            try:
                self.install(client)
            except SystemExit as error:
                if error.code not in (None, 0):
                    print(f"[ERROR]\tMCP installation failed for {client}; continuing with other clients")
                    success = False
            except (OSError, ValueError) as error:
                print(f"[ERROR]\tMCP installation failed for {client}: {error}")
                success = False
        return success

    def install(self, to: str):
        client = self.CLIENT_ALIASES.get(to, to)
        install_func = self.client_function_mapping.get(client, None)
        if install_func:
            # A client-specific override must not leak into subsequent --all targets.
            saved_args, saved_env = list(self.args), dict(self.env)
            try:
                try:
                    install_func()
                except SystemExit as error:
                    if error.code not in (None, 0):
                        raise
                self.install_addons(client)
            finally:
                self.args, self.env = saved_args, saved_env
        else:
            print(f"{to} is not a valid client.")
            print(f"Please choose a valid client from {self.client_function_mapping.keys()}")
            sys.exit(1)

    def install_addons(self, client=None, config_path=None, config_index=None):
        """Install optional components only when enabled by the CLI."""
        if self.addons is not None:
            self.addons.install(client, config_path, config_index)

    def install_to_json_config(
        self,
        config_path: Path,
        key: "str | list[str]" = "mcpServers",
        custom_config: dict = None,
        exit_if_exists: bool = True,
    ) -> bool:
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        keys = [key] if isinstance(key, str) else list(key)
        try:
            self._backup_before_write(config_path)
        except OSError as exc:
            print(f"[ERROR]\tFailed to backup {config_path}: {exc}")
            sys.exit(1)

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                overwrite = input(
                    f"We could not open your config file {config_path.as_posix()}, "
                    "whether continue (This might overwrite your config file)\n[Y]es/[N]o"
                ).lower()
                if overwrite in ["y", "yes"]:
                    config = {}
                else:
                    sys.exit(1)
        else:
            config = {}

        cursor = config
        for k in keys:
            cursor = cursor.setdefault(k, {})
        servers = cursor

        if "stata-mcp" in servers:
            print(f"[DONE]\tstata-mcp is already installed in {config_path}.")
            if exit_if_exists:
                sys.exit(0)
            return False

        servers.update(custom_config or self.STATA_MCP_COMMON_CONFIG)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("Wrote MCP config to %s", config_path)
        return True

    def install_to_toml_config(self, config_path: Path, key: str = "mcpServers"):
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._backup_before_write(config_path)
        except OSError as exc:
            print(f"[ERROR]\tFailed to backup {config_path}: {exc}")
            sys.exit(1)

        # Check if stata-mcp already exists
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    config = tomllib.load(f)
                if key in config and "stata-mcp" in config[key]:
                    print("stata-mcp is already installed.")
                    sys.exit(0)
            except Exception:
                pass  # Continue with installation

        # Append stata-mcp config to file
        with open(config_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{key}.stata-mcp]\n")
            f.write(f'command = "{self.command}"\n')
            f.write(f"args = {self._format_toml_list(self.args)}\n")
            if self.is_env:
                f.write(f"env = {self._format_inline_table(self.env)}\n")

        logger.info("Wrote MCP config to %s", config_path)
        print(f"✅ Successfully installed stata-mcp to: {config_path}")

    def install_to_yaml_config(self, config_path: Path, key: str = "mcpServers"):
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._backup_before_write(config_path)
        except OSError as exc:
            print(f"[ERROR]\tFailed to backup {config_path}: {exc}")
            sys.exit(1)

        print(
            "[NOTE]\tHermes Agent uses YAML for mcpServers config."
            " This is a text-based implementation without a YAML parser. Use with caution."
        )

        server_yaml = [
            "  stata-mcp:",
            f'    command: "{self.command}"',
            f'    args: {json.dumps(self.args)}',
        ]
        if self.is_env:
            server_yaml.append("    env:")
            for k, v in self.env.items():
                server_yaml.append(f'      {k}: "{v}"')

        if config_path.exists():
            existing = config_path.read_text(encoding="utf-8")
            if "stata-mcp:" in existing:
                print("stata-mcp is already installed.")
                sys.exit(0)

            if f"{key}:" in existing:
                lines = existing.splitlines()
                new_lines = []
                inserted = False
                for line in lines:
                    new_lines.append(line)
                    if not inserted and line.strip() == f"{key}:":
                        new_lines.extend(server_yaml)
                        inserted = True
                if not inserted:
                    new_lines.extend(["", f"{key}:"] + server_yaml)
                config_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            else:
                sep = "\n\n" if existing.strip() else ""
                config_path.write_text(
                    existing.rstrip("\n") + sep + f"{key}:\n" + "\n".join(server_yaml) + "\n",
                    encoding="utf-8",
                )
        else:
            config_path.write_text(
                f"{key}:\n" + "\n".join(server_yaml) + "\n",
                encoding="utf-8",
            )

        logger.info("Wrote MCP config to %s", config_path)
        print(f"✅ Successfully installed stata-mcp to: {config_path}")

    def _backup_before_write(self, config_path: Path) -> Optional[Path]:
        """Copy an existing config file before editing it."""
        if not config_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        suffix = config_path.suffix.lstrip(".")
        backup_name = f"{config_path.stem}.backup-{timestamp}"
        if suffix:
            backup_name = f"{backup_name}.{suffix}"
        backup_path = config_path.with_name(backup_name)

        shutil.copy2(config_path, backup_path)

        logger.info("Backed up %s to %s", config_path, backup_path)
        print(f"[BACKUP]\tOriginal config backed up to: {backup_path.resolve()}")
        return backup_path

    def _write_toml(self, file, config, prefix=""):
        """Recursively write config to TOML format."""
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Check if it's a simple dict (inline table) or nested table
                if self._is_simple_dict(value):
                    file.write(f"{key} = {self._format_inline_table(value)}\n")
                else:
                    file.write(f"[{full_key}]\n")
                    self._write_toml(file, value, full_key)
            elif isinstance(value, list):
                file.write(f"{key} = {self._format_toml_list(value)}\n")
            elif isinstance(value, str):
                file.write(f'{key} = "{value}"\n')
            elif isinstance(value, bool):
                file.write(f"{key} = {str(value).lower()}\n")
            else:
                file.write(f"{key} = {value}\n")

    def _is_simple_dict(self, d):
        """Check if dict can be formatted as inline table."""
        return len(d) <= 3 and not any(isinstance(v, (dict, list)) for v in d.values())

    def _format_inline_table(self, d):
        """Format dict as inline table."""
        items = []
        for k, v in d.items():
            if isinstance(v, str):
                items.append(f'{k} = "{v}"')
            elif isinstance(v, bool):
                items.append(f"{k} = {str(v).lower()}")
            elif isinstance(v, list):
                items.append(f"{k} = {self._format_toml_list(v)}")
            else:
                items.append(f"{k} = {v}")
        return "{" + ", ".join(items) + "}"

    def _format_toml_list(self, lst):
        """Format list for TOML output."""
        if not lst:
            return "[]"
        formatted = [f'"{item}"' if isinstance(item, str) else str(item) for item in lst]
        return "[" + ", ".join(formatted) + "]"

    def find_config_path(self, client: str) -> Path:
        """Return the config file path for the given client (read-only).

        Mirrors the path-discovery blocks from ``install_to_<client>`` but does
        not write any file. The caller is responsible for handling a missing
        file with an appropriate "file not found" error.
        """
        client = self.CLIENT_ALIASES.get(client, client)

        if client in {"claude", "claude-desktop"}:
            if self.sys_os.lower() == "darwin":
                return Path(os.path.expanduser(
                    "~/Library/Application Support/Claude/claude_desktop_config.json"
                ))
            if self.sys_os.lower() == "linux":
                raise ValueError(f"There is not a Linux version of Claude yet: {client}")
            if self.sys_os.lower() in {"windows", "win32"}:
                appdata = os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
                return Path(os.path.join(appdata, "Claude", "claude_desktop_config.json"))
            raise ValueError(f"Unsupported platform: {self.sys_os}")

        if client in {"cc", "claude-code"}:
            config_directory = os.getenv("CLAUDE_CONFIG_DIR")
            if config_directory:
                return Path(config_directory).expanduser() / ".claude.json"
            return Path.home() / ".claude.json"

        if client == "gemini":
            return Path.home() / ".gemini" / "settings.json"

        if client == "cursor":
            return Path.home() / ".cursor" / "mcp.json"

        if client == "cline":
            if self.sys_os.lower() == "darwin":
                return (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Code"
                    / "User"
                    / "globalStorage"
                    / "saoudrizwan.claude-dev"
                    / "settings"
                    / "cline_mcp_settings.json"
                )
            if self.sys_os.lower() == "linux":
                return (
                    Path.home()
                    / ".config"
                    / "Code"
                    / "User"
                    / "globalStorage"
                    / "saoudrizwan.claude-dev"
                    / "settings"
                    / "cline_mcp_settings.json"
                )
            if self.sys_os.lower() in {"windows", "win32"}:
                appdata = os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
                return (
                    Path(appdata)
                    / "Code"
                    / "User"
                    / "globalStorage"
                    / "saoudrizwan.claude-dev"
                    / "settings"
                    / "cline_mcp_settings.json"
                )
            raise ValueError(f"Unsupported platform: {self.sys_os}")

        if client == "opencode":
            config_directory = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config")
            return config_directory.expanduser() / "opencode" / "opencode.json"

        if client == "codex":
            config_directory = Path(os.getenv("CODEX_HOME") or Path.home() / ".codex")
            return config_directory.expanduser() / "config.toml"

        if client == "copilot":
            return Path.home() / ".copilot" / "mcp-config.json"

        if client == "openclaw":
            return Path.home() / ".openclaw" / "openclaw.json"

        if client == "workbuddy":
            return Path.home() / ".workbuddy" / "mcp.json"

        if client == "pi":
            return Path.home() / ".pi" / "agent" / "mcp.json"

        if client in {"hermes", "hermes-agent"}:
            return Path.home() / ".hermes" / "config.yaml"

        raise ValueError(f"unknown client: {client}")

    def find_default_index(self, client: str) -> "str | list[str]":
        """Return the default key path inside the client's config file."""
        client = self.CLIENT_ALIASES.get(client, client)
        if client in self.CLIENT_DEFAULT_KEY:
            return self.CLIENT_DEFAULT_KEY[client]
        if client == "opencode":
            return "mcp"
        if client == "codex":
            return "mcp_servers"
        if client in {"hermes", "hermes-agent"}:
            return "mcp_servers"
        raise ValueError(f"unknown client: {client}")

    def install_from_cli(self, cli_bin: str, command: list[str]) -> bool:
        """Try to install via a CLI tool. Return True if successful."""
        if not shutil.which(cli_bin):
            print(f"[WARN]\t{cli_bin} is not found, falling back to config file.")
            return False
        full_cmd = [cli_bin, *command]
        logger.info("Running installer: %s", ' '.join(full_cmd))
        print(f"$ {' '.join(full_cmd)}")
        try:
            result = subprocess.run(
                full_cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                print(result.stdout)
            print(f"[DONE]\tSuccessfully installed Stata-MCP via {cli_bin}")
            return True
        except subprocess.CalledProcessError as e:
            if e.stdout:
                print(">", e.stdout)
            if e.stderr:
                print(">", e.stderr)
            stderr = (e.stderr or "").lower()
            if "already exists" in stderr:
                return True
            print(f"[WARN]\tFailed to install Stata-MCP with {cli_bin}, falling back to config file")
            return False

    def install_to_claude_code(self):
        if self.install_from_cli(
            cli_bin="claude",
            command=["mcp", "add", "stata-mcp", "--scope", "user", "--env",
                     f"STATA_CLI={self.STATA_CLI}", "--", self.command, *self.args]
        ):
            return
        cc_mcp_config_file = self.find_config_path("claude-code")
        self.install_to_json_config(cc_mcp_config_file)

    def install_to_claude_desktop(self):
        # Get config file path based on OS
        if self.sys_os.lower() == "darwin":
            config_file_path = os.path.expanduser(
                "~/Library/Application Support/Claude/claude_desktop_config.json"
            )
        elif self.sys_os.lower() == "linux":
            print("There is not a Linux version of Claude yet.")
            sys.exit(1)
        elif self.sys_os.lower() in {"windows", "win32"}:
            appdata = os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
            config_file_path = os.path.join(appdata, "Claude", "claude_desktop_config.json")
        else:
            print(f"Unsupported platform: {self.sys_os}")
            sys.exit(1)

        self.install_to_json_config(Path(config_file_path))

    def install_to_gemini(self):
        gemini_user_settings_file = Path.home() / ".gemini" / "settings.json"
        self.install_to_json_config(gemini_user_settings_file)

    def install_to_cursor(self):
        config_file = Path.home() / ".cursor" / "mcp.json"  # Only works on macOS as not other device to test

        # As some reason, cursor should config more args to use.
        document_path = Path.home() / "Documents"
        self.args = ["--directory", document_path.as_posix(), "stata-mcp"]
        self.env["STATA_MCP__CWD"] = document_path.as_posix()

        self.install_to_json_config(config_file)

    def install_to_cline(self):
        # Get config file path based on OS
        if self.sys_os.lower() == "darwin":
            config_file = Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / \
                "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        elif self.sys_os.lower() == "linux":
            config_file = Path.home() / ".config" / "Code" / "User" / "globalStorage" / \
                "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        elif self.sys_os.lower() in {"windows", "win32"}:
            appdata = os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
            config_file = Path(appdata) / "Code" / "User" / "globalStorage" / \
                "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        else:
            print(f"Unsupported platform: {self.sys_os}")
            sys.exit(1)

        self.install_to_json_config(config_file)

    def install_to_opencode(self):
        config_file = self.find_config_path("opencode")
        opencode_config = {
            "stata-mcp": {
                "type": "local",
                "command": [self.command] + self.args,
                **({"environment": self.env} if self.is_env and self.env else {})
            }
        }
        self.install_to_json_config(
            config_file,
            key="mcp",
            custom_config=opencode_config
        )

    def install_to_codex(self):
        if self.install_from_cli(
            cli_bin="codex",
            command=["mcp", "add", "--env", f"STATA_CLI={self.STATA_CLI}", "stata-mcp", "--", self.command, *self.args]
        ):
            return
        config_file = self.find_config_path("codex")
        self.install_to_toml_config(config_file, key="mcp_servers")

    def install_to_copilot(self):
        """Install Stata-MCP into GitHub Copilot CLI."""
        if self.install_from_cli(
            cli_bin="copilot",
            command=[
                "mcp",
                "add",
                "stata-mcp",
                "--env",
                f"STATA_CLI={self.STATA_CLI}",
                "--",
                self.command,
                *self.args,
            ],
        ):
            return

        config_file = Path.home() / ".copilot" / "mcp-config.json"
        copilot_config = {
            "stata-mcp": {
                "type": "local",
                "command": self.command,
                "args": self.args,
                "env": self.env,
                "tools": ["*"],
            }
        }
        self.install_to_json_config(
            config_file,
            custom_config=copilot_config,
        )

    def install_to_openclaw(self):
        _json_config = json.dumps(
            {"command": self.command, "args": self.args, "env": self.env}
        )
        if self.install_from_cli(
            cli_bin="openclaw",
            command=["mcp", "set", "stata-mcp", _json_config]
        ):
            return
        config_file = Path.home() / ".openclaw" / "openclaw.json"
        self.install_to_json_config(config_file, key=["mcp", "servers"])

    def install_to_workbuddy(self):
        """Install Stata-MCP into WorkBuddy's user MCP configuration."""
        config_file = Path.home() / ".workbuddy" / "mcp.json"
        self.install_to_json_config(config_file)

    def install_to_pi(self):
        """Install the Pi MCP adapter when available and prepare its config."""
        pi_available = self.is_pi_available()
        adapter_ready = self.install_pi_adapter() if pi_available else False
        config_file = Path.home() / ".pi" / "agent" / "mcp.json"
        self.install_to_json_config(config_file, exit_if_exists=False)

        if adapter_ready:
            print("[DONE]\tPi MCP adapter and Stata-MCP configuration are ready.")
            return

        if pi_available:
            print(
                "[WARN]\tPi was found, but pi-mcp-adapter could not be installed. "
                f"The Stata-MCP configuration was prepared at {config_file}."
            )
        else:
            print(
                "[WARN]\tPi is not installed. "
                f"The Stata-MCP configuration was prepared at {config_file}, "
                "but it is not active yet."
            )
        print(
            f"[NOTE]\tAfter Pi is available, run: pi install {self.PI_MCP_ADAPTER_SOURCE}"
        )

    @staticmethod
    def is_pi_available() -> bool:
        """Return whether the Pi CLI is available on PATH."""
        return shutil.which("pi") is not None

    def install_pi_adapter(self) -> bool:
        """Install Pi's third-party MCP adapter through the Pi package manager."""
        pi_bin = shutil.which("pi")
        if not pi_bin:
            return False

        command = [pi_bin, "install", self.PI_MCP_ADAPTER_SOURCE]
        logger.info("Installing Pi MCP adapter: %s", " ".join(command))
        print(f"$ pi install {self.PI_MCP_ADAPTER_SOURCE}")
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            if exc.stdout:
                print(">", exc.stdout)
            if exc.stderr:
                print(">", exc.stderr)
            combined = f"{exc.stdout or ''}\n{exc.stderr or ''}".lower()
            if "already installed" in combined or "already exists" in combined:
                return True
            print("[WARN]\tFailed to install pi-mcp-adapter through Pi.")
            return False

        if result.stdout:
            print(result.stdout)
        print("[DONE]\tSuccessfully installed pi-mcp-adapter through Pi.")
        return True

    def is_pi_adapter_installed(self) -> bool:
        """Check Pi's installed package list for the MCP adapter."""
        pi_bin = shutil.which("pi")
        if not pi_bin:
            return False
        try:
            result = subprocess.run(
                [pi_bin, "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        output = f"{result.stdout}\n{result.stderr}".lower()
        return result.returncode == 0 and self.PI_MCP_ADAPTER in output

    def install_to_hermes_agent(self):
        if self.install_from_cli(
            cli_bin="hermes",
            command=[
                "mcp", "add", "stata-mcp", "--command", self.command, "--args", ",".join(self.args),
            ],
        ):
            return
        config_file = Path.home() / ".hermes" / "config.yaml"
        self.install_to_yaml_config(config_file, key="mcp_servers")

    def install_to_deepseek_harness(self):
        """Install Stata-MCP into the DeepSeek Harness web profile."""
        dsh_home = Path(os.getenv("DSH_HOME", Path.home() / ".dsh")).expanduser()
        config_file = dsh_home / "profiles" / "web" / "cordis.patch.yml"
        self.install_to_deepseek_harness_config(config_file)

    def install_to_deepseek_harness_config(self, config_path: Path):
        """Append the DSH MCP bridge entry without rewriting other YAML."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        existing = ""
        if config_path.exists():
            existing = config_path.read_text(encoding="utf-8")
            if not self._is_deepseek_harness_patch_sequence(existing):
                print(
                    f"[ERROR]\t{config_path} must contain a top-level YAML list; "
                    "the file was not changed."
                )
                sys.exit(1)
            if self._has_deepseek_harness_stata_entry(existing):
                print(f"[DONE]\tstata-mcp is already installed in {config_path}.")
                return

        try:
            self._backup_before_write(config_path)
        except OSError as exc:
            print(f"[ERROR]\tFailed to backup {config_path}: {exc}")
            sys.exit(1)

        entry = self._deepseek_harness_config_entry()
        separator = "\n\n" if existing.strip() else ""
        content = existing.rstrip("\n") + separator + entry
        config_path.write_text(content, encoding="utf-8")

        logger.info("Wrote DeepSeek Harness MCP config to %s", config_path)
        print(f"✅ Successfully installed stata-mcp to: {config_path}")

    @staticmethod
    def _has_deepseek_harness_stata_entry(content: str) -> bool:
        """Return whether the canonical Stata MCP entry id is present."""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("- id:"):
                entry_id = stripped.split(":", 1)[1].strip().strip("'\"")
                if entry_id == "stata-mcp":
                    return True
        return False

    @staticmethod
    def _is_deepseek_harness_patch_sequence(content: str) -> bool:
        """Conservatively check that existing DSH YAML has a top-level list."""
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped in {"---", "..."} or stripped.startswith("%"):
                continue
            return line.startswith("-")
        return True

    @staticmethod
    def _deepseek_harness_config_entry() -> str:
        """Build the DSH patch entry requested for Stata-MCP."""
        lines = [
            "# If there is an error in Stata-MCP, open an issue on GitHub.",
            "# Stata MCP server (https://github.com/SepineTam/mcp-for-stata) wired into",
            "# DSH via the built-in MCP client bridge. Tools appear as mcp__stata-mcp__*.",
            "- insert:",
            "    - id: stata-mcp",
            "      name: '@deepseek-ai/dsh-mcp-client'",
            "      config:",
            "        serverName: stata-mcp",
            "        transport: stdio",
            "        command: uvx",
            "        args: ['stata-mcp', 'server']",
            "        # Stata 跑大回归可能超 60s 默认值，设置成 20 分钟",
            "        toolCallTimeoutMs: 1200000",
            "        reconnect:",
            "          maxAttempts: 5",
            "",
        ]
        return "\n".join(lines)
