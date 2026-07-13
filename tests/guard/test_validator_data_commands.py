"""Tests for GuardValidator data-command path auditing."""

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from stata_mcp.guard.validator import GuardValidator


@pytest.fixture
def working_dir(tmp_path: Path) -> Path:
    work = tmp_path / "work"
    work.mkdir()
    return work


@pytest.fixture
def enabled_config(working_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        ENABLE_DATA_COMMAND_PATH_GUARD=True,
        STRICT_DATA_INFO_LOCAL_BOUNDARY=True,
        ENABLE_DATA_INFO_URL_GUARD=True,
        DATA_INFO_ALLOWED_URL_DOMAINS=("example.com",),
        WORKING_DIR=working_dir,
    )


@pytest.fixture
def disabled_config(working_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        ENABLE_DATA_COMMAND_PATH_GUARD=False,
        STRICT_DATA_INFO_LOCAL_BOUNDARY=True,
        ENABLE_DATA_INFO_URL_GUARD=True,
        DATA_INFO_ALLOWED_URL_DOMAINS=("example.com",),
        WORKING_DIR=working_dir,
    )


def test_data_command_with_safe_local_path_passes(
    enabled_config, working_dir: Path
) -> None:
    data_file = working_dir / "data.csv"
    data_file.write_text("x,y\n1,2\n", encoding="utf-8")
    code = f'use "{data_file.as_posix()}"\nregress y x'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_data_command_with_prefixes_is_detected(
    enabled_config, working_dir: Path
) -> None:
    data_file = working_dir / "data.csv"
    data_file.write_text("x,y\n1,2\n", encoding="utf-8")
    code = f'capture noisily: use "{data_file.as_posix()}"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_use_command_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'use "/etc/passwd"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/etc/passwd" in item.content
        for item in report.dangerous_items
    )


def test_import_delimited_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'import delimited "/tmp/secret.csv"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.csv" in item.content
        for item in report.dangerous_items
    )


def test_use_using_syntax_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'use price mpg using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_relative_path_escaping_working_dir_is_rejected(enabled_config) -> None:
    code = 'use "../secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_url_command_with_disallowed_domain_is_rejected(enabled_config) -> None:
    code = 'import excel "https://evil.com/data.xlsx"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "evil.com" in item.content
        for item in report.dangerous_items
    )


def test_url_command_with_http_scheme_is_rejected(enabled_config) -> None:
    code = 'use "http://example.com/data.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_url_command_with_allowlisted_domain_passes(enabled_config) -> None:
    code = 'import delimited "https://example.com/data.csv"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_data_command_path_guard_disabled_allows_outside_path(disabled_config) -> None:
    code = 'use "/etc/passwd"'

    report = GuardValidator().validate(code, config=disabled_config)

    assert report.is_safe is True


def test_data_command_path_guard_without_config_is_disabled() -> None:
    code = 'use "/etc/passwd"'

    report = GuardValidator().validate(code)

    assert report.is_safe is True


def test_data_command_path_violation_is_logged(
    caplog,
    enabled_config,
) -> None:
    code = 'use "https://evil.com/data.dta?token=secret"'

    with caplog.at_level(logging.WARNING):
        report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    messages = "\n".join(caplog.messages)
    assert "[SECURITY VIOLATION]" in messages
    assert "token=secret" not in messages
    assert "evil.com" in messages


def test_insheet_command_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'insheet using "/tmp/secret.csv"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_infile_command_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'infile "/tmp/secret.raw"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_infix_command_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'infix "/tmp/secret.raw"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_use_abbreviation_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'u "/etc/passwd"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_use_abbreviation_us_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'us "/etc/passwd"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_apply_command_is_not_treated_as_data_command(enabled_config) -> None:
    code = 'apply "../secret.dta", replace'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_useful_word_is_not_treated_as_data_command(enabled_config) -> None:
    code = 'useful_command "../secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_commented_data_command_is_ignored(enabled_config) -> None:
    code = '* use "/etc/passwd"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_data_command_inside_block_comment_is_ignored(enabled_config) -> None:
    code = '/* use "/etc/passwd" */'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_dangerous_command_still_detected_alongside_data_path(enabled_config) -> None:
    code = 'shell rm -rf /\nuse "/etc/passwd"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "command" and item.content == "shell"
        for item in report.dangerous_items
    )
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_import_dbase_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'import dbase "/tmp/secret.dbf"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dbf" in item.content
        for item in report.dangerous_items
    )


def test_import_xml_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'import xml "/tmp/secret.xml"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_merge_using_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'merge 1:1 id using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_append_using_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'append using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_joinby_using_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'joinby id using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_merge_using_safe_local_path_passes(enabled_config, working_dir: Path) -> None:
    data_file = working_dir / "secret.dta"
    data_file.write_text("", encoding="utf-8")
    code = f'merge 1:1 id using "{data_file.as_posix()}"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_import_with_prefixes_is_detected(enabled_config) -> None:
    code = 'capture quietly: import dbase "/tmp/secret.dbf"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_merge_with_prefixes_is_detected(enabled_config) -> None:
    code = 'capture quietly: merge 1:1 id using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_merge_abbreviation_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'mer 1:1 id using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_append_abbreviation_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'app using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


@pytest.mark.parametrize("abbrev", ["ap", "appe", "appen", "app"])
def test_append_abbreviations_outside_working_dir_are_rejected(
    enabled_config, abbrev: str
) -> None:
    code = f'{abbrev} using "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_insheet_abbreviation_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'insh using "/tmp/secret.csv"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.csv" in item.content
        for item in report.dangerous_items
    )


def test_append_using_multiple_files_audits_all_paths(enabled_config) -> None:
    code = 'append using "/tmp/secret1.dta" "/tmp/secret2.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    data_path_items = [
        item for item in report.dangerous_items if item.type == "data_path"
    ]
    assert len(data_path_items) == 2
    assert any("/tmp/secret1.dta" in item.content for item in data_path_items)
    assert any("/tmp/secret2.dta" in item.content for item in data_path_items)


def test_continuation_use_using_outside_working_dir_is_rejected(enabled_config) -> None:
    code = 'use price mpg ///\nusing "/tmp/secret.dta"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_local_macro_data_path_is_expanded_and_rejected(enabled_config) -> None:
    code = 'local p "/tmp/secret.dta"\nuse "`p\'"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_global_macro_data_path_is_expanded_and_rejected(enabled_config) -> None:
    code = 'global P /tmp/secret.dta\nuse "$P"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_unresolved_macro_data_path_is_rejected(enabled_config) -> None:
    code = 'use "$P"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "$P" in item.content
        for item in report.dangerous_items
    )


def test_dynamic_macro_data_path_fails_closed(enabled_config) -> None:
    code = 'local p : env HOME\nuse "`p\'"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "parse" and item.content == "unresolved-macro"
        for item in report.dangerous_items
    )
    assert any(
        item.type == "data_path" and "`p'" in item.content
        for item in report.dangerous_items
    )


def test_non_sensitive_line_scoped_diagnostic_does_not_fail_whole_file(
    enabled_config,
) -> None:
    code = 'display "$S_DATE"'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is True


def test_compound_quoted_data_path_is_rejected(enabled_config) -> None:
    code = 'use `"/tmp/secret.dta"\''

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.dta" in item.content
        for item in report.dangerous_items
    )


def test_import_using_parentheses_outside_working_dir_is_rejected(
    enabled_config,
) -> None:
    code = 'import delimited using("/tmp/secret.csv")'

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and "/tmp/secret.csv" in item.content
        for item in report.dangerous_items
    )


def test_cd_is_rejected_when_data_command_path_guard_is_enabled(enabled_config) -> None:
    code = "cd /tmp\nuse secret.dta"

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "context" and item.content == "cd"
        for item in report.dangerous_items
    )


def test_cd_is_allowed_when_data_command_path_guard_is_disabled(
    disabled_config,
) -> None:
    code = "cd /tmp\nuse secret.dta"

    report = GuardValidator().validate(code, config=disabled_config)

    assert report.is_safe is True


def test_webuse_set_disallowed_url_is_rejected(enabled_config) -> None:
    code = "webuse set http://127.0.0.1/private"

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(item.type == "data_path" for item in report.dangerous_items)


def test_webuse_data_load_is_rejected_when_url_cannot_be_audited(
    enabled_config,
) -> None:
    code = "webuse auto, clear"

    report = GuardValidator().validate(code, config=enabled_config)

    assert report.is_safe is False
    assert any(
        item.type == "data_path" and item.content == "webuse"
        for item in report.dangerous_items
    )
