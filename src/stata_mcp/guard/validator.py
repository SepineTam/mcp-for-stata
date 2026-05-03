#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : validator.py

"""Security validation module for Stata dofiles.

This module provides the core validation logic for detecting dangerous
commands and patterns in Stata dofile code.
"""

import re
from dataclasses import dataclass, field
from typing import List

from .blacklist import DANGEROUS_COMMANDS, DANGEROUS_PATTERNS, STATA_PREFIXES

# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class RiskItem:
    """Represents a single security risk item found in the code.

    Attributes:
        type: The type of risk ("command" or "pattern")
        content: The actual content that triggered the risk
        line: Line number where the risk was found (1-indexed)
    """

    type: str
    content: str
    line: int

    def __str__(self) -> str:
        """Return string representation of the risk item."""
        return f"Line {self.line}: {self.type} '{self.content}'"


@dataclass
class SecurityReport:
    """Security validation report for Stata dofile code.

    Attributes:
        is_safe: True if no dangerous items were found, False otherwise
        dangerous_items: List of all dangerous items found in the code
    """

    is_safe: bool
    dangerous_items: List[RiskItem] = field(default_factory=list)

    def __str__(self) -> str:
        """Return string representation of the security report."""
        if self.is_safe:
            return "✅ Code passed security validation"

        lines = ["❌ Security validation failed. Found dangerous items:"]
        for item in self.dangerous_items:
            lines.append(f"  - {item}")
        return "\n".join(lines)


# ============================================================================
# Core Validator
# ============================================================================

class GuardValidator:
    """Validator for Stata dofile security.

    This class validates Stata dofile code against a blacklist of
    dangerous commands and patterns.
    """

    def __init__(self) -> None:
        """Initialize the validator with default blacklist."""
        self.dangerous_commands = DANGEROUS_COMMANDS
        self.dangerous_patterns = DANGEROUS_PATTERNS
        self.stata_prefixes = set(STATA_PREFIXES)

    @staticmethod
    def _strip_prefixes(line: str, prefixes: set) -> str:
        """Remove Stata command prefixes from a line.

        Stata allows stacking prefixes (e.g., ``cap qui shell ...``),
        so we loop until no more prefixes remain.

        Args:
            line: The code line to strip
            prefixes: Set of prefix strings to remove

        Returns:
            The line with all leading prefixes removed
        """
        words = line.split()
        while words and words[0].lower() in prefixes:
            words.pop(0)
        return " ".join(words) if words else ""

    def validate(self, code: str) -> SecurityReport:
        """Validate Stata dofile code for security risks.

        Args:
            code: The Stata dofile code to validate

        Returns:
            SecurityReport containing validation results
        """
        dangerous_items: List[RiskItem] = []

        # Split code into lines for line number tracking
        lines = code.split("\n")

        dangerous_local_names = self._collect_dangerous_local_names(lines)

        for line_num, line in enumerate(lines, start=1):
            # Skip empty lines and comments
            stripped_line = line.strip()
            if (
                not stripped_line
                or stripped_line.startswith("*")
                or stripped_line.startswith("//")
            ):
                continue

            # Strip Stata prefixes (capture, quietly, etc.) before checking
            cleaned_line = self._strip_prefixes(stripped_line, self.stata_prefixes)
            if not cleaned_line:
                continue

            macro_items = self._check_macro_expansion(cleaned_line, line_num, dangerous_local_names)
            dangerous_items.extend(macro_items)

            # Check for dangerous commands
            command_items = self._check_dangerous_commands(cleaned_line, line_num)
            dangerous_items.extend(command_items)

            # Check for dangerous patterns
            pattern_items = self._check_dangerous_patterns(cleaned_line, line_num)
            dangerous_items.extend(pattern_items)

        # Generate report
        is_safe = len(dangerous_items) == 0
        return SecurityReport(is_safe=is_safe, dangerous_items=dangerous_items)

    def _collect_dangerous_local_names(self, lines: List[str]) -> set[str]:
        """Collect local macro names whose values are dangerous commands."""
        dangerous_names: set[str] = set()
        local_pattern = re.compile(r"^\s*local\s+(\w+)\s+['\"]([^'\"]+)['\"]", re.IGNORECASE)

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("*") or stripped_line.startswith("//"):
                continue

            matched = local_pattern.search(line)
            if not matched:
                continue

            local_name, local_value = matched.group(1), matched.group(2)
            if local_value.strip().lower() in self.dangerous_commands:
                dangerous_names.add(local_name)

        return dangerous_names

    @staticmethod
    def _check_macro_expansion(line: str, line_num: int, dangerous_local_names: set[str]) -> List[RiskItem]:
        """Check whether a line expands a dangerous local macro."""
        items: List[RiskItem] = []
        for local_name in dangerous_local_names:
            macro_token = f"`{local_name}'"
            if macro_token in line:
                items.append(RiskItem(type="macro", content=macro_token, line=line_num))
        return items

    def _check_dangerous_commands(self, line: str, line_num: int) -> List[RiskItem]:
        """Check if a line contains dangerous commands.

        Args:
            line: The code line to check
            line_num: Line number

        Returns:
            List of RiskItem objects found
        """
        items: List[RiskItem] = []

        # Get the first word (command)
        first_word = line.split()[0].lower() if line.split() else ""

        if first_word in self.dangerous_commands:
            items.append(RiskItem(
                type="command",
                content=first_word,
                line=line_num
            ))

        # Special check for "!" which is a prefix
        if line.startswith("!"):
            items.append(RiskItem(
                type="command",
                content="!",
                line=line_num
            ))

        return items

    def _check_dangerous_patterns(self, line: str, line_num: int) -> List[RiskItem]:
        """Check if a line matches dangerous patterns.

        Args:
            line: The code line to check
            line_num: Line number

        Returns:
            List of RiskItem objects found
        """
        items: List[RiskItem] = []

        for pattern in self.dangerous_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                items.append(RiskItem(
                    type="pattern",
                    content=pattern,
                    line=line_num
                ))

        return items


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "RiskItem",
    "SecurityReport",
    "GuardValidator",
]
