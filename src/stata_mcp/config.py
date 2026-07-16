#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : config.py

import logging
import os
import platform
import re
import sys
import tomllib
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Literal, Optional, Union

import tomli_w

from .core.types import StataCLINotFoundError
from .stata import StataFinder

logger = logging.getLogger(__name__)

ToolContext = Literal["api", "cli", "mcp"]
DATA_INFO_METRICS = (
    "obs",
    "mean",
    "stderr",
    "min",
    "max",
    "med",
    "q1",
    "q3",
    "skewness",
    "kurtosis",
)
DEFAULT_DATA_INFO_METRICS = ("obs", "mean", "stderr", "min", "max")
LEGACY_DATA_INFO_HEADER_PATTERN = re.compile(
    r"^(?P<indent>[ \t]*)"
    r"\[(?P<quote>[\"']?)data_info(?P=quote)\]"
    r"(?P<suffix>[ \t]*(?:#[^\r\n]*)?)"
    r"(?P<carriage_return>\r?)$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class HelpToolConfig:
    """Resolved help settings for one invocation context."""

    is_cache: bool
    is_save: bool


@dataclass(frozen=True)
class DataInfoToolConfig:
    """Resolved data-info settings for one invocation context."""

    is_cache: bool
    metrics: tuple[str, ...]
    string_keep_number: int
    decimal_places: int
    hash_length: int
    heads: int


class StataMcpFolder:
    """Lazy-create stata-mcp-folder sub-directories on first property access."""

    def __init__(self, base: Path):
        self._base = base

    def _ensure_base(self):
        self._base.mkdir(exist_ok=True, parents=True)
        gitignore = self._base / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*", encoding="utf-8")
            logger.info("Ensured stata-mcp folder at %s; wrote .gitignore", self._base)

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
    SYSTEM_CONFIG_FILE = Path("/etc/statamcp/config.toml")
    SECURITY_SECTION = "SECURITY"

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        env_config_file = self._clean_string_value(os.getenv(self.ENV_CONFIG_FILE))
        debug_config_file = config_file if config_file is not None else env_config_file
        self.is_debug_config = debug_config_file is not None
        self.system_config_file = (
            self.SYSTEM_CONFIG_FILE if platform.system() == "Linux" else None
        )

        if debug_config_file is not None:
            self.config_file = Path(debug_config_file).expanduser()
            self.user_config_file = self.config_file
            self.project_config_file = None
            self.config_files = tuple(
                path
                for path in (self.config_file, self.system_config_file)
                if path is not None
            )
        else:
            self.user_config_file = self.STATA_MCP_DIRECTORY / self.USER_CONFIG_NAME
            self.project_config_file = (Path.cwd() / self.PROJECT_CONFIG_PATH).resolve()
            self.config_file = self.user_config_file
            self.config_files = tuple(
                path
                for path in (
                    self.user_config_file,
                    self.project_config_file,
                    self.system_config_file,
                )
                if path is not None
            )

        for active_config_file in dict.fromkeys(self.config_files):
            self._migrate_legacy_data_info_section(active_config_file)

    @classmethod
    def _migrate_legacy_data_info_section(cls, config_file: Path) -> None:
        """Rename `[data_info]` without making configuration loading fail."""
        try:
            target_file = config_file.resolve(strict=True)
            content = target_file.read_bytes().decode("utf-8")
            config_data = tomllib.loads(content)
            legacy_section = config_data.get("data_info")
            if not isinstance(legacy_section, dict):
                return
            if "DATA_INFO" in config_data:
                logger.warning(
                    "Could not automatically migrate legacy [data_info] in %s: "
                    "both [data_info] and [DATA_INFO] exist; keeping both to "
                    "avoid overwriting configuration.",
                    config_file,
                )
                return

            migrated_content, replacement_count = cls._replace_legacy_data_info_header(
                content
            )
            if replacement_count != 1:
                logger.warning(
                    "Could not automatically migrate legacy [data_info] in %s: "
                    "the section is not represented by a standalone TOML table "
                    "header; keeping the compatibility fallback.",
                    config_file,
                )
                return

            cls._replace_config_text(
                target_file,
                migrated_content,
                expected_content=content,
            )
            logger.info(
                "Migrated legacy [data_info] to [DATA_INFO] in %s.",
                config_file,
            )
        except FileNotFoundError:
            return
        except PermissionError as error:
            logger.warning(
                "Could not migrate legacy [data_info] to [DATA_INFO] in %s: "
                "permission denied (%s). The legacy section remains supported.",
                config_file,
                error,
            )
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            logger.warning(
                "Could not migrate legacy [data_info] to [DATA_INFO] in %s: "
                "the config file could not be parsed (%s).",
                config_file,
                error,
            )
        except OSError as error:
            logger.warning(
                "Could not migrate legacy [data_info] to [DATA_INFO] in %s: "
                "filesystem error (%s). The legacy section remains supported.",
                config_file,
                error,
            )
        except Exception as error:
            logger.warning(
                "Could not migrate legacy [data_info] to [DATA_INFO] in %s: "
                "unexpected error %s (%s). The legacy section remains supported.",
                config_file,
                type(error).__name__,
                error,
            )

    @classmethod
    def _replace_legacy_data_info_header(cls, content: str) -> tuple[str, int]:
        """Replace a real table header while ignoring TOML multiline strings."""
        migrated_lines: list[str] = []
        multiline_delimiter: str | None = None
        replacement_count = 0

        for line in content.splitlines(keepends=True):
            line_body = line[:-1] if line.endswith("\n") else line
            line_ending = "\n" if line.endswith("\n") else ""
            migrated_line_body = line_body

            if multiline_delimiter is None and replacement_count == 0:
                match = LEGACY_DATA_INFO_HEADER_PATTERN.fullmatch(line_body)
                if match is not None:
                    quote = match.group("quote")
                    migrated_line_body = (
                        f"{match.group('indent')}[{quote}DATA_INFO{quote}]"
                        f"{match.group('suffix')}"
                        f"{match.group('carriage_return')}"
                    )
                    replacement_count = 1

            multiline_delimiter = cls._toml_multiline_delimiter_after_line(
                migrated_line_body,
                multiline_delimiter,
            )
            migrated_lines.append(migrated_line_body + line_ending)

        return "".join(migrated_lines), replacement_count

    @staticmethod
    def _toml_multiline_delimiter_after_line(
        line: str,
        multiline_delimiter: str | None,
    ) -> str | None:
        """Track whether the next TOML line starts inside a multiline string."""
        index = 0
        while index < len(line):
            if multiline_delimiter is not None:
                delimiter_index = line.find(multiline_delimiter, index)
                if delimiter_index < 0:
                    return multiline_delimiter
                if multiline_delimiter == '"""':
                    preceding_backslashes = 0
                    cursor = delimiter_index - 1
                    while cursor >= 0 and line[cursor] == "\\":
                        preceding_backslashes += 1
                        cursor -= 1
                    if preceding_backslashes % 2 == 1:
                        index = delimiter_index + len(multiline_delimiter)
                        continue
                index = delimiter_index + len(multiline_delimiter)
                multiline_delimiter = None
                continue

            if line[index] == "#":
                break
            if line.startswith('"""', index):
                multiline_delimiter = '"""'
                index += 3
                continue
            if line.startswith("'''", index):
                multiline_delimiter = "'''"
                index += 3
                continue
            if line[index] == '"':
                index += 1
                while index < len(line):
                    if line[index] == "\\":
                        index += 2
                        continue
                    if line[index] == '"':
                        index += 1
                        break
                    index += 1
                continue
            if line[index] == "'":
                closing_quote = line.find("'", index + 1)
                index = len(line) if closing_quote < 0 else closing_quote + 1
                continue
            index += 1

        return multiline_delimiter

    @staticmethod
    def _replace_config_text(
        config_file: Path,
        content: str,
        *,
        expected_content: str | None = None,
    ) -> None:
        """Patch equal-length text in place so all file metadata stays attached."""
        replacement_bytes = content.encode("utf-8")
        expected_bytes = (
            config_file.read_bytes()
            if expected_content is None
            else expected_content.encode("utf-8")
        )
        if len(replacement_bytes) != len(expected_bytes):
            raise ValueError("config migration must preserve the file length")

        difference_indices = [
            index
            for index, (original_byte, replacement_byte) in enumerate(
                zip(expected_bytes, replacement_bytes)
            )
            if original_byte != replacement_byte
        ]
        if not difference_indices:
            return
        patch_start = difference_indices[0]
        patch_end = difference_indices[-1] + 1
        original_patch = expected_bytes[patch_start:patch_end]
        replacement_patch = replacement_bytes[patch_start:patch_end]
        if original_patch != b"data_info" or replacement_patch != b"DATA_INFO":
            raise ValueError("config migration may only rename the data-info header")

        with open(config_file, "r+b") as config_stream:
            current_bytes = config_stream.read()
            if current_bytes == replacement_bytes:
                return
            if current_bytes != expected_bytes:
                raise OSError("config file changed while migration was in progress")

            try:
                config_stream.seek(patch_start)
                written_bytes = config_stream.write(replacement_patch)
                if written_bytes != len(replacement_patch):
                    raise OSError("config migration wrote an incomplete header")
                config_stream.flush()
                os.fsync(config_stream.fileno())
                config_stream.seek(0)
                if config_stream.read() != replacement_bytes:
                    raise OSError("config migration verification failed")
            except Exception as write_error:
                try:
                    config_stream.seek(patch_start)
                    rollback_bytes = config_stream.write(original_patch)
                    if rollback_bytes != len(original_patch):
                        raise OSError("config migration rollback was incomplete")
                    config_stream.flush()
                    os.fsync(config_stream.fileno())
                    config_stream.seek(0)
                    if config_stream.read() != expected_bytes:
                        raise OSError("config migration rollback verification failed")
                except Exception as rollback_error:
                    raise OSError(
                        "config migration failed "
                        f"({write_error}); rollback also failed ({rollback_error})"
                    ) from write_error
                raise

    @cached_property
    def config(self) -> dict[str, Any]:
        system_config = self._read_toml_file(self.system_config_file)
        if self.is_debug_config:
            debug_config = self._read_toml_file(self.config_file)
            return self._deep_merge(debug_config, system_config)

        user_config = self._read_toml_file(self.user_config_file)
        project_config = self._read_toml_file(self.project_config_file)
        return self._merge_config(user_config, project_config, system_config)

    @staticmethod
    def _read_toml_file(config_file: Path | None) -> dict[str, Any]:
        if config_file is None:
            return {}
        try:
            with open(config_file, "rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            return {}
        except Exception as exc:
            logger.warning("Could not read config file %s: %s", config_file, exc)
            return {}

    @classmethod
    def _merge_config(
        cls,
        user_config: dict[str, Any],
        project_config: dict[str, Any],
        system_config: dict[str, Any],
    ) -> dict[str, Any]:
        merged = cls._deep_merge(user_config, project_config)
        user_security = user_config.get(cls.SECURITY_SECTION)
        if isinstance(user_security, dict):
            project_security = project_config.get(cls.SECURITY_SECTION, {})
            if not isinstance(project_security, dict):
                project_security = {}
            merged[cls.SECURITY_SECTION] = cls._deep_merge(
                project_security, user_security
            )
        return cls._deep_merge(merged, system_config)

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

    def _get_raw_config_value(
        self, config_data: dict[str, Any], config_keys: list[str]
    ) -> Any | None:
        config_dict = config_data
        for key in config_keys[:-1]:
            config_dict = config_dict.get(key, {})
            if not isinstance(config_dict, dict):
                return None

        if isinstance(config_dict, dict):
            value = config_dict.get(config_keys[-1], None)
            return self._clean_string_value(value)
        return None

    def _write_toml(self, data: dict) -> None:
        """Write TOML content using tomli_w library."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        content = tomli_w.dumps(data)
        self.config_file.write_text(content, encoding="utf-8")
        logger.info("Wrote config file %s", self.config_file)
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
        logger.info("Set STATA.STATA_CLI = %s in %s", cleaned_value, self.config_file)
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
        logger.info(
            "Updated config %s = %s in %s", dot_key, cleaned_value, self.config_file
        )

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

    def _get_config_value(
        self,
        config_keys: list[str],
        env_var: str,
        default,
        converter=None,
        validator=None,
    ):
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
        return self._get_config_value_from_paths(
            config_paths=[config_keys],
            env_vars=[env_var] if env_var else [],
            default=default,
            converter=converter,
            validator=validator,
        )

    def _get_config_value_from_paths(
        self,
        config_paths: list[list[str]],
        env_vars: list[str],
        default,
        converter=None,
        validator=None,
    ):
        """Resolve ordered config paths without mixing source and specificity.

        Source precedence is system configuration, environment, merged runtime
        configuration, then the built-in default. Within each source, paths and
        environment aliases are checked from most specific to least specific.
        """
        system_config = self._read_toml_file(self.system_config_file)
        value = self._first_config_value(system_config, config_paths)

        if value is None:
            value = self._first_environment_value(env_vars)

        if value is None:
            for runtime_config in self._runtime_config_sources(config_paths):
                value = self._first_config_value(runtime_config, config_paths)
                if value is not None:
                    break

        if value is None:
            return default

        if converter is not None:
            try:
                value = converter(value)
            except (ValueError, TypeError):
                return default

        if validator is not None and not validator(value):
            return default

        return value

    def _runtime_config_sources(
        self,
        config_paths: list[list[str]],
    ) -> tuple[dict[str, Any], ...]:
        """Return runtime TOML sources in authority order.

        Context specificity must only compare keys from the same source.
        Otherwise a specific user key could incorrectly outrank a generic
        project key. Security keeps its deliberate user-before-project order.
        """
        if self.is_debug_config:
            return (self._read_toml_file(self.config_file),)

        is_security_value = all(
            config_path and config_path[0] == self.SECURITY_SECTION
            for config_path in config_paths
        )
        user_config = self._read_toml_file(self.user_config_file)
        project_config = self._read_toml_file(self.project_config_file)
        if is_security_value:
            return user_config, project_config
        return project_config, user_config

    def _first_config_value(
        self,
        config_data: dict[str, Any],
        config_paths: list[list[str]],
    ) -> Any | None:
        for config_path in config_paths:
            value = self._get_raw_config_value(config_data, config_path)
            if value is not None:
                return value
        return None

    def _first_environment_value(self, env_vars: list[str]) -> Any | None:
        for env_var in env_vars:
            value = self._clean_string_value(os.getenv(env_var))
            if value is not None:
                return value
        return None

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

    @staticmethod
    def _to_metrics(value) -> tuple[str, ...]:
        metrics = Config._to_str_tuple(value)
        normalized_metrics = tuple(metric.lower() for metric in metrics)
        if not normalized_metrics:
            raise ValueError("At least one data-info metric is required.")
        if any(metric not in DATA_INFO_METRICS for metric in normalized_metrics):
            raise ValueError("Unsupported data-info metric.")
        return tuple(dict.fromkeys(normalized_metrics))

    @staticmethod
    def _normalize_tool_context(context: ToolContext | None) -> ToolContext:
        normalized_context = "api" if context is None else str(context).lower()
        if normalized_context not in {"api", "cli", "mcp"}:
            raise ValueError(f"Unsupported tool context: {context}")
        return normalized_context  # type: ignore[return-value]

    @classmethod
    def _tool_config_paths(
        cls,
        context: ToolContext | None,
        tool_name: str,
        key: str,
        generic_sections: tuple[str, ...],
    ) -> list[list[str]]:
        normalized_context = cls._normalize_tool_context(context)
        config_paths: list[list[str]] = []
        if normalized_context in {"mcp", "cli"}:
            config_paths.append(
                [normalized_context.upper(), "TOOLS", tool_name.upper(), key]
            )
        config_paths.extend([[section, key] for section in generic_sections])
        return config_paths

    @classmethod
    def _tool_environment_vars(
        cls,
        context: ToolContext | None,
        tool_name: str,
        key: str,
        legacy_aliases: tuple[str, ...] = (),
    ) -> list[str]:
        normalized_context = cls._normalize_tool_context(context)
        env_vars: list[str] = []
        if normalized_context in {"mcp", "cli"}:
            env_vars.append(
                f"STATA_MCP__{normalized_context.upper()}__TOOLS__"
                f"{tool_name.upper()}__{key.upper()}"
            )
        env_vars.append(f"STATA_MCP__{tool_name.upper()}__{key.upper()}")
        env_vars.extend(legacy_aliases)
        return env_vars

    def _get_tool_config_value(
        self,
        *,
        context: ToolContext | None,
        tool_name: str,
        key: str,
        generic_sections: tuple[str, ...],
        default,
        converter=None,
        validator=None,
        legacy_env_vars: tuple[str, ...] = (),
    ):
        return self._get_config_value_from_paths(
            config_paths=self._tool_config_paths(
                context,
                tool_name,
                key,
                generic_sections,
            ),
            env_vars=self._tool_environment_vars(
                context,
                tool_name,
                key,
                legacy_env_vars,
            ),
            default=default,
            converter=converter,
            validator=validator,
        )

    def get_help_config(self, context: ToolContext | None = None) -> HelpToolConfig:
        """Return help settings with context-specific values before `[HELP]`."""
        is_cache = self._get_tool_config_value(
            context=context,
            tool_name="HELP",
            key="IS_CACHE",
            generic_sections=("HELP",),
            legacy_env_vars=("STATA_MCP__CACHE_HELP",),
            default=True,
            converter=self._to_bool,
            validator=lambda value: isinstance(value, bool),
        )
        is_save = self._get_tool_config_value(
            context=context,
            tool_name="HELP",
            key="IS_SAVE",
            generic_sections=("HELP",),
            legacy_env_vars=("STATA_MCP__SAVE_HELP",),
            default=True,
            converter=self._to_bool,
            validator=lambda value: isinstance(value, bool),
        )
        return HelpToolConfig(is_cache=is_cache, is_save=is_save)

    def get_data_info_config(
        self,
        context: ToolContext | None = None,
    ) -> DataInfoToolConfig:
        """Return validated data-info settings for API, CLI, or MCP usage."""
        normalized_context = self._normalize_tool_context(context)
        generic_sections = ("DATA_INFO", "data_info")
        default_heads = 5 if normalized_context == "cli" else 0

        is_cache = self._get_tool_config_value(
            context=normalized_context,
            tool_name="DATA_INFO",
            key="is_cache",
            generic_sections=generic_sections,
            legacy_env_vars=(
                "STATA_MCP__DATA_INFO_IS_CACHE",
                "STATA_MCP_DATA_INFO_IS_CACHE",
            ),
            default=True,
            converter=self._to_bool,
            validator=lambda value: isinstance(value, bool),
        )
        metrics = self._get_tool_config_value(
            context=normalized_context,
            tool_name="DATA_INFO",
            key="metrics",
            generic_sections=generic_sections,
            default=DEFAULT_DATA_INFO_METRICS,
            converter=self._to_metrics,
            validator=lambda value: isinstance(value, tuple),
        )
        string_keep_number = self._get_tool_config_value(
            context=normalized_context,
            tool_name="DATA_INFO",
            key="string_keep_number",
            generic_sections=generic_sections,
            legacy_env_vars=("STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER",),
            default=10,
            converter=self._to_int,
            validator=lambda value: isinstance(value, int) and value >= 0,
        )
        decimal_places = self._get_tool_config_value(
            context=normalized_context,
            tool_name="DATA_INFO",
            key="decimal_places",
            generic_sections=generic_sections,
            legacy_env_vars=("STATA_MCP_DATA_INFO_DECIMAL_PLACES",),
            default=3,
            converter=self._to_int,
            validator=lambda value: isinstance(value, int) and value >= 0,
        )
        hash_length = self._get_tool_config_value(
            context=normalized_context,
            tool_name="DATA_INFO",
            key="hash_length",
            generic_sections=generic_sections,
            legacy_env_vars=("STATA_MCP_DATA_INFO_HASH_LENGTH",),
            default=12,
            converter=self._to_int,
            validator=lambda value: isinstance(value, int) and 1 <= value <= 32,
        )
        heads = self._get_tool_config_value(
            context=normalized_context,
            tool_name="DATA_INFO",
            key="heads",
            generic_sections=generic_sections,
            default=default_heads,
            converter=self._to_int,
            validator=lambda value: isinstance(value, int),
        )
        return DataInfoToolConfig(
            is_cache=is_cache,
            metrics=metrics,
            string_keep_number=string_keep_number,
            decimal_places=decimal_places,
            hash_length=hash_length,
            heads=heads,
        )

    def is_tool_enabled(
        self,
        context: ToolContext,
        tool_name: str,
        *,
        default: bool = True,
    ) -> bool:
        """Return a context tool switch without bypassing profile restrictions."""
        normalized_context = self._normalize_tool_context(context)
        if normalized_context == "api":
            return default
        normalized_tool_name = tool_name.upper()
        return self._get_config_value_from_paths(
            config_paths=[
                [
                    normalized_context.upper(),
                    "TOOLS",
                    f"ENABLE_{normalized_tool_name}",
                ]
            ],
            env_vars=[
                f"STATA_MCP__{normalized_context.upper()}__TOOLS__"
                f"ENABLE_{normalized_tool_name}"
            ],
            default=default,
            converter=self._to_bool,
            validator=lambda value: isinstance(value, bool),
        )

    @cached_property
    def ENABLE_DATA_INFO_URL_GUARD(self) -> bool:
        return self._get_config_value(
            config_keys=["BETA", "enable_data_info_url_guard"],
            env_var="",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

    @cached_property
    def DATA_INFO_ALLOWED_URL_DOMAINS(self) -> tuple[str, ...]:
        return self._get_config_value(
            config_keys=["BETA", "data_info_allowed_url_domains"],
            env_var="",
            default=(),
            converter=self._to_str_tuple,
            validator=lambda x: isinstance(x, tuple),
        )

    @cached_property
    def DATA_INFO_IS_CACHE(self) -> bool:
        return self.get_data_info_config("api").is_cache

    @cached_property
    def ENABLE_STRUCTURED_LOG(self) -> bool:
        return self._get_config_value(
            config_keys=["BETA", "enable_structured_log"],
            env_var="",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

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
            validator=lambda x: isinstance(x, bool),
        )

    @property
    def IS_ASYNC_DO(self) -> bool:
        return self._get_config_value(
            config_keys=["BETA", "IS_ASYNC_DO"],
            env_var="STATA_MCP__IS_ASYNC_DO",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

    @property
    def MAX_ASYNC_DO(self) -> int:
        return self._get_config_value(
            config_keys=["BETA", "MAX_ASYNC_DO"],
            env_var="STATA_MCP__MAX_ASYNC_DO",
            default=3,
            converter=self._to_int,
            validator=lambda x: isinstance(x, int) and x > 0,
        )

    @property
    def IS_CACHE_HELP(self) -> bool:
        return self.get_help_config("api").is_cache

    @property
    def IS_SAVE_HELP(self) -> bool:
        return self.get_help_config("api").is_save

    @property
    def LOGGING_ON(self) -> bool:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "LOGGING_ON"],
            env_var="STATA_MCP__LOGGING_ON",
            default=True,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

    @property
    def LOGGING_CONSOLE_HANDLER_ON(self) -> bool:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "LOGGING_CONSOLE_HANDLER_ON"],
            env_var="STATA_MCP__LOGGING_CONSOLE_HANDLER_ON",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

    @property
    def LOGGING_FILE_HANDLER_ON(self) -> bool:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "LOGGING_FILE_HANDLER_ON"],
            env_var="STATA_MCP__LOGGING_FILE_HANDLER_ON",
            default=True,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

    @property
    def LOG_FILE(self) -> Path:
        log_file = self._get_config_value(
            config_keys=["DEBUG", "logging", "LOG_FILE"],
            env_var="STATA_MCP__LOG_FILE",
            default=self.STATA_MCP_DIRECTORY / "stata_mcp_debug.log",
            converter=self._to_path,
            validator=lambda x: isinstance(x, Path),
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
            validator=lambda x: isinstance(x, int) and x > 0,
        )

    @property
    def BACKUP_COUNT(self) -> int:
        return self._get_config_value(
            config_keys=["DEBUG", "logging", "BACKUP_COUNT"],
            env_var="STATA_MCP__LOGGING__BACKUP_COUNT",
            default=5,
            converter=self._to_int,
            validator=lambda x: isinstance(x, int) and x >= 0,
        )

    @property
    def SYSTEM_OS(self) -> str:
        system_os = platform.system()
        if system_os not in ["Darwin", "Linux", "Windows"]:
            # Here, if unknown system -> exit.
            logger.critical("Unknown/unsupported operating system: %s", system_os)
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
            validator=lambda x: isinstance(x, bool),
        )

    @cached_property
    def STRICT_READ_LOG_BOUNDARY(self) -> bool:
        return self._get_config_value(
            config_keys=["SECURITY", "strict_read_log_boundary"],
            env_var="",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

    @cached_property
    def STRICT_DATA_INFO_LOCAL_BOUNDARY(self) -> bool:
        return self._get_config_value(
            config_keys=["SECURITY", "strict_data_info_local_boundary"],
            env_var="",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
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

    @cached_property
    def ENABLE_DATA_COMMAND_PATH_GUARD(self) -> bool:
        return self._get_config_value(
            config_keys=["SECURITY", "enable_data_command_path_guard"],
            env_var="STATA_MCP__ENABLE_DATA_COMMAND_PATH_GUARD",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
        )

    @cached_property
    def ADDITIONAL_ALLOWED_DIRS(self) -> tuple[Path, ...]:
        """Return additional security roots resolved against `WORKING_DIR`."""
        configured_paths = self._get_config_value(
            config_keys=["SECURITY", "ADDITIONAL_ALLOWED_DIRS"],
            env_var="STATA_MCP__ADDITIONAL_ALLOWED_DIRS",
            default=(),
            converter=self._to_str_tuple,
            validator=lambda value: isinstance(value, tuple),
        )
        resolved_paths = []
        for configured_path in configured_paths:
            path = Path(configured_path).expanduser()
            if not path.is_absolute():
                path = self.WORKING_DIR / path
            resolved_paths.append(path.resolve())
        return tuple(dict.fromkeys(resolved_paths))

    @property
    def IS_MONITOR(self) -> bool:
        return self._get_config_value(
            config_keys=["MONITOR", "IS_MONITOR"],
            env_var="STATA_MCP__IS_MONITOR",
            default=False,
            converter=self._to_bool,
            validator=lambda x: isinstance(x, bool),
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
            fallback = Path.home() / "Documents"
            logger.warning(
                "WORKING_DIR %s is not writable; falling back to %s", cwd, fallback
            )
            cwd = fallback

        return cwd

    def _migrate_stata_mcp_folder_warning(self):
        old_folder = self.WORKING_DIR / "stata-mcp-folder"
        if not old_folder.exists():
            return

        migrated_marker = old_folder / ".migrated"
        if migrated_marker.exists():
            return

        migrate_message = (
            'Warning! Stata MCP has migrated from "$PWD / stata-mcp-folder" '
            'to "$PWD / .statamcp" since v1.16.0. '
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
        logger.info(
            "Migrated old stata-mcp-folder to new layout; wrote README at %s",
            warning_file,
        )

    @cached_property
    def STATA_MCP_FOLDER_TAG(self) -> str:
        return self._get_config_value(
            config_keys=["PROJECT", "FOLDER_TAG"],
            env_var="STATA_MCP__FOLDER_TAG",
            default=".statamcp",
            converter=self._to_str,
            validator=lambda x: isinstance(x, str),
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
            validator=lambda x: isinstance(x, int),
        )

        # Convert -1 to None (no limit)
        if value == -1:
            return None
        return value


if __name__ == "__main__":
    cfg = Config("./config.example.toml")
    print(cfg.IS_DEBUG)
    print(type(cfg.config))
