#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : ssc_install.py

from .base import AdoInstallBase


class SSC_Install(AdoInstallBase):
    def install(self, package: str) -> str:
        install_command = f"ssc install {package}{self.REPLACE_MESSAGE}"
        runner_result = self.controller.run(install_command)
        return self._install_msg_template(runner_result)

    @staticmethod
    def check_install(message: str) -> bool:
        signature_messages = [
            # for the package is not install before or not found in current.
            "installing into ",
            "installation complete.",

            # for replace arg, the package is already exist and up to date
            "all files already exist and are up to date.",
        ]

        # Return True if any content from signature messages is found in the message, otherwise False
        return any(signature_msg in str(message) for signature_msg in signature_messages)
