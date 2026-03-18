#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : config.py

import os
import platform
import sys
import tomllib
from pathlib import Path
from typing import Dict

import tomli_w

from .core.types import StataCLINotFoundError
from .stata import StataFinder


class Config:
    def __init__(self, config_file: Path = None):
        self.config_file = config_file or self.STATA_MCP_DIRECTORY / "config.toml"

    @property
    def config(self) -> Dict:
        try:
            with open(self.config_file, "rb") as f:
                config = tomllib.load(f)
        except Exception:
            config = {}
        return config

    def read_config_text(self) -> str:
        """Return raw configuration file content."""
        if not self.config_file.exists():
            return ""
        return self.config_file.read_text(encoding="utf-8")

    def _write_toml(self, data: dict) -> None:
        """Write TOML content using tomli_w library."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        content = tomli_w.dumps(data)
        self.config_file.write_text(content, encoding="utf-8")

    def set_stata_cli(self, value: str | None = None) -> str:
        """Persist STATA_CLI to config file and return the saved value."""
        cleaned_value = self._clean_string_value(value)
        if cleaned_value is None:
            cleaned_value = StataFinder(None).STATA_CLI

        if cleaned_value is None:
            raise StataCLINotFoundError()

        updated = self.config
        stata_section = updated.get("STATA", {})
        if not isinstance(stata_section, dict):
            stata_section = {}
        stata_section["STATA_CLI"] = cleaned_value
        updated["STATA"] = stata_section
        self._write_toml(updated)
        return cleaned_value

    @staticmethod
    def _clean_string_value(value):
        """
        Clean string value by stripping whitespace and processing escape sequences.

        Args:
            value: The value to clean

        Returns:
            Cleaned value (only processes strings, returns other types as-is)
        """
        if isinstance(value, str):
            value = value.strip()
        if value == "":
            value = None
        return value

    def _get_config_value(self, config_keys: list, env_var: str, default, converter=None, validator=None):
        """
        Generic configuration reading method with priority: environment variable > toml config file > default value

        Args:
            config_keys: Key path in config file, e.g. ["DEBUG", "logging", "MAX_BYTES"]
            env_var: Environment variable name
            default: Default value
            converter: Value conversion function, e.g. bool, int, Path, etc.
            validator: Validation function that accepts the converted value, returns True if valid

        Returns:
            Configuration value (processed by converter and validator)
        """
        # 1. Read from environment variable first
        value = os.getenv(env_var, None)  # str | None
        value = self._clean_string_value(value)

        # 2. If no environment variable, read from config file
        if value is None:
            config_dict = self.config
            for key in config_keys[:-1]:
                config_dict = config_dict.get(key, {})
                if not isinstance(config_dict, dict):
                    config_dict = {}
                    break

            if isinstance(config_dict, dict):
                value = config_dict.get(config_keys[-1], None)  # str | bool | dict | list | int | float | None
                value = self._clean_string_value(value)

        # 3. If still no value, return default
        if value is None:
            return default

        # 4. Convert value
        if converter is not None:
            try:
                value = converter(value)
            except (ValueError, TypeError):
                return default

        # 5. Validate value
        if validator is not None and not validator(value):
            return default

        return value

    @staticmethod
    def _to_bool(value):
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)

    @staticmethod
    def _to_int(value):
        """Convert value to integer."""
        return int(value)

    @staticmethod
    def _to_path(value):
        """Convert value to Path object."""
        return Path(value).expanduser().absolute() if value else None

    @property
    def STATA_MCP_DIRECTORY(self) -> Path:
        base_dir = Path.home() / ".statamcp"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    @property
    def IS_DEBUG(self) -> bool:
        return self._get_config_value(
            config_keys=["DEBUG", "IS_DEBUG"],
            env_var="STATA_MCP__IS_DEBUG",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def ENABLE_WRITE_DOFILE(self) -> bool:
        return self._get_config_value(
            config_keys=["BETA", "ENABLE_WRITE_DOFILE"],
            env_var="STATA_MCP__ENABLE_WRITE_DOFILE",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def LOGGING_ON(self) -> bool:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "LOGGING_ON"],
            env_var="STATA_MCP__LOGGING_ON",
            default=True,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def LOGGING_CONSOLE_HANDLER_ON(self) -> bool:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "LOGGING_CONSOLE_HANDLER_ON"],
            env_var="STATA_MCP__LOGGING_CONSOLE_HANDLER_ON",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def LOGGING_FILE_HANDLER_ON(self) -> bool:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "LOGGING_FILE_HANDLER_ON"],
            env_var="STATA_MCP__LOGGING_FILE_HANDLER_ON",
            default=True,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def LOG_FILE(self) -> Path:
        log_file = self._get_config_value(
            config_keys=["DEBUG", "logging", "LOG_FILE"],
            env_var="STATA_MCP__LOG_FILE",
            default=self.STATA_MCP_DIRECTORY / "stata_mcp_debug.log",
            converter=self._to_path,
            validator=lambda x: isinstance(x, Path)
        )

        log_file.parent.mkdir(parents=True, exist_ok=True)
        return log_file

    @property
    def MAX_BYTES(self) -> int:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "MAX_BYTES"],
            env_var="STATA_MCP__LOGGING__MAX_BYTES",
            default=10_000_000,
            converter=self._to_int,
            validator=lambda x: isinstance(x, int) and x > 0
        )

    @property
    def BACKUP_COUNT(self) -> int:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "BACKUP_COUNT"],
            env_var="STATA_MCP__LOGGING__BACKUP_COUNT",
            default=5,
            converter=self._to_int,
            validator=lambda x: isinstance(x, int) and x >= 0
        )

    @property
    def SYSTEM_OS(self) -> str:
        system_os = platform.system()
        if system_os not in ["Darwin", "Linux", "Windows"]:
            # Here, if unknown system -> exit.
            sys.exit(f"Unknown System: {system_os}")
        return system_os

    @property
    def IS_UNIX(self) -> bool:
        return self.SYSTEM_OS.lower() in ["darwin", "linux"]

    @property
    def STATA_CLI(self) -> str:
        finder = StataFinder(self.config.get("STATA", {}).get("STATA_CLI", None))
        cli = finder.STATA_CLI
        if cli is None:
            raise StataCLINotFoundError()
        return cli

    @property
    def IS_GUARD(self) -> bool:
        return self._get_config_value(
            config_keys=["SECURITY", "IS_GUARD"],
            env_var="STATA_MCP__IS_GUARD",
            default=True,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def IS_MONITOR(self) -> bool:
        return self._get_config_value(
            config_keys=["MONITOR", "IS_MONITOR"],
            env_var="STATA_MCP__IS_MONITOR",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def WORKING_DIR(self) -> Dict[str, Path]:
        cwd = self._get_config_value(
            config_keys=["PROJECT", "WORKING_DIR"],
            env_var="STATA_MCP__CWD",
            default=None,
            converter=self._to_path,
        )

        if cwd is None:
            # Backward compatibility support
            cwd = os.getenv("STATA_MCP_CWD", Path.cwd())

        cwd = self._to_path(cwd)

        try:
            cwd.mkdir(parents=True, exist_ok=True)
            test_file = cwd / ".stata_mcp_write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            cwd = Path.home() / "Documents"

        output_base_path = cwd / "stata-mcp-folder"
        output_base_path.mkdir(exist_ok=True, parents=True)  # make sure this folder exists

        # sub-based path
        log_base_path = output_base_path / "stata-mcp-log"
        log_base_path.mkdir(exist_ok=True)
        dofile_base_path = output_base_path / "stata-mcp-dofile"
        dofile_base_path.mkdir(exist_ok=True)
        tmp_base_path = output_base_path / "stata-mcp-tmp"
        tmp_base_path.mkdir(exist_ok=True)

        # Config gitignore in STATA_MCP_FOLDER
        if not (GITIGNORE_FILE := output_base_path / ".gitignore").exists():
            with open(GITIGNORE_FILE, "w", encoding="utf-8") as f:
                f.write("*")

        return {
            "cwd": cwd,
            "output_base": output_base_path,
            "log_base": log_base_path,
            "dofile_base": dofile_base_path,
            "tmp_base": tmp_base_path
        }

    @property
    def PROJECT_NAME(self) -> str:
        return self.WORKING_DIR.get("cwd").name

    @property
    def MAX_RAM_MB(self) -> int | None:
        """Get RAM limit for stata_do execution in MB.

        Returns:
            int | None: RAM limit in MB, or None if no limit is configured

        Configuration priority:
            1. Environment variable: STATA_MCP__RAM_LIMIT
            2. Config file: [MONITOR] MAX_RAM_MB
            3. Default: None (no limit)

        Note:
            -1 in config file means no limit (will be converted to None)
        """
        value = self._get_config_value(
            config_keys=["MONITOR", "MAX_RAM_MB"],
            env_var="STATA_MCP__RAM_LIMIT",
            default=-1,
            converter=self._to_int,
            validator=lambda x: isinstance(x, int)
        )

        # Convert -1 to None (no limit)
        if value == -1:
            return None
        return value


if __name__ == "__main__":
    cfg = Config("./config.example.toml")
    print(cfg.IS_DEBUG)
    print(type(cfg.config))
