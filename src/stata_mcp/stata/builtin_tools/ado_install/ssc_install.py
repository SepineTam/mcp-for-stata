#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : ssc_install.py

from collections.abc import Collection

from ....guard import require_ado_install_confirmation, validate_ssc_package_allowed
from .base import AdoInstallBase


class SSC_Install(AdoInstallBase):
    def install(
        self,
        package: str,
        *,
        confirm: bool = False,
        allowed_packages: Collection[str] = (),
    ) -> str:
        require_ado_install_confirmation(confirm)
        package = validate_ssc_package_allowed(
            package,
            allowed_packages=allowed_packages,
        )
        install_command = f"ssc install {package}{self.REPLACE_MESSAGE}"
        runner_result = self.controller.run(install_command)
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
