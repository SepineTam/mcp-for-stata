#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : stata_help.py

from pathlib import Path
from typing import Any, Dict

from ..stata import StataHelp
from ._runtime import create_runtime_context
from .stata_do import stata_do
from .write_dofile import write_dofile


def stata_help(
    cmd: str,
    is_read_log: bool = True,
    enable_smcl: bool = True,
    config_file: str | Path | None = None,
) -> str | Dict[str, Any]:
    """Return Stata help content or execute help through a generated do-file."""
    runtime = create_runtime_context(config_file=config_file, require_stata=True)

    if is_read_log:
        dofile_path = write_dofile(f"help {cmd}", config_file=config_file)
        return stata_do(
            dofile_path=dofile_path,
            is_read_log=is_read_log,
            enable_smcl=enable_smcl,
            config_file=config_file,
        )

    help_reader = StataHelp(
        stata_cli=runtime.stata_cli,
        project_tmp_dir=runtime.tmp_base_path,
        cache_dir=runtime.config.STATA_MCP_DIRECTORY / "help",
    )
    return help_reader.help(cmd)
