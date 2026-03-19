#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : windows.py

import glob
import os
import re
import string
from typing import Dict, List

from .base import FinderBase, StataEditionConfig


def get_available_drives():
    drives = []
    for letter in string.ascii_uppercase:
        if os.path.exists(f"{letter}:\\"):
            drives.append(f"{letter}:\\")
    return drives


def windows_stata_match(path: str) -> bool:
    """
    Check whether the given path matches the pattern of a Windows
    Stata executable.

    Args:
        path: Path string to be checked.

    Returns:
        bool: ``True`` if the path matches a Stata executable pattern,
        otherwise ``False``.
    """
    # Regular expression matching ``Stata\d+\Stata(MP|SE|BE|IC)?.exe``
    # ``\d+`` matches one or more digits (the version number)
    # ``(MP|SE|BE|IC)?`` matches an optional edition suffix
    pattern = r"Stata\d+\\\\Stata(MP|SE|BE|IC)?\.exe$"

    if re.search(pattern, path):
        return True
    return False


class FinderWindows(FinderBase):
    def finder(self) -> str:
        default_results = self.find_from_default_install_path()
        if default_results:
            return max(default_results).stata_cli_path

        driver_results = self.scan_stata_from_drivers()
        if driver_results:
            return max(driver_results).stata_cli_path

        deep_results = self.scan_stata_deeply()
        if deep_results:
            return max(deep_results).stata_cli_path
        else:
            raise FileNotFoundError("Stata executable not found")

    def find_path_base(self) -> Dict[str, List[str]]:
        return {
            "default": [
                r"C:\Program Files\Stata*",
                r"C:\Program Files (x86)\Stata*",
                r"D:\Program Files\Stata*",
                r"D:\Program Files (x86)\Stata*",
            ],
            "drivers": get_available_drives()
        }

    def find_from_default_install_path(self) -> List[StataEditionConfig]:
        """Find Stata installations in default Windows installation paths.

        This function searches for Stata in standard Windows locations
        like Program Files directories using simple matching.

        Returns:
            List of StataEditionConfig objects found in default paths
        """
        found_configs = []

        # Common Windows installation paths
        common_paths = self.find_path_base().get("default")

        for path_pattern in common_paths:
            try:
                matches = glob.glob(path_pattern)
                for match in matches:
                    # Search in these Stata directories for executables
                    executables = glob.glob(os.path.join(match, "*.exe"))
                    for exe in executables:
                        # Simple matching like the original implementation
                        if "stata" in exe.lower() and exe.lower().endswith(".exe"):
                            config = StataEditionConfig.from_path(exe)
                            found_configs.append(config)
            except Exception:
                pass

        return found_configs

    def scan_stata_from_drivers(self) -> List[StataEditionConfig]:
        """Scan all available drivers for Stata installations in non-standard locations.

        This method searches for Stata in locations that are NOT in standard
        installation paths (Program Files, etc.), focusing on custom or
        alternative installation locations.

        Returns:
            List of StataEditionConfig objects found in non-standard locations
        """
        drivers_base = self.find_path_base().get("drivers")
        found_configs = []

        if not drivers_base:
            return found_configs

        for driver in drivers_base:
            # Skip standard installation directories to avoid duplication
            skip_patterns = [
                os.path.join(driver, "Program Files"),
                os.path.join(driver, "Program Files (x86)"),
            ]

            try:
                # Limit search depth to avoid excessive scanning
                for root, dirs, files in os.walk(driver):
                    # Skip standard installation directories
                    should_skip = False
                    for skip_pattern in skip_patterns:
                        if root.lower().startswith(skip_pattern.lower()):
                            should_skip = True
                            break

                    if should_skip:
                        continue

                    # Limit depth to 4 levels
                    if root.count(os.sep) - driver.count(os.sep) > 4:
                        dirs.clear()
                        continue

                    for file in files:
                        if (
                            file.lower().endswith(".exe")
                            and "stata" in file.lower()
                        ):
                            full_path = os.path.join(root, file)
                            config = StataEditionConfig.from_path(full_path)
                            found_configs.append(config)
            except Exception:
                pass

        return found_configs

    def scan_stata_deeply(self) -> List[StataEditionConfig]:
        """Perform deep scan across all drives for any Stata installation.

        This is the final fallback search method that scans everywhere
        without restrictions, including standard paths, to find any possible
        Stata installation that might have been missed.

        Returns:
            List of StataEditionConfig objects found through deep scanning
        """
        drivers_base = self.find_path_base().get("drivers")
        found_configs = []

        if not drivers_base:
            return found_configs

        for driver in drivers_base:
            try:
                # Deep scan without restrictions
                for root, dirs, files in os.walk(driver):
                    for file in files:
                        if file.lower().endswith(".exe") and "stata" in file.lower():
                            full_path = os.path.join(root, file)
                            # Less strict matching for deep scan
                            if "stata" in full_path.lower():
                                config = StataEditionConfig.from_path(full_path)
                                found_configs.append(config)
            except Exception:
                pass

        return found_configs
