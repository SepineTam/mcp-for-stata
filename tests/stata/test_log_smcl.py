from pathlib import Path

from stata_mcp.stata.builtin_tools.stata_log.read_smcl import (
    MAX_SMCL_EXPANSION,
    StataLogSMCL,
)


def _write_smcl(tmp_path: Path, content: str) -> Path:
    log_path = tmp_path / "test.smcl"
    log_path.write_text(content, encoding="utf-8")
    return log_path


def test_smcl_space_and_hline_preserve_normal_counts(tmp_path: Path) -> None:
    log_path = _write_smcl(tmp_path, "")

    content = StataLogSMCL(log_path)._strip_smcl_tags("a{space 5}b\nx{hline 8}y")

    assert "a     b" in content
    assert "x--------y" in content


def test_smcl_space_and_hline_large_counts_are_bounded(tmp_path: Path) -> None:
    log_path = _write_smcl(tmp_path, "")

    content = StataLogSMCL(log_path)._strip_smcl_tags(
        "{space 999999999}x\nx{hline 999999999}y"
    )

    assert f"{' ' * MAX_SMCL_EXPANSION}x" in content
    assert "-" * MAX_SMCL_EXPANSION in content
    assert len(content) <= (MAX_SMCL_EXPANSION * 2) + 4


def test_smcl_hline_without_count_uses_default(tmp_path: Path) -> None:
    log_path = _write_smcl(tmp_path, "")

    content = StataLogSMCL(log_path)._strip_smcl_tags("{hline}")

    assert content == "-" * 13
