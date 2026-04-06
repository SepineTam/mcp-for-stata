"""CLI command handlers."""

from __future__ import annotations

import json
import sys
import warnings
from argparse import Namespace
from importlib.metadata import PackageNotFoundError

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
    warnings.simplefilter("default", DeprecationWarning)
    warnings.warn(
        "'--usable' is deprecated and will be removed in v1.16.0. "
        "Use 'stata-mcp doctor' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ..utils.doctor import format_report_text, run_doctor

    config = Config()
    report = run_doctor(config)
    print(format_report_text(report))
    return 1 if report.has_failures else 0


def handle_doctor(args: Namespace) -> int:
    """Handle the doctor subcommand."""
    from ..utils.doctor import AVAILABLE_CHECKS, format_report_text, run_doctor

    if args.checks:
        invalid_checks = sorted(set(args.checks) - set(AVAILABLE_CHECKS))
        if invalid_checks:
            print(
                "Unknown check name(s): "
                + ", ".join(invalid_checks)
                + f". Available checks: {', '.join(AVAILABLE_CHECKS)}",
                file=sys.stderr,
            )
            return 2

    try:
        config = Config()
    except Exception as error:
        print(f"Failed to initialize configuration for doctor: {error}", file=sys.stderr)
        return 1

    report = run_doctor(config, only_checks=args.checks)

    if args.output_json:
        print(report.to_json())
    else:
        print(format_report_text(report, verbose=args.verbose))

    return 1 if report.has_failures else 0


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


def handle_update(args: Namespace) -> int:
    """Handle the update subcommand."""
    from ..utils.update import (
        InstallMethod,
        build_update_command,
        detect_install_method,
        execute_update,
        get_current_version,
        get_latest_version,
    )

    try:
        if args.check:
            try:
                current = get_current_version()
            except PackageNotFoundError:
                print("stata-mcp is not installed in this Python environment.")
                return 1

            latest, latest_error = get_latest_version()
            if latest is None:
                print(latest_error or "Failed to check for updates.")
                return 1

            print(f"Current: v{current}")
            print(f"Latest:  v{latest}")
            if current == latest:
                print("Up to date")
            else:
                print(f"Update available: v{current} → v{latest}")
            return 0

        selected_method = None
        if args.method != "auto":
            selected_method = InstallMethod(args.method)

        if args.dry_run:
            try:
                current = get_current_version()
            except PackageNotFoundError:
                print("stata-mcp is not installed in this Python environment.")
                return 1

            latest, latest_error = get_latest_version()
            detected_method = selected_method or detect_install_method()

            print(f"Current version: {current}")
            if latest is None:
                print("Latest version:  unavailable")
                print(f"Latest check:    {latest_error or 'Unknown error'}")
            else:
                print(f"Latest version:  {latest}")
            print(f"Install method:  {detected_method.value}")

            update_command = build_update_command(detected_method)
            if update_command:
                print(f"Update command:  {' '.join(update_command)}")
            elif detected_method == InstallMethod.UVX:
                print("Note: uvx always uses latest, no update needed")
            elif detected_method == InstallMethod.EDITABLE:
                print("Note: editable install, use git pull + pip install -e .")
            elif detected_method == InstallMethod.UNKNOWN:
                print("Note: unknown install method; auto update is blocked for safety.")

            return 0

        success, message = execute_update(selected_method)
        print(message)
        return 0 if success else 1
    except ImportError as error:
        print(f"Failed to load update dependencies: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(error, file=sys.stderr)
        return 1
