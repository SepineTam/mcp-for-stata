#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : installer.py

import json
import os
import platform
import sys
import tomllib
from pathlib import Path
from typing import Callable, Dict, Optional

from ...stata import StataFinder


class Installer:
    def __init__(self, sys_os: str = None, is_env: bool = True):
        self.sys_os = sys_os or sys.platform
        self.is_env = is_env

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
            "opencode": self.install_to_opencode,
        }

    def install_all(self):
        func = self.client_function_mapping.values()
        for func in func:
            func()

    def install(self, to: str):
        install_func = self.client_function_mapping.get(to, None)
        if install_func:
            install_func()
        else:
            print(f"{to} is not a valid client.")
            print(f"Please choose a valid client from {self.client_function_mapping.keys()}")
            sys.exit(1)

    def install_to_json_config(
        self,
        config_path: Path,
        key: str = "mcpServers",
        custom_config: dict = None
    ):
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

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
                    config = {key: {}}
                else:
                    sys.exit(1)
        else:
            config = {key: {}}

        servers = config.setdefault(key, {})
        if "stata-mcp" in servers:
            print("stata-mcp is already installed.")
            sys.exit(0)

        servers.update(custom_config or self.STATA_MCP_COMMON_CONFIG)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def install_to_toml_config(self, config_path: Path, key: str = "mcpServers"):
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

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

        print(f"✅ Successfully installed stata-mcp to: {config_path}")

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

    def install_to_claude_code(self):
        cc_mcp_config_file = Path.home() / ".claude.json"
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
        elif self.sys_os.lower() == "windows":
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
        self.env["STATA_MCP_CWD"] = document_path.as_posix()

        self.install_to_json_config(config_file)

    def install_to_cline(self):
        # Get config file path based on OS
        if self.sys_os.lower() == "darwin":
            config_file = Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / \
                "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        elif self.sys_os.lower() == "linux":
            config_file = Path.home() / ".config" / "Code" / "User" / "globalStorage" / \
                "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        elif self.sys_os.lower() == "windows":
            appdata = os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
            config_file = Path(appdata) / "Code" / "User" / "globalStorage" / \
                "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        else:
            print(f"Unsupported platform: {self.sys_os}")
            sys.exit(1)

        self.install_to_json_config(config_file)

    def install_to_opencode(self):
        config_file = Path.home() / ".config" / "opencode" / "opencode.json"
        opencode_config = {
            "stata-mcp": {
                "type": "local",
                "command": [self.command] + self.args,
                **({"env": self.env} if self.is_env and self.env else {})
            }
        }
        self.install_to_json_config(
            config_file,
            key="mcp",
            custom_config=opencode_config
        )

    def install_to_codex(self):
        config_file = Path.home() / ".codex" / "config.toml"
        self.install_to_toml_config(config_file, key="mcp_servers")


class InstallerDockerMode(Installer):
    def __init__(self,
                 license_file_path: Path,
                 work_dir: Optional[Path] = None,
                 cpus: Optional[float] = None,
                 memory: Optional[str] = None,
                 image: str = "ghcr.io/sepinetam/stata-mcp:latest"):
        # Skip parent __init__ to avoid calling parent _post_init
        self.license_file_path = Path(license_file_path)
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self.cpus = cpus
        self.memory = memory
        self.image = image

        super().__init__(is_env=False)

    def _post_init(self):
        self.args = [
            "run",
            "--rm",
            "-i",
        ]

        # Add platform flag for non-amd64 machines (amd64-only images)
        if platform.machine() not in ("x86_64", "amd64"):
            self.args.extend(["--platform", "linux/amd64"])

        if self.cpus:
            self.args.extend(["--cpus", str(self.cpus)])
        if self.memory:
            self.args.extend(["--memory", self.memory])

        self.args.extend([
            "-v",
            f"{self.license_file_path.as_posix()}:/usr/local/stata/stata.lic",
            "-v",
            f"{self.work_dir.as_posix()}:/workspace",
            self.image,
        ])

        self.command = "docker"
        self.env = {}
