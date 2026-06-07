#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : stata_help.py

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ...stata_controller import StataController

if TYPE_CHECKING:
    from ...config import Config


STATA_COMMAND_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class StataHelp:
    def __init__(
        self,
        stata_cli: str,
        project_tmp_dir: Path | None = None,
        cache_dir: Path | None = None,
        config: "Config | None" = None,
    ):
        self._config = config
        self.help_cache_dir = cache_dir or (
            config.HELP_CACHE_DIR if config else Path.home() / ".statamcp" / "help"
        )
        self.help_cache_dir.mkdir(parents=True, exist_ok=True)
        self.project_tmp_dir = project_tmp_dir
        if self.project_tmp_dir is not None:
            self.project_tmp_dir.mkdir(parents=True, exist_ok=True)
        self.controller = StataController(stata_cli)

    @property
    def IS_SAVE(self) -> bool:
        if self._config:
            return self._config.IS_SAVE_HELP
        return True

    @property
    def IS_CACHE(self) -> bool:
        if self._config:
            return self._config.IS_CACHE_HELP
        return False

    def help(self, cmd: str, replace: bool = False) -> str:
        cmd = self._validate_command_name(cmd)

        if not replace:
            cached_help_result = self._load_latest_cached_help(cmd)
            if cached_help_result is not None:
                cache_label, help_content = cached_help_result
                return f"{cache_label} result for {cmd}\n" + help_content

        # If no cached help found, get from Stata
        try:
            help_result = self.load_from_stata(cmd)
        except Exception as e:
            return str(e)

        self._cache_and_save(cmd, content=help_result, force=replace)
        return help_result

    def _load_latest_cached_help(self, cmd: str) -> tuple[str, str] | None:
        """Return the newest help result from the enabled cache locations."""
        candidates: list[tuple[int, int, str, Path]] = []

        if self.IS_SAVE and self.project_tmp_dir is not None:
            project_help_file = self.project_tmp_dir / f"help__{cmd}.txt"
            self._add_cache_candidate(
                candidates,
                path=project_help_file,
                priority=1,
                label="Saved",
            )

        if self.IS_CACHE:
            cached_help_file = self.help_cache_dir / f"help__{cmd}.txt"
            self._add_cache_candidate(
                candidates,
                path=cached_help_file,
                priority=0,
                label="Cached",
            )

        for _, _, label, path in sorted(candidates, reverse=True):
            content = self._load_from_file(path)
            if content:
                return label, content
        return None

    @staticmethod
    def _add_cache_candidate(
        candidates: list[tuple[int, int, str, Path]],
        *,
        path: Path,
        priority: int,
        label: str,
    ) -> None:
        """Add an existing cache file to the freshness-ordered candidate list."""
        try:
            modified_at = path.stat().st_mtime_ns
        except FileNotFoundError:
            return
        candidates.append((modified_at, priority, label, path))

    @staticmethod
    def _validate_command_name(cmd: str) -> str:
        """Return a normalized Stata command name or reject unsafe input."""
        if not isinstance(cmd, str):
            raise TypeError("Stata command name must be a string.")

        command = cmd.strip()
        if not STATA_COMMAND_NAME_PATTERN.fullmatch(command):
            raise ValueError(
                "Invalid Stata command name. "
                "Only letters, numbers, and underscores are allowed."
            )
        return command

    def _cache_and_save(self, cmd: str, content: str, force: bool = False) -> None:
        if force or self.IS_CACHE:
            try:
                with open(
                    self.help_cache_dir / f"help__{cmd}.txt", "w", encoding="utf-8"
                ) as f:
                    f.write(content)
            except Exception:
                pass
        if (force or self.IS_SAVE) and self.project_tmp_dir is not None:
            try:
                with open(
                    self.project_tmp_dir / f"help__{cmd}.txt", "w", encoding="utf-8"
                ) as f:
                    f.write(content)
            except Exception:
                pass
        return None

    @staticmethod
    def _load_from_file(file_path: Path) -> str | None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def load_from_cache(self, cmd: str):
        cached_cmd_help_file = self.help_cache_dir / f"help__{cmd}.txt"
        return self._load_from_file(cached_cmd_help_file)

    def load_from_project(self, cmd: str):
        if self.project_tmp_dir is None:
            return None
        project_help_file = self.project_tmp_dir / f"help__{cmd}.txt"
        return self._load_from_file(project_help_file)

    def load_from_stata(self, cmd: str):
        std_error_msg = (
            f"help {cmd}\r\n"
            f"help for {cmd} not found\r\n"
            f"try help contents or search {cmd}"
        )
        help_result = self.controller.run(f"help {cmd}")

        if help_result != std_error_msg:
            return help_result
        else:
            raise Exception(
                "No help found for the command in Stata ado locally: " + cmd
            )

    def check_command_exist_with_help(self, cmd: str) -> bool:
        cmd = self._validate_command_name(cmd)

        std_error_msg = (
            f"help {cmd}\r\n"
            f"help for {cmd} not found\r\n"
            f"try help contents or search {cmd}"
        )
        help_result = self.controller.run(f"help {cmd}")
        if help_result != std_error_msg:
            return True
        else:
            return False
