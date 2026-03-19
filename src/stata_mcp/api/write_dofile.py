#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : write_dofile.py

from datetime import datetime
from pathlib import Path

from ._runtime import create_runtime_context


def write_dofile(
    content: str,
    encoding: str = None,
    config_file: str | Path | None = None,
) -> str:
    """Write Stata code to a do-file and return the generated path."""
    runtime = create_runtime_context(config_file=config_file)
    file_path = runtime.dofile_base_path / f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.do"
    target_encoding = encoding or "utf-8"
    file_path.write_text(content, encoding=target_encoding)
    return file_path.as_posix()
