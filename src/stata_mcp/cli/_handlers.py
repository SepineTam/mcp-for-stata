"""CLI command handlers."""

from __future__ import annotations

import json
import logging
import sys
import warnings
from argparse import Namespace
from importlib.metadata import PackageNotFoundError


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
    from ..config import Config

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
    from ..config import Config
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
        config = Config(config_file=getattr(args, "config_file", None))
    except Exception as error:
        print(f"Failed to initialize configuration for doctor: {error}", file=sys.stderr)
        return 1

    report = run_doctor(config, only_checks=args.checks, dry_run=args.dry_run)

    if args.output_json:
        print(report.to_json())
    else:
        print(format_report_text(report, verbose=args.verbose))

    return 1 if report.has_failures else 0


def handle_tool(args: Namespace) -> int:
    """Handle the tool subcommand."""
    from ..api import ado_package_install, get_data_info, read_log, stata_do, stata_help

    try:
        config_file = getattr(args, "config_file", None)
        config_kwargs = {"config_file": config_file} if config_file is not None else {}
        if args.tool_action == "ado-install":
            if not args.yes and not _confirm_ado_install(args):
                print("Ado package installation cancelled.", file=sys.stderr)
                return 1
            result = ado_package_install(
                package=args.package_name,
                source=args.source,
                is_replace=args.is_replace,
                package_source_from=args.package_source_from,
                **config_kwargs,
            )
        elif args.tool_action == "do":
            result = stata_do(
                dofile_path=args.dofile_path,
                log_file_name=args.log_file_name,
                read_log_when_error=args.is_read_log,
                is_replace_log=args.is_replace_log,
                enable_smcl=args.enable_smcl,
                timeout=args.timeout,
                **config_kwargs,
            )
        elif args.tool_action == "help":
            result = stata_help(
                cmd=args.stata_command,
                replace=args.replace,
                **config_kwargs,
            )
        elif args.tool_action == "data-info":
            result = get_data_info(
                data_path=args.data_path,
                vars_list=args.vars_list,
                encoding=args.encoding,
                **config_kwargs,
            )
        elif args.tool_action == "read-log":
            result = read_log(
                file_path=args.file_path,
                encoding=args.encoding,
                output_format=args.output_format,
                **config_kwargs,
            )
        else:
            return 2
    except Exception as error:
        print(error, file=sys.stderr)
        return 1

    print_cli_result(result)
    return 0


def _confirm_ado_install(args: Namespace) -> bool:
    """Prompt for confirmation before a CLI ado package installation."""
    source_details = (
        f", source URL={args.package_source_from!r}"
        if args.package_source_from is not None
        else ""
    )
    prompt = (
        "Install third-party Stata package "
        f"{args.package_name!r} from {args.source!r}"
        f"{source_details}, replace={args.is_replace!r}? [y/N]: "
    )
    try:
        response = input(prompt)
    except (EOFError, KeyboardInterrupt):
        return False
    return response.strip().lower() in {"y", "yes"}


def handle_config(args: Namespace) -> int:
    """Handle the config subcommand."""
    from ..config import Config

    cfg = Config(config_file=getattr(args, "config_file", None))

    if args.config_action is None:
        content = cfg.read_config_text()
        if content:
            print(content, end="" if content.endswith("\n") else "\n")
        else:
            if cfg.is_debug_config:
                print(f"No config file found at: {cfg.config_file}")
            else:
                paths = ", ".join(str(path) for path in cfg.config_files)
                print(f"No config file found at: {paths}")
        return 0

    if args.config_action == "set":
        if args.key == "cli":
            value = cfg.set_stata_cli(args.value)
            print(f"Set STATA.STATA_CLI = {value}")
        return 0

    if args.config_action == "show":
        if args.dot_key == "cli":
            value = cfg.get_stata_cli()
        else:
            try:
                value = cfg.get_value(args.dot_key)
            except KeyError as error:
                print(error, file=sys.stderr)
                return 1
        if value is None:
            print(f"{args.dot_key} is not set")
        else:
            print(value)
        return 0

    if args.config_action == "edit":
        try:
            cfg.edit_value(args.dot_key, args.value)
        except KeyError as error:
            print(error, file=sys.stderr)
            return 1
        print(f"Updated {args.dot_key} = {args.value}")
        return 0

    return 2


def handle_install(args: Namespace) -> int:
    """Handle the install subcommand."""
    from ..utils.installer import Installer, colored_stdout

    installer = Installer(sys_os=sys.platform)

    client = args.client
    json_file = args.json_file
    json_index = args.json_index

    # 1. bare `stata-mcp install` -> equivalent to --all
    if not args.all and not client and not json_file and not json_index:
        args.all = True

    # 2. --all wins, ignore everything else
    if args.all:
        with colored_stdout():
            installer.install_all()
        return 0

    # 3. --json-index requires --json-file
    if json_index and not json_file:
        print("[ERROR]\t--json-index must be used together with --json-file", file=sys.stderr)
        return 1

    # 4. opencode / codex / hermes have client-specific schemas; ignore custom path
    if client in {"opencode", "codex", "hermes", "hermes-agent"}:
        with colored_stdout():
            if json_file or json_index:
                print(
                    f"[WARN]\t--json-file/--json-index are ignored for {client}; "
                    "using the default config path."
                )
            installer.install(client)
            print(f"[DONE]\tStata-MCP has been installed to {client}.")
        return 0

    # 5. -c CLIENT (generic-JSON clients)
    if client:
        if json_file:
            key = _parse_json_index(json_index) if json_index else Installer.CLIENT_DEFAULT_KEY[client]
            with colored_stdout():
                installer.install_to_json_config(json_file, key=key)
                print(f"[DONE]\tStata-MCP has been installed to {json_file}.")
            return 0
        with colored_stdout():
            installer.install(client)
            print(f"[DONE]\tStata-MCP has been installed to {client}.")
        return 0

    # 6. only --json-file (no -c)
    key = _parse_json_index(json_index) if json_index else "mcpServers"
    with colored_stdout():
        installer.install_to_json_config(json_file, key=key)
        print(f"[DONE]\tStata-MCP has been installed to {json_file}.")
    return 0


def _parse_json_index(raw: str) -> "list[str]":
    """Split a dot-separated nested key path into a list of segments."""
    return [segment for segment in raw.split(".") if segment]


def handle_verify(args: Namespace) -> int:
    """Handle the verify subcommand."""
    from ..utils.installer import (
        Verifier,
        VerifyOutcome,
        paint_green,
        paint_red,
        paint_yellow,
    )

    client = args.client
    file = args.file
    index = args.index
    key = args.key

    if client:
        if file is not None:
            print(
                "warning: -c takes precedence; -f is ignored",
                file=sys.stderr,
            )
        if index is not None:
            print(
                "warning: -c takes precedence; --index is ignored",
                file=sys.stderr,
            )
        result = Verifier(sys_os=sys.platform).verify_client(client, key=key)
    elif file is not None:
        result = Verifier(sys_os=sys.platform).verify_file(file, index=index, key=key)
    else:
        print(
            "error: must specify one of -c/--client or -f/--file",
            file=sys.stderr,
        )
        return 5

    if result.outcome == VerifyOutcome.VERIFIED:
        print(paint_green(f"Verified: stata-mcp is installed at {result.location}."))
        return 0
    if result.outcome == VerifyOutcome.WARNING:
        for w in result.warnings:
            print(paint_yellow(w))
        print(paint_green(f"Verified: stata-mcp is installed at {result.location}."))
        return 0
    print(paint_red(f"Failed: {result.reason}."))
    return result.exit_code


def handle_server(args: Namespace) -> None:
    """Handle the default behavior of starting the MCP server."""
    from ..mcp_servers import register_tools
    from ..mcp_servers import stata_mcp as mcp

    if getattr(args, "unsafe_profile", False):
        profile = "unsafe"
    elif getattr(args, "core_profile", False):
        profile = "core"
    elif getattr(args, "all_profile", False):
        profile = "all"
    else:
        profile = "all"

    logging.info("Starting server with tool profile: %s", profile)
    register_tools(mcp, profile=profile)

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
