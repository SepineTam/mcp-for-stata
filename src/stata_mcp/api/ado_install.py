#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : ado_install.py

from pathlib import Path

from ..stata import GITHUB_Install, NET_Install, SSC_Install
from ._runtime import create_runtime_context
from .stata_do import stata_do
from .write_dofile import write_dofile

SOURCE_MAPPING = {
    "github": GITHUB_Install,
    "net": NET_Install,
    "ssc": SSC_Install,
}


def ado_package_install(
    package: str,
    source: str = "ssc",
    is_replace: bool = True,
    package_source_from: str = None,
    config_file: str | Path | None = None,
    timeout: int = 300,
) -> str:
    """Install an ado package from SSC, net, or GitHub."""
    runtime = create_runtime_context(config_file=config_file, require_stata=True)
    source = source.lower()

    if runtime.is_unix:
        installer_cls = SOURCE_MAPPING.get(source, SSC_Install)
        install_args = [package, package_source_from] if source == "net" else [package]
        install_message = installer_cls(runtime.stata_cli, is_replace, timeout=timeout).install(*install_args)

        if not installer_cls.check_installed_from_msg(install_message):
            error_summary = installer_cls.extract_error_summary(install_message)
            install_message += (
                f"\nError: Failed to install package '{package}' from source '{source}'. "
                f"Details: {error_summary}"
            )
            if source == "github":
                install_message += (
                    "\nPlease check the GitHub repository URL, verify case sensitivity, "
                    "and ensure the github command is installed in Stata."
                )
        else:
            try:
                from ..mcp_servers import _load_help_cls

                _load_help_cls().help(package, replace=True)
            except Exception:
                pass
        return install_message

    from_message = f"from({package_source_from})" if (package_source_from and source == "net") else ""
    replace_flag = "replace" if is_replace else ""
    command = f"{source} install {package}, {replace_flag} {from_message}".strip()
    dofile_path = write_dofile(command, config_file=config_file)
    return str(stata_do(dofile_path, read_log_when_error=False, config_file=config_file).get("log_content", {}))
