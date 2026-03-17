#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : base.py

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union


@dataclass
class StataEditionConfig:
    """
    StataEditionConfig class for comparing Stata versions with sorting support.

    Attributes:
        edition (str): Edition type (mp > se > be > ic > default)
        version (Union[int, float]): Version number (e.g., 18, 19.5). Default 99 if not found, indicating current default version
        path (str): Full path to Stata executable

    Comparison Rules:
        1. First compare edition priority: mp > se > be > ic > default (edition type always has priority)
        2. Then compare numeric version: higher > lower (only for same edition type)
        3. Support float versions like 19.5 > 19
        4. Version 99 is used when version info is not available (default edition gets highest version within its type)

    Example:
        >>> p1 = StataEditionConfig("mp", 18, "/usr/local/bin/stata-mp")
        >>> p2 = StataEditionConfig.from_path("/usr/local/bin/stata")  # Auto-detect as default with version 99
        >>> p1 > p2  # True (mp edition has higher priority than default, regardless of version numbers)
    """

    edition: str
    version: Union[int, float]
    path: str

    # Edition priority mapping
    _EDITION_PRIORITY = {
        "mp": 5,
        "se": 4,
        "be": 3,
        "ic": 2,
        "default": 1,
        "unknown": 0,
    }

    def __post_init__(self):
        """Validation and processing after initialization."""
        # Normalize edition type to lowercase
        self.edition = self.edition.lower()

        # If edition type is not in priority mapping, mark as unknown
        if self.edition not in self._EDITION_PRIORITY:
            self.edition = "unknown"

    @classmethod
    def from_path(cls, path: str) -> 'StataEditionConfig':
        """
        Create StataEditionConfig from path, automatically extracting edition and version.

        Args:
            path: Full path to Stata executable

        Returns:
            StataEditionConfig with auto-detected edition and version
        """
        import os

        filename = os.path.basename(path).lower()
        full_path_lower = path.lower()

        # Extract edition
        edition = "default"
        edition_patterns = [
            (r'stata-mp', 'mp'),
            (r'satamp', 'mp'),
            (r'stata-se', 'se'),
            (r'statase', 'se'),
            (r'sata-be', 'be'),
            (r'satabe', 'be'),
            (r'sata-ic', 'ic'),
            (r'sataic', 'ic'),
        ]

        for pattern, ed in edition_patterns:
            if re.search(pattern, filename):
                edition = ed
                break

        # Extract version (default to 99 if not found, indicating current default version)
        version = 99

        # Try to extract version from directory name first
        dir_version_match = re.search(r'stata(\d+(?:\.\d+)?)', full_path_lower)
        if dir_version_match:
            try:
                version = float(dir_version_match.group(1))
            except ValueError:
                pass

        # Try to extract version from filename
        file_version_patterns = [
            r'stata-[a-z]+-(\d+(?:\.\d+)?)',  # stata-mp-17.5
            r'stata(\d+(?:\.\d+)?)',          # stata17.5
        ]

        for pattern in file_version_patterns:
            file_version_match = re.search(pattern, filename)
            if file_version_match:
                try:
                    file_version = float(file_version_match.group(1))
                    # Only use reasonable version numbers (1-30)
                    if 1 <= file_version <= 30:
                        version = max(version, file_version)
                        break
                except ValueError:
                    continue

        return cls(edition=edition, version=version, path=path)

    @property
    def edition_priority(self) -> int:
        """Get the priority value of the edition type."""
        return self._EDITION_PRIORITY[self.edition]

    def __lt__(self, other) -> bool:
        """Less than comparison for sorting."""
        if not isinstance(other, StataEditionConfig):
            return NotImplemented

        # First compare edition priority
        if self.edition_priority != other.edition_priority:
            return self.edition_priority < other.edition_priority

        # Same edition, compare version number
        return self.version < other.version

    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if not isinstance(other, StataEditionConfig):
            return NotImplemented

        # First compare edition priority
        if self.edition_priority != other.edition_priority:
            return self.edition_priority > other.edition_priority

        # Same edition, compare version number
        return self.version > other.version

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self > other or self == other

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, StataEditionConfig):
            return NotImplemented

        return (self.edition_priority == other.edition_priority and
                self.version == other.version)

    def __str__(self) -> str:
        """String representation - returns the path."""
        return self.path

    def __repr__(self) -> str:
        """Detailed string representation - returns the path."""
        return self.path

    def __int__(self) -> int:
        """Integer conversion - returns the version number."""
        return int(self.version)

    def __float__(self) -> float:
        """Float conversion - returns the version number."""
        return float(self.version)

    @property
    def stata_cli_path(self) -> str:
        """Get the Stata CLI path."""
        return self.path


class FinderBase(ABC):
    stata_cli: str = None

    def __init__(self, stata_cli: str = None):
        # If there is any setting, use the input and environment first
        self.stata_cli = stata_cli or os.getenv("STATA_CLI") or os.getenv("stata_cli")

    def find_stata(self) -> str | None:
        if self.stata_cli:
            return self.stata_cli
        return self.finder()

    @abstractmethod
    def finder(self) -> str:
        """
        Find the Stata executable on the current platform.

        This method must be implemented by each platform-specific finder class
        to locate Stata installations using platform-appropriate search strategies.

        Returns:
            str: The full path to the Stata executable

        Raises:
            FileNotFoundError: If no Stata installation is found

        Note:
            This is an abstract method and must be implemented by concrete finder classes
            such as FinderMacOS, FinderWindows, or FinderLinux.

            Each platform should implement appropriate search strategies for finding
            Stata installations in their typical locations (e.g., /Applications for macOS,
            Program Files for Windows, system PATH for Linux).
        """
        ...

    @abstractmethod
    def find_path_base(self) -> Dict[str, List[str]]: ...

    @staticmethod
    def priority() -> Dict[str, List[str]]:
        name_priority = {
            "mp": ["stata-mp"],
            "se": ["stata-se"],
            "be": ["stata-be"],
            "default": ["stata"],
        }
        return name_priority

    @staticmethod
    def _is_executable(p: Path) -> bool:
        try:
            return p.is_file() and os.access(p, os.X_OK)
        except OSError:
            return False

    def find_from_bin(self,
                      *,
                      priority: Optional[Iterable[str]] = None) -> List[StataEditionConfig]:
        """
        Find all available Stata executables in bin directories.

        Args:
            priority: Edition priority order (default: ["mp", "se", "be", "default"])

        Returns:
            List of all executable Stata paths found in bin directories,
            ordered by priority. Returns empty list if no executables found.
        """
        pr = list(priority) if priority else ["mp", "se", "be", "default"]
        name_priority = self.priority()
        bins = self.find_path_base().get("bin")

        if not bins:
            return []

        # Build ordered list of executable names by priority
        ordered_names: List[str] = []
        for key in pr:
            ordered_names.extend(name_priority.get(key, []))

        found_executables: List[StataEditionConfig] = []

        # Search for executables in all bin directories
        for b in bins:
            base = Path(b)

            # Check weather the bin directory exists
            if not base.exists():
                continue

            for name in ordered_names:
                p = base / name
                if self._is_executable(p):
                    # Convert path to StataEditionConfig
                    config = StataEditionConfig.from_path(str(p))
                    found_executables.append(config)

        return found_executables
