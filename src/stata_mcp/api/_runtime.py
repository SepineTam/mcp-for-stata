#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : _runtime.py

from dataclasses import dataclass
from pathlib import Path

from ..config import Config


@dataclass(frozen=True)
class RuntimeContext:
    config: Config
    output_base_path: Path
    log_base_path: Path
    dofile_base_path: Path
    tmp_base_path: Path
    cwd: Path
    stata_cli: str | None
    is_unix: bool


def create_runtime_context(
    config_file: str | Path | None = None,
    *,
    require_stata: bool = False,
) -> RuntimeContext:
    config = Config(config_file=config_file)
    stata_cli = config.STATA_CLI if require_stata else None
    return RuntimeContext(
        config=config,
        output_base_path=config.STATA_MCP_FOLDER.path,
        log_base_path=config.STATA_MCP_FOLDER.LOG,
        dofile_base_path=config.STATA_MCP_FOLDER.DO,
        tmp_base_path=config.STATA_MCP_FOLDER.TMP,
        cwd=config.WORKING_DIR,
        stata_cli=stata_cli,
        is_unix=config.IS_UNIX,
    )
