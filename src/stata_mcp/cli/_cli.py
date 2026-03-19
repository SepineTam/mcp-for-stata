#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _cli.py

import argparse
import json
import sys
from importlib.metadata import version

from ..config import Config


def _add_bool_argument(parser: argparse.ArgumentParser, name: str, default: bool, help_text: str) -> None:
    """Add a CLI boolean flag that accepts explicit true or false values."""
    parser.add_argument(
        name,
        type=lambda value: str(value).lower() == "true",
        choices=[True, False],
        default=default,
        metavar="{true,false}",
        help=f"{help_text} (default: {str(default).lower()})",
    )


def _print_cli_result(result) -> None:
    """Print API results consistently for CLI usage."""
    if result is None:
        return

    if isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if isinstance(result, (list, tuple)):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(result)


def main() -> None:
    """Entry point for the command line interface."""
    parser = argparse.ArgumentParser(
        prog="stata-mcp",
        description="Stata-MCP command line interface",
        add_help=True)

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {version('stata-mcp')}",
        help="show version information",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # MCP server options (default behavior)
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
        help="Check whether Stata-MCP can be used on this computer",
    )

    # Agent subcommand
    agent_parser = subparsers.add_parser(
        "agent",
        help="Run Stata-MCP as agent mode"
    )
    agent_subparsers = agent_parser.add_subparsers(dest="agent_action")

    agent_run_parser = agent_subparsers.add_parser("run", help="Start agent")
    agent_run_parser.add_argument(
        "--work-dir",
        default="./",
        help="Working directory for agent (default: current directory)",
    )

    # Tool subcommand
    tool_parser = subparsers.add_parser(
        "tool",
        help="Run local Stata tools through the API module"
    )
    tool_subparsers = tool_parser.add_subparsers(dest="tool_action")

    tool_ado_install_parser = tool_subparsers.add_parser(
        "ado-install",
        help="Install an ado package through the API module"
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
    _add_bool_argument(
        tool_ado_install_parser,
        "--is-replace",
        default=True,
        help_text="Replace existing package files when supported",
    )

    tool_do_parser = tool_subparsers.add_parser(
        "do",
        help="Run a do-file through the API module"
    )
    tool_do_parser.add_argument("dofile_path", help="Path to the do-file")
    tool_do_parser.add_argument(
        "--log-file-name",
        default=None,
        help="Optional log file name without extension",
    )
    _add_bool_argument(
        tool_do_parser,
        "--is-read-log",
        default=True,
        help_text="Read log content after execution",
    )
    _add_bool_argument(
        tool_do_parser,
        "--is-replace-log",
        default=True,
        help_text="Replace the existing log file",
    )
    _add_bool_argument(
        tool_do_parser,
        "--enable-smcl",
        default=True,
        help_text="Generate the SMCL log file",
    )

    tool_help_parser = tool_subparsers.add_parser(
        "help",
        help="Read Stata help output through the API module"
    )
    tool_help_parser.add_argument("stata_command", help="Stata command name")
    _add_bool_argument(
        tool_help_parser,
        "--is-read-log",
        default=True,
        help_text="Read log content after execution",
    )
    _add_bool_argument(
        tool_help_parser,
        "--enable-smcl",
        default=True,
        help_text="Generate the SMCL log file",
    )

    tool_data_info_parser = tool_subparsers.add_parser(
        "data-info",
        help="Read dataset metadata through the API module"
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
        help="Read a Stata log through the API module"
    )
    tool_read_log_parser.add_argument("file_path", help="Path to the log file")
    tool_read_log_parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Log file encoding (default: utf-8)",
    )
    _add_bool_argument(
        tool_read_log_parser,
        "--is-beta",
        default=False,
        help_text="Use the structured beta log reader",
    )
    tool_read_log_parser.add_argument(
        "--output-format",
        choices=["full", "core", "dict"],
        default="dict",
        help="Structured output format when --is-beta true (default: dict)",
    )

    # Config subcommand
    config_parser = subparsers.add_parser(
        "config",
        help="Show and manage Stata-MCP configuration"
    )
    config_subparsers = config_parser.add_subparsers(dest="config_target")

    config_cli_parser = config_subparsers.add_parser(
        "cli",
        help="Manage Stata CLI executable path"
    )
    config_cli_subparsers = config_cli_parser.add_subparsers(dest="config_cli_action")

    config_cli_set_parser = config_cli_subparsers.add_parser(
        "set",
        help="Set STATA_CLI path in config file"
    )
    config_cli_set_parser.add_argument(
        "value",
        nargs="?",
        default=None,
        help="Optional STATA_CLI path. If omitted, auto-detect from StataFinder.",
    )

    # Install subcommand
    install_parser = subparsers.add_parser(
        "install",
        help="Install Stata-MCP to MCP clients"
    )
    install_parser.add_argument(
        "-c",
        "--client",
        choices=["claude", "cc", "gemini", "cursor", "cline", "codex", "opencode"],
        default="claude",
        help="Target client (default: claude)",
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

    # Sandbox-install subcommand
    sandbox_parser = subparsers.add_parser(
        "sandbox-install",
        help="Install Docker-based Stata-MCP to MCP client"
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

    args = parser.parse_args()

    # Handle --usable flag
    if args.usable:
        from ..utils.usable import usable
        sys.exit(usable())

    # Handle subcommands
    if args.command == "agent":
        if args.agent_action == "run":
            from ..agent_as import REPLAgent
            agent = REPLAgent(work_dir=args.work_dir)
            agent.run()
        else:
            agent_parser.print_help()

    elif args.command == "tool":
        from ..api import ado_package_install, get_data_info, read_log, stata_do, stata_help

        try:
            if args.tool_action == "ado-install":
                result = ado_package_install(
                    package=args.package_name,
                    source=args.source,
                    is_replace=args.is_replace,
                    package_source_from=args.package_source_from,
                )
            elif args.tool_action == "do":
                result = stata_do(
                    dofile_path=args.dofile_path,
                    log_file_name=args.log_file_name,
                    is_read_log=args.is_read_log,
                    is_replace_log=args.is_replace_log,
                    enable_smcl=args.enable_smcl,
                )
            elif args.tool_action == "help":
                result = stata_help(
                    cmd=args.stata_command,
                    is_read_log=args.is_read_log,
                    enable_smcl=args.enable_smcl,
                )
            elif args.tool_action == "data-info":
                result = get_data_info(
                    data_path=args.data_path,
                    vars_list=args.vars_list,
                    encoding=args.encoding,
                )
            elif args.tool_action == "read-log":
                result = read_log(
                    file_path=args.file_path,
                    encoding=args.encoding,
                    is_beta=args.is_beta,
                    output_format=args.output_format,
                )
            else:
                tool_parser.print_help()
                sys.exit(2)
        except Exception as error:
            print(error, file=sys.stderr)
            sys.exit(1)

        _print_cli_result(result)
        sys.exit(0)

    elif args.command == "config":
        cfg = Config()
        if args.config_target is None:
            content = cfg.read_config_text()
            if content:
                print(content, end="" if content.endswith("\n") else "\n")
            else:
                print(f"No config file found at: {cfg.config_file}")
            sys.exit(0)

        if args.config_target == "cli":
            if args.config_cli_action == "set":
                value = cfg.set_stata_cli(args.value)
                print(f"Set STATA.STATA_CLI = {value}")
                sys.exit(0)
            config_cli_parser.print_help()
            sys.exit(2)

        config_parser.print_help()
        sys.exit(2)

    elif args.command == "install":
        from ..utils.Installer import Installer
        installer = Installer(sys_os=sys.platform)
        if args.all:
            installer.install_all()
            sys.exit(0)
        if args.json_file:
            installer.install_to_json_config(args.json_file)
            sys.exit(0)
        installer.install(args.client)
        print(f"Stata-MCP has been installed to {args.client}.")
        sys.exit(0)

    elif args.command == "sandbox-install":
        from ..utils.Installer.installer import InstallerDockerMode

        # Build image name based on source
        image_name = f"stata-mcp_{args.version}_{args.edition}:{args.tag}"
        if args.source.lower() == "github":
            image = f"ghcr.io/sepinetam/{image_name}"
        else:  # docker
            image = f"sepinetam/{image_name}"
        installer = InstallerDockerMode(
            license_file_path=args.license_file,
            work_dir=args.work_dir,
            cpus=args.cpus,
            memory=args.memory,
            image=image,
        )
        installer.install(args.client)
        print(f"Docker-based Stata-MCP has been installed to {args.client}.")
        sys.exit(0)

    # Default: Start MCP server
    else:
        from ..mcp_servers import stata_mcp as mcp

        transport = args.transport
        if transport == "http":
            transport = "streamable-http"
        mcp.run(transport=transport)
