#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : linux.py

from pathlib import Path
from typing import Dict, List

from .base import FinderBase


class FinderLinux(FinderBase):
    def finder(self) -> str:
        bin_results = self.find_from_bin()
        if bin_results:
            return max(bin_results).stata_cli_path
        else:
            raise FileNotFoundError("Stata CLI not found")

    def find_path_base(self) -> Dict[str, List[str]]:
        # Start with default bin directory
        bin_dirs = ["/usr/local/bin"]

        # Search for additional directories containing "stata" in /usr/local/bin
        usr_local_bin = Path("/usr/local/bin")
        if usr_local_bin.exists() and usr_local_bin.is_dir():
            # Look for directories containing "stata" in their name
            for item in usr_local_bin.iterdir():
                if item.is_dir() and "stata" in item.name.lower():
                    # Add the stata directory path to search directories
                    bin_dirs.append(str(item))

        return {
            "bin": bin_dirs,
        }


if __name__ == "__main__":
    finder = FinderLinux()
