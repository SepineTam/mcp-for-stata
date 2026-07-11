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

import logging
import re
from dataclasses import dataclass, field
from typing import Any, List

from ..utils.parse_dofile import (
    ExpansionResult,
    ParsedCommand,
    expand_code_for_security,
)
from .blacklist import (
    DANGEROUS_COMMANDS,
    DANGEROUS_PATTERNS,
    PACKAGE_MANAGEMENT_COMMANDS,
    STATA_PREFIXES,
)
from .data_path_auditor import DataPathAuditor

logger = logging.getLogger(__name__)

DIRECT_DATA_COMMANDS = {
    "use",
    "import",
    "insheet",
    "infile",
    "infix",
}
USING_DATA_COMMANDS = {
    "merge",
    "merg",
    "mer",
    "append",
    "appen",
    "appe",
    "app",
    "ap",
    "joinby",
    "joinb",
}
CONTEXT_MUTATION_COMMANDS = {"cd", "chdir"}
PATH_LIKE_COMMANDS = (
    DIRECT_DATA_COMMANDS
    | USING_DATA_COMMANDS
    | {
        "save",
        "saveold",
        "sysuse",
        "webuse",
        "export",
        "outfile",
        "outsheet",
        "do",
        "run",
        "include",
        "type",
        "erase",
        "rmdir",
        "mkdir",
        "copy",
    }
)
UNRESOLVED_MACRO_PATTERN = re.compile(
    r"`[A-Za-z_][A-Za-z0-9_]*'|"
    r"`[=:]|"
    r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|"
    r"\$[A-Za-z_][A-Za-z0-9_]*"
)

# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class RiskItem:
    """Represents a single security risk item found in the code.

    Attributes:
        type: The type of risk ("command", "pattern", "macro", "parse",
            "context", or "data_path")
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
        cleaned_line = line
        prefix_pattern = re.compile(r"^\s*(\w+)\s*:?\s*", re.IGNORECASE)
        version_prefix_pattern = re.compile(
            r"^\s*version\s+\d+(?:\.\d+)?\s*:\s*",
            re.IGNORECASE,
        )
        frame_prefix_pattern = re.compile(
            r"^\s*frame\s+[A-Za-z_][A-Za-z0-9_]*\s*:\s*",
            re.IGNORECASE,
        )
        while cleaned_line:
            version_match = version_prefix_pattern.match(cleaned_line)
            if version_match:
                cleaned_line = cleaned_line[version_match.end():]
                continue
            frame_match = frame_prefix_pattern.match(cleaned_line)
            if frame_match:
                cleaned_line = cleaned_line[frame_match.end():]
                continue
            matched = prefix_pattern.match(cleaned_line)
            if not matched or matched.group(1).lower() not in prefixes:
                break
            cleaned_line = cleaned_line[matched.end():]
        return cleaned_line.strip()

    @staticmethod
    def _iter_executable_lines(lines: List[str]) -> List[tuple[int, str]]:
        """Return lines after removing Stata block comments."""
        executable_lines: List[tuple[int, str]] = []
        in_block_comment = False

        for line_num, line in enumerate(lines, start=1):
            index = 0
            cleaned_parts: List[str] = []

            while index < len(line):
                if in_block_comment:
                    comment_end = line.find("*/", index)
                    if comment_end == -1:
                        index = len(line)
                    else:
                        index = comment_end + 2
                        in_block_comment = False
                    continue

                comment_start = line.find("/*", index)
                if comment_start == -1:
                    cleaned_parts.append(line[index:])
                    break

                cleaned_parts.append(line[index:comment_start])
                index = comment_start + 2
                in_block_comment = True

            executable_lines.append((line_num, "".join(cleaned_parts)))

        return executable_lines

    def validate(self, code: str, config: Any | None = None) -> SecurityReport:
        """Validate Stata dofile code for security risks.

        Args:
            code: The Stata dofile code to validate
            config: Optional runtime config. When provided and
                ``ENABLE_DATA_COMMAND_PATH_GUARD`` is True, data-loading
                commands are audited for path/URL boundary violations.

        Returns:
            SecurityReport containing validation results
        """
        dangerous_items: List[RiskItem] = []

        original_executable_lines = self._iter_executable_lines(code.split("\n"))
        dangerous_local_names = self._collect_dangerous_local_names(
            original_executable_lines
        )
        for line_num, line in original_executable_lines:
            stripped_line = line.strip()
            if (
                not stripped_line
                or stripped_line.startswith("*")
                or stripped_line.startswith("//")
            ):
                continue
            cleaned_line = self._strip_prefixes(stripped_line, self.stata_prefixes)
            dangerous_items.extend(
                self._check_macro_expansion(
                    cleaned_line, line_num, dangerous_local_names
                )
            )
            dangerous_items.extend(
                self._check_dangerous_patterns(cleaned_line, line_num)
            )

        expansion_result = expand_code_for_security(code)
        if expansion_result.requires_global_fail_closed:
            for diagnostic in expansion_result.diagnostics:
                if not diagnostic.security_relevant or diagnostic.scope != "global":
                    continue
                dangerous_items.append(
                    RiskItem(
                        type="parse",
                        content=diagnostic.code,
                        line=diagnostic.line,
                    )
                )

        lines = expansion_result.expanded_code.split("\n")
        executable_lines = self._iter_executable_lines(lines)

        data_path_auditor = None
        if config is not None and getattr(
            config, "ENABLE_DATA_COMMAND_PATH_GUARD", False
        ):
            data_path_auditor = DataPathAuditor(
                working_dir=config.WORKING_DIR,
                strict_local_boundary=config.STRICT_DATA_INFO_LOCAL_BOUNDARY,
                enable_url_guard=config.ENABLE_DATA_INFO_URL_GUARD,
                allowed_url_domains=config.DATA_INFO_ALLOWED_URL_DOMAINS,
            )

        for line_num, line in executable_lines:
            origin_line_num = self._origin_line_for_expanded_line(
                line_num,
                expansion_result.line_map,
            )
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

            # Check for dangerous commands
            command_items = self._check_dangerous_commands(
                cleaned_line, origin_line_num
            )
            dangerous_items.extend(command_items)

            # Check for dangerous patterns
            pattern_items = self._check_dangerous_patterns(
                cleaned_line, origin_line_num
            )
            dangerous_items.extend(pattern_items)

        for command in expansion_result.commands:
            dangerous_items.extend(
                self._check_command_parse_diagnostics(
                    command,
                    expansion_result,
                    data_path_guard_enabled=data_path_auditor is not None,
                )
            )

        # Check data-loading command paths when the guard is enabled.
        if data_path_auditor is not None:
            for command in expansion_result.commands:
                dangerous_items.extend(self._check_context_mutation_command(command))
                dangerous_items.extend(
                    self._check_data_command_path(command, data_path_auditor)
                )

        # Generate report
        is_safe = len(dangerous_items) == 0
        if not is_safe:
            item_summary = ", ".join(
                f"line {item.line}:{item.type}" for item in dangerous_items
            )
            logger.warning(
                "[SECURITY VIOLATION] Guard blocked dangerous dofile; items=[%s]",
                item_summary,
            )
        else:
            logger.debug("Guard validation passed with no dangerous items")
        return SecurityReport(is_safe=is_safe, dangerous_items=dangerous_items)

    @staticmethod
    def _origin_line_for_expanded_line(
        expanded_line_num: int,
        line_map: dict[int, list[int]],
    ) -> int:
        """Return the first original source line for an expanded line."""
        origins = line_map.get(expanded_line_num)
        if origins:
            return origins[0]
        return expanded_line_num

    def _collect_dangerous_local_names(self, lines: List[tuple[int, str]]) -> set[str]:
        """Collect macro names whose values are dangerous commands."""
        dangerous_names: set[str] = set()
        macro_pattern = re.compile(
            r"^\s*(?:local|global)\s+(\w+)\s+(.+)$", re.IGNORECASE
        )

        for _line_num, line in lines:
            stripped_line = line.strip()
            if (
                not stripped_line
                or stripped_line.startswith("*")
                or stripped_line.startswith("//")
            ):
                continue

            cleaned_line = self._strip_prefixes(stripped_line, self.stata_prefixes)
            matched = macro_pattern.search(cleaned_line)
            if not matched:
                continue

            local_name, local_value = matched.group(1), self._strip_macro_value_quotes(
                matched.group(2)
            )
            first_value_token = (
                self._normalize_command_token(local_value.split()[0])
                if local_value.split()
                else ""
            )
            if first_value_token in self.dangerous_commands:
                dangerous_names.add(local_name)

        return dangerous_names

    @staticmethod
    def _strip_macro_value_quotes(value: str) -> str:
        """Remove Stata macro value quotes, including compound quotes."""
        stripped_value = value.strip()
        if (
            len(stripped_value) >= 4
            and stripped_value.startswith('`"')
            and stripped_value.endswith("\"'")
        ):
            return stripped_value[2:-2]
        if (
            len(stripped_value) >= 2
            and stripped_value[0] == stripped_value[-1]
            and stripped_value[0] in {'"', "'"}
        ):
            return stripped_value[1:-1]
        return stripped_value

    @staticmethod
    def _check_macro_expansion(
        line: str, line_num: int, dangerous_local_names: set[str]
    ) -> List[RiskItem]:
        """Check whether a line expands a dangerous macro."""
        items: List[RiskItem] = []
        for local_name in dangerous_local_names:
            if re.search(rf"(?<!\w)`{re.escape(local_name)}'(?!\w)", line):
                macro_token = f"`{local_name}'"
                items.append(RiskItem(type="macro", content=macro_token, line=line_num))
            if re.search(rf"(?<!\w)\${re.escape(local_name)}(?!\w)", line):
                macro_token = f"${local_name}"
                items.append(RiskItem(type="macro", content=macro_token, line=line_num))
            if re.search(rf"(?<!\w)\$\{{{re.escape(local_name)}\}}(?!\w)", line):
                macro_token = f"${local_name}"
                items.append(RiskItem(type="macro", content=macro_token, line=line_num))
        return items

    def _check_command_parse_diagnostics(
        self,
        command: ParsedCommand,
        expansion_result: ExpansionResult,
        data_path_guard_enabled: bool,
    ) -> List[RiskItem]:
        """Fail closed on line-scoped parser uncertainty for sensitive commands."""
        diagnostics = [
            diagnostic
            for diagnostic in expansion_result.diagnostics_on(command)
            if diagnostic.security_relevant and diagnostic.scope == "line"
        ]
        if not diagnostics:
            return []

        if not self._command_requires_line_fail_closed(
            command,
            data_path_guard_enabled=data_path_guard_enabled,
        ):
            return []

        line_num = self._command_origin_line(command)
        return [
            RiskItem(
                type="parse",
                content=diagnostic.code,
                line=diagnostic.line or line_num,
            )
            for diagnostic in diagnostics
        ]

    def _command_requires_line_fail_closed(
        self,
        command: ParsedCommand,
        data_path_guard_enabled: bool,
    ) -> bool:
        """Return True when parser uncertainty on this command is security-sensitive."""
        if UNRESOLVED_MACRO_PATTERN.search(command.name):
            return True
        if command.name in self.dangerous_commands:
            return True
        if command.text.startswith("!"):
            return True
        if data_path_guard_enabled and (
            command.name in PATH_LIKE_COMMANDS
            or command.name in CONTEXT_MUTATION_COMMANDS
        ):
            return True
        return False

    @staticmethod
    def _check_context_mutation_command(command: ParsedCommand) -> List[RiskItem]:
        """Reject commands that make later relative path auditing unreliable."""
        if command.name not in CONTEXT_MUTATION_COMMANDS:
            return []
        line_num = GuardValidator._command_origin_line(command)
        logger.warning(
            "[SECURITY VIOLATION] Guard blocked context-mutating command: "
            "command='%s', line=%d",
            command.name,
            line_num,
        )
        return [RiskItem(type="context", content=command.name, line=line_num)]

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
        first_word = (
            self._normalize_command_token(line.split()[0]) if line.split() else ""
        )

        if first_word in self.dangerous_commands:
            items.append(RiskItem(type="command", content=first_word, line=line_num))

        # Special check for "!" which is a prefix
        if line.startswith("!"):
            items.append(RiskItem(type="command", content="!", line=line_num))

        return items

    @staticmethod
    def _normalize_command_token(token: str) -> str:
        """Normalize command-position punctuation before blacklist matching."""
        return token.lower().rstrip(",:")

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
                items.append(RiskItem(type="pattern", content=pattern, line=line_num))

        return items

    def _check_data_command_path(
        self,
        command: ParsedCommand,
        data_path_auditor: DataPathAuditor,
    ) -> List[RiskItem]:
        """Check whether a data-loading command references a disallowed path or URL.

        Covers direct loaders such as ``use`` and ``import <subcmd>`` as well
        as ``merge`` / ``append`` / ``joinby ... using`` syntax.
        """
        line_num = self._command_origin_line(command)

        if command.name == "webuse":
            return self._check_webuse_command(command, data_path_auditor)

        if command.name not in PATH_LIKE_COMMANDS:
            return []

        items: List[RiskItem] = []
        for data_path in command.data_paths:
            item = self._audit_data_path(data_path, line_num, data_path_auditor)
            if item is not None:
                items.append(item)

        return items

    def _check_webuse_command(
        self,
        command: ParsedCommand,
        data_path_auditor: DataPathAuditor,
    ) -> List[RiskItem]:
        """Reject unauditable ``webuse`` loads and audit ``webuse set`` URLs."""
        line_num = self._command_origin_line(command)
        remainder = command.text[len("webuse"):]
        normalized = remainder.strip()
        if not normalized.lower().startswith("set"):
            logger.warning(
                "[SECURITY VIOLATION] Guard blocked webuse data load: line=%d",
                line_num,
            )
            return [RiskItem(type="data_path", content="webuse", line=line_num)]

        data_paths = list(command.data_paths)
        if not data_paths:
            return [RiskItem(type="data_path", content="webuse set", line=line_num)]

        items: List[RiskItem] = []
        for data_path in data_paths:
            item = self._audit_data_path(data_path, line_num, data_path_auditor)
            if item is not None:
                items.append(item)
        return items

    @staticmethod
    def _command_origin_line(command: ParsedCommand) -> int:
        """Return the first original source line for a parsed command."""
        if command.origins:
            return command.origins[0]
        return command.line

    @staticmethod
    def _audit_data_path(
        data_path: str,
        line_num: int,
        data_path_auditor: DataPathAuditor,
    ) -> RiskItem | None:
        """Return a risk item when ``data_path`` violates the configured policy."""
        if UNRESOLVED_MACRO_PATTERN.search(data_path):
            logger.warning(
                "[SECURITY VIOLATION] Guard blocked data command with unresolved macro: "
                "line=%d",
                line_num,
            )
            return RiskItem(type="data_path", content=data_path, line=line_num)

        if data_path_auditor.is_url(data_path):
            result = data_path_auditor.validate_url(data_path)
            if isinstance(result, str):
                logger.warning(
                    "[SECURITY VIOLATION] Guard blocked data command with disallowed URL: "
                    "requested_url='%s', line=%d",
                    data_path_auditor._safe_url_for_log(data_path),
                    line_num,
                )
                return RiskItem(type="data_path", content=data_path, line=line_num)
            return None

        result = data_path_auditor.validate_local_path(data_path)
        if isinstance(result, str):
            logger.warning(
                "[SECURITY VIOLATION] Guard blocked data command with disallowed local path: "
                "line=%d",
                line_num,
            )
            return RiskItem(type="data_path", content=data_path, line=line_num)
        return None


class PackageManagementGuardValidator(GuardValidator):
    """Always block package-management commands from arbitrary dofiles."""

    def __init__(self) -> None:
        self.dangerous_commands = PACKAGE_MANAGEMENT_COMMANDS
        self.dangerous_patterns = [
            r"^\s*`[A-Za-z_]\w*'\s*",
            r"^\s*\$[A-Za-z_]\w*\s*",
            r"^\s*\$\{[A-Za-z_]\w*\}\s*",
        ]
        self.stata_prefixes = set(STATA_PREFIXES)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "RiskItem",
    "SecurityReport",
    "GuardValidator",
    "PackageManagementGuardValidator",
]
