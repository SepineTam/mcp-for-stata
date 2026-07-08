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
from functools import cached_property
from pathlib import Path
from typing import Any, Optional, Union

import tomli_w

from .core.types import StataCLINotFoundError
from .stata import StataFinder


class StataMcpFolder:
    """Lazy-create stata-mcp-folder sub-directories on first property access."""

    def __init__(self, base: Path):
        self._base = base

    def _ensure_base(self):
        self._base.mkdir(exist_ok=True, parents=True)
        gitignore = self._base / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*", encoding="utf-8")

    @cached_property
    def LOG(self) -> Path:
        self._ensure_base()
        p = self._base / "stata-mcp-log"
        p.mkdir(exist_ok=True)
        return p

    @cached_property
    def DO(self) -> Path:
        self._ensure_base()
        p = self._base / "stata-mcp-dofile"
        p.mkdir(exist_ok=True)
        return p

    @cached_property
    def TMP(self) -> Path:
        self._ensure_base()
        p = self._base / "stata-mcp-tmp"
        p.mkdir(exist_ok=True)
        return p

    @property
    def path(self) -> Path:
        """Return base path without triggering directory creation."""
        return self._base


class Config:
    ENV_CONFIG_FILE = "STATA_MCP_CONFIG_FILE"
    USER_CONFIG_NAME = "config.toml"
    PROJECT_CONFIG_PATH = Path(".statamcp") / "config.toml"
    SECURITY_SECTION = "SECURITY"

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        env_config_file = self._clean_string_value(os.getenv(self.ENV_CONFIG_FILE))
        debug_config_file = config_file if config_file is not None else env_config_file
        self.is_debug_config = debug_config_file is not None

        if debug_config_file is not None:
            self.config_file = Path(debug_config_file).expanduser()
            self.user_config_file = self.config_file
            self.project_config_file = None
            self.config_files = (self.config_file,)
        else:
            self.user_config_file = self.STATA_MCP_DIRECTORY / self.USER_CONFIG_NAME
            self.project_config_file = (Path.cwd() / self.PROJECT_CONFIG_PATH).resolve()
            self.config_file = self.user_config_file
            self.config_files = (self.user_config_file, self.project_config_file)

    @cached_property
    def config(self) -> dict[str, Any]:
        if self.is_debug_config:
            return self._read_toml_file(self.config_file)

        user_config = self._read_toml_file(self.user_config_file)
        project_config = self._read_toml_file(self.project_config_file)
        return self._merge_config(user_config, project_config)

    @staticmethod
    def _read_toml_file(config_file: Path | None) -> dict[str, Any]:
        if config_file is None:
            return {}
        try:
            with open(config_file, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    @classmethod
    def _merge_config(
        cls,
        user_config: dict[str, Any],
        project_config: dict[str, Any],
    ) -> dict[str, Any]:
        merged = cls._deep_merge(user_config, project_config)

        user_security = user_config.get(cls.SECURITY_SECTION)
        if isinstance(user_security, dict):
            project_security = project_config.get(cls.SECURITY_SECTION, {})
            if not isinstance(project_security, dict):
                project_security = {}
            merged[cls.SECURITY_SECTION] = cls._deep_merge(project_security, user_security)

        return merged

    @classmethod
    def _deep_merge(
        cls,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            base_value = merged.get(key)
            if isinstance(base_value, dict) and isinstance(value, dict):
                merged[key] = cls._deep_merge(base_value, value)
            else:
                merged[key] = value
        return merged

    def read_config_text(self) -> str:
        """Return raw configuration file content."""
        if self.is_debug_config:
            return self._read_config_file_text(self.config_file)

        parts = []
        for config_file in self.config_files:
            content = self._read_config_file_text(config_file)
            if content:
                parts.append(f"# {config_file}\n{content}")
        return "\n\n".join(parts)

    @staticmethod
    def _read_config_file_text(config_file: Path | None) -> str:
        if config_file is None or not config_file.exists():
            return ""
        return config_file.read_text(encoding="utf-8")

    def _write_toml(self, data: dict) -> None:
        """Write TOML content using tomli_w library."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        content = tomli_w.dumps(data)
        self.config_file.write_text(content, encoding="utf-8")
        # Invalidate cached config so next access re-reads the file
        self.__dict__.pop("config", None)

    def set_stata_cli(self, value: str | None = None) -> str:
        """Persist STATA_CLI to config file and return the saved value."""
        cleaned_value = self._clean_string_value(value)
        if cleaned_value is None:
            cleaned_value = StataFinder(None).STATA_CLI

        if cleaned_value is None:
            raise StataCLINotFoundError()

        updated = self._read_toml_file(self.config_file)
        stata_section = updated.get("STATA", {})
        if not isinstance(stata_section, dict):
            stata_section = {}
        stata_section["STATA_CLI"] = cleaned_value
        updated["STATA"] = stata_section
        self._write_toml(updated)
        return cleaned_value

    def get_stata_cli(self) -> str | None:
        """Return the persisted STATA.STATA_CLI value, or None if not set."""
        return self.config.get("STATA", {}).get("STATA_CLI", None)

    def get_value(self, dot_key: str) -> Any | None:
        """Return a config value by dot notation (Section.Key), or None if not set."""
        if "." not in dot_key:
            raise KeyError(f"Invalid key format '{dot_key}': expected Section.Key")

        section, key = dot_key.split(".", 1)
        section_data = self.config.get(section)
        if not isinstance(section_data, dict):
            return None
        return section_data.get(key, None)

    def edit_value(self, dot_key: str, value: str) -> None:
        """Edit an existing config key using dot notation (Section.Key).

        Raises:
            KeyError: If the section or key does not exist in the config file.
        """
        if "." not in dot_key:
            raise KeyError(f"Invalid key format '{dot_key}': expected Section.Key")

        section, key = dot_key.split(".", 1)
        cleaned_value = self._clean_string_value(value)

        updated = self._read_toml_file(self.config_file)
        if section not in updated:
            raise KeyError(f"Section '{section}' not found")
        if not isinstance(updated[section], dict):
            raise KeyError(f"Section '{section}' is not a table")
        if key not in updated[section]:
            raise KeyError(f"Key '{key}' not found in section '{section}'")

        updated[section][key] = cleaned_value
        self._write_toml(updated)

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
        """Convert only explicit boolean values, failing closed otherwise."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized_value = value.strip().lower()
            if normalized_value == "true":
                return True
            if normalized_value == "false":
                return False
            raise ValueError("Expected 'true' or 'false'.")
        raise TypeError("Expected a boolean or an explicit boolean string.")

    @staticmethod
    def _to_int(value):
        """Convert value to integer."""
        return int(value)

    @staticmethod
    def _to_path(value):
        """Convert value to Path object."""
        return Path(value).expanduser().absolute() if value else None

    @staticmethod
    def _to_str(value):
        return str(value)

    @staticmethod
    def _to_str_tuple(value):
        if isinstance(value, str):
            values = value.split(",")
        elif isinstance(value, (list, tuple, set)):
            values = value
        else:
            raise TypeError("Expected a comma-separated string or string collection.")
        return tuple(str(item).strip() for item in values if str(item).strip())

    @property
    def STATA_MCP_DIRECTORY(self) -> Path:
        base_dir = Path.home() / ".statamcp"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    @property
    def HELP_CACHE_DIR(self) -> Path:
        cache_dir = self.STATA_MCP_DIRECTORY / "help"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

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
    def IS_ASYNC_DO(self) -> bool:
        return self._get_config_value(
            config_keys=["BETA", "IS_ASYNC_DO"],
            env_var="STATA_MCP__IS_ASYNC_DO",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def MAX_ASYNC_DO(self) -> int:
        return self._get_config_value(
            config_keys=["BETA", "MAX_ASYNC_DO"],
            env_var="STATA_MCP__MAX_ASYNC_DO",
            default=3,
            converter=self._to_int,
            validator=lambda x: isinstance(x, int) and x > 0
        )

    @property
    def IS_CACHE_HELP(self) -> bool:
        return self._get_config_value(
            config_keys=["HELP", "IS_CACHE"],
            env_var="STATA_MCP__CACHE_HELP",
            default=True,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool)
        )

    @property
    def IS_SAVE_HELP(self) -> bool:
        return self._get_config_value(
            config_keys=["HELP", "IS_SAVE"],
            env_var="STATA_MCP__SAVE_HELP",
            default=True,
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

    @cached_property
    def STATA_CLI(self) -> str:
        cached = self.config.get("STATA", {}).get("STATA_CLI", None)
        if cached:
            return cached

        finder = StataFinder(None)
        cli = finder.STATA_CLI
        if cli is None:
            raise StataCLINotFoundError()

        # Cache the found path for faster startup next time
        if not cached:
            self.set_stata_cli(cli)
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

    @cached_property
    def ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES(self) -> tuple[str, ...]:
        """Return GitHub repositories explicitly allowed for ado installation."""
        return self._get_config_value(
            config_keys=["SECURITY", "ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES"],
            env_var="STATA_MCP__ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES",
            default=(),
            converter=self._to_str_tuple,
            validator=lambda x: isinstance(x, tuple),
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
    def WORKING_DIR(self) -> Path:
        cwd = self._get_config_value(
            config_keys=["PROJECT", "WORKING_DIR"],
            env_var="STATA_MCP__CWD",
            # Backward compatibility support
            default=os.getenv("STATA_MCP_CWD", Path.cwd()),
            converter=self._to_path,
        )

        try:
            cwd.mkdir(parents=True, exist_ok=True)
            test_file = cwd / ".stata_mcp_write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            cwd = Path.home() / "Documents"

        return cwd

    def _migrate_stata_mcp_folder_warning(self):
        old_folder = self.WORKING_DIR / "stata-mcp-folder"
        if not old_folder.exists():
            return

        migrated_marker = old_folder / ".migrated"
        if migrated_marker.exists():
            return

        migrate_message = (
            "Warning! Stata MCP has migrated from \"$PWD / stata-mcp-folder\" "
            "to \"$PWD / .statamcp\" since v1.16.0. "
            "To keep using the old folder, set environment variable "
            "STATA_MCP__FOLDER_TAG=stata-mcp-folder."
        )
        warning_file = old_folder / "README"
        if not warning_file.exists():
            warning_file.write_text(migrate_message)
        else:
            old_folder_readme = warning_file.read_text()
            if migrate_message not in old_folder_readme:
                warning_file.write_text(migrate_message + "\n" + old_folder_readme)

        migrated_marker.touch()

    @cached_property
    def STATA_MCP_FOLDER_TAG(self) -> str:
        return self._get_config_value(
            config_keys=["PROJECT", "FOLDER_TAG"],
            env_var="STATA_MCP__FOLDER_TAG",
            default=".statamcp",
            converter=self._to_str,
            validator=lambda x: isinstance(x, str)
        )

    @cached_property
    def STATA_MCP_FOLDER(self) -> StataMcpFolder:
        self._migrate_stata_mcp_folder_warning()
        return StataMcpFolder(self.WORKING_DIR / self.STATA_MCP_FOLDER_TAG)

    @property
    def CLEAN_LOG_DAYS(self) -> int:
        return self._get_config_value(
            config_keys=["PROJECT", "CLEAN_LOG_DAYS"],
            env_var="STATA_MCP__CLEAN_LOG_DAYS",
            default=-1,
            converter=self._to_int,
            validator=lambda x: isinstance(x, int),
        )

    @property
    def PROJECT_NAME(self) -> str:
        return self.WORKING_DIR.name

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
