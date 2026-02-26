#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _cli.py

import argparse
import sys
from importlib.metadata import version


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

    elif args.command == "install":
        from ..utils.Installer import Installer
        installer = Installer(sys_os=sys.platform)
        if args.all:
            installer.install("all")
            sys.exit(0)  # if all clients are installed, exit with 0
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
