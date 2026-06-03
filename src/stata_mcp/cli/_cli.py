#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _cli.py

from __future__ import annotations

import sys

from ._handlers import (
    handle_config,
    handle_doctor,
    handle_install,
    handle_server,
    handle_tool,
    handle_update,
    handle_usable,
    handle_verify,
)
from ._parsers import (
    add_config_parser,
    add_doctor_parser,
    add_install_parser,
    add_server_parser,
    add_tool_parser,
    add_update_parser,
    add_verify_parser,
    create_root_parser,
)


def main() -> None:
    """Entry point for the command line interface."""
    parser = create_root_parser()
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_doctor_parser(subparsers)
    add_server_parser(subparsers)
    tool_parser = add_tool_parser(subparsers)
    config_parser = add_config_parser(subparsers)
    add_install_parser(subparsers)
    add_update_parser(subparsers)
    add_verify_parser(subparsers)

    args = parser.parse_args()

    if args.usable:
        sys.exit(handle_usable())

    if args.command == "tool":
        exit_code = handle_tool(args)
        if exit_code == 2:
            tool_parser.print_help()
        sys.exit(exit_code)

    if args.command == "doctor":
        sys.exit(handle_doctor(args))

    if args.command == "server":
        handle_server(args)
        return

    if args.command == "config":
        exit_code = handle_config(args)
        if exit_code == 2:
            config_parser.print_help()
        sys.exit(exit_code)

    if args.command == "install":
        sys.exit(handle_install(args))

    if args.command == "update":
        sys.exit(handle_update(args))

    if args.command == "verify":
        sys.exit(handle_verify(args))

    handle_server(args)
