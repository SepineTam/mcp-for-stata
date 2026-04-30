#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : stata_do.py

import logging
import re
from pathlib import Path
from typing import Any, Dict

from ..core.types import RAMLimitExceededError
from ..guard import GuardValidator
from ..monitor import RAMMonitor
from ..stata import StataDo, StataLog
from ._runtime import create_runtime_context


def _is_within_allowed_directories(target_path: Path, allowed_dirs: list[Path]) -> bool:
    """Return True when target_path is under one of the allowed directories."""
    for allowed_dir in allowed_dirs:
        try:
            target_path.relative_to(allowed_dir)
            return True
        except ValueError:
            continue
    return False


def stata_do(
    dofile_path: str,
    log_file_name: str = None,
    read_log_when_error: bool = False,
    is_replace_log: bool = True,
    enable_smcl: bool = True,
    config_file: str | Path | None = None,
) -> Dict[str, Any]:
    """Execute a Stata do-file and optionally return log content when errors occur."""
    runtime = create_runtime_context(config_file=config_file, require_stata=True)

    try:
        resolved_dofile_path = Path(dofile_path)
        if not resolved_dofile_path.exists():
            return {"error": f"Dofile {resolved_dofile_path} does not exist"}
    except Exception as error:
        return {"error": f"Could not recognize dofile_path as pathlib.Path object: {error}"}

    resolved_dofile_path = resolved_dofile_path.resolve()
    candidate_allowed_dirs = [
        runtime.config.STATA_MCP_FOLDER.DO,
        runtime.config.WORKING_DIR,
    ]
    allowed_dirs: list[Path] = []
    for candidate_dir in candidate_allowed_dirs:
        if candidate_dir.exists():
            allowed_dirs.append(candidate_dir.resolve())
        else:
            logging.warning(
                "Skip missing allowed directory for dofile execution boundary check: "
                f"{candidate_dir}"
            )

    if not _is_within_allowed_directories(resolved_dofile_path, allowed_dirs):
        logging.warning(
            f"[SECURITY VIOLATION] Attempted to execute dofile outside allowed directories: "
            f"requested_path='{dofile_path}', "
            f"resolved_path='{resolved_dofile_path}', "
            f"allowed_directories='{[allowed_dir.as_posix() for allowed_dir in allowed_dirs]}'"
        )
        return {
            "error": f"Access denied: Dofile '{resolved_dofile_path}' is outside allowed directories.",
            "allowed_directories": [allowed_dir.as_posix() for allowed_dir in allowed_dirs],
        }

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

    if read_log_when_error:
        text_log_reader = StataLog.from_path(text_log_path)
        text_content = text_log_reader.read_without_framework()

        if not _has_stata_error(text_content):
            text_content = (
                "There is no Stata return-code error in this execution. "
                "If you want to view the full log, use the read_log tool."
            )

        log_content = {"text": text_content}
        if enable_smcl and "smcl" in log_file_path_mapping:
            log_content["smcl"] = log_file_path_mapping["smcl"].as_posix()
        result["log_content"] = log_content

    return result


def _has_stata_error(content: str) -> bool:
    """Return True when the text log contains a Stata return code pattern like r(198)."""
    return re.search(r"r\(\d+\)", content) is not None
