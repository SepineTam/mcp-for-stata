#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : finder.py

import platform

from .linux import FinderLinux
from .macos import FinderMacOS
from .windows import FinderWindows


class StataFinder:
    FINDER_MAPPING = {
        "Darwin": FinderMacOS,
        "Windows": FinderWindows,
        "Linux": FinderLinux,
    }

    def __init__(self, stata_cli: str = None):
        finder_cls = self.FINDER_MAPPING.get(platform.system())
        self.finder = finder_cls(stata_cli)

    @property
    def STATA_CLI(self) -> str | None:
        try:
            return self.finder.find_stata()
        except (FileNotFoundError, AttributeError):
            return None
