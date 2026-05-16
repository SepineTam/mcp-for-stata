"""CLI argument parser definitions."""

from __future__ import annotations

import argparse
import warnings
from importlib.metadata import PackageNotFoundError, version
from typing import Callable

BoolConverter = Callable[[str], bool]


def _parse_bool(value: str) -> bool:
    """Convert CLI boolean input to a Python bool."""
    return str(value).lower() == "true"


def add_bool_argument(
    parser: argparse.ArgumentParser,
    name: str,
    default: bool,
    help_text: str,
    *,
    converter: BoolConverter = _parse_bool,
) -> None:
    """Add a CLI boolean flag that accepts explicit true or false values."""
    parser.add_argument(
        name,
        type=converter,
        choices=[True, False],
        default=default,
        metavar="{true,false}",
        help=f"{help_text} (default: {str(default).lower()})",
    )


def create_root_parser() -> argparse.ArgumentParser:
    """Create the root parser with global options."""
    try:
        package_version = version("stata-mcp")
    except PackageNotFoundError:
        package_version = "0.0.0"
        warnings.warn(
            "Package metadata for 'stata-mcp' is unavailable. Falling back to version '0.0.0'.",
            RuntimeWarning,
            stacklevel=2,
        )

    parser = argparse.ArgumentParser(
        prog="stata-mcp",
        description="Stata-MCP command line interface",
        add_help=True,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {package_version}",
        help="show version information",
    )
    parser.add_argument(
        "-t",
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="MCP server transport method (default: stdio)",
    )
    parser.add_argument(
        "-u",
        "--usable",
        action="store_true",
        help="(Deprecated) Check whether Stata-MCP can be used on this computer",
    )
    return parser


def add_agent_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the agent subcommand parser."""
    agent_parser = subparsers.add_parser(
        "agent",
        help="(Deprecated) Run Stata-MCP as agent mode",
        description="WARNING: Agent mode is deprecated and will be removed in a future version. Use MCP server mode instead.",
    )
    agent_subparsers = agent_parser.add_subparsers(dest="agent_action")

    agent_run_parser = agent_subparsers.add_parser("run", help="Start agent")
    agent_run_parser.add_argument(
        "--work-dir",
        default="./",
        help="Working directory for agent (default: current directory)",
    )
    return agent_parser


def add_server_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the server subcommand parser."""
    server_parser = subparsers.add_parser(
        "server",
        help="Start MCP server (default behavior when no subcommand is given)",
    )
    profile_group = server_parser.add_mutually_exclusive_group()
    profile_group.add_argument(
        "--core",
        action="store_true",
        dest="core_profile",
        help="Register only core tools (stata_do, get_data_info, help)",
    )
    profile_group.add_argument(
        "--all",
        action="store_true",
        dest="all_profile",
        help="Register all tools (default)",
    )
    server_parser.add_argument(
        "-t",
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="MCP server transport method (default: stdio)",
    )
    return server_parser


def add_tool_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the tool subcommand parser."""
    tool_parser = subparsers.add_parser("tool", help="Run local Stata tools through the API module")
    tool_subparsers = tool_parser.add_subparsers(dest="tool_action")

    tool_ado_install_parser = tool_subparsers.add_parser(
        "ado-install",
        help="Install an ado package through the API module",
    )
    tool_ado_install_parser.add_argument("package_name", help="Ado package name")
    tool_ado_install_parser.add_argument(
        "--source",
        choices=["ssc", "net", "github"],
        default="ssc",
        help="Package source (default: ssc)",
    )
    tool_ado_install_parser.add_argument(
        "--package-source-from",
        default=None,
        help="Net install source URL used when --source net",
    )
    add_bool_argument(
        tool_ado_install_parser,
        "--is-replace",
        default=True,
        help_text="Replace existing package files when supported",
    )

    tool_do_parser = tool_subparsers.add_parser("do", help="Run a do-file through the API module")
    tool_do_parser.add_argument("dofile_path", help="Path to the do-file")
    tool_do_parser.add_argument(
        "--log-file-name",
        default=None,
        help="Optional log file name without extension",
    )
    add_bool_argument(
        tool_do_parser,
        "--is-read-log",
        default=True,
        help_text="Read log content after execution",
    )
    add_bool_argument(
        tool_do_parser,
        "--is-replace-log",
        default=True,
        help_text="Replace the existing log file",
    )
    add_bool_argument(
        tool_do_parser,
        "--enable-smcl",
        default=True,
        help_text="Generate the SMCL log file",
    )

    tool_help_parser = tool_subparsers.add_parser(
        "help",
        help="Read Stata help output through the API module",
    )
    tool_help_parser.add_argument("stata_command", help="Stata command name")
    add_bool_argument(
        tool_help_parser,
        "--is-read-log",
        default=True,
        help_text="Read log content after execution",
    )
    add_bool_argument(
        tool_help_parser,
        "--enable-smcl",
        default=True,
        help_text="Generate the SMCL log file",
    )

    tool_data_info_parser = tool_subparsers.add_parser(
        "data-info",
        help="Read dataset metadata through the API module",
    )
    tool_data_info_parser.add_argument("data_path", help="Path to the data file")
    tool_data_info_parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding for supported text-based data files (default: utf-8)",
    )
    tool_data_info_parser.add_argument(
        "--vars-list",
        nargs="+",
        default=None,
        help="Optional variable names to inspect",
    )

    tool_read_log_parser = tool_subparsers.add_parser(
        "read-log",
        help="Read a Stata log through the API module",
    )
    tool_read_log_parser.add_argument("file_path", help="Path to the log file")
    tool_read_log_parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Log file encoding (default: utf-8)",
    )
    tool_read_log_parser.add_argument(
        "--output-format",
        choices=["full", "core", "dict"],
        default="core",
        help="Output format for supported .log and .smcl files (default: core)",
    )
    return tool_parser


def add_doctor_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the doctor subcommand parser."""
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Run diagnostics to check stata-mcp health status",
    )
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output report in JSON format",
    )
    doctor_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information for each check",
    )
    doctor_parser.add_argument(
        "--check",
        action="append",
        dest="checks",
        default=None,
        help="Run only specified check names (repeatable)",
    )
    doctor_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview cleanup actions without deleting files",
    )
    return doctor_parser


def add_config_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the config subcommand parser."""
    config_parser = subparsers.add_parser("config", help="Show and manage Stata-MCP configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_action")

    config_set_parser = config_subparsers.add_parser("set", help="Set a config value")
    config_set_parser.add_argument(
        "key",
        choices=["cli"],
        help="Config key to set",
    )
    config_set_parser.add_argument(
        "value",
        nargs="?",
        default=None,
        help="Value to set. If omitted, auto-detect from StataFinder.",
    )

    config_show_parser = config_subparsers.add_parser("show", help="Show a config value")
    config_show_parser.add_argument(
        "dot_key",
        help="Config key to show. Use 'cli' as shorthand for STATA.STATA_CLI, or Section.Key notation.",
    )

    config_edit_parser = config_subparsers.add_parser(
        "edit",
        help="Edit a config value by section.key",
    )
    config_edit_parser.add_argument(
        "dot_key",
        help="Dot-notation key, e.g. STATA.STATA_CLI",
    )
    config_edit_parser.add_argument(
        "value",
        help="New value",
    )
    return config_parser


def add_install_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the install subcommand parser."""
    install_parser = subparsers.add_parser("install", help="Install Stata-MCP to MCP clients")
    install_parser.add_argument(
        "-c",
        "--client",
        choices=["claude", "cc", "claude-code", "gemini", "cursor", "cline", "codex",
                 "opencode", "openclaw", "hermes", "hermes-agent"],
        default=None,
        help="Target client. Omit -c (and --json-file) to install to all clients.",
    )
    install_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Install to all supported clients",
    )
    install_parser.add_argument(
        "--json-file",
        type=str,
        help="Custom target client config file path",
    )
    install_parser.add_argument(
        "--json-index",
        type=str,
        default=None,
        help="Dot-separated nested key path (e.g. 'mcp.servers'). Only valid with --json-file.",
    )
    return install_parser


def add_sandbox_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the sandbox-install subcommand parser."""
    sandbox_parser = subparsers.add_parser(
        "sandbox-install",
        help="Install Docker-based Stata-MCP to MCP client",
    )
    sandbox_parser.add_argument(
        "-c",
        "--client",
        choices=["claude", "cc", "claude-code", "gemini", "cursor", "cline", "codex", "opencode"],
        default="claude",
        help="Target client (default: claude)",
    )
    sandbox_parser.add_argument(
        "-l",
        "--license-file",
        required=True,
        help="Path to Stata license file (stata.lic)",
    )
    sandbox_parser.add_argument(
        "--work-dir",
        default="./",
        help="Working directory for Stata operations (default: current directory)",
    )
    sandbox_parser.add_argument(
        "--cpus",
        type=float,
        default=None,
        help="CPU core limit for container (e.g., 2.0)",
    )
    sandbox_parser.add_argument(
        "--memory",
        type=str,
        default=None,
        help="Memory limit for container (e.g., 4g, 512m)",
    )
    sandbox_parser.add_argument(
        "-V",
        "--version",
        choices=["19_5", "18_5", "18"],
        default="19_5",
        help="Stata version (default: 19_5)",
    )
    sandbox_parser.add_argument(
        "-e",
        "--edition",
        choices=["mp", "se", "be"],
        default="mp",
        help="Stata edition: mp (Multi-processor), se (Standard), be (Basic) (default: mp)",
    )
    sandbox_parser.add_argument(
        "--tag",
        default="latest",
        help="Docker image tag (default: latest)",
    )
    sandbox_parser.add_argument(
        "-s",
        "--source",
        choices=["github", "docker"],
        default="github",
        help="Docker image registry source: github (ghcr.io) or docker (DockerHub) (default: github)",
    )
    return sandbox_parser


def add_update_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the update subcommand parser."""
    update_parser = subparsers.add_parser("update", help="Update stata-mcp to latest version")
    update_parser.add_argument(
        "--method",
        choices=["auto", "pip", "uv-tool", "homebrew"],
        default="auto",
        help="Force specific update method (default: auto-detect)",
    )
    update_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show detected method and available update without executing",
    )
    update_parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if a newer version is available",
    )
    return update_parser
