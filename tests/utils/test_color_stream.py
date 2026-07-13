"""Tests for installer colored output helpers."""

from __future__ import annotations

import io
import sys

import pytest

from stata_mcp.utils.installer import ColorStream, colored_stdout, paint_green


class TtyStringIO(io.StringIO):
    name = "<tty>"
    mode = "w"

    def isatty(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def clear_no_color(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)


def test_write_matching_tag_wraps_line():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("[DONE]\tok\n")

    assert stream.getvalue() == "\033[32m[DONE]\tok\n\033[0m"


def test_write_without_tag_passes_through_plain():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("plain line\n")

    assert stream.getvalue() == "plain line\n"


def test_write_buffers_until_newline():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("[WARN]\t")
    assert stream.getvalue() == ""

    color_stream.write("careful\n")
    assert stream.getvalue() == "\033[33m[WARN]\tcareful\n\033[0m"


def test_write_multiline_content_colors_each_line():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("[ERROR]\tbad\n[BACKUP]\tsaved\n")

    assert stream.getvalue() == (
        "\033[31m[ERROR]\tbad\n\033[0m"
        "\033[36m[BACKUP]\tsaved\n\033[0m"
    )


def test_flush_writes_partial_line_without_newline():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("[DONE]\tpartial")
    color_stream.flush()

    assert stream.getvalue() == "\033[32m[DONE]\tpartial\033[0m"


def test_leading_whitespace_before_tag_is_detected():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("  [WARN]\tindented\n")

    assert stream.getvalue() == "\033[33m  [WARN]\tindented\n\033[0m"


def test_tag_casing_mismatch_passes_through_plain():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("[error]\tbad\n")

    assert stream.getvalue() == "[error]\tbad\n"


def test_no_color_env_disables_ansi(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    color_stream.write("[DONE]\tok\n")

    assert stream.getvalue() == "[DONE]\tok\n"


def test_non_tty_stream_disables_ansi():
    stream = io.StringIO()
    color_stream = ColorStream(stream)

    color_stream.write("[DONE]\tok\n")

    assert stream.getvalue() == "[DONE]\tok\n"


def test_colored_stdout_restores_original_stdout(monkeypatch):
    original_stdout = TtyStringIO()
    monkeypatch.setattr(sys, "stdout", original_stdout)

    with colored_stdout() as color_stream:
        assert sys.stdout is color_stream
        print("[DONE]\tok")

    assert sys.stdout is original_stdout
    assert original_stdout.getvalue() == "\033[32m[DONE]\tok\n\033[0m"


def test_colored_stdout_restores_stdout_after_exception(monkeypatch):
    original_stdout = TtyStringIO()
    monkeypatch.setattr(sys, "stdout", original_stdout)

    with pytest.raises(RuntimeError, match="boom"):
        with colored_stdout():
            print("[DONE]\tpartial", end="")
            raise RuntimeError("boom")

    assert sys.stdout is original_stdout
    assert original_stdout.getvalue() == "\033[32m[DONE]\tpartial\033[0m"


def test_getattr_passthrough_returns_underlying_attribute():
    stream = TtyStringIO()
    color_stream = ColorStream(stream)

    assert color_stream.name == "<tty>"


def test_paint_green_uses_shared_color_gate(monkeypatch):
    original_stdout = TtyStringIO()
    monkeypatch.setattr(sys, "stdout", original_stdout)

    assert paint_green("ok") == "\033[32mok\033[0m"

    monkeypatch.setenv("NO_COLOR", "1")
    assert paint_green("ok") == "ok"
