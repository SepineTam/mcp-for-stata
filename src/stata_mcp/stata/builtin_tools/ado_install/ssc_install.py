#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : ssc_install.py

from ....guard import require_ado_install_confirmation, validate_ado_package_name
from .base import AdoInstallBase


class SSC_Install(AdoInstallBase):
    def install(
        self,
        package: str,
        *,
        confirm: bool = False,
    ) -> str:
        require_ado_install_confirmation(confirm)
        package = validate_ado_package_name(package, source="ssc")
        install_command = f"ssc install {package}{self.REPLACE_MESSAGE}"
        runner_result = self._run_install_command(install_command, source="ssc", package=package)
        return self._install_msg_template(runner_result)

    @staticmethod
    def check_install(message: str) -> bool:
        normalized_message = str(message).lower()
        success_signatures = [
            "installing into ",
            "installation complete",
            "all files already exist and are up to date",
        ]
        return any(signature_msg in normalized_message for signature_msg in success_signatures)
