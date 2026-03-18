#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : stata_help.py

from pathlib import Path

from ..stata import StataHelp
from . import create_runtime_context


def stata_help(cmd: str, config_file: str | Path | None = None) -> str:
    """Return Stata help content for a command."""
    runtime = create_runtime_context(config_file=config_file, require_stata=True)
    help_reader = StataHelp(
        stata_cli=runtime.stata_cli,
        project_tmp_dir=runtime.tmp_base_path,
        cache_dir=runtime.config.STATA_MCP_DIRECTORY / "help",
    )
    return help_reader.help(cmd)
