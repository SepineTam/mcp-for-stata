#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : mcp_servers.py

import json
import logging
import logging.handlers
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal

from mcp.server.fastmcp import FastMCP, Icon

from .config import Config

# Init project config
config = Config()

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

        # Use RotatingFileHandler to limit file size and implement log rotation
        # Single file max size: 10MB, backup count: 5 (total 6 files including current)
        file_handler = logging.handlers.RotatingFileHandler(
            stata_mcp_dot_log_file_path,
            maxBytes=config.MAX_BYTES,  # 10MB
            backupCount=config.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(
            logging.DEBUG if config.IS_DEBUG else logging.INFO
        )

        logging_handlers.append(file_handler)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=logging_handlers
    )
else:
    # Disable all logging by setting level above CRITICAL
    logging.disable(logging.CRITICAL + 1)

logging.info(f"Using {config.WORKING_DIR.as_posix()} as working directory")

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
        icons=[Icon(
            src="https://r2.statamcp.com/android-chrome-512x512.png",
            mimeType="image/png",
            sizes=["512x512"]
        )]
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

        _help_cls = StataHelp(
            stata_cli=config.STATA_CLI,
            project_tmp_dir=config.STATA_MCP_FOLDER.TMP,
            cache_dir=config.HELP_CACHE_DIR,
            config=config,
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


def stata_do(
        dofile_path: str,
        log_file_name: str = None,
        read_log_when_error: bool = False,
        is_replace_log: bool = True,
        enable_smcl: bool = True
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
                "Skip missing allowed directory for dofile execution boundary check: "
                f"{candidate_dir}"
            )
    is_allowed = _is_within_allowed_directories(dofile_path_resolved, allowed_dirs)
    if not is_allowed:
        logging.warning(
            f"[SECURITY VIOLATION] Attempted to execute dofile outside allowed directories: "
            f"requested_path='{dofile_path}', "
            f"resolved_path='{dofile_path_resolved}', "
            f"allowed_directories='{[d.as_posix() for d in allowed_dirs]}'"
        )
        return {
            "error": f"Access denied: Dofile '{dofile_path}' is outside allowed directories.",
            "allowed_directories": [d.as_posix() for d in allowed_dirs],
        }

    # Security check: validate dofile before execution
    if config.IS_GUARD:
        from .guard import GuardValidator

        # Read dofile content
        try:
            with open(dofile_path, 'r', encoding='utf-8') as f:
                dofile_content = f.read()
        except Exception as e:
            logging.error(f"Failed to read dofile {dofile_path}: {str(e)}")
            return {"error": f"Failed to read dofile for security check: {str(e)}"}

        # Config guard validator (platform-independent)
        guard_validator = GuardValidator()  # TODO: It may be make an error for windows user

        # Perform security validation
        report = guard_validator.validate(dofile_content)

        if not report.is_safe:
            warning_msg = "⚠️  Security warning: Dangerous commands detected:\n"
            for item in report.dangerous_items:
                warning_msg += f"  - Line {item.line}: {item.type} '{item.content}'\n"
            logging.warning(warning_msg)
            return {
                "action": "Security check, dofile not executed",
                "warning": warning_msg,
                "suggesting": (
                    "Modify the dofile to ensure safety\n"
                    "or set environment variable `STATA_MCP__IS_GUARD` to `false` (not recommended)"
                )
            }
        else:
            logging.info(f"✅ {dofile_path} - Security check passed")
    else:
        logging.warning("[SECURITY] Guard is disabled. Dangerous dofile commands will not be blocked.")

    # Initialize monitors
    monitors = []
    if config.IS_MONITOR:
        if config.MAX_RAM_MB is not None:
            from .monitor import RAMMonitor
            monitors.append(RAMMonitor(max_ram_mb=config.MAX_RAM_MB))

    # Initialize Stata executor with system configuration
    from .stata import StataDo
    stata_executor = StataDo(
        stata_cli=config.STATA_CLI,  # Path to Stata executable
        log_file_path=config.STATA_MCP_FOLDER.LOG,  # Directory for log files
        is_unix=config.IS_UNIX,  # Whether the OS is Unix-like
        cwd=config.WORKING_DIR,
        monitors=monitors
    )

    # Execute the do-file and get log file path
    logging.info(f"Try to running file {dofile_path}")

    from .core.types import RAMLimitExceededError

    try:
        log_file_path_mapping: Dict[str, Path] = stata_executor.execute_dofile(
            dofile_path, log_file_name, is_replace_log, enable_smcl
        )
        text_log = log_file_path_mapping.get("text").as_posix()
        logging.info(f"{dofile_path} is executed successfully. Log file path: {text_log}")
    except RAMLimitExceededError as e:
        logging.error(f"Out of max RAM limit: {e}")
        return {"error": f"Out of max RAM limit: {e}"}
    except Exception as e:
        logging.error(f"Failed to execute {dofile_path}. Error: {str(e)}")
        return {"error": str(e)}

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


def ado_package_install(
        package: str,
        source: str = "ssc",
        is_replace: bool = True,
        package_source_from: str = None
) -> str:
    """
    Install a Stata package from SSC, GitHub, or net.

    Args:
        package (str): Package name. For GitHub, use "user/repo" format.
        source (str): "ssc" (default), "github", or "net".
        is_replace (bool): Force reinstallation if already present.
        package_source_from (str): Directory or URL (required only for source="net").

    Returns:
        str: Stata installation log as a string.

    Examples:
        >>> ado_package_install(package="outreg2")
        >>> ado_package_install(package="SepineTam/TexIV", source="github")

    Notes:
        SSC installs can be slow; skip if the package is likely already installed.
    """
    source = source.lower()

    if config.IS_UNIX:
        from .stata import GITHUB_Install, NET_Install, SSC_Install

        SOURCE_MAPPING: Dict = {
            "github": GITHUB_Install,
            "net": NET_Install,
            "ssc": SSC_Install
        }
        installer = SOURCE_MAPPING.get(source, SSC_Install)

        logging.info(f"Try to use {installer.__name__} to install {package}.")

        # set the args for the special cases
        args = [package, package_source_from] if source == "net" else [package]
        install_msg = installer(config.STATA_CLI, is_replace, timeout=300).install(*args)

        if installer.check_installed_from_msg(install_msg):
            logging.info(f"{package} is installed successfully.")
        else:
            error_summary = installer.extract_error_summary(install_msg)
            install_msg += (
                f"\nError: Failed to install package '{package}' from source '{source}'. "
                f"Details: {error_summary}"
            )
            if source == "github":
                install_msg += (
                    "\nPlease check the GitHub repo URL, verify case sensitivity, "
                    "and ensure the GitHub command is installed in Stata"
                )
            logging.error(f"{package} installation failed.")
            logging.debug(f"Full installation message: {install_msg}")

        return install_msg
    else:
        from_message = f"from({package_source_from})" if (package_source_from and source == "net") else ""
        replace_str = "replace" if is_replace else ""
        tmp_file = write_dofile(f"{source} install {package}, {replace_str} {from_message}")
        return stata_do(tmp_file, read_log_when_error=False).get("log_content")


# =============================================================================
# STATA_MCP.TOOLS: Data Operation Tools
# =============================================================================

def get_data_info(
        data_path: str,
        vars_list: List[str] | None = None,
        encoding: str = "utf-8",
        head: int = 0,
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
    data_path = Path(data_path).expanduser().resolve()
    data_extension = data_path.suffix.lower().strip(".")

    # Lazy import: pandas/numpy/requests are heavy, only load when needed
    from .data_info import get_data_handler

    # Get the appropriate data handler class from the registry
    data_info_cls = get_data_handler(data_extension)

    if not data_info_cls:
        logging.error(f"Unsupported file extension: {data_extension} for data file: {data_path}")
        return f"Unsupported file extension now: {data_extension}"

    data_info = data_info_cls(data_path, vars_list, encoding=encoding, cache_dir=config.STATA_MCP_FOLDER.TMP, head=head)
    try:
        info = data_info.info
        if data_info.is_cache:
            saved_path = info.get("saved_path", None)
            logging.info(f"Successfully generated data summary for {data_path}, saved to {saved_path}")
        else:
            logging.info(f"Successfully generated data summary for {data_path}")
        return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Failed to generate data summary for {data_path}: {str(e)}")
        return f"Failed to generate data summary for {data_path}: {str(e)}"


# =============================================================================
# STATA_MCP.TOOLS: File Management Tools
# =============================================================================

def read_log(
        file_path: str,
        encoding: str = "utf-8",
        is_beta: bool = False,
        *,
        output_format: Literal["full", "core", "dict"] = "dict",
        lines: int = 0,
) -> str:
    """
    Read a Stata log file (.log or .smcl) and return its content.

    Args:
        file_path (str): The full path to the file to be read.
        encoding (str, optional): The encoding used to decode the file. Defaults to "utf-8".
        is_beta (bool): whether to use beta-function to read log-file, default is False, Windows device not works.
            for is_beta, we recommend use it when you are trying to read a ".smcl" log file with dict format.

        * following is beta args.
        output_format (Literal["full", "core", "dict"]): log information content output format.
            - full: all the original content;
            - core: remove useless information, saving content;
            - dict (default): structure format to quickly match command and result.
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
        The beta version code of StataLog is generated by Claude Code, it may make mistake.

    """
    path = Path(file_path).resolve()  # Resolve to handle symlinks and ..

    # Security check: ensure the file is within the allowed directory
    try:
        path.relative_to(config.STATA_MCP_FOLDER.path.resolve())
    except ValueError:
        allowed_path = config.STATA_MCP_FOLDER.path.resolve()
        # Log security violation for audit purposes.
        # If this security warning appears, it may indicate that the current model has been compromised/poisoned.
        logging.warning(
            f"[SECURITY VIOLATION] Attempted to access file outside allowed directory: "
            f"requested_path='{file_path}', "
            f"resolved_path='{path}', "
            f"allowed_directory='{allowed_path}'"
        )
        raise PermissionError(
            f"Access denied: File '{file_path}' is outside the allowed directory '{allowed_path}'. "
            f"read_file can only read files within the stata-mcp-folder."
        )

    if not path.exists():
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    if is_beta and config.IS_UNIX:
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
    # if not beta version and Windows user using read file text directly.
    try:
        with open(path, "r", encoding=encoding) as file:
            log_content = file.read()
        logging.info(f"Successfully read file: {file_path}")
        return _trim_lines(log_content, lines)
    except IOError as e:
        logging.error(f"Failed to read file {file_path}: {str(e)}")
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


def write_dofile(content: str, encoding: str = None) -> str:
    """
    Write stata code to a dofile and return the do-file path.

    Args:
        content (str): The stata code content which will be writen to the designated do-file.
        encoding (str): The encoding method for the dofile, default -> 'utf-8'

    Returns:
        the do-file path

    Notes:
        Please be careful about the first command in dofile should be use data.
        For avoiding make mistake, you can generate stata-code with the function from `StataCommandGenerator` class.
        Please avoid writing any code that draws graphics or requires human intervention for uncertainty bug.
        If you find something went wrong about the code, you can use the function from `StataCommandGenerator` class.

    Warnings:
        This tool will be removed in an upcoming version because modern coding agents
        (Claude Code, Codex, Cursor, etc.) have native file writing capabilities.
        If you are using such agents, consider creating a 'code' directory to manage
        your Stata do-files directly.

    """
    file_path = config.STATA_MCP_FOLDER.DO / f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.do"
    encoding = encoding or "utf-8"
    try:
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        logging.info(f"Successful write dofile to {file_path}")
    except Exception as e:
        logging.error(f"Failed to write dofile to {file_path}: {str(e)}")
    return file_path.as_posix()


ToolFunc = Callable[..., Any]

_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "stata_do": {
        "description": (
            "Execute a Stata do-file and return the execution log. "
            "Accepts a do-file path, runs it via the configured Stata executable, "
            "and can optionally read log content only when return-code errors are detected."
        ),
        "func": stata_do,
        "profiles": {"core", "all"},
    },
    "get_data_info": {
        "description": (
            "Get descriptive statistics and a data preview for a data file "
            "(dta, csv, xlsx). Returns overview, variable details, "
            "and optional head rows filtered by requested variables."
        ),
        "func": get_data_info,
        "profiles": {"core", "all"},
    },
    "help": {
        "description": (
            "Retrieve documentation and usage information for a Stata command. "
            "Use when you need to understand a command's syntax, options, "
            "or troubleshoot errors before running it."
        ),
        "func": help,
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
        "profiles": {"all"},
    },
    "ado_package_install": {
        "description": (
            "Install a Stata ado package from SSC, GitHub, or net sources. "
            "Use before running commands that require third-party packages."
        ),
        "func": ado_package_install,
        "profiles": {"all"},
    },
    "write_dofile": {
        "description": "write the stata-code to dofile",
        "func": write_dofile,
        "profiles": {"all"},
        "deprecated": True,
    },
}

_registered_profile: str | None = None


def register_tools(server: FastMCP, profile: str = "all") -> None:
    """Register tools and resources based on a selected profile."""
    global _registered_profile

    if profile not in {"core", "all"}:
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
        if meta.get("deprecated") and not config.ENABLE_WRITE_DOFILE:
            continue
        if profile not in meta["profiles"]:
            continue

        tool_func: ToolFunc | None = meta.get("func")
        if tool_func is None:
            logging.warning("Skipping tool '%s' because its registry entry has no callable func.", name)
            continue
        server.tool(name=name, description=meta["description"])(tool_func)

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
    "write_dofile",

    # Utilities
    "read_log",
    "ado_package_install",
]

if config.IS_UNIX:
    __all__.extend([
        "help"
    ])
