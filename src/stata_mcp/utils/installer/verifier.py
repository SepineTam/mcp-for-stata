#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : utils/installer/verifier.py

from __future__ import annotations

import json
import sys
import tomllib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from .installer import Installer
from .output import _should_color, _wrap


class VerifyOutcome(str, Enum):
    VERIFIED = "verified"
    WARNING = "warning"
    FAILED = "failed"


@dataclass
class VerifyResult:
    outcome: VerifyOutcome
    exit_code: int
    location: Optional[str] = None
    reason: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


class Verifier:
    def __init__(self, sys_os: "str | None" = None) -> None:
        self.sys_os = sys_os or sys.platform
        self.installer = Installer(sys_os=self.sys_os)

    def verify_client(self, client: str, key: str = "stata-mcp") -> VerifyResult:
        """Verify a built-in client. Path and index come from the installer."""
        try:
            path = self.installer.find_config_path(client)
        except ValueError as exc:
            return VerifyResult(VerifyOutcome.FAILED, 5, reason=str(exc))
        try:
            index = self.installer.find_default_index(client)
        except ValueError as exc:
            return VerifyResult(VerifyOutcome.FAILED, 5, reason=str(exc))
        return self.verify_file(path, index=index, key=key, client=client)

    def verify_file(
        self,
        path: Path,
        index: "str | list[str] | None" = None,
        key: str = "stata-mcp",
        client: "str | None" = None,
    ) -> VerifyResult:
        """Verify an arbitrary JSON or TOML file."""
        path = Path(path)

        if not path.exists():
            return VerifyResult(
                VerifyOutcome.FAILED, 1, reason=f"file not found: {path}"
            )
        if path.is_dir():
            return VerifyResult(
                VerifyOutcome.FAILED,
                1,
                reason=f"path is a directory, expected a file: {path}",
            )
        ext = path.suffix.lower()
        if ext not in {".json", ".toml"}:
            return VerifyResult(
                VerifyOutcome.FAILED,
                1,
                reason=(
                    f"unsupported file extension '{ext}' "
                    "(supported: .json, .toml)"
                ),
            )
        if not path.is_file():
            return VerifyResult(
                VerifyOutcome.FAILED, 1, reason=f"cannot read file: {path}"
            )

        try:
            data = self._load(path, ext)
        except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
            return VerifyResult(
                VerifyOutcome.FAILED,
                3,
                reason=f"failed to parse {path}: {exc}",
            )
        except OSError:
            return VerifyResult(
                VerifyOutcome.FAILED,
                1,
                reason=f"cannot read file: {path}",
            )

        if index is None:
            index = "mcpServers" if ext == ".json" else "mcp_servers"
        if isinstance(index, str):
            keys = [segment for segment in index.split(".") if segment]
        else:
            keys = list(index)

        cursor = data
        for k in keys:
            if not isinstance(cursor, dict) or k not in cursor:
                return VerifyResult(
                    VerifyOutcome.FAILED,
                    2,
                    reason=f"key '{k}' not found in {path}",
                )
            cursor = cursor[k]

        if not cursor:
            return VerifyResult(
                VerifyOutcome.FAILED,
                2,
                reason=f"key '{'.'.join(keys)}' is empty in {path}",
            )
        if not isinstance(cursor, dict):
            return VerifyResult(
                VerifyOutcome.FAILED,
                2,
                reason=(
                    f"key '{'.'.join(keys)}' must be a dict, "
                    f"got {type(cursor).__name__}"
                ),
            )

        if key not in cursor:
            return VerifyResult(
                VerifyOutcome.FAILED,
                2,
                reason=f"entry '{key}' not found in '{'.'.join(keys)}'",
            )
        entry = cursor[key]
        if not isinstance(entry, dict):
            return VerifyResult(
                VerifyOutcome.FAILED,
                4,
                reason=(
                    f"entry '{key}' must be a dict, "
                    f"got {type(entry).__name__}"
                ),
            )

        if "command" not in entry:
            return VerifyResult(
                VerifyOutcome.FAILED,
                4,
                reason=f"missing required field 'command' in entry '{key}'",
            )
        command = entry["command"]
        if not isinstance(command, str):
            return VerifyResult(
                VerifyOutcome.FAILED,
                4,
                reason=(
                    f"field 'command' must be a string, "
                    f"got {type(command).__name__}"
                ),
            )

        warnings: list[str] = []
        if self._is_stdio(entry):
            warnings.extend(self._stdio_warnings(command))

        location = self._format_location(path, index, keys, client)
        outcome = VerifyOutcome.WARNING if warnings else VerifyOutcome.VERIFIED
        return VerifyResult(
            outcome, 0, location=location, warnings=warnings
        )

    def _is_stdio(self, entry: dict) -> bool:
        t = entry.get("type")
        if t in {"http", "sse", "streamable-http", "websocket"}:
            return False
        if "url" in entry:
            return False
        return True

    def _stdio_warnings(self, command: str) -> list[str]:
        warnings: list[str] = []
        lowered = command.lower()
        for needle in ("localhost", "127.0.0.1", "0.0.0.0"):
            if needle in lowered:
                warnings.append(
                    f"warning: localhost-like address '{needle}' in stdio "
                    "command - usually means http config was pasted into stdio"
                )
        for scheme in ("http://", "https://"):
            if command.lower().startswith(scheme):
                warnings.append(
                    f"warning: command starts with '{scheme}' "
                    "- looks like a URL, not an executable"
                )
        return warnings

    def _load(self, path: Path, ext: str):
        if ext == ".json":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        with open(path, "rb") as f:
            return tomllib.load(f)

    def _format_location(
        self,
        path: Path,
        index: "str | list[str] | None",
        keys: list[str],
        client: "str | None",
    ) -> str:
        if client is not None:
            return client
        default_keys = {"mcpServers", "mcp_servers"}
        if isinstance(index, list) and tuple(index) in {("mcpServers",), ("mcp_servers",)}:
            return path.as_posix()
        if index in default_keys:
            return path.as_posix()
        return f"{'.'.join(keys)} in {path.as_posix()}"


def paint_red(text: str) -> str:
    return _paint(text, "31")


def paint_green(text: str) -> str:
    return _paint(text, "32")


def paint_yellow(text: str) -> str:
    return _paint(text, "33")


def _paint(text: str, code: str) -> str:
    if not _should_color(sys.stdout):
        return text
    return _wrap(code, text)
