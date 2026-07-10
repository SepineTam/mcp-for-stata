#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for stata_mcp.utils.parse_dofile static expansion."""

import pytest

from stata_mcp.utils.parse_dofile import (
    expand_code,
    expand_code_for_security,
    expand_dofile,
    expand_dofile_for_security,
)


def _lines(result: str) -> list[str]:
    """Non-blank, stripped lines of an expansion result."""
    return [line.strip() for line in result.splitlines() if line.strip()]


# ============================================================================
# Basics and comments
# ============================================================================


def test_plain_code_passthrough():
    code = 'use "auto.dta", clear\nsummarize price\n'
    result = expand_code(code)
    assert 'use "auto.dta", clear' in result
    assert "summarize price" in result


def test_empty_code():
    assert expand_code("") == ""


def test_star_and_slash_comments_stripped():
    code = "* full line comment\nuse auto.dta // trailing comment\n// own line\n"
    result = expand_code(code)
    assert "comment" not in result
    assert _lines(result) == ["use auto.dta"]


def test_block_comment_join_exposes_obfuscation():
    result = expand_code("she/*hidden*/ll ls\n")
    assert _lines(result) == ["shell ls"]


def test_continuation_joined():
    result = expand_code('display ///\n    "hello"\n')
    first = _lines(result)[0]
    assert first.startswith("display")
    assert '"hello"' in first


def test_nested_block_comment():
    code = "/* outer /* inner */ still comment */display 1\n"
    assert _lines(expand_code(code)) == ["display 1"]


def test_comment_tokens_inside_strings_preserved():
    code = 'display "// not a comment /* nope */ * neither"\n'
    result = expand_code(code)
    assert '"// not a comment /* nope */ * neither"' in result


# ============================================================================
# #delimit normalization
# ============================================================================


def test_delimit_semicolon_normalized():
    code = (
        "#delimit ;\n"
        "display\n"
        '  "a";\n'
        "gen x = 1; gen y = 2;\n"
        "#delimit cr\n"
        "list\n"
    )
    lines = _lines(expand_code(code))
    assert 'display "a"' in lines
    assert "generate x = 1" in lines
    assert "generate y = 2" in lines
    assert "list" in lines
    assert not any("#delimit" in line for line in lines)


def test_delimit_semicolon_string_with_semicolon():
    code = '#delimit ;\ndisplay "a;b";\n#delimit cr\n'
    assert 'display "a;b"' in _lines(expand_code(code))


# ============================================================================
# Abbreviation expansion
# ============================================================================


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("u mydata.dta, clear", "use mydata.dta, clear"),
        ("cap qui sh ls", "capture quietly shell ls"),
        ("era temp.dta", "erase temp.dta"),
        ("loc x 5", "local x 5"),
        ("gl y 6", "global y 6"),
        ("g z = 1", "generate z = 1"),
        ("di 2 + 2", "display 2 + 2"),
        ("l", "list"),
        ("by rep78: g y = 1", "by rep78: generate y = 1"),
    ],
)
def test_abbreviations_expanded(source, expected):
    assert _lines(expand_code(source + "\n")) == [expected]


def test_invalid_abbreviation_untouched():
    # "lo" is below local's minimum abbreviation ("loc") and is not list
    assert _lines(expand_code("lo x 5\n")) == ["lo x 5"]


# ============================================================================
# Macro expansion
# ============================================================================


def test_local_macro_expanded():
    code = "local cmd shell\n`cmd' rm -rf /tmp/x\n"
    lines = _lines(expand_code(code))
    assert "local cmd shell" in lines
    assert "shell rm -rf /tmp/x" in lines


def test_undefined_local_blanks_like_runtime():
    result = expand_code("`nothing'shell ls\n")
    assert _lines(result) == ["shell ls"]


def test_global_macro_expanded():
    code = "global tool shell\n$tool ls\n${tool} pwd\n"
    lines = _lines(expand_code(code))
    assert "shell ls" in lines
    assert "shell pwd" in lines


def test_undefined_global_kept():
    result = expand_code('display "$S_DATE"\n')
    assert "$S_DATE" in result


def test_dynamic_local_reference_untouched():
    code = "local n : word count a b c\ndisplay `n'\n"
    result = expand_code(code)
    assert "display `n'" in result


def test_equals_literal_local_expanded():
    code = "local x = 5\nlocal s = \"abc\"\ndisplay `x' `s'\n"
    result = expand_code(code)
    assert "display 5 abc" in result


def test_equals_expression_local_untouched():
    code = "local x = 2 + 2\ndisplay `x'\n"
    result = expand_code(code)
    assert "display `x'" in result


def test_nested_macro_references():
    code = "local x1 shell\nlocal i 1\n`x`i'' ls\n"
    assert "shell ls" in _lines(expand_code(code))


def test_local_redefinition_uses_latest_value():
    code = "local a one\nlocal a two\ndisplay `a'\n"
    assert "display two" in expand_code(code)


# ============================================================================
# Loop unrolling
# ============================================================================


def test_foreach_in_unrolled():
    code = 'foreach v in a b c {\n    display "`v\'"\n}\n'
    lines = _lines(expand_code(code))
    assert lines == ['display "a"', 'display "b"', 'display "c"']


def test_foreach_of_local_unrolled():
    code = "local vars price mpg\nforeach v of local vars {\n    summarize `v'\n}\n"
    lines = _lines(expand_code(code))
    assert "summarize price" in lines
    assert "summarize mpg" in lines


def test_foreach_of_numlist_unrolled():
    code = "foreach k of numlist 1/3 {\n    display `k'\n}\n"
    lines = _lines(expand_code(code))
    assert lines == ["display 1", "display 2", "display 3"]


def test_forvalues_unrolled():
    code = "forvalues i = 1/3 {\n    generate x`i' = `i'\n}\n"
    lines = _lines(expand_code(code))
    assert lines == [
        "generate x1 = 1",
        "generate x2 = 2",
        "generate x3 = 3",
    ]


def test_forvalues_step_unrolled():
    code = "forv i = 1(2)5 {\n    display `i'\n}\n"
    assert _lines(expand_code(code)) == ["display 1", "display 3", "display 5"]


def test_forvalues_negative_step_unrolled():
    code = "forvalues i = 3(-1)1 {\n    display `i'\n}\n"
    assert _lines(expand_code(code)) == ["display 3", "display 2", "display 1"]


def test_nested_loops_unrolled():
    code = (
        "foreach a in 1 2 {\n"
        "    foreach b in x y {\n"
        "        display \"`a'`b'\"\n"
        "    }\n"
        "}\n"
    )
    lines = _lines(expand_code(code))
    assert lines == ['display "1x"', 'display "1y"', 'display "2x"', 'display "2y"']


def test_loop_hides_dangerous_command_in_pieces():
    code = (
        'local x ""\n'
        "foreach p in sh ell {\n"
        "    local x \"`x'`p'\"\n"
        "}\n"
        "`x' ls\n"
    )
    lines = _lines(expand_code(code))
    assert "shell ls" in lines


def test_quoted_foreach_items():
    code = 'foreach f in "my data.dta" other.dta {\n' '    use "`f\'", clear\n' "}\n"
    lines = _lines(expand_code(code))
    assert 'use "my data.dta", clear' in lines
    assert 'use "other.dta", clear' in lines


# ============================================================================
# Preserved (non-expandable) loops
# ============================================================================


def test_huge_forvalues_preserved():
    code = "forvalues i = 1/999999 {\n    display `i'\n}\n"
    result = expand_code(code)
    assert "forvalues i = 1/999999 {" in result
    assert "display `i'" in result
    assert "}" in result


def test_over_budget_loop_preserved():
    code = "forvalues i = 1/60000 {\n    display `i'\n}\n"
    result = expand_code(code)
    assert "forvalues i = 1/60000 {" in result
    assert "display `i'" in result


def test_zero_step_forvalues_preserved():
    code = "forvalues i = 1(0)5 {\n    display `i'\n}\n"
    result = expand_code(code)
    assert "forvalues i = 1(0)5 {" in result
    assert "display `i'" in result


def test_foreach_of_varlist_preserved_and_var_protected():
    code = "foreach v of varlist price mpg {\n    summarize `v'\n}\n"
    result = expand_code(code)
    assert "foreach v of varlist price mpg {" in result
    assert "summarize `v'" in result


def test_while_preserved_with_body_expanded():
    code = (
        "local i 1\n"
        "while `i' < 3 {\n"
        "    display `i'\n"
        "    local i = `i' + 1\n"
        "}\n"
    )
    result = expand_code(code)
    assert "while 1 < 3 {" in result
    assert "display 1" in result


def test_unbalanced_loop_keeps_content():
    code = "foreach v in a b {\n    display `v'\n"
    result = expand_code(code)
    assert "foreach v in a b {" in result
    assert "display `v'" in result


# ============================================================================
# Program blocks
# ============================================================================


def test_program_block_unknown_locals_untouched():
    code = 'program define myprog\n    display "`msg\'"\nend\n'
    result = expand_code(code)
    assert '"`msg\'"' in result
    assert "program define myprog" in result
    assert "end" in result


def test_program_drop_does_not_open_block():
    code = "program drop _all\ndisplay `undefined'\n"
    result = expand_code(code)
    # after "program drop" we are NOT inside a program: blanking applies
    assert "display" in result
    assert "`undefined'" not in result


# ============================================================================
# File reading
# ============================================================================


def test_expand_dofile_reads_path(tmp_path):
    dofile = tmp_path / "job.do"
    dofile.write_text("loc cmd shell\n`cmd' ls\n", encoding="utf-8")
    result = expand_dofile(dofile)
    assert "shell ls" in result


def test_expand_dofile_accepts_str_path(tmp_path):
    dofile = tmp_path / "job.do"
    dofile.write_text("u auto.dta\n", encoding="utf-8")
    assert "use auto.dta" in expand_dofile(str(dofile))


def test_expand_dofile_missing_file():
    with pytest.raises(FileNotFoundError):
        expand_dofile("/nonexistent/path/job.do")


def test_expand_dofile_gbk_encoding(tmp_path):
    dofile = tmp_path / "gbk.do"
    dofile.write_bytes('display "使用中文数据"\n'.encode("gbk"))
    result = expand_dofile(dofile)
    assert "使用中文数据" in result


# ============================================================================
# Guard integration
# ============================================================================


def test_guard_catches_macro_obfuscated_shell():
    from stata_mcp.guard.validator import GuardValidator

    code = "`oops'shell rm -rf /tmp/x\n"
    validator = GuardValidator()
    # raw source slips past the command check (line starts with a macro)
    assert validator.validate(code).is_safe is True
    # expanded source is caught
    assert validator.validate(expand_code(code)).is_safe is False


def test_guard_catches_loop_assembled_command():
    from stata_mcp.guard.validator import GuardValidator

    code = (
        'local x ""\n'
        "foreach p in sh ell {\n"
        "    local x \"`x'`p'\"\n"
        "}\n"
        "`x' ls\n"
    )
    expanded = expand_code(code)
    assert GuardValidator().validate(expanded).is_safe is False


# ============================================================================
# ExpansionResult contract: diagnostics, line map, fail-closed signal
# ============================================================================


def _diag_codes(result):
    return {d.code for d in result.diagnostics}


def test_clean_code_has_no_diagnostics():
    result = expand_code_for_security('use "auto.dta", clear\nsummarize price\n')
    assert result.diagnostics == ()
    assert result.has_unsupported_security_construct is False
    assert result.line_map[1] == [1]
    assert result.line_map[2] == [2]


def test_delimit_diagnostic_is_not_security_relevant():
    result = expand_code_for_security('#delimit ;\ndisplay "a";\n#delimit cr\n')
    assert "delimit-normalized" in _diag_codes(result)
    assert result.has_unsupported_security_construct is False


def test_unresolved_dynamic_macro_fails_closed():
    code = 'local p : env HOME\nuse "`p\'"\n'
    result = expand_code_for_security(code)
    assert "unresolved-macro" in _diag_codes(result)
    assert result.has_unsupported_security_construct is True
    use_cmd = [c for c in result.commands if c.name == "use"][0]
    assert use_cmd.has_unresolved_macro is True


def test_preserved_while_loop_reports_diagnostic():
    code = "local i 1\nwhile `i' < 3 {\n    display `i'\n}\n"
    result = expand_code_for_security(code)
    assert "preserved-loop" in _diag_codes(result)
    assert result.has_unsupported_security_construct is True


def test_preserved_varlist_loop_reports_diagnostic():
    code = "foreach v of varlist price mpg {\n    summarize `v'\n}\n"
    result = expand_code_for_security(code)
    assert "preserved-loop" in _diag_codes(result)
    assert "unresolved-macro" in _diag_codes(result)


def test_oversized_loop_reports_diagnostic():
    code = "forvalues i = 1/999999 {\n    display `i'\n}\n"
    result = expand_code_for_security(code)
    assert "preserved-loop" in _diag_codes(result)
    assert result.has_unsupported_security_construct is True


def test_unbalanced_quotes_reports_diagnostic():
    result = expand_code_for_security('use "unterminated.dta\n')
    assert "unbalanced-quotes" in _diag_codes(result)
    assert result.has_unsupported_security_construct is True


def test_unbalanced_block_reports_diagnostic():
    result = expand_code_for_security("foreach v in a b {\n    display `v'\n")
    assert "unbalanced-block" in _diag_codes(result)
    assert result.has_unsupported_security_construct is True


def test_program_block_macro_fails_closed():
    code = 'program define myprog\n    display "`msg\'"\nend\n'
    result = expand_code_for_security(code)
    assert "unresolved-macro" in _diag_codes(result)
    assert result.has_unsupported_security_construct is True


def test_internal_error_is_reported_not_swallowed(monkeypatch):
    import stata_mcp.utils.parse_dofile as module

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(module, "_process_lines", boom)
    original = "display 1\n"
    result = expand_code_for_security(original)
    assert result.expanded_code == original
    assert "internal-error" in _diag_codes(result)
    assert result.has_unsupported_security_construct is True
    # the best-effort wrapper still returns the original content
    assert expand_code(original) == original


def test_line_map_tracks_continuation():
    code = 'use keepvar ///\nusing "/tmp/secret.dta"\n'
    result = expand_code_for_security(code)
    assert result.line_map[1] == [1, 2]
    assert 'using "/tmp/secret.dta"' in result.expanded_code


def test_line_map_tracks_unrolled_loop():
    code = "forvalues i = 1/2 {\n    display `i'\n}\n"
    result = expand_code_for_security(code)
    assert result.line_map[1] == [2]
    assert result.line_map[2] == [2]


def test_expand_dofile_for_security_reads_path(tmp_path):
    dofile = tmp_path / "job.do"
    dofile.write_text("u auto.dta\n", encoding="utf-8")
    result = expand_dofile_for_security(dofile)
    assert "use auto.dta" in result.expanded_code
    assert result.commands[0].name == "use"


# ============================================================================
# Command tokenization: data-path bypass surfaces
# ============================================================================


def test_commands_cd_then_use():
    result = expand_code_for_security("cd /tmp\nuse secret.dta\n")
    names = [c.name for c in result.commands]
    assert names == ["cd", "use"]
    assert result.commands[1].text == "use secret.dta"


def test_commands_macro_path_expanded():
    code = 'local p "/tmp/secret.dta"\nuse "`p\'"\n'
    result = expand_code_for_security(code)
    assert result.has_unsupported_security_construct is False
    use_cmd = [c for c in result.commands if c.name == "use"][0]
    assert "/tmp/secret.dta" in use_cmd.string_literals


def test_commands_using_after_continuation():
    code = 'use keepvar ///\nusing "/tmp/secret.dta"\n'
    result = expand_code_for_security(code)
    use_cmd = result.commands[0]
    assert use_cmd.name == "use"
    assert use_cmd.using_paths == ("/tmp/secret.dta",)


def test_commands_compound_quoted_path():
    code = 'use `"/tmp/secret.dta"\'\n'
    result = expand_code_for_security(code)
    assert result.commands[0].string_literals == ("/tmp/secret.dta",)


def test_commands_using_paren_form():
    code = 'import delimited using("/tmp/secret.csv")\n'
    result = expand_code_for_security(code)
    command = result.commands[0]
    assert command.name == "import"
    assert command.using_paths == ("/tmp/secret.csv",)


def test_commands_webuse_set():
    code = "webuse set http://127.0.0.1/private\nwebuse secret, clear\n"
    result = expand_code_for_security(code)
    names = [c.name for c in result.commands]
    assert names == ["webuse", "webuse"]
    assert result.commands[1].options == "clear"


def test_commands_multiple_using_paths():
    code = 'append using "a.dta" "b.dta"\n'
    result = expand_code_for_security(code)
    assert result.commands[0].using_paths == ("a.dta", "b.dta")


def test_commands_name_strips_prefixes():
    code = 'cap qui use "x.dta", clear\nby rep78: generate y = 1\n'
    result = expand_code_for_security(code)
    assert result.commands[0].name == "use"
    assert result.commands[0].options == "clear"
    assert result.commands[1].name == "generate"
