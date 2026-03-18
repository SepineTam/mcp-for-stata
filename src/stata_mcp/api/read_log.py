#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : read_log.py

from pathlib import Path
from typing import Literal

from ..stata import StataLog
from . import create_runtime_context


def read_log(
    file_path: str,
    encoding: str = "utf-8",
    is_beta: bool = False,
    *,
    output_format: Literal["full", "core", "dict"] = "dict",
    config_file: str | Path | None = None,
) -> str:
    """Read a generated log file from the configured output directory."""
    runtime = create_runtime_context(config_file=config_file)
    path = Path(file_path).resolve()

    try:
        path.relative_to(runtime.output_base_path.resolve())
    except ValueError as error:
        raise PermissionError(
            f"Access denied: File '{file_path}' is outside the allowed directory "
            f"'{runtime.output_base_path.resolve()}'."
        ) from error

    if not path.exists():
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    if is_beta and runtime.is_unix:
        log_reader = StataLog.from_path(path, encoding=encoding)
        if output_format == "full":
            return log_reader.read_plain_text()
        if output_format == "core":
            return log_reader.read_without_framework()
        if output_format == "dict":
            return str(log_reader.read_as_dict())
        raise ValueError(f"Invalid output_format: {output_format}")

    return path.read_text(encoding=encoding)
