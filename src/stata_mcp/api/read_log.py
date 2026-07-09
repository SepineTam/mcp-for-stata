#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : api/read_log.py

import logging
from pathlib import Path
from typing import Literal

from ..stata import StataLog

logger = logging.getLogger(__name__)


def read_log(
    file_path: str,
    encoding: str = "utf-8",
    is_beta: bool = False,
    *,
    output_format: Literal["full", "core", "dict"] = "core",
    config_file: str | Path | None = None,
) -> str:
    """Read a Stata log file as a direct one-shot utility."""
    _ = is_beta

    from ._runtime import create_runtime_context

    runtime = create_runtime_context(config_file=config_file)

    path = Path(file_path).expanduser().resolve()

    if runtime.config.STRICT_READ_LOG_BOUNDARY:
        allowed_base = runtime.config.STATA_MCP_FOLDER.path.resolve()
        try:
            path.relative_to(allowed_base)
        except ValueError:
            logger.warning(
                "[SECURITY VIOLATION] read_log outside allowed directory: %s",
                path,
            )
            return "Access denied: log file must be within the stata-mcp folder."

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
