#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : mcp_servers.py

import asyncio
import importlib.metadata
import logging
import logging.handlers
import os
import re
import sys
import threading
import time
import weakref
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, NamedTuple

from mcp.server.fastmcp import Context, FastMCP, Icon
from pydantic import BaseModel, Field

from ._diagnostic_logging import (
    DIAGNOSTIC_BUILD_ID,
    DIAGNOSTIC_SCHEMA_VERSION,
    DiagnosticWatchdog,
    elapsed_ms,
    log_event,
    new_request_id,
    process_log_path,
    safe_stack,
    source_reference,
    utf8_size,
)
from .config import Config

# Init project config
config = Config()
_ASYNC_DO_SEMAPHORES: weakref.WeakKeyDictionary[Any, tuple[int, asyncio.Semaphore]] = (
    weakref.WeakKeyDictionary()
)

# Maybe somebody does not like logging.
# Whatever, left a controller switch `logging STATA_MCP_LOGGING_ON`. Turn off all logging with setting it as false.
# Default Logging Status: File (on), Console (off).
if config.LOGGING_ON:
    # Configure logging
    logging_handlers = []

    if config.LOGGING_CONSOLE_HANDLER_ON:
        # config logging in console.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        logging_handlers.append(console_handler)

    if config.LOGGING_FILE_HANDLER_ON:
        # Add file-handler with rotation support if enabled.
        stata_mcp_dot_log_file_path = config.LOG_FILE
        if config.IS_DEBUG:
            stata_mcp_dot_log_file_path = process_log_path(
                stata_mcp_dot_log_file_path,
                pid=os.getpid(),
            )

        # Use RotatingFileHandler to limit file size and implement log rotation
        # Single file max size: 10MB, backup count: 5 (total 6 files including current)
        file_handler = logging.handlers.RotatingFileHandler(
            stata_mcp_dot_log_file_path,
            maxBytes=config.MAX_BYTES,  # 10MB
            backupCount=config.BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG if config.IS_DEBUG else logging.INFO)

        logging_handlers.append(file_handler)

    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s - %(levelname)s - %(name)s - "
            "pid=%(process)d - thread=%(threadName)s - %(message)s"
        ),
        handlers=logging_handlers,
    )
else:
    # Disable all logging by setting level above CRITICAL
    logging.disable(logging.CRITICAL + 1)

logging.info("Working directory configured.")

# Initialize MCP Server, avoiding FastMCP server timeout caused by Icon src fetch
instructions = (
    "Stata-MCP provides a set of tools to operate Stata locally. "
    "Typically, it writes code to do-file and executes them. "
    "The minimum operation unit should be the do-file; there is no session config."
)
try:
    stata_mcp = FastMCP(
        name="stata-mcp",
        instructions=instructions,
        website_url="https://www.statamcp.com",
        icons=[
            Icon(
                src="https://r2.statamcp.com/android-chrome-512x512.png",
                mimeType="image/png",
                sizes=["512x512"],
            )
        ],
    )
except Exception:
    stata_mcp = FastMCP(
        name="stata-mcp",
        instructions=instructions,
        website_url="https://www.statamcp.com",
    )

# =============================================================================
# STATA_MCP.TOOLS: Stata Core Tools
# =============================================================================

_help_cls = None


def _load_help_cls():
    """Lazy-load and cache the Stata help provider."""
    global _help_cls

    if not config.IS_UNIX:
        raise RuntimeError("The help tool is only available on Unix-like platforms.")

    if _help_cls is None:
        from .stata import StataHelp

        help_config = config.get_help_config("mcp")
        _help_cls = StataHelp(
            stata_cli=config.STATA_CLI,
            project_tmp_dir=config.STATA_MCP_FOLDER.TMP,
            cache_dir=config.HELP_CACHE_DIR,
            config=config,
            is_cache=help_config.is_cache,
            is_save=help_config.is_save,
        )

    return _help_cls


def help(cmd: str, replace: bool = False) -> str:
    """
    Retrieve documentation and usage information for a Stata command.

    Args:
        cmd (str): The name of the Stata command to query, e.g., "regress" or "describe".

    Returns:
        str: The help text returned by Stata for the specified command,
             or a message indicating that no help was found.

    Notes:
        If the returned content starts with 'Cached result for {cmd}', but the output shows the command
        does not exist or you believe the cached content is incorrect, and you are certain the command exists,
        set the environment variable STATA_MCP__CACHE_HELP to false. STATA_MCP__SAVE_HELP works similarly.
    """
    return _load_help_cls().help(cmd, replace=replace)


class _StataDoRequest(NamedTuple):
    dofile_path: Path
    monitors: list[Any]


def _prepare_stata_do_request(dofile_path: str) -> Dict[str, Any] | _StataDoRequest:
    """Validate a do-file request and build shared execution inputs."""
    # Convert dofile_path from str to Path
    try:
        dofile_path = Path(dofile_path)
        if not dofile_path.exists():
            return {"error": f"Dofile {dofile_path} does not exist"}
    except Exception as e:
        return {"error": f"Could not recognize dofile_path as pathlib.Path object: {e}"}

    dofile_path_resolved = dofile_path.resolve()
    candidate_allowed_dirs = [
        config.STATA_MCP_FOLDER.DO,
        config.WORKING_DIR,
    ]
    allowed_dirs: List[Path] = []
    for candidate_dir in candidate_allowed_dirs:
        if candidate_dir.exists():
            allowed_dirs.append(candidate_dir.resolve())
        else:
            logging.warning(
                "Skip missing allowed directory for dofile execution boundary check."
            )
    is_allowed = _is_within_allowed_directories(dofile_path_resolved, allowed_dirs)
    if not is_allowed:
        logging.warning(
            "[SECURITY VIOLATION] Attempted to execute dofile outside allowed directories."
        )
        return {
            "error": f"Access denied: Dofile '{dofile_path}' is outside allowed directories.",
            "allowed_directories": [d.as_posix() for d in allowed_dirs],
        }

    try:
        with open(dofile_path, "r", encoding="utf-8") as f:
            dofile_content = f.read()
    except Exception as e:
        logging.error("Failed to read dofile for security check.")
        return {"error": f"Failed to read dofile for security check: {str(e)}"}

    from .guard import PackageManagementGuardValidator

    package_report = PackageManagementGuardValidator().validate(dofile_content)
    if not package_report.is_safe:
        warning_msg = "⚠️  Security warning: Package-management commands detected:\n"
        for item in package_report.dangerous_items:
            warning_msg += f"  - Line {item.line}: {item.type} '{item.content}'\n"
        return {
            "action": "Security check, dofile not executed",
            "warning": warning_msg,
            "suggesting": (
                "Third-party package management must use the controlled "
                "ado_package_install interface."
            ),
        }

    # Security check: validate dofile before execution
    if config.IS_GUARD:
        from .guard import GuardValidator

        # Config guard validator (platform-independent)
        guard_validator = (
            GuardValidator()
        )  # TODO: It may be make an error for windows user

        # Perform security validation
        report = guard_validator.validate(dofile_content, config=config)

        if not report.is_safe:
            dangerous_summary = ", ".join(
                f"line {item.line}:{item.type}" for item in report.dangerous_items
            )
            logging.warning(
                "[SECURITY VIOLATION] Security rejection for dofile: %s",
                dangerous_summary,
            )
            warning_msg = "⚠️  Security warning: Dangerous commands detected:\n"
            for item in report.dangerous_items:
                warning_msg += f"  - Line {item.line}: {item.type} '{item.content}'\n"
            return {
                "action": "Security check, dofile not executed",
                "warning": warning_msg,
                "suggesting": (
                    "Modify the dofile to ensure safety\n"
                    "or set environment variable `STATA_MCP__IS_GUARD` to `false` (not recommended)"
                ),
            }
        else:
            logging.info("Security check passed for dofile.")
    else:
        logging.warning(
            "[SECURITY] Guard is disabled. Dangerous dofile commands will not be blocked."
        )

    # Initialize monitors
    monitors = []
    if config.IS_MONITOR:
        if config.MAX_RAM_MB is not None:
            from .monitor import RAMMonitor

            monitors.append(RAMMonitor(max_ram_mb=config.MAX_RAM_MB))

    return _StataDoRequest(dofile_path=dofile_path, monitors=monitors)


def _format_stata_do_result(
    log_file_path_mapping: Dict[str, Path],
    read_log_when_error: bool,
    enable_smcl: bool,
    stata_executor: Any,
    text_log: str,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "log_file_path": {
            k: v.as_posix()  # avoiding issues with some AI clients that may not recognize Path objects
            for k, v in log_file_path_mapping.items()
        },
    }

    # Return log content based on user preference
    if read_log_when_error:
        text_content = stata_executor.read_log(text_log)
        if not _has_stata_error(text_content):
            text_content = (
                "There is no Stata return-code error in this execution. "
                "If you want to view the full log, use the read_log tool."
            )

        log_content = {"text": text_content}
        if enable_smcl:
            log_content["smcl"] = (
                "Generally, text log is sufficient."
                "If need to read smcl log, please use `mcp__stata-mcp__read_log` tool."
            )
        result["log_content"] = log_content

    return result


def _get_async_do_semaphore() -> asyncio.Semaphore:
    """Return the per-event-loop async do-file concurrency limiter."""
    limit = getattr(config, "MAX_ASYNC_DO", 3)
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        limit = 3
    loop = asyncio.get_running_loop()
    cached = _ASYNC_DO_SEMAPHORES.get(loop)
    if cached is None or cached[0] != limit:
        semaphore = asyncio.Semaphore(limit)
        _ASYNC_DO_SEMAPHORES[loop] = (limit, semaphore)
        return semaphore
    return cached[1]


def _sync_stata_do(
    dofile_path: str,
    log_file_name: str = None,
    read_log_when_error: bool = False,
    is_replace_log: bool = True,
    enable_smcl: bool = True,
    timeout: float | None = None,
) -> Dict[str, Any]:
    """
    Execute a Stata do-file and return log file paths.

    Args:
        dofile_path (str): Path to the .do file.
        log_file_name (str, optional): Custom log name without timestamp. Default uses current time.
        read_log_when_error (bool): If True, include log text only when a Stata return-code error
            (e.g. r(198)) is present. If no error is found, returns a short confirmation instead.
        is_replace_log (bool): Overwrite existing log files. Defaults to True.
        enable_smcl (bool): Also generate .smcl log (Unix only). Defaults to True.
        timeout (float, optional): Maximum execution time in seconds. Defaults to no timeout.

    Returns:
        Dict[str, Any]: "log_file_path" (text/smcl) and optionally "log_content".

    Examples:
        >>> stata_do("/path/to/analysis.do")
        >>> stata_do("/path/to/analysis.do", read_log_when_error=True)

    Raises:
        FileNotFoundError: If the specified do-file does not exist.
        RuntimeError: If Stata execution fails or log file cannot be generated.
        PermissionError: If there are insufficient permissions to execute Stata or write log files.

    Notes:
        - Log files are automatically created in the configured log directory.
        - Supports multiple operating systems through the StataDo executor.
        - SMCL format preserves hyperlinks from findsj, getiref commands (Unix only).
        - Security guard blocks execution when dangerous commands are detected.
        - To disable security guard, set STATA_MCP__IS_GUARD=false (not recommended).
    """
    request = _prepare_stata_do_request(dofile_path)
    if isinstance(request, dict):
        return request

    # Initialize Stata executor with system configuration
    from .stata import StataDo

    stata_executor = StataDo(
        stata_cli=config.STATA_CLI,  # Path to Stata executable
        log_file_path=config.STATA_MCP_FOLDER.LOG,  # Directory for log files
        is_unix=config.IS_UNIX,  # Whether the OS is Unix-like
        cwd=config.WORKING_DIR,
        monitors=request.monitors,
    )

    # Execute the do-file and get log file path
    logging.info("Try to running dofile.")

    from .core.types import RAMLimitExceededError

    try:
        log_file_path_mapping: Dict[str, Path] = stata_executor.execute_dofile(
            request.dofile_path,
            log_file_name,
            is_replace_log,
            enable_smcl,
            timeout=timeout,
        )
        text_log = log_file_path_mapping.get("text").as_posix()
        logging.info("Dofile executed successfully.")
    except RAMLimitExceededError as e:
        logging.error("Out of max RAM limit: %s", e)
        return {"error": f"Out of max RAM limit: {e}"}
    except Exception as e:
        logging.error("Failed to execute dofile.")
        logging.debug("Execution exception details: %s", e)
        return {"error": str(e)}

    return _format_stata_do_result(
        log_file_path_mapping,
        read_log_when_error,
        enable_smcl,
        stata_executor,
        text_log,
    )


async def _async_stata_do(
    dofile_path: str,
    log_file_name: str = None,
    read_log_when_error: bool = False,
    is_replace_log: bool = True,
    enable_smcl: bool = True,
    timeout: float | None = None,
) -> Dict[str, Any]:
    """Async Stata do-file tool implementation."""
    request = _prepare_stata_do_request(dofile_path)
    if isinstance(request, dict):
        return request

    from .stata.stata_do.async_do import AsyncStataDo

    stata_executor = AsyncStataDo(
        stata_cli=config.STATA_CLI,
        log_file_path=config.STATA_MCP_FOLDER.LOG,
        is_unix=config.IS_UNIX,
        cwd=config.WORKING_DIR,
        monitors=request.monitors,
    )

    logging.info("Try to running dofile.")

    from .core.types import RAMLimitExceededError

    try:
        async with _get_async_do_semaphore():
            log_file_path_mapping: Dict[str, Path] = (
                await stata_executor.execute_dofile_async(
                    request.dofile_path,
                    log_file_name,
                    is_replace_log,
                    enable_smcl,
                    timeout=timeout,
                )
            )
        text_log = log_file_path_mapping.get("text").as_posix()
        logging.info("Dofile executed successfully.")
    except RAMLimitExceededError as e:
        logging.error("Out of max RAM limit: %s", e)
        return {"error": f"Out of max RAM limit: {e}"}
    except Exception as e:
        logging.error("Failed to execute dofile.")
        logging.debug("Execution exception details: %s", e)
        return {"error": str(e)}

    return _format_stata_do_result(
        log_file_path_mapping,
        read_log_when_error,
        enable_smcl,
        stata_executor,
        text_log,
    )


stata_do = _async_stata_do if getattr(config, "IS_ASYNC_DO", False) else _sync_stata_do


class _AdoInstallApproval(BaseModel):
    """Structured user approval collected through MCP elicitation."""

    approved: bool = Field(
        description="Approve installation of the exact third-party package and source."
    )


async def ado_package_install(
    package: str,
    source: str = "ssc",
    is_replace: bool = False,
    package_source_from: str = None,
    ctx: Context = None,
) -> str:
    """
    Install a Stata package from SSC, GitHub, or net.

    Args:
        package (str): Package name. For GitHub, use "user/repo" format.
        source (str): "ssc" (default), "github", or "net".
        is_replace (bool): Force reinstallation if already present.
        package_source_from (str): Validated HTTPS URL for source="net".
        ctx (Context): MCP context used to request trusted user approval.

    Returns:
        str: Stata installation log as a string.

    Examples:
        >>> await ado_package_install(package="outreg2", ctx=context)
        >>> await ado_package_install(
        ...     package="SepineTam/TexIV",
        ...     source="github",
        ...     ctx=context,
        ... )

    Notes:
        This high-risk tool is registered only in the unsafe profile.
        GitHub repositories receive no content-level security protection.
        Inspect the repository before installation.
    """
    from .api.ado_install import ado_package_install as api_ado_package_install

    if ctx is None:
        raise PermissionError("MCP user approval context is required.")
    approval = await ctx.elicit(
        message=(
            "Approve third-party Stata package installation? "
            f"package={package!r}, source={source!r}, "
            f"package_source_from={package_source_from!r}, "
            f"is_replace={is_replace!r}"
        ),
        schema=_AdoInstallApproval,
    )
    if (
        approval.action != "accept"
        or approval.data is None
        or approval.data.approved is not True
    ):
        logging.info("User denied ado install of %s from %s", package, source)
        raise PermissionError("Ado package installation was not approved by the user.")

    logging.info("User approved ado install of %s from %s", package, source)

    return api_ado_package_install(
        package=package,
        source=source,
        is_replace=is_replace,
        package_source_from=package_source_from,
        config_file=config.config_file,
    )


# =============================================================================
# STATA_MCP.TOOLS: Data Operation Tools
# =============================================================================


def get_data_info(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    head: int | None = None,
    ctx: Context | None = None,
) -> str:
    """
    Return descriptive statistics for a supported data file.

    Args:
        data_path (str): Absolute path to .dta, .csv, .xlsx, .xls, .sav file.
        vars_list (List[str] | None): Optional variable subset (default: all variables).
        encoding (str): File encoding (ignored for .dta).
        head (int): Number of preview rows (0 = disabled).

    Returns:
        str: JSON string with overview, variable details, and config.

    Examples:
        >>> get_data_info("/Applications/Stata/auto.dta")
        >>> get_data_info("/Applications/Stata/auto.dta", vars_list=["price", "mpg"], head=5)
    """
    request_id = new_request_id()
    started_at = time.perf_counter()
    requested_vars_count = len(vars_list) if vars_list is not None else 0
    diagnostic_logger = logging.getLogger(__name__)
    try:
        mcp_request_id = ctx.request_id if ctx is not None else None
    except Exception:
        mcp_request_id = None

    log_event(
        diagnostic_logger,
        logging.INFO,
        "get_data_info.mcp_tool.started",
        request_id,
        diagnostic_build_id=DIAGNOSTIC_BUILD_ID,
        diagnostic_schema_version=DIAGNOSTIC_SCHEMA_VERSION,
        head=head,
        mcp_request_id=mcp_request_id,
        pid=os.getpid(),
        platform=sys.platform,
        requested_vars_count=requested_vars_count,
        source_ref=source_reference(data_path),
        thread=threading.current_thread().name,
    )

    watchdog = DiagnosticWatchdog(diagnostic_logger, request_id)
    if config.IS_DEBUG:
        watchdog.start()

    try:
        package_versions = {
            package_name: _installed_package_version(package_name)
            for package_name in ("mcp", "stata-mcp", "pandas", "numpy", "pyreadstat")
        }
        log_event(
            diagnostic_logger,
            logging.DEBUG,
            "get_data_info.mcp_tool.environment",
            request_id,
            mcp_version=package_versions["mcp"],
            numpy_version=package_versions["numpy"],
            pandas_version=package_versions["pandas"],
            pyreadstat_version=package_versions["pyreadstat"],
            python_version=".".join(str(part) for part in sys.version_info[:3]),
            stata_mcp_version=package_versions["stata-mcp"],
        )
        import_started_at = time.perf_counter()
        log_event(
            diagnostic_logger,
            logging.DEBUG,
            "get_data_info.mcp_tool.lazy_import.started",
            request_id,
        )
        from .api.get_data_info import _get_data_info_impl

        log_event(
            diagnostic_logger,
            logging.DEBUG,
            "get_data_info.mcp_tool.lazy_import.completed",
            request_id,
            duration_ms=elapsed_ms(import_started_at),
        )
        result = _get_data_info_impl(
            data_path=data_path,
            vars_list=vars_list,
            encoding=encoding,
            config_file=None,
            head=head,
            tool_context="mcp",
            request_id=request_id,
        )
        log_event(
            diagnostic_logger,
            logging.INFO,
            "get_data_info.mcp_tool.completed",
            request_id,
            duration_ms=elapsed_ms(started_at),
            result_chars=len(result),
            structured_output_enabled=True,
            tool_result_utf8_bytes=utf8_size(result),
        )
        return result
    except BaseException as error:
        log_event(
            diagnostic_logger,
            logging.ERROR,
            "get_data_info.mcp_tool.failed",
            request_id,
            duration_ms=elapsed_ms(started_at),
            error_type=type(error).__name__,
        )
        log_event(
            diagnostic_logger,
            logging.ERROR,
            "get_data_info.mcp_tool.stack",
            request_id,
            stack=safe_stack(error),
        )
        raise
    finally:
        watchdog.cancel()


def _installed_package_version(package_name: str) -> str:
    """Return an installed package version without allowing diagnostics to fail."""
    try:
        return importlib.metadata.version(package_name)
    except Exception:
        return "unknown"


# =============================================================================
# STATA_MCP.TOOLS: File Management Tools
# =============================================================================


def read_log(
    file_path: str,
    encoding: str = "utf-8",
    *,
    output_format: Literal["full", "core", "dict"] = "core",
    lines: int = 0,
) -> str:
    """
    Read a Stata log file (.log or .smcl) and return its content.

    Args:
        file_path (str): The full path to the file to be read.
        encoding (str, optional): The encoding used to decode the file. Defaults to "utf-8".
        output_format (Literal["full", "core", "dict"]): log information content output format.
            - full: all the original content;
            - core: remove useless information, saving content;
            - dict: structure format to quickly match command and result.
        lines (int): Content trimming control for output.
            - 0 (default): return all content.
            - > 0: return first N items (lines for full/core, entries for dict).
            - < 0: return last |N| items (lines for full/core, entries for dict).

    Returns:
        str: The content of the file as a string.

    Raises:
        PermissionError: If the file is not within the allowed stata-mcp-folder directory.
        FileNotFoundError: If the file does not exist.
        IOError: If an error occurs while reading the file.

    Notes:
        Structured log parsing is controlled by the `[BETA] enable_structured_log`
        configuration option. The beta version code of StataLog is generated by
        Claude Code, it may make mistake.

    """
    path = Path(file_path).resolve()  # Resolve to handle symlinks and ..

    # Security check: ensure the file is within the allowed directory
    try:
        path.relative_to(config.STATA_MCP_FOLDER.path.resolve())
    except ValueError:
        # Log security violation for audit purposes.
        # If this security warning appears, it may indicate that the current model has been compromised/poisoned.
        logging.warning(
            "[SECURITY VIOLATION] Attempted to access file outside allowed directory."
        )
        raise PermissionError(
            "Access denied: File is outside the allowed directory. "
            "read_file can only read files within the stata-mcp-folder."
        )

    if not path.exists():
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    if config.ENABLE_STRUCTURED_LOG:
        from .stata import StataLog

        loger = StataLog.from_path(file_path, encoding=encoding)
        if output_format not in ["full", "core", "dict"]:
            raise ValueError(f"Invalid output_format: {output_format}")
        elif output_format == "full":
            return _trim_lines(loger.read_plain_text(), lines)
        elif output_format == "core":
            return _trim_lines(loger.read_without_framework(), lines)
        elif output_format == "dict":
            dict_data = loger.read_as_dict()
            if lines == 0:
                return str(dict_data)
            if lines > 0:
                return str(dict_data[:lines])
            return str(dict_data[-abs(lines):])
    # If structured log parsing is disabled, read the file directly.
    try:
        with open(path, "r", encoding=encoding) as file:
            log_content = file.read()
        logging.info("Successfully read file.")
        return _trim_lines(log_content, lines)
    except IOError as e:
        logging.error("Failed to read file.")
        logging.debug("Read file exception details: %s", e)
        raise IOError(f"An error occurred while reading the file: {e}")


def _trim_lines(content: str, lines: int) -> str:
    """Trim content to requested line range."""
    if lines == 0:
        return content

    all_lines = content.splitlines()
    if lines > 0:
        return "\n".join(all_lines[:lines])
    return "\n".join(all_lines[-abs(lines):])


def _is_within_allowed_directories(target_path: Path, allowed_dirs: List[Path]) -> bool:
    """Return True when target_path is under one of the allowed directories."""
    for allowed_dir in allowed_dirs:
        try:
            target_path.relative_to(allowed_dir)
            return True
        except ValueError:
            continue
    return False


def _has_stata_error(content: str) -> bool:
    """Return True when the text log contains a Stata return code pattern like r(198)."""
    return re.search(r"r\(\d+\)", content) is not None


ToolFunc = Callable[..., Any]

_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "stata_do": {
        "description": (
            "Execute a Stata do-file and return the execution log. "
            "Accepts a do-file path, runs it via the configured Stata executable, "
            "and can optionally read log content only when return-code errors are detected. "
            "Use when you need to run Stata commands, perform regression or statistical analysis, "
            "or execute a do-file. "
        ),
        "func": stata_do,
        "config_name": "STATA_DO",
        "profiles": {"core", "all"},
    },
    "get_data_info": {
        "description": (
            "Get descriptive statistics and a data preview for a supported data file "
            "(.dta, .csv, .tsv, .psv, .xlsx, .xls, .sav, .zsav). Returns overview, variable details, "
            "and optional head rows filtered by requested variables. "
            "Use when you need to understand a dataset or have no prior knowledge of the data."
        ),
        "func": get_data_info,
        "config_name": "DATA_INFO",
        "profiles": {"core", "all"},
    },
    "help": {
        "description": (
            "Retrieve documentation and usage information for a Stata command. "
            "Use when you need to understand a command's syntax, options, "
            "or troubleshoot errors before running it."
        ),
        "func": help,
        "config_name": "HELP",
        "profiles": {"core", "all"},
        "unix_only": True,
    },
    "read_log": {
        "description": (
            "Read a Stata log file (.log or .smcl) and return its content. "
            "Supports full, core, and dict output formats. "
            "Use `lines` to return only the first/last N lines."
        ),
        "func": read_log,
        "config_name": "READ_LOG",
        "profiles": {"all"},
    },
    "ado_package_install": {
        "description": (
            "Install a Stata ado package from SSC, GitHub, or net sources. "
            "This high-risk tool requires explicit operator enablement and "
            "per-call user confirmation."
        ),
        "func": ado_package_install,
        "config_name": "ADO_INSTALL",
        "profiles": {"unsafe"},
    },
}

_registered_profile: str | None = None


def register_tools(server: FastMCP, profile: str = "all") -> None:
    """Register tools and resources based on a selected profile."""
    global _registered_profile

    if profile not in {"core", "all", "unsafe"}:
        raise ValueError(f"Unsupported profile: {profile}")

    if _registered_profile == profile:
        return
    if _registered_profile is not None and _registered_profile != profile:
        raise RuntimeError(
            "Tools are already registered with a different profile. "
            "Create a new process to switch profile."
        )

    for name, meta in _TOOL_REGISTRY.items():
        if meta.get("unix_only") and not config.IS_UNIX:
            continue
        eligible_profiles = {"all", "unsafe"} if profile == "unsafe" else {profile}
        if not eligible_profiles.intersection(meta["profiles"]):
            continue
        is_tool_enabled = getattr(config, "is_tool_enabled", None)
        if callable(is_tool_enabled) and not is_tool_enabled(
            "mcp",
            meta.get("config_name", name),
        ):
            continue

        tool_func: ToolFunc | None = meta.get("func")
        if tool_func is None:
            logging.warning(
                "Skipping tool '%s' because its registry entry has no callable func.",
                name,
            )
            continue
        server.tool(name=name, description=meta["description"])(tool_func)

    logging.info("Registered tools for profile: %s", profile)

    # # Keep help as both tool and resource on Unix platforms.
    # # NOTE: Temporarily disabled due to MCP resource URI parameter mismatch
    # if config.IS_UNIX and profile in {"core", "all"}:
    #     server.resource(
    #         uri="help://stata/{cmd}",
    #         name="help",
    #         description="Get help for a Stata command"
    #     )(help)

    _registered_profile = profile


__all__ = [
    "stata_mcp",
    # Functions (Core)
    "get_data_info",
    "stata_do",
    "register_tools",
    # Utilities
    "read_log",
    "ado_package_install",
]

if config.IS_UNIX:
    __all__.extend(["help"])
