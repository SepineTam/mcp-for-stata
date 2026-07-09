#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : net_install.py

from ....guard import (
    require_ado_install_confirmation,
    validate_ado_package_name,
    validate_net_source_location,
)
from .base import AdoInstallBase


class NET_Install(AdoInstallBase):
    def install(
        self,
        package: str,
        directory_or_url: str = None,
        *,
        confirm: bool = False,
    ) -> str:
        require_ado_install_confirmation(confirm)
        package = validate_ado_package_name(package, source="net")
        directory_or_url = validate_net_source_location(directory_or_url)
        options = []
        if self.is_replace:
            options.append("replace")
        options.append(f"from({directory_or_url})")
        install_command = f"net install {package}, {' '.join(options)}"
        runner_result = self._run_install_command(install_command, source="net", package=package)
        return self._install_msg_template(runner_result)

    @staticmethod
    def check_install(message: str) -> bool:
        normalized_message = str(message).lower()
        success_signatures = [
            "installing into ",
            "installation complete",
            "all files already exist and are up to date",
        ]
        return any(
            signature_msg in normalized_message
            for signature_msg in success_signatures
        )
