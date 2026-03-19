"""CLI command handlers."""

from __future__ import annotations

import json
import sys
from argparse import Namespace

from ..config import Config


def print_cli_result(result: object) -> None:
    """Print API results consistently for CLI usage."""
    if result is None:
        return

    if isinstance(result, dict):
        if "log_content" in result and isinstance(result["log_content"], dict):
            preferred_content = result["log_content"].get("text") or result["log_content"].get("smcl")
            if preferred_content:
                print(preferred_content)
                return
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if isinstance(result, (list, tuple)):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(result)


def handle_usable() -> int:
    """Handle the --usable flag."""
    from ..utils.usable import usable

    return usable()


def handle_agent(args: Namespace) -> None:
    """Handle the agent subcommand."""
    if args.agent_action == "run":
        from ..agent_as import REPLAgent

        agent = REPLAgent(work_dir=args.work_dir)
        agent.run()


def handle_tool(args: Namespace) -> int:
    """Handle the tool subcommand."""
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
                output_format=args.output_format,
            )
        else:
            return 2
    except Exception as error:
        print(error, file=sys.stderr)
        return 1

    print_cli_result(result)
    return 0


def handle_config(args: Namespace) -> int:
    """Handle the config subcommand."""
    cfg = Config()

    if args.config_target is None:
        content = cfg.read_config_text()
        if content:
            print(content, end="" if content.endswith("\n") else "\n")
        else:
            print(f"No config file found at: {cfg.config_file}")
        return 0

    if args.config_target == "cli" and args.config_cli_action == "set":
        value = cfg.set_stata_cli(args.value)
        print(f"Set STATA.STATA_CLI = {value}")
        return 0

    return 2


def handle_install(args: Namespace) -> int:
    """Handle the install subcommand."""
    from ..utils.Installer import Installer

    installer = Installer(sys_os=sys.platform)
    if args.all:
        installer.install_all()
        return 0
    if args.json_file:
        installer.install_to_json_config(args.json_file)
        return 0

    installer.install(args.client)
    print(f"Stata-MCP has been installed to {args.client}.")
    return 0


def handle_sandbox(args: Namespace) -> int:
    """Handle the sandbox-install subcommand."""
    from ..utils.Installer.installer import InstallerDockerMode

    image_name = f"stata-mcp_{args.version}_{args.edition}:{args.tag}"
    if args.source.lower() == "github":
        image = f"ghcr.io/sepinetam/{image_name}"
    else:
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
    return 0


def handle_server(args: Namespace) -> None:
    """Handle the default behavior of starting the MCP server."""
    from ..mcp_servers import stata_mcp as mcp

    transport = args.transport
    if transport == "http":
        transport = "streamable-http"
    mcp.run(transport=transport)
