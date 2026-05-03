"""Tests for guard blacklist and validator protections."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stata_mcp.guard.blacklist import DANGEROUS_COMMANDS
from stata_mcp.guard.validator import GuardValidator


def test_dangerous_command_abbreviations_are_blacklisted() -> None:
    expected = {"sh", "xsh", "winex", "unixc", "era", "rmd"}
    assert expected.issubset(DANGEROUS_COMMANDS)


def test_macro_expansion_with_dangerous_local_is_flagged() -> None:
    code = 'local cmd "shell"\n`cmd\' "rm -rf /"'  # noqa: S608
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "`cmd'" for item in report.dangerous_items)


def test_macro_expansion_with_safe_local_is_not_flagged() -> None:
    code = 'local cmd "regress"\n`cmd\' y x'
    report = GuardValidator().validate(code)
    assert report.is_safe is True


def test_commented_local_definition_is_ignored() -> None:
    code = '* local cmd "shell"\n`cmd\' "rm -rf /"'  # noqa: S608
    report = GuardValidator().validate(code)
    assert report.is_safe is True
