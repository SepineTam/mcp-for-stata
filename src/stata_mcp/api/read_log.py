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


def read_log(
    file_path: str,
    encoding: str = "utf-8",
    is_beta: bool = False,
    *,
    output_format: Literal["full", "core", "dict"] = "core",
    config_file: str | Path | None = None,
) -> str:
    """Read a Stata log file as a direct one-shot utility."""
    _ = (is_beta, config_file)
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    if path.suffix.lower() not in {".log", ".smcl"}:
        return path.read_text(encoding=encoding)

    log_reader = StataLog.from_path(path, encoding=encoding)
    if output_format == "full":
        return log_reader.read_plain_text()
    if output_format == "core":
        return log_reader.read_without_framework()
    if output_format == "dict":
        return str(log_reader.read_as_dict())
    raise ValueError(f"Invalid output_format: {output_format}")
