"""Output helpers for installer status messages."""

from __future__ import annotations

import contextlib
import os
import sys
from typing import Iterator, TextIO

TAG_COLORS = {
    "[ERROR]\t": "31",
    "[DONE]\t": "32",
    "[WARN]\t": "33",
    "[BACKUP]\t": "36",
}


def _should_color(stream: TextIO) -> bool:
    """Return True if ANSI color should be applied to output on stream."""
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(stream.isatty())
    except AttributeError:
        return False


def _wrap(code: str, text: str) -> str:
    """Wrap text in ANSI color escape. Caller must gate with _should_color."""
    return f"\033[{code}m{text}\033[0m"


class ColorStream:
    """File-like wrapper that colorizes lines by [TAG]\\t prefix."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._buffer = ""
        self._enabled = _should_color(stream)

    def write(self, text: str) -> int:
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._write_line(f"{line}\n")
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            self._write_line(self._buffer)
            self._buffer = ""
        self._stream.flush()

    def isatty(self) -> bool:
        return self._stream.isatty()

    def __getattr__(self, name: str):
        return getattr(self._stream, name)

    def _write_line(self, line: str) -> None:
        if self._enabled:
            code = self._matching_code(line)
            if code is not None:
                self._stream.write(_wrap(code, line))
                return
        self._stream.write(line)

    def _matching_code(self, line: str) -> "str | None":
        stripped_line = line.lstrip()
        for prefix, code in TAG_COLORS.items():
            if stripped_line.startswith(prefix):
                return code
        return None


@contextlib.contextmanager
def colored_stdout() -> Iterator[ColorStream]:
    """Wrap sys.stdout with a ColorStream and restore it on exit."""
    original_stdout = sys.stdout
    color_stream = ColorStream(original_stdout)
    sys.stdout = color_stream
    try:
        yield color_stream
    finally:
        try:
            color_stream.flush()
        finally:
            sys.stdout = original_stdout
