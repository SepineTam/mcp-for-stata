#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : macos.py

import re
from pathlib import Path
from typing import Dict, List

from .base import FinderBase, StataEditionConfig


class FinderMacOS(FinderBase):
    def finder(self) -> str | None:
        bin_results = self.find_from_bin()
        if bin_results:
            return max(bin_results).stata_cli_path

        application_results = self.find_from_application()
        if application_results:
            return max(application_results).stata_cli_path
        else:  # If there is no Stata CLI found, raise an error
            raise FileNotFoundError("Stata CLI not found")

    def find_path_base(self) -> Dict[str, List[str]]:
        return {
            "bin": ["/usr/local/bin"],
            "application": [
                "/Applications",
                "~/Applications"
            ],
        }

    def _application_find_base(self,
                               dot_app: str | Path,
                               version: int | float = None) -> StataEditionConfig | None:
        _version = version
        _edition = None
        stata_cli_path = None

        if not _version:
            for isstata_file in dot_app.glob("isstata.*"):
                if isstata_file.is_file():
                    # Extract version number from filename like "isstata.180"
                    match = re.search(r'isstata\.(\d+)', isstata_file.name.lower())
                    if match:
                        _version = float(match.group(1)) / 10
                        break
        for stata_app in dot_app.glob("Stata*.app"):
            if stata_app.is_dir():
                # Extract edition from Stata app name (MP, SE, BE, IC)
                # Remove "Stata" prefix and ".app" suffix, then convert to lowercase
                _edition = stata_app.name.replace("Stata", "").replace(".app", "").lower()

                # Try multiple possible executable names (for different Stata versions)
                possible_names = [
                    f"stata-{_edition}",              # stata-be (traditional format)
                    f"Stata{_edition.upper()}",       # StataBE (StataNow format)
                    f"Stata{_edition.capitalize()}",  # StataBe (alternative capitalization)
                ]

                for name in possible_names:
                    __stata_cli_path = stata_app / "Contents" / "MacOS" / name
                    if self._is_executable(__stata_cli_path):
                        stata_cli_path = str(__stata_cli_path)
                        break
        if _version and _edition and stata_cli_path:
            return StataEditionConfig(_edition, _version, stata_cli_path)

        else:
            return None

    def find_from_application(self) -> List[StataEditionConfig]:
        found_executables: List[StataEditionConfig] = []
        applications_dirs = [Path(a) for a in self.find_path_base().get("application")]
        stata_feature_names = ["StataNow", "Stata"]

        # Check for /Applications/Stata directory for Multi-Stata Exist
        default_stata_list = []
        for applications_dir in applications_dirs:  # priority: system applications > user applications
            for stata_feature_name in stata_feature_names:  # priority: StataNow > Stata
                stata_dir = applications_dir / stata_feature_name

                if default_stata := self._application_find_base(stata_dir):  # If exist default, add to waitlist.
                    default_stata_list.append(default_stata)
        if default_stata_list:
            return default_stata_list  # Finally choose the max-edition by max() function

        # Loop through applications_dir to find stata*.app
        for applications_dir in applications_dirs:
            for stata_app in applications_dir.glob("Stata *"):
                _version = None
                if stata_app.is_dir():
                    try:
                        _version = float(stata_app.name.split()[-1])
                    except (ValueError, TypeError):
                        continue  # Skip invalid version format
                    if stata_app_config := self._application_find_base(stata_app, version=_version):
                        found_executables.append(stata_app_config)

        return found_executables


if __name__ == "__main__":
    finder = FinderMacOS()
    print(finder.finder())
