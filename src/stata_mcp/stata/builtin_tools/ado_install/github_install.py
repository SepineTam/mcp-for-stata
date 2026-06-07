#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : github_install.py

from collections.abc import Collection

from ....guard import (
    require_ado_install_confirmation,
    validate_github_repository_allowed,
)
from ..help import StataHelp
from .base import AdoInstallBase


class GITHUB_Install(AdoInstallBase):
    def install(
        self,
        package: str,
        *,
        confirm: bool = False,
        allowed_repositories: Collection[str] = (),
    ) -> str:
        require_ado_install_confirmation(confirm)
        package = validate_github_repository_allowed(
            package,
            allowed_repositories=allowed_repositories,
        )
        if not self.IS_EXIST_GITHUB:
            raise RuntimeError(
                "The Stata github helper is not installed. Install and verify it "
                "manually before using GitHub as an ado package source."
            )
        install_command = f"github install {package}{self.REPLACE_MESSAGE}"
        runner_result = self.controller.run(install_command)
        return self._install_msg_template(runner_result)

    @property
    def IS_EXIST_GITHUB(self) -> bool:
        return StataHelp(self.stata_cli).check_command_exist_with_help("github")

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
