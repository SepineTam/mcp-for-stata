#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class StataLogInfo:
    log_file_path: Path
    command_result_mapping: Dict[str, str]  # {command: results}
    do_file_path: Path = None


class StataLogBase(ABC):
    def __init__(self, log_file_path: Path, encoding: str = "utf-8"):
        self.log_file_path = log_file_path
        self.encoding = encoding

    @abstractmethod
    def _convert_to_dataclass(self) -> StataLogInfo:
        pass

    @property
    def log_info(self) -> StataLogInfo:
        return self._convert_to_dataclass()

    def read_plain_text(self) -> str:
        """
        Directly return log file content without any process.

        Returns:
            str: content of log file.
        """
        return self.log_file_path.read_text(encoding=self.encoding)

    @abstractmethod
    def read_without_framework(self) -> str:
        """
        Process cleaned log file via removing framework content, based on plain text.

        Returns:
            str: core content of log file, without noise to disturb context.
        """
        pass

    def read_as_dict(self) -> Dict[str, str]:
        return self.log_info.__dict__
