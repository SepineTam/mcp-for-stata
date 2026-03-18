#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : __init__.py

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
    working_dir = config.WORKING_DIR
    stata_cli = config.STATA_CLI if require_stata else None
    return RuntimeContext(
        config=config,
        output_base_path=working_dir["output_base"],
        log_base_path=working_dir["log_base"],
        dofile_base_path=working_dir["dofile_base"],
        tmp_base_path=working_dir["tmp_base"],
        cwd=working_dir["cwd"],
        stata_cli=stata_cli,
        is_unix=config.IS_UNIX,
    )


from .ado_install import ado_package_install
from .get_data_info import get_data_info
from .read_log import read_log
from .stata_do import stata_do
from .stata_help import stata_help
from .write_dofile import write_dofile

__all__ = [
    "RuntimeContext",
    "create_runtime_context",
    "ado_package_install",
    "get_data_info",
    "read_log",
    "stata_do",
    "stata_help",
    "write_dofile",
]
