#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : read_log.py

from pathlib import Path
from typing import Union

from .read_smcl import StataLogSMCL
from .read_text import StataLogTEXT


class StataLog:
    """
    Factory class for Stata log file processing.

    Provides a unified interface to read and process Stata log files
    in different formats (TEXT and SMCL).
    """

    @classmethod
    def log(
        cls,
        log_file_path: Path | str,
        encoding: str = "utf-8"
    ) -> Union[StataLogTEXT, StataLogSMCL]:
        """
        Create appropriate log processor based on file extension.

        Args:
            log_file_path: Path to the Stata log file (.log or .smcl)
            encoding: File encoding (default: utf-8)

        Returns:
            StataLogTEXT for .log files, StataLogSMCL for .smcl files

        Raises:
            ValueError: If file extension is not .log or .smcl
            FileNotFoundError: If log file does not exist
        """

        if not log_file_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_file_path}")

        extension = log_file_path.suffix.lower()

        if extension == '.log':
            return StataLogTEXT(log_file_path, encoding=encoding)
        elif extension == '.smcl':
            return StataLogSMCL(log_file_path, encoding=encoding)
        else:
            raise ValueError(
                f"Unsupported log file extension: {extension}. "
                f"Expected .log or .smcl"
            )

    @classmethod
    def from_path(
        cls,
        log_file_path: Path | str,
        encoding: str = "utf-8"
    ) -> Union[StataLogTEXT, StataLogSMCL]:
        """Alias for log() method for backward compatibility."""
        try:
            log_file_path = Path(log_file_path).resolve()
            return cls.log(log_file_path, encoding)
        except Exception as e:
            raise ValueError(f"Invalid log file path: {log_file_path}") from e
