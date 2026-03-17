#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : github_install.py

from ..help import StataHelp
from .base import AdoInstallBase


class GITHUB_Install(AdoInstallBase):
    def install(self, package: str) -> str:
        install_command = f"github install {package}{self.REPLACE_MESSAGE}"
        runner_result = self.controller.run(install_command)
        return self._install_msg_template(runner_result)

    @property
    def IS_EXIST_GITHUB(self) -> bool:
        return StataHelp(self.stata_cli).check_command_exist_with_help("github")

    def __post_initialization(self):
        # if not exist `GitHub` command, install it.
        if not self.IS_EXIST_GITHUB:
            self.__install_github()

    def __install_github(self):
        install_command = 'net install github, from("https://haghish.github.io/github/")'
        runner_result = self.controller.run(install_command)
        return runner_result

    @staticmethod
    def check_install(message: str) -> bool:
        # I am not sure whether this is robust, if not please email me.
        signature_messages = [
            # GitHub specific success messages
            "connected to github.com",
            "repository exists:",
            "installation complete",

            # for replace arg, the package is already exist and up to date
            "all files already exist and are up to date",
        ]

        return any(signature_msg in str(message).lower() for signature_msg in signature_messages)
