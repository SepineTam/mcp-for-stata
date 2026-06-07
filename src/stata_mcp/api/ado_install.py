#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : ado_install.py

from pathlib import Path

from ..config import Config
from ..guard import (
    require_ado_install_confirmation,
    validate_ado_install_request,
)
from ..stata.builtin_tools.ado_install import GITHUB_Install, NET_Install, SSC_Install
from ._runtime import create_runtime_context
from .read_log import read_log
from .stata_do import _stata_do
from .write_dofile import write_dofile

SOURCE_MAPPING = {
    "github": GITHUB_Install,
    "net": NET_Install,
    "ssc": SSC_Install,
}


def ado_package_install(
    package: str,
    source: str = "ssc",
    is_replace: bool = False,
    package_source_from: str = None,
    config_file: str | Path | None = None,
    timeout: int = 300,
    confirm: bool = False,
) -> str:
    """Install an explicitly enabled and confirmed ado package.

    GitHub repositories are allowlisted by name only and receive no content-level
    security protection. Inspect the repository before installation.
    """
    config = Config(config_file=config_file)
    if not config.ENABLE_ADO_INSTALL:
        raise PermissionError(
            "Ado package installation is disabled. Set "
            "SECURITY.ENABLE_ADO_INSTALL=true only in trusted environments."
        )
    require_ado_install_confirmation(confirm)
    package, source, package_source_from = validate_ado_install_request(
        package,
        source,
        package_source_from,
        allowed_github_repositories=(
            config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES
        ),
    )
    runtime = create_runtime_context(config_file=config_file, require_stata=True)

    if runtime.is_unix:
        installer_cls = SOURCE_MAPPING[source]
        install_args = [package, package_source_from] if source == "net" else [package]
        install_kwargs = {"confirm": True}
        if source == "github":
            install_kwargs["allowed_repositories"] = (
                config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES
            )
        install_message = installer_cls(
            runtime.stata_cli,
            is_replace,
            timeout=timeout,
        ).install(*install_args, **install_kwargs)

        return _finalize_install_message(
            installer_cls,
            package,
            source,
            install_message,
            installer_cls.check_installed_from_msg(install_message),
        )

    options = []
    if is_replace:
        options.append("replace")
    if source == "net":
        options.append(f"from({package_source_from})")
    option_text = f", {' '.join(options)}" if options else ""
    command = f"{source} install {package}{option_text}"
    dofile_path = write_dofile(command, config_file=config_file)
    result = _stata_do(
        dofile_path,
        read_log_when_error=False,
        config_file=config_file,
        allow_package_management=True,
    )
    text_log_path = result.get("log_file_path", {}).get("text")
    if not text_log_path:
        return (
            "Installation State: False\n"
            f"Error: Stata did not produce an installation log. Details: {result}"
        )

    log_content = read_log(
        text_log_path,
        output_format="core",
        config_file=config_file,
    )
    installer_cls = SOURCE_MAPPING[source]
    is_installed = installer_cls.check_install(log_content)
    install_message = f"Installation State: {is_installed}\n{log_content}"
    return _finalize_install_message(
        installer_cls,
        package,
        source,
        install_message,
        is_installed,
    )


def _finalize_install_message(
    installer_cls,
    package: str,
    source: str,
    install_message: str,
    is_installed: bool,
) -> str:
    """Append consistent failure details to a platform-specific install log."""
    if is_installed:
        return install_message

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
    return install_message
