#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : stata_help.py

import os
from pathlib import Path

from ...stata_controller import StataController


class StataHelp:
    def __init__(self, stata_cli: str, project_tmp_dir: Path = None, cache_dir: Path = None):
        self.help_cache_dir = cache_dir or Path.home() / ".statamcp" / "help"
        self.help_cache_dir.mkdir(parents=True, exist_ok=True)
        self.project_tmp_dir = project_tmp_dir
        self.controller = StataController(stata_cli)

    @property
    def IS_SAVE(self) -> bool:
        return os.getenv("STATA_MCP_SAVE_HELP", 'true').lower() == "true"

    @property
    def IS_CACHE(self) -> bool:
        return os.getenv("STATA_MCP_CACHE_HELP", "false").lower() == "true"

    def help(self, cmd: str) -> str:
        saved_help_result = self.load_from_project(cmd)
        cached_help_result = self.load_from_cache(cmd)
        if saved_help_result and self.IS_SAVE:
            return f"Saved result for {cmd}\n" + saved_help_result
        if cached_help_result and self.IS_CACHE:
            return f"Cached result for {cmd}\n" + cached_help_result

        # If no cached help found, get from Stata
        try:
            help_result = self.load_from_stata(cmd)
        except Exception as e:
            return str(e)

        self._cache_and_save(cmd, content=help_result)
        return help_result

    def _cache_and_save(self, cmd: str, content: str) -> None:
        if self.IS_CACHE:
            try:
                with open(self.help_cache_dir / f"help__{cmd}.txt", "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass
        if self.IS_SAVE:
            try:
                with open(self.project_tmp_dir / f"help__{cmd}.txt", "w", encoding="utf-8") as f:
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
            raise Exception("No help found for the command in Stata ado locally: " + cmd)

    def check_command_exist_with_help(self, cmd: str) -> bool:
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
