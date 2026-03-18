#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : stata_do.py

from pathlib import Path
from typing import Any, Dict

from ..core.types import RAMLimitExceededError
from ..guard import GuardValidator
from ..monitor import RAMMonitor
from ..stata import StataDo
from ._runtime import create_runtime_context


def stata_do(
    dofile_path: str,
    log_file_name: str = None,
    is_read_log: bool = True,
    is_replace_log: bool = True,
    enable_smcl: bool = True,
    config_file: str | Path | None = None,
) -> Dict[str, Any]:
    """Execute a Stata do-file and optionally return log content."""
    runtime = create_runtime_context(config_file=config_file, require_stata=True)

    try:
        resolved_dofile_path = Path(dofile_path)
        if not resolved_dofile_path.exists():
            return {"error": f"Dofile {resolved_dofile_path} does not exist"}
    except Exception as error:
        return {"error": f"Could not recognize dofile_path as pathlib.Path object: {error}"}

    if runtime.config.IS_GUARD:
        try:
            dofile_content = resolved_dofile_path.read_text(encoding="utf-8")
        except Exception as error:
            return {"error": f"Failed to read dofile for security check: {error}"}

        report = GuardValidator().validate(dofile_content)
        if not report.is_safe:
            warning_message = "⚠️  Security warning: Dangerous commands detected:\n"
            for item in report.dangerous_items:
                warning_message += f"  - Line {item.line}: {item.type} '{item.content}'\n"
            return {
                "action": "Security check, dofile not executed",
                "warning": warning_message,
                "suggesting": (
                    "Modify the dofile to ensure safety\n"
                    "or set environment variable `STATA_MCP__IS_GUARD` to `false` (not recommended)"
                ),
            }

    monitors = []
    if runtime.config.IS_MONITOR and runtime.config.MAX_RAM_MB is not None:
        monitors.append(RAMMonitor(max_ram_mb=runtime.config.MAX_RAM_MB))

    stata_executor = StataDo(
        stata_cli=runtime.stata_cli,
        log_file_path=runtime.log_base_path,
        is_unix=runtime.is_unix,
        cwd=runtime.cwd,
        monitors=monitors,
    )

    try:
        log_file_path_mapping = stata_executor.execute_dofile(
            resolved_dofile_path,
            log_file_name,
            is_replace_log,
            enable_smcl,
        )
        text_log_path = log_file_path_mapping["text"]
    except RAMLimitExceededError as error:
        return {"error": f"Out of max RAM limit: {error}"}
    except Exception as error:
        return {"error": str(error)}

    result: Dict[str, Any] = {
        "log_file_path": {
            key: value.as_posix()
            for key, value in log_file_path_mapping.items()
        }
    }

    if is_read_log:
        log_content = {"text": stata_executor.read_log(text_log_path.as_posix())}
        if enable_smcl:
            log_content["smcl"] = (
                "Generally, text log is sufficient."
                "If you need to read an smcl log, please use the read_log API."
            )
        result["log_content"] = log_content

    return result
