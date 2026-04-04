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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal

from mcp.server.fastmcp import FastMCP, Icon

from .config import Config
from .core.types import RAMLimitExceededError
from .guard import GuardValidator
from .monitor import RAMMonitor
from .stata import (
    GITHUB_Install,
    NET_Install,
    SSC_Install,
    StataDo,
    StataHelp,
    StataLog,
)

# Init project config
config = Config()
STATA_MCP_DIRECTORY = config.STATA_MCP_DIRECTORY

# Maybe somebody does not like logging.
# Whatever, left a controller switch `logging STATA_MCP_LOGGING_ON`. Turn off all logging with setting it as false.
# Default Logging Status: File (on), Console (off).
IS_DEBUG = config.IS_DEBUG
ENABLE_WRITE_DOFILE = config.ENABLE_WRITE_DOFILE

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
        IS_DEBUG = True
        stata_mcp_dot_log_file_path = config.LOG_FILE

        # Use RotatingFileHandler to limit file size and implement log rotation
        # Single file max size: 10MB, backup count: 5 (total 6 files including current)
        file_handler = logging.handlers.RotatingFileHandler(
            stata_mcp_dot_log_file_path,
            maxBytes=config.MAX_BYTES,  # 10MB
            backupCount=config.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        logging_handlers.append(file_handler)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=logging_handlers
    )
else:
    # Disable all logging by setting level above CRITICAL
    logging.disable(logging.CRITICAL + 1)

# Initialize optional parameters
SYSTEM_OS = config.SYSTEM_OS
IS_UNIX = config.IS_UNIX

# Get working directory from environment variable (fallback: auto-detect writable directory)
WORKING_DIR = config.WORKING_DIR
cwd = WORKING_DIR.get("cwd")

# Use configured output path if available
output_base_path = WORKING_DIR.get("output_base", cwd / "stata-mcp-folder")

log_base_path = WORKING_DIR.get("log_base", output_base_path / "stata-mcp-log")
dofile_base_path = WORKING_DIR.get("dofile_base", output_base_path / "stata-mcp-dofile")
tmp_base_path = WORKING_DIR.get("tmp_base", output_base_path / "stata-mcp-tmp")

logging.info(f"Using {output_base_path.as_posix()} as output base folder")

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

if IS_UNIX:
    _help_cls = None

    def _load_help_cls():
        global _help_cls

        if _help_cls is None:
            # Config help class
            _help_cls = StataHelp(
                stata_cli=config.STATA_CLI,
                project_tmp_dir=tmp_base_path,
                cache_dir=STATA_MCP_DIRECTORY / "help"
            )

        return _help_cls

    # As AI-Client does not support Resource at a board yet, we still keep the resource

    @stata_mcp.resource(
        uri="help://stata/{cmd}",
        name="help",
        description="Get help for a Stata command"
    )
    @stata_mcp.tool(name="help", description="Get help for a Stata command")
    def help(cmd: str) -> str:
        """
        Execute the Stata 'help' command and return its output.

        Args:
            cmd (str): The name of the Stata command to query, e.g., "regress" or "describe".

        Returns:
            str: The help text returned by Stata for the specified command,
                 or a message indicating that no help was found.

        Notes:
            If the returned content starts with 'Cached result for {cmd}', but the output shows the command
            doesn't exist or you believe the cached content is incorrect, and you're certain the command exists,
            set the environment variable STATA_MCP_CACHE_HELP to false. STATA_MCP_SAVE_HELP is same working method.
        """
        return _load_help_cls().help(cmd)


@stata_mcp.tool(name="stata_do", description="Run a stata-code via Stata")
def stata_do(
        dofile_path: str,
        log_file_name: str = None,
        is_read_log: bool = True,
        is_replace_log: bool = True,
        enable_smcl: bool = True
) -> Dict[str, Any]:
    """
    Execute a Stata do-file and return the log file path with optional log content.

    This function runs a Stata do-file using the configured Stata executable and
    generates a log file. It supports cross-platform execution (macOS, Windows, Linux).

    Args:
        dofile_path (str): Absolute or relative path to the Stata do-file (.do) to execute.
        log_file_name (str, optional): Set log file name without a time-string.
            If None, using nowtime as filename. Recommand use default setting (nowtime).
        is_read_log (bool, optional): Whether to read and return the log file content.
            Defaults to True.
        is_replace_log (bool, optional): Whether to replace existing log file.
            Defaults to True.
        enable_smcl (bool, optional): Whether to generate SMCL format log (.smcl).
            SMCL logs preserve hyperlink information from commands like findsj, getiref.
            Defaults to True. (Unix only, Windows support pending)

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "log_file_path" (Dict[str, str]): Paths to generated log files.
                - "text": Path to .log file
                - "smcl": Path to .smcl file (if enable_smcl is True)
            - "log_content" (Dict[str, str]): Content of log files if is_read_log is True.
                - "text": Content of .log file
                - "smcl": Message about reading smcl log
            - "error" (str): Error message if execution fails

    Raises:
        FileNotFoundError: If the specified do-file does not exist
        RuntimeError: If Stata execution fails or log file cannot be generated
        PermissionError: If there are insufficient permissions to execute Stata or write log files

    Example:
        >>> result = stata_do("/path/to/analysis.do", is_read_log=True)
        {
            "log_file_path": {
                "text": "/path/to/your/log/log_file_name.log",
                "smcl": "/path/to/your/log/log_file_name.smcl"
            },
            "log_content": {
                "text": "log content ...",
                ...
            }
        }
        >>> print(result["log_file_path"]["text"])
        /path/to/your/log/log_file_name.log
        >>> print(result["log_file_path"]["smcl"])
        /path/to/your/log/log_file_name.smcl

        >>> result = stata_do("/not/exist/file.do")
        {'error': 'Dofile /not/exist/file.do does not exist'}

    Note:
        - The log file is automatically created in the configured log_file_path directory
        - Supports multiple operating systems through the StataDo executor
        - SMCL format preserves hyperlinks from findsj, getiref commands
        - Security guard blocks execution when dangerous commands are detected
        - To disable security guard, set environment variable STATA_MCP__IS_GUARD=false
    """
    # Convert dofile_path from str to Path
    try:
        dofile_path = Path(dofile_path)
        if not dofile_path.exists():
            return {"error": f"Dofile {dofile_path} does not exist"}
    except Exception as e:
        return {"error": f"Could not recognize dofile_path as pathlib.Path object: {e}"}

    # Security check: validate dofile before execution
    if config.IS_GUARD:
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

    # Initialize monitors
    monitors = []
    if config.IS_MONITOR:
        if config.MAX_RAM_MB is not None:
            monitors.append(RAMMonitor(max_ram_mb=config.MAX_RAM_MB))

    # Initialize Stata executor with system configuration
    stata_executor = StataDo(
        stata_cli=config.STATA_CLI,  # Path to Stata executable
        log_file_path=log_base_path,  # Directory for log files
        is_unix=IS_UNIX,  # Whether the OS is Unix-like
        cwd=cwd,
        monitors=monitors
    )

    # Execute the do-file and get log file path
    logging.info(f"Try to running file {dofile_path}")

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
    if is_read_log:
        log_content = {"text": stata_executor.read_log(text_log)}
        if enable_smcl:
            log_content["smcl"] = (
                "Generally, text log is sufficient."
                "If need to read smcl log, please use `mcp__stata-mcp__read_log` tool."
            )
        result["log_content"] = log_content

    return result


@stata_mcp.tool(name="ado_package_install", description="Install ado package from ssc or github")
def ado_package_install(
        package: str,
        source: str = "ssc",
        is_replace: bool = True,
        package_source_from: str = None
) -> str:
    """
    Install a package from SSC or GitHub

    Args:
        package (str): The name of the package to be installed.
                       for SSC, use package name;
                       for GitHub, use "username/reponame" format.
        source (str): The source to install from. Options are "ssc" (default) or "GitHub".
        is_replace (bool): Whether to force replacement of an existing installation. Defaults to True.
        package_source_from (str): The directory or url of the package from, only works if source == 'net'

    Returns:
        str: The execution log returned by Stata after running the installation.

    Examples:
        >>> ado_package_install(package="outreg2", source="ssc")
        >>> # this would install outreg2 from ssc
        >>> ado_package_install(package="sepinetam/texiv", source="github")
        >>> # this would install texiv from https://github.com/sepinetam/texiv
        -------------------------------------------------------------------------------
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012185447.log
        log type:  text
        opened on:  12 Oct 2025, 18:54:47

        . do "/Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-dofile/20251012185447.do"

        . ssc install outreg2, replace
        checking outreg2 consistency and verifying not already installed...
        all files already exist and are up to date.

        .
        end of do-file

        . log close
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012185447.log
        log type:  text
        closed on:  12 Oct 2025, 18:54:55
        -------------------------------------------------------------------------------

        >>> ado_package_install(command="a_fake_command")
        -------------------------------------------------------------------------------
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012190159.log
        log type:  text
        opened on:  12 Oct 2025, 19:01:59

        . do "/Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-dofile/20251012190159.do"

        . ssc install a_fake_command, replace
        ssc install: "a_fake_command" not found at SSC, type search a_fake_command
        (To find all packages at SSC that start with a, type ssc describe a)
        r(601);

        end of do-file

        r(601);

        . log close
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012190159.log
        log type:  text
        closed on:  12 Oct 2025, 19:02:00
        -------------------------------------------------------------------------------

    Notes:
        Avoid using this tool unless strictly necessary, as SSC installation can be time-consuming
        and may not be required if the package is already present.
    """
    source = source.lower()

    if IS_UNIX:
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
        return stata_do(tmp_file, is_read_log=True).get("log_content")


# =============================================================================
# STATA_MCP.TOOLS: Data Operation Tools
# =============================================================================

@stata_mcp.tool(
    name="get_data_info",
    description="Get descriptive statistics for the data file"
)
def get_data_info(
        data_path: str,
        vars_list: List[str] | None = None,
        encoding: str = "utf-8"
) -> str:
    """
    Get descriptive statistics for the data file.

    Args:
        data_path (str): the data file's absolutely path.
            Current, only allow [dta, csv, tsv, psv, xlsx, xls] file.
        vars_list (List[str] | None): the vars you want to get info (default is None, means all vars).
        encoding (str): data file encoding method (dta file is not supported this arg),
            if you do not know your data ignore this arg, for most of the data files are `UTF-8`.

    Returns:
        str: JSON string containing data summary with following structure:
            - overview: Basic information including source, obs, var_numbers, var_list
            - info_config: Configuration settings (metrics, max_display, decimal_places)
            - vars_detail: Detailed statistics for each variable
            - saved_path: Path to cached JSON file

    Examples:
        >>> get_data_info("/Applications/Stata/auto.dta")
        {
            'overview': {
                'source': '/Applications/Stata/auto.dta',
                'obs': 74,
                'var_numbers': 12,
                'var_list': ['make', 'price', 'mpg', 'rep78', 'headroom', 'trunk',
                             'weight', 'length', 'turn', 'displacement', 'gear_ratio', 'foreign'],
                'hash': 'c557a2db346b522404c2f22932048de4'
            },
            'info_config': {
                'metrics': ['obs', 'mean', 'stderr', 'min', 'max'],
                'max_display': 10,
                'decimal_places': 3
            },
            'vars_detail': {
                'make': {
                    'type': 'str',
                    'var': 'make',
                    'summary': {
                        'obs': 74,
                        'value_list': ['AMC Pacer', 'Chev. Chevette', 'Chev. Nova',
                                      'Honda Accord', 'Merc. Monarch', 'Olds Cutl Supr',
                                      'Olds Delta 88', 'Pont. Catalina', 'Renault Le Car', 'Volvo 260']
                    }
                },
                'price': {
                    'type': 'float',
                    'var': 'price',
                    'summary': {
                        'obs': 74, 'mean': 6165.257, 'stderr': 342.872, 'min': 3291.0, 'max': 15906.0,
                        'q1': 4220.25, 'med': 5006.5, 'q3': 6332.25, 'skewness': 1.688, 'kurtosis': 2.034
                    }
                },
                'mpg': {
                    'type': 'float',
                    'var': 'mpg',
                    'summary': {
                        'obs': 74, 'mean': 21.297, 'stderr': 0.673, 'min': 12.0, 'max': 41.0,
                        'q1': 18.0, 'med': 20.0, 'q3': 24.75, 'skewness': 0.968, 'kurtosis': 1.13
                    }
                },
                'rep78': {
                    'type': 'float',
                    'var': 'rep78',
                    'summary': {
                        'obs': 69, 'mean': 3.406, 'stderr': 0.119, 'min': 1.0, 'max': 5.0,
                        'q1': 3.0, 'med': 3.0, 'q3': 4.0, 'skewness': -0.058, 'kurtosis': -0.254
                    }
                },
                ...
            },
            'saved_path': '$cwd/stata-mcp-folder/stata-mcp-tmp/data_info__auto_dta__hash_c557a2db346b.json'
        }
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

    data_info = data_info_cls(data_path, vars_list, encoding=encoding, cache_dir=tmp_base_path)
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

@stata_mcp.tool(
    name="read_log",
    description="Reads a log file and returns its content as a string"
)
def read_log(
        file_path: str,
        encoding: str = "utf-8",
        is_beta: bool = False,
        *,
        output_format: Literal["full", "core", "dict"] = "dict",
) -> str:
    """
    Reads a log file and returns its content as a string.

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
        path.relative_to(output_base_path.resolve())
    except ValueError:
        allowed_path = output_base_path.resolve()
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

    if is_beta and IS_UNIX:
        loger = StataLog.from_path(file_path, encoding=encoding)
        if output_format not in ["full", "core", "dict"]:
            raise ValueError(f"Invalid output_format: {output_format}")
        elif output_format == "full":
            return loger.read_plain_text()
        elif output_format == "core":
            return loger.read_without_framework()
        elif output_format == "dict":
            return str(loger.read_as_dict())
    # if not beta version and Windows user using read file text directly.
    try:
        with open(path, "r", encoding=encoding) as file:
            log_content = file.read()
        logging.info(f"Successfully read file: {file_path}")
        return log_content
    except IOError as e:
        logging.error(f"Failed to read file {file_path}: {str(e)}")
        raise IOError(f"An error occurred while reading the file: {e}")


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
    file_path = dofile_base_path / f"{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S%f')}.do"
    encoding = encoding or "utf-8"
    try:
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        logging.info(f"Successful write dofile to {file_path}")
    except Exception as e:
        logging.error(f"Failed to write dofile to {file_path}: {str(e)}")
    return file_path.as_posix()


if ENABLE_WRITE_DOFILE:
    # When stata-mcp was first developed, agent capabilities were still immature.
    # However, modern agents like Claude Code, Codex, and Cursor now have native
    # file modification capabilities with better implementations. Additionally,
    # with Claude Code's LSP support, write_dofile has become obsolete.
    # This tool will be completely removed in a few versions.
    stata_mcp.tool(
        name="write_dofile",
        description="write the stata-code to dofile"
    )(write_dofile)

__all__ = [
    "stata_mcp",

    # Functions (Core)
    "get_data_info",
    "stata_do",
    "write_dofile",

    # Utilities
    "read_log",
    "ado_package_install",
]

if IS_UNIX:
    __all__.extend([
        "help"
    ])
