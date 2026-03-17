#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : net_install.py

from .base import AdoInstallBase


class NET_Install(AdoInstallBase):
    def install(self, package: str, directory_or_url: str = None) -> str:
        ex_from = ", " if directory_or_url and not self.REPLACE_MESSAGE else ""
        from_message = f"{ex_from} from({directory_or_url})" if directory_or_url else ""

        install_command = f"net install {package}{self.REPLACE_MESSAGE}{from_message}"
        runner_result = self.controller.run(install_command)
        return self._install_msg_template(runner_result)

    @staticmethod
    def check_install(message: str) -> bool:
        wrong_signature_messages = [
            # for sure error message
            "not found",
            "could not load"
        ]

        return any(signature_msg not in str(message) for signature_msg in wrong_signature_messages)
