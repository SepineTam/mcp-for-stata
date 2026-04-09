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
from ._runtime import create_runtime_context


def stata_help(
    cmd: str,
    is_read_log: bool = True,
    enable_smcl: bool = True,
    config_file: str | Path | None = None,
) -> str:
    """Return help content for a Stata command through a one-shot helper."""
    runtime = create_runtime_context(config_file=config_file, require_stata=True)
    _ = (is_read_log, enable_smcl)
    help_reader = StataHelp(
        stata_cli=runtime.stata_cli,
        project_tmp_dir=runtime.tmp_base_path,
        cache_dir=runtime.config.HELP_CACHE_DIR,
        config=runtime.config,
    )
    return help_reader.help(cmd)
