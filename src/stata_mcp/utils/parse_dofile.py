#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : parse_dofile.py

"""Security-oriented static expansion of Stata dofiles.

This module is a **normalizer for security checking, not a Stata
interpreter**. It rewrites a dofile into the flat form Stata would
actually execute so that downstream validators scan real commands
instead of obfuscated source text:

- comments (``*``, ``//``, ``///``, nested ``/* */``) are removed with
  string awareness; inline block comments join the surrounding text,
  which surfaces obfuscation such as ``she/**/ll``
- ``#delimit ;`` blocks are normalized back to one command per line
- command abbreviations are spelled out per Stata's minimum
  abbreviation rules (``u`` -> ``use``, ``loc`` -> ``local``,
  ``cap qui sh`` -> ``capture quietly shell``, ...)
- ``local`` / ``global`` literal definitions are tracked and their
  references substituted; a local never defined in the file expands to
  an empty string (matching Stata runtime, which defeats
  ``` `undefined'shell ``` style concatenation)
- ``foreach`` / ``forvalues`` loops are unrolled when their item list
  is statically resolvable, within an output budget

Anything that cannot be resolved statically (``while`` loops,
``foreach ... of varlist``, ``=`` expressions, extended macro
functions, oversized loops, unbalanced quotes or braces) is preserved
verbatim — the expanded text never contains less than the original
source did — **and** reported as a :class:`ParseDiagnostic` so that a
security consumer can fail closed instead of trusting a best-effort
result.

Two API levels are provided:

- :func:`expand_code_for_security` / :func:`expand_dofile_for_security`
  return an :class:`ExpansionResult` with the expanded code, structured
  diagnostics, a line map back to the original source, and a light
  per-command tokenization (:class:`ParsedCommand`).
- :func:`expand_code` / :func:`expand_dofile` are best-effort
  conveniences that return only the expanded string (suitable for
  display; security callers should use the ``*_for_security`` forms).

Usage::

    from stata_mcp.utils.parse_dofile import expand_code_for_security

    result = expand_code_for_security(code)

    # conservative policy: fail closed on anything unresolved
    if result.has_unsupported_security_construct:
        ...  # reject

    # graded policy: always reject structural damage, then decide
    # per command for line-scoped diagnostics
    if result.requires_global_fail_closed:
        ...  # reject
    for command in result.commands:
        ...  # audit command.name / command.data_paths;
        #      reject sensitive commands when
        #      command.has_unresolved_macro or
        #      result.diagnostics_on(command) is non-empty
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

#: Encodings tried in order when reading a dofile from disk. The last
#: entry decodes with ``errors="replace"`` so reading never raises.
_ENCODING_FALLBACKS: tuple[str, ...] = ("utf-8-sig", "gbk", "latin-1")

#: Default cap on emitted lines, bounding loop-unrolling explosion.
DEFAULT_MAX_OUTPUT_LINES: int = 50_000

#: Maximum nesting depth for recursive block expansion.
_MAX_EXPANSION_DEPTH: int = 32

#: Maximum substitution passes per line (bounds nested macro references).
_MAX_MACRO_PASSES: int = 20

#: Maximum iterations a single loop may unroll to.
_MAX_LOOP_ITERATIONS: int = 100_000

#: Commands expanded from their Stata minimum abbreviations. Values are
#: the minimum number of leading characters Stata accepts. A token is
#: expanded only when it prefixes exactly one entry at sufficient length.
_COMMAND_MIN_ABBREV: dict[str, int] = {
    "use": 1,
    "save": 2,
    "local": 3,
    "global": 2,
    "generate": 1,
    "display": 2,
    "describe": 1,
    "summarize": 2,
    "list": 1,
    "regress": 3,
    "tabulate": 2,
    "program": 2,
    "forvalues": 4,
    # data-read commands: infile owns the "inf" abbreviation, so infix
    # must be spelled out (min length = full name)
    "infile": 3,
    "infix": 5,
    "insheet": 4,
    # security-relevant abbreviations mirrored from guard/blacklist.py
    "shell": 2,
    "xshell": 3,
    "winexec": 5,
    "unixcmd": 5,
    "erase": 3,
    "rmdir": 3,
}

#: Prefix commands that may stack in front of another command.
_PREFIX_MIN_ABBREV: dict[str, int] = {
    "capture": 3,
    "quietly": 3,
    "noisily": 1,
}

#: ``by``-style prefixes: the varlist between the prefix and the colon
#: is kept verbatim, then expansion continues after the colon.
_BY_PREFIXES: frozenset[str] = frozenset({"by", "bys", "byso", "bysor", "bysort"})

#: List types accepted by ``foreach ... of``.
_FOREACH_OF_KINDS: tuple[str, ...] = (
    "local",
    "global",
    "numlist",
    "varlist",
    "newlist",
)

# ============================================================================
# Regular expressions
# ============================================================================

_LOCAL_REF_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)'")
_MACRO_EXPRESSION_RE = re.compile(r"`[=:]")
_GLOBAL_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_GLOBAL_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
_MACRO_DEF_RE = re.compile(
    r"^\s*(local|global)\s+([A-Za-z_][A-Za-z0-9_]*)(.*)$", re.IGNORECASE
)
_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
_PREFIX_STRIP_RE = re.compile(
    r"^\s*(?:(?:capture|quietly|noisily):?\s+)+", re.IGNORECASE
)
_BY_PREFIX_STRIP_RE = re.compile(r"^\s*bys?\w*\s+[^:\"']*:\s*", re.IGNORECASE)
_PROGRAM_START_RE = re.compile(
    r"^\s*program\s+(?:define\s+)?([A-Za-z_]\w*)", re.IGNORECASE
)
_PROGRAM_END_RE = re.compile(r"^\s*end\s*$", re.IGNORECASE)
_FOREACH_IN_RE = re.compile(
    r"^\s*foreach\s+([A-Za-z_]\w*)\s+in\s+(.*?)\s*\{\s*$", re.IGNORECASE
)
_FOREACH_OF_RE = re.compile(
    r"^\s*foreach\s+([A-Za-z_]\w*)\s+of\s+(\w+)\s+(.*?)\s*\{\s*$", re.IGNORECASE
)
_FORVALUES_RE = re.compile(
    r"^\s*forvalues\s+([A-Za-z_]\w*)\s*=\s*(.*?)\s*\{\s*$", re.IGNORECASE
)
_WHILE_RE = re.compile(r"^\s*while\b.*\{\s*$", re.IGNORECASE)
_DELIMIT_RE = re.compile(r"^\s*#d[a-z]*\s*(.*)$", re.IGNORECASE)
_USING_PAREN_RE = re.compile(r"\busing\b\s*\(", re.IGNORECASE)

#: Subcommands of ``program`` that do not open a program block.
_PROGRAM_NON_BLOCK_SUBCOMMANDS: frozenset[str] = frozenset({"drop", "dir", "list"})


# ============================================================================
# Public data structures
# ============================================================================


@dataclass(frozen=True)
class ParseDiagnostic:
    """A structured note about a construct the expander could not resolve.

    Attributes:
        code: Machine-readable diagnostic kind, e.g. ``unresolved-macro``,
            ``preserved-loop``, ``unbalanced-quotes``, ``internal-error``.
        message: Human-readable explanation.
        line: 1-indexed line number in the **original** source
            (0 when no specific line applies).
        security_relevant: True when a security consumer should treat the
            construct as unsupported and fail closed.
        scope: Blast radius of the problem. ``"global"`` means the
            normalized view as a whole may be unreliable (structural
            damage: unbalanced quotes/blocks, exhausted budget,
            internal errors) and a security consumer should reject the
            dofile outright. ``"line"`` means the problem is confined
            to the reported line(s) (unresolved macros, preserved
            loops); the rest of the expansion is still faithful, so a
            consumer may choose to fail closed only when the affected
            lines intersect security-sensitive commands.
    """

    code: str
    message: str
    line: int
    security_relevant: bool = True
    scope: str = "line"

    def __str__(self) -> str:
        """Return a compact human-readable representation."""
        return f"Line {self.line}: [{self.code}] {self.message}"


@dataclass(frozen=True)
class ParsedCommand:
    """Light tokenization of one expanded command line.

    This is deliberately not an AST: it extracts just enough structure
    for a security guard to audit commands and data paths without
    re-guessing strings.

    Attributes:
        name: Normalized command token (prefixes such as
            ``capture``/``quietly``/``by ...:`` stripped, abbreviations
            already spelled out by the expander), lowercased.
        text: The full expanded command line, stripped.
        line: 1-indexed line number in the expanded code.
        origins: 1-indexed line numbers in the original source.
        options: Text after the first top-level comma ("" when absent).
        string_literals: Contents of all ``"..."`` and ``` `"..."' ```
            literals on the line, in order.
        using_paths: Targets of ``using ...`` / ``using(...)`` clauses
            (quoted or bare, multiple targets supported).
        data_paths: Unified file/URL arguments of this command: all
            ``using`` targets plus, for known file commands (``use``,
            ``save``, ``import``/``export``, ``append``, ``merge``,
            ``do``/``run``/``include``, ``erase``, ``copy``, ``cd``,
            ``webuse``/``sysuse``, ...), the direct path argument
            (``use "x.dta"``, ``import delimited "x.csv"``,
            ``webuse set <url>``). Guards should audit this field
            instead of inferring paths per command type.
        has_unresolved_macro: True when the line still contains macro
            references or expressions the expander could not resolve.
    """

    name: str
    text: str
    line: int
    origins: tuple[int, ...]
    options: str
    string_literals: tuple[str, ...]
    using_paths: tuple[str, ...]
    data_paths: tuple[str, ...]
    has_unresolved_macro: bool


@dataclass
class ExpansionResult:
    """Full result of a security-oriented expansion.

    Attributes:
        expanded_code: The expanded dofile content.
        diagnostics: Structured notes about unsupported constructs.
        line_map: Mapping from 1-indexed line numbers in
            ``expanded_code`` to the 1-indexed original source lines
            that produced them.
        commands: Per-line light tokenization of the expanded code.
    """

    expanded_code: str
    diagnostics: tuple[ParseDiagnostic, ...]
    line_map: dict[int, list[int]]
    commands: tuple[ParsedCommand, ...]

    @property
    def has_unsupported_security_construct(self) -> bool:
        """True when any security-relevant diagnostic exists.

        This is the conservative aggregate: rejecting on it fails
        closed on every unresolved construct anywhere in the file. For
        a graded policy, reject on
        :attr:`requires_global_fail_closed` unconditionally and handle
        line-scoped diagnostics per command via :meth:`diagnostics_on`
        or :attr:`ParsedCommand.has_unresolved_macro`.
        """
        return any(d.security_relevant for d in self.diagnostics)

    @property
    def requires_global_fail_closed(self) -> bool:
        """True when the expanded view itself may be unreliable.

        Set by ``scope="global"`` diagnostics (unbalanced quotes or
        blocks, exhausted expansion budget, depth overflow, internal
        errors). A security consumer must reject the whole dofile in
        this case regardless of per-command policy.
        """
        return any(
            d.security_relevant and d.scope == "global" for d in self.diagnostics
        )

    def diagnostics_on(self, command: ParsedCommand) -> tuple[ParseDiagnostic, ...]:
        """Diagnostics whose original lines intersect ``command``.

        Useful for line-scoped fail-closed policies: reject when a
        security-sensitive command carries any security-relevant
        diagnostic.
        """
        origins = set(command.origins)
        return tuple(d for d in self.diagnostics if d.line in origins)


# ============================================================================
# Internal state containers
# ============================================================================


@dataclass
class _Line:
    """A logical line of code with its originating source lines."""

    text: str
    origins: tuple[int, ...]

    @property
    def first_origin(self) -> int:
        """First original line number (0 when unknown)."""
        return self.origins[0] if self.origins else 0


class _DiagnosticCollector:
    """Accumulates deduplicated diagnostics during expansion."""

    def __init__(self) -> None:
        self.items: list[ParseDiagnostic] = []
        self._seen: set[tuple[str, str, int]] = set()

    def add(
        self,
        code: str,
        message: str,
        line: int,
        security_relevant: bool = True,
        scope: str = "line",
    ) -> None:
        """Record a diagnostic unless an identical one already exists."""
        key = (code, message, line)
        if key in self._seen:
            return
        self._seen.add(key)
        self.items.append(
            ParseDiagnostic(
                code=code,
                message=message,
                line=line,
                security_relevant=security_relevant,
                scope=scope,
            )
        )


@dataclass
class _MacroState:
    """Tracks macro definitions collected while walking the dofile.

    Attributes:
        locals_: Locals with statically known literal values.
        globals_: Globals with statically known literal values.
        dynamic_locals: Local names defined via ``=`` expressions or
            extended macro functions; their references stay untouched.
        dynamic_globals: Same as above, for globals.
        protected: Loop variables of loops that could not be unrolled;
            their references stay untouched.
        program_depth: Nesting depth of ``program define`` blocks.
            Inside a program, undefined locals are runtime-scoped and
            must not be blanked.
    """

    locals_: dict[str, str] = field(default_factory=dict)
    globals_: dict[str, str] = field(default_factory=dict)
    dynamic_locals: set[str] = field(default_factory=set)
    dynamic_globals: set[str] = field(default_factory=set)
    protected: set[str] = field(default_factory=set)
    program_depth: int = 0


@dataclass
class _Budget:
    """Shared output-line budget bounding loop-unrolling growth."""

    remaining: int

    def spend(self, count: int = 1) -> None:
        """Consume ``count`` lines from the budget."""
        self.remaining -= count

    @property
    def exhausted(self) -> bool:
        """Return True when no budget is left."""
        return self.remaining <= 0


@dataclass
class _LoopHeader:
    """Parsed representation of a loop header line."""

    kind: str  # "in" | "of" | "forvalues" | "while"
    var: str | None
    of_kind: str = ""
    spec: str = ""


# ============================================================================
# Public API
# ============================================================================


def expand_dofile_for_security(dofile: str | Path) -> ExpansionResult:
    """Read a dofile and expand it, returning the structured result.

    Args:
        dofile: Path to the dofile to expand.

    Returns:
        The :class:`ExpansionResult` for the file content.

    Raises:
        FileNotFoundError: If ``dofile`` does not exist or is not a file.
    """
    path = Path(dofile)
    if not path.is_file():
        raise FileNotFoundError(f"dofile not found: {path}")
    return expand_code_for_security(_read_dofile(path))


def expand_dofile(dofile: str | Path) -> str:
    """Read a dofile and return its expanded content (best-effort).

    Args:
        dofile: Path to the dofile to expand.

    Returns:
        The expanded dofile content as a single string.

    Raises:
        FileNotFoundError: If ``dofile`` does not exist or is not a file.
    """
    return expand_dofile_for_security(dofile).expanded_code


def expand_code_for_security(
    code: str, *, max_output_lines: int = DEFAULT_MAX_OUTPUT_LINES
) -> ExpansionResult:
    """Statically expand Stata code and report everything unresolved.

    This is the entry point security consumers should use. Any
    construct that could not be resolved statically is preserved
    verbatim in ``expanded_code`` and surfaced as a diagnostic; check
    :attr:`ExpansionResult.has_unsupported_security_construct` to
    decide whether to fail closed.

    Args:
        code: Raw dofile content.
        max_output_lines: Cap on emitted lines; loops whose expansion
            would exceed the remaining budget are preserved verbatim.

    Returns:
        The :class:`ExpansionResult`. This function never raises on
        malformed Stata code; even an unexpected internal error yields
        a result carrying the original code and an ``internal-error``
        diagnostic.
    """
    collector = _DiagnosticCollector()
    try:
        lines = _strip_comments(code, collector)
        lines = _normalize_delimiter(lines, collector)
        state = _MacroState()
        budget = _Budget(remaining=max_output_lines)
        out_lines = _process_lines(lines, state, budget, 0, collector)
        _report_unresolved_macros(out_lines, collector)
        return ExpansionResult(
            expanded_code="\n".join(entry.text for entry in out_lines),
            diagnostics=tuple(collector.items),
            line_map={
                number: list(entry.origins)
                for number, entry in enumerate(out_lines, start=1)
            },
            commands=_extract_commands(out_lines),
        )
    except Exception:
        logger.error(
            "Dofile expansion failed; returning original content",
            exc_info=True,
        )
        collector.add(
            "internal-error",
            "expansion failed unexpectedly; original code returned unmodified",
            0,
            scope="global",
        )
        return ExpansionResult(
            expanded_code=code,
            diagnostics=tuple(collector.items),
            line_map={number: [number] for number in range(1, code.count("\n") + 2)},
            commands=(),
        )


def expand_code(code: str, *, max_output_lines: int = DEFAULT_MAX_OUTPUT_LINES) -> str:
    """Statically expand Stata code, returning only the expanded string.

    Best-effort convenience wrapper around
    :func:`expand_code_for_security` for display purposes; security
    callers should use the structured form and honor its diagnostics.

    Args:
        code: Raw dofile content.
        max_output_lines: Cap on emitted lines.

    Returns:
        The expanded code; on internal errors, the original ``code``.
    """
    return expand_code_for_security(
        code, max_output_lines=max_output_lines
    ).expanded_code


# ============================================================================
# File reading
# ============================================================================


def _read_dofile(path: Path) -> str:
    """Read dofile bytes and decode with an encoding fallback chain."""
    data = path.read_bytes()
    for encoding in _ENCODING_FALLBACKS[:-1]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            logger.debug("Decoding dofile with %s failed; trying next", encoding)
    return data.decode(_ENCODING_FALLBACKS[-1], errors="replace")


# ============================================================================
# String-aware scanning helpers
# ============================================================================


def _scan_string(text: str, start: int) -> tuple[int, bool]:
    """Scan a ``"..."`` or ``` `"..."' ``` literal starting at ``start``.

    Scanning stops at end of line. Returns ``(end_index, closed)``.
    """
    length = len(text)
    if text.startswith('`"', start):
        depth = 1
        index = start + 2
        while index < length and depth and text[index] != "\n":
            if text.startswith('`"', index):
                depth += 1
                index += 2
            elif text.startswith("\"'", index):
                depth -= 1
                index += 2
            else:
                index += 1
        return index, depth == 0
    index = start + 1
    while index < length and text[index] not in '"\n':
        index += 1
    if index < length and text[index] == '"':
        return index + 1, True
    return index, False


def _skip_simple_string(text: str, start: int) -> int:
    """Return the index just past a ``"..."`` string starting at ``start``."""
    end, _closed = _scan_string(text, start)
    return end


def _skip_compound_string(text: str, start: int) -> int:
    """Return the index just past a ``` `"..."' ``` string at ``start``."""
    end, _closed = _scan_string(text, start)
    return end


def _find_unquoted(text: str, target: str) -> int:
    """Find the first ``target`` character outside any Stata string."""
    index = 0
    length = len(text)
    while index < length:
        if text.startswith('`"', index):
            index = _skip_compound_string(text, index)
        elif text[index] == '"':
            index = _skip_simple_string(text, index)
        elif text[index] == target:
            return index
        else:
            index += 1
    return -1


def _find_top_level_comma(text: str) -> int:
    """Find the first comma outside strings and parentheses."""
    index = 0
    length = len(text)
    paren_depth = 0
    while index < length:
        if text.startswith('`"', index):
            index = _skip_compound_string(text, index)
        elif text[index] == '"':
            index = _skip_simple_string(text, index)
        elif text[index] == "(":
            paren_depth += 1
            index += 1
        elif text[index] == ")":
            paren_depth = max(paren_depth - 1, 0)
            index += 1
        elif text[index] == "," and paren_depth == 0:
            return index
        else:
            index += 1
    return -1


def _paren_contents(text: str, open_index: int) -> str:
    """Contents of the parenthesized group opening at ``open_index``."""
    index = open_index + 1
    depth = 1
    length = len(text)
    while index < length and depth:
        if text.startswith('`"', index):
            index = _skip_compound_string(text, index)
            continue
        if text[index] == '"':
            index = _skip_simple_string(text, index)
            continue
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
        index += 1
    end = index - 1 if depth == 0 else index
    return text[open_index + 1: end]


def _brace_delta(line: str) -> int:
    """Net ``{`` / ``}`` count of a line, ignoring strings and ``${...}``."""
    delta = 0
    index = 0
    length = len(line)
    while index < length:
        if line.startswith('`"', index):
            index = _skip_compound_string(line, index)
        elif line[index] == '"':
            index = _skip_simple_string(line, index)
        elif line.startswith("${", index):
            closing = line.find("}", index)
            index = length if closing == -1 else closing + 1
        elif line[index] == "{":
            delta += 1
            index += 1
        elif line[index] == "}":
            delta -= 1
            index += 1
        else:
            index += 1
    return delta


# ============================================================================
# Stage 1: comment and continuation stripping
# ============================================================================


def _strip_comments(code: str, collector: _DiagnosticCollector) -> list[_Line]:
    """Remove Stata comments and join continuation lines.

    Handles, with awareness of ``"..."`` and ``` `"..."' ``` strings:

    - ``*`` full-line comments (dropped, line break kept)
    - ``//`` end-of-line comments (dropped, line break kept)
    - ``///`` continuations (rest of line and the line break dropped)
    - nested ``/* ... */`` block comments (replaced by nothing, so the
      surrounding text joins — mirroring how Stata's do-file processor
      splices lines, and exposing ``she/**/ll`` obfuscation)

    Returns logical lines annotated with their original line numbers.
    Unterminated strings and block comments produce diagnostics.
    """
    lines: list[_Line] = []
    buffer: list[str] = []
    origins: set[int] = set()
    orig_line = 1
    index = 0
    length = len(code)
    line_blank = True  # only whitespace seen so far on the current line

    def flush() -> None:
        nonlocal buffer, origins
        line_origins = tuple(sorted(origins)) if origins else (orig_line,)
        lines.append(_Line("".join(buffer), line_origins))
        buffer = []
        origins = set()

    while index < length:
        char = code[index]

        if char == '"' or code.startswith('`"', index):
            end, closed = _scan_string(code, index)
            buffer.append(code[index:end])
            origins.add(orig_line)
            if not closed:
                collector.add(
                    "unbalanced-quotes",
                    "string literal is not terminated on its line",
                    orig_line,
                    scope="global",
                )
            index = end
            line_blank = False
            continue

        at_boundary = line_blank or (index > 0 and code[index - 1] in " \t")

        if code.startswith("///", index) and at_boundary:
            origins.add(orig_line)
            buffer.append(" ")
            newline = code.find("\n", index)
            if newline == -1:
                index = length
            else:
                index = newline + 1
                orig_line += 1
            continue

        if code.startswith("//", index) and at_boundary:
            newline = code.find("\n", index)
            index = length if newline == -1 else newline
            continue

        if code.startswith("/*", index):
            depth = 1
            start_line = orig_line
            index += 2
            while index < length and depth:
                if code.startswith("/*", index):
                    depth += 1
                    index += 2
                elif code.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    if code[index] == "\n":
                        orig_line += 1
                    index += 1
            if depth:
                collector.add(
                    "unbalanced-comment",
                    "block comment is never closed",
                    start_line,
                    scope="global",
                )
            continue

        if char == "*" and line_blank:
            newline = code.find("\n", index)
            index = length if newline == -1 else newline
            continue

        if char == "\n":
            flush()
            orig_line += 1
            index += 1
            line_blank = True
            continue

        buffer.append(char)
        origins.add(orig_line)
        if char not in " \t":
            line_blank = False
        index += 1

    flush()
    return lines


# ============================================================================
# Stage 2: #delimit normalization
# ============================================================================


def _is_delimit_cr(line: str) -> bool:
    """Return True if ``line`` is a ``#delimit cr`` directive."""
    matched = _DELIMIT_RE.match(line)
    if not matched:
        return False
    argument = matched.group(1).strip().rstrip(";").strip().lower()
    return argument == "cr"


def _normalize_delimiter(
    lines: list[_Line], collector: _DiagnosticCollector
) -> list[_Line]:
    """Convert ``#delimit ;`` regions back to one command per line."""
    output: list[_Line] = []
    semicolon_mode = False
    buffer_text = ""
    buffer_origins: set[int] = set()

    def flush_buffer() -> None:
        nonlocal buffer_text, buffer_origins
        collapsed = " ".join(buffer_text.split())
        if collapsed:
            output.append(_Line(collapsed, tuple(sorted(buffer_origins))))
        buffer_text = ""
        buffer_origins = set()

    for entry in lines:
        if not semicolon_mode:
            matched = _DELIMIT_RE.match(entry.text)
            if matched:
                if matched.group(1).strip().startswith(";"):
                    semicolon_mode = True
                    collector.add(
                        "delimit-normalized",
                        "'#delimit ;' region normalized to line delimiters",
                        entry.first_origin,
                        security_relevant=False,
                    )
                # directives are dropped from the normalized output
                continue
            output.append(entry)
            continue

        if _is_delimit_cr(entry.text):
            flush_buffer()
            semicolon_mode = False
            continue

        buffer_text = f"{buffer_text} {entry.text}" if buffer_text else entry.text
        buffer_origins.update(entry.origins)
        while True:
            split_at = _find_unquoted(buffer_text, ";")
            if split_at == -1:
                break
            command = " ".join(buffer_text[:split_at].split())
            buffer_text = buffer_text[split_at + 1:]
            if command:
                output.append(_Line(command, tuple(sorted(buffer_origins))))
            if not buffer_text.strip():
                buffer_origins = set()

    if semicolon_mode and buffer_text.strip():
        flush_buffer()
    return output


# ============================================================================
# Stage 3: abbreviation expansion
# ============================================================================


def _match_abbreviation(token: str, table: dict[str, int]) -> str | None:
    """Return the unique full command ``token`` abbreviates, if any."""
    lowered = token.lower()
    candidates = [
        full
        for full, min_len in table.items()
        if len(lowered) >= min_len and full.startswith(lowered)
    ]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _expand_abbreviations(line: str) -> str:
    """Spell out abbreviated prefixes and the command token of a line."""
    parts: list[str] = []
    rest = line

    while True:
        matched = re.match(r"(\s*)(\S+)", rest)
        if not matched:
            parts.append(rest)
            break
        whitespace, token = matched.group(1), matched.group(2)
        rest = rest[matched.end():]

        core = token
        trailer = ""
        while core and core[-1] in ",:":
            trailer = core[-1] + trailer
            core = core[:-1]

        if not re.fullmatch(r"[A-Za-z]+", core):
            parts.append(whitespace + token + rest)
            break

        if core.lower() in _BY_PREFIXES:
            colon = _find_unquoted(rest, ":")
            if trailer.endswith(":"):
                parts.append(whitespace + token)
                continue
            if colon == -1:
                parts.append(whitespace + token + rest)
                break
            parts.append(whitespace + token + rest[: colon + 1])
            rest = rest[colon + 1:]
            continue

        full_prefix = _match_abbreviation(core, _PREFIX_MIN_ABBREV)
        if full_prefix:
            parts.append(whitespace + full_prefix + trailer)
            continue

        full_command = _match_abbreviation(core, _COMMAND_MIN_ABBREV)
        parts.append(whitespace + (full_command + trailer if full_command else token))
        parts.append(rest)
        break

    return "".join(parts)


# ============================================================================
# Stage 4: macro tracking and expansion
# ============================================================================


def _expand_macros(line: str, state: _MacroState) -> str:
    """Substitute known macro references in ``line``.

    Undefined locals expand to an empty string (Stata runtime
    behavior) unless they are dynamic, protected loop variables, or the
    line sits inside a ``program define`` block. Globals are only
    substituted when defined in the file, since system globals may
    exist at runtime.
    """

    def replace_local(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in state.locals_:
            return state.locals_[name]
        if name in state.dynamic_locals or name in state.protected:
            return match.group(0)
        if state.program_depth > 0:
            return match.group(0)
        return ""

    def replace_global(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in state.globals_:
            return state.globals_[name]
        return match.group(0)

    current = line
    for _ in range(_MAX_MACRO_PASSES):
        expanded = _LOCAL_REF_RE.sub(replace_local, current)
        expanded = _GLOBAL_BRACE_RE.sub(replace_global, expanded)
        expanded = _GLOBAL_RE.sub(replace_global, expanded)
        if expanded == current:
            break
        current = expanded
    return current


def _strip_value_quotes(value: str) -> str:
    """Remove one layer of Stata value quotes, including compound quotes."""
    trimmed = value.strip()
    if trimmed.startswith('`"') and trimmed.endswith("\"'") and len(trimmed) >= 4:
        return trimmed[2:-2]
    if len(trimmed) >= 2 and trimmed[0] == '"' and trimmed[-1] == '"':
        return trimmed[1:-1]
    return trimmed


def _literal_value(expression: str) -> str | None:
    """Return the literal value of a ``=`` RHS, or None if not static."""
    trimmed = expression.strip()
    if _NUMBER_RE.fullmatch(trimmed):
        return trimmed
    if (
        len(trimmed) >= 2
        and trimmed[0] == '"'
        and trimmed[-1] == '"'
        and '"' not in trimmed[1:-1]
    ):
        return trimmed[1:-1]
    if trimmed.startswith('`"') and trimmed.endswith("\"'") and len(trimmed) >= 4:
        return trimmed[2:-2]
    return None


def _record_macro_definition(line: str, state: _MacroState) -> None:
    """Track a ``local`` / ``global`` definition found on ``line``."""
    body = _PREFIX_STRIP_RE.sub("", line)
    matched = _MACRO_DEF_RE.match(body)
    if not matched:
        return

    kind = matched.group(1).lower()
    name = matched.group(2)
    rest = matched.group(3).strip()

    if kind == "local":
        values, dynamics = state.locals_, state.dynamic_locals
    else:
        values, dynamics = state.globals_, state.dynamic_globals

    if rest.startswith("="):
        literal = _literal_value(rest[1:])
        if literal is None:
            values.pop(name, None)
            dynamics.add(name)
        else:
            values[name] = literal
            dynamics.discard(name)
        return

    if rest.startswith(":"):
        values.pop(name, None)
        dynamics.add(name)
        return

    values[name] = _strip_value_quotes(rest)
    dynamics.discard(name)


# ============================================================================
# Stage 5: loop parsing and unrolling
# ============================================================================


def _match_loop_header(line: str) -> _LoopHeader | None:
    """Parse ``line`` as a loop header, if it is one."""
    body = _PREFIX_STRIP_RE.sub("", line)
    matched = _FOREACH_IN_RE.match(body)
    if matched:
        return _LoopHeader("in", matched.group(1), spec=matched.group(2))
    matched = _FOREACH_OF_RE.match(body)
    if matched:
        return _LoopHeader(
            "of",
            matched.group(1),
            of_kind=matched.group(2).lower(),
            spec=matched.group(3),
        )
    matched = _FORVALUES_RE.match(body)
    if matched:
        return _LoopHeader("forvalues", matched.group(1), spec=matched.group(2))
    if _WHILE_RE.match(body):
        return _LoopHeader("while", None)
    return None


def _find_block_close(lines: list[_Line], start: int) -> int | None:
    """Index of the line closing the block opened at ``lines[start]``."""
    depth = 0
    for index in range(start, len(lines)):
        depth += _brace_delta(lines[index].text)
        if depth <= 0:
            if index == start:
                return None
            if lines[index].text.strip() == "}":
                return index
            return None
    return None


def _split_items(spec: str) -> list[str]:
    """Split a foreach item list, honoring quoted items."""
    items: list[str] = []
    index = 0
    length = len(spec)
    while index < length:
        if spec[index] in " \t":
            index += 1
            continue
        if spec.startswith('`"', index):
            end = _skip_compound_string(spec, index)
            inner_end = end - 2 if spec.startswith("\"'", end - 2) else end
            items.append(spec[index + 2: max(inner_end, index + 2)])
            index = end
            continue
        if spec[index] == '"':
            end = _skip_simple_string(spec, index)
            inner_end = end - 1 if end > index + 1 and spec[end - 1] == '"' else end
            items.append(spec[index + 1: inner_end])
            index = end
            continue
        end = index
        while end < length and spec[end] not in " \t":
            end += 1
        items.append(spec[index:end])
        index = end
    return items


def _parse_range(spec: str) -> list[str] | None:
    """Expand a ``first/last`` or ``first(step)last`` integer range."""
    trimmed = spec.strip()
    matched = re.fullmatch(r"(-?\d+)\s*/\s*(-?\d+)", trimmed)
    if matched:
        first, last = int(matched.group(1)), int(matched.group(2))
        step = 1
    else:
        matched = re.fullmatch(r"(-?\d+)\s*\(\s*(-?\d+)\s*\)\s*(-?\d+)", trimmed)
        if not matched:
            return None
        first, step, last = (int(g) for g in matched.groups())
        if step == 0:
            return None
    count = (last - first) // step + 1
    if count <= 0 or count > _MAX_LOOP_ITERATIONS:
        return None
    return [str(first + offset * step) for offset in range(count)]


def _parse_numlist(spec: str) -> list[str] | None:
    """Expand a numlist of integers, ranges, and stepped ranges."""
    values: list[str] = []
    for token in spec.split():
        expanded = _parse_range(token)
        if expanded is not None:
            values.extend(expanded)
            continue
        if _NUMBER_RE.fullmatch(token):
            values.append(token)
            continue
        return None
    return values or None


def _resolve_loop_items(header: _LoopHeader, state: _MacroState) -> list[str] | None:
    """Resolve a loop header to its concrete items, if statically possible."""
    if header.kind == "while":
        return None
    if header.kind == "in":
        items = _split_items(header.spec)
        return items or None
    if header.kind == "forvalues":
        return _parse_range(header.spec)

    # foreach ... of <kind> <spec>
    of_kind = None
    for full in _FOREACH_OF_KINDS:
        if len(header.of_kind) >= 3 and full.startswith(header.of_kind):
            of_kind = full
            break
    if of_kind == "local":
        name = header.spec.strip()
        if name in state.locals_ and name not in state.protected:
            return _split_items(state.locals_[name]) or None
        return None
    if of_kind == "global":
        name = header.spec.strip()
        if name in state.globals_:
            return _split_items(state.globals_[name]) or None
        return None
    if of_kind == "numlist":
        return _parse_numlist(header.spec)
    return None


def _preserved_loop_reason(header: _LoopHeader, items: list[str] | None) -> str:
    """Explain why a loop was kept verbatim."""
    if header.kind == "while":
        return "while loops are runtime-dependent"
    if header.kind == "of" and header.of_kind[:3] in ("var", "new"):
        return "loop list depends on runtime data"
    if items is None:
        return "loop list or range is not statically resolvable"
    return "expansion would exceed the output budget"


def _unroll_loop(
    var: str,
    items: list[str],
    body: list[_Line],
    state: _MacroState,
    budget: _Budget,
    depth: int,
    collector: _DiagnosticCollector,
) -> list[_Line]:
    """Emit the loop body once per item with the loop variable bound."""
    output: list[_Line] = []
    had_value = var in state.locals_
    previous_value = state.locals_.get(var)
    was_dynamic = var in state.dynamic_locals
    state.dynamic_locals.discard(var)

    for item in items:
        if budget.exhausted:
            logger.debug("Expansion budget exhausted; truncating unrolled loop")
            break
        state.locals_[var] = item
        output.extend(_process_lines(body, state, budget, depth + 1, collector))

    if had_value and previous_value is not None:
        state.locals_[var] = previous_value
    else:
        state.locals_.pop(var, None)
    if was_dynamic:
        state.dynamic_locals.add(var)
    return output


def _process_preserved_block(
    var: str | None,
    body: list[_Line],
    state: _MacroState,
    budget: _Budget,
    depth: int,
    collector: _DiagnosticCollector,
) -> list[_Line]:
    """Process the body of a loop kept verbatim, protecting its variable."""
    added = False
    if var is not None and var not in state.protected:
        state.protected.add(var)
        added = True
    try:
        return _process_lines(body, state, budget, depth + 1, collector)
    finally:
        if added and var is not None:
            state.protected.discard(var)


# ============================================================================
# Core line processor
# ============================================================================


def _process_lines(
    lines: list[_Line],
    state: _MacroState,
    budget: _Budget,
    depth: int,
    collector: _DiagnosticCollector,
) -> list[_Line]:
    """Expand a list of logical lines sequentially."""
    output: list[_Line] = []
    index = 0
    total = len(lines)

    while index < total:
        if budget.exhausted or depth > _MAX_EXPANSION_DEPTH:
            # fail-safe: keep the remaining source verbatim
            reason = (
                ("expansion-budget-exhausted", "output budget exhausted")
                if budget.exhausted
                else ("max-depth-exceeded", "block nesting exceeds expansion depth")
            )
            collector.add(
                reason[0],
                f"{reason[1]}; remaining source preserved verbatim",
                lines[index].first_origin,
                scope="global",
            )
            output.extend(lines[index:])
            break

        entry = lines[index]
        text = _expand_macros(entry.text, state)
        text = _expand_abbreviations(text)
        line = _Line(text, entry.origins)

        program_match = _PROGRAM_START_RE.match(text)
        if (
            program_match
            and program_match.group(1).lower() not in _PROGRAM_NON_BLOCK_SUBCOMMANDS
        ):
            state.program_depth += 1
            output.append(line)
            budget.spend()
            index += 1
            continue

        if state.program_depth > 0 and _PROGRAM_END_RE.match(text):
            state.program_depth -= 1
            output.append(line)
            budget.spend()
            index += 1
            continue

        header = _match_loop_header(text)
        if header is not None:
            close = _find_block_close(lines, index)
            if close is None:
                # unbalanced block: emit the header and permanently
                # protect the loop variable so later references survive
                if header.var is not None:
                    state.protected.add(header.var)
                collector.add(
                    "unbalanced-block",
                    "loop block has no matching closing brace",
                    entry.first_origin,
                    scope="global",
                )
                output.append(line)
                budget.spend()
                index += 1
                continue

            body = lines[index + 1: close]
            items = _resolve_loop_items(header, state)
            if (
                items is not None
                and header.var is not None
                and len(items) * max(len(body), 1) <= budget.remaining
            ):
                output.extend(
                    _unroll_loop(
                        header.var, items, body, state, budget, depth, collector
                    )
                )
            else:
                collector.add(
                    "preserved-loop",
                    f"loop preserved verbatim: "
                    f"{_preserved_loop_reason(header, items)}",
                    entry.first_origin,
                )
                output.append(line)
                budget.spend()
                output.extend(
                    _process_preserved_block(
                        header.var, body, state, budget, depth, collector
                    )
                )
                output.append(lines[close])
                budget.spend()
            index = close + 1
            continue

        _record_macro_definition(text, state)
        output.append(line)
        budget.spend()
        index += 1

    return output


# ============================================================================
# Post-processing: unresolved macro reporting and command tokenization
# ============================================================================


def _has_unresolved_macro(text: str) -> bool:
    """True when ``text`` still contains macro references/expressions."""
    return bool(
        _LOCAL_REF_RE.search(text)
        or _MACRO_EXPRESSION_RE.search(text)
        or _GLOBAL_BRACE_RE.search(text)
        or _GLOBAL_RE.search(text)
    )


def _report_unresolved_macros(
    out_lines: list[_Line], collector: _DiagnosticCollector
) -> None:
    """Emit a diagnostic for every macro token left in the output.

    Anything still looking like a macro after expansion is, by
    construction, unresolved (dynamic definitions, protected loop
    variables, program-scope locals, undefined globals, ``=``/``:``
    expressions). Security consumers must treat the containing lines
    as having unknown runtime content.
    """
    patterns: tuple[tuple[re.Pattern[str], str], ...] = (
        (_LOCAL_REF_RE, "local macro"),
        (_MACRO_EXPRESSION_RE, "macro expression"),
        (_GLOBAL_BRACE_RE, "global macro"),
        (_GLOBAL_RE, "global macro"),
    )
    for entry in out_lines:
        for pattern, kind in patterns:
            for matched in pattern.finditer(entry.text):
                collector.add(
                    "unresolved-macro",
                    f"unresolved {kind} '{matched.group(0)}' remains "
                    "after expansion",
                    entry.first_origin,
                )


def _command_name(text: str) -> str:
    """Extract the normalized command token of an expanded line."""
    tokens = _strip_command_prefixes(text).split()
    if not tokens:
        return ""
    return tokens[0].lower().rstrip(",:")


def _extract_string_literals(text: str) -> tuple[str, ...]:
    """Contents of all string literals on ``text``, in order."""
    literals: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if text.startswith('`"', index):
            end = _skip_compound_string(text, index)
            inner_end = end - 2 if text.startswith("\"'", end - 2) else end
            literals.append(text[index + 2: max(inner_end, index + 2)])
            index = end
        elif text[index] == '"':
            end = _skip_simple_string(text, index)
            inner_end = end - 1 if end > index + 1 and text[end - 1] == '"' else end
            literals.append(text[index + 1: inner_end])
            index = end
        else:
            index += 1
    return tuple(literals)


def _extract_using_paths(text: str) -> tuple[str, ...]:
    """Targets of ``using ...`` / ``using(...)`` clauses on a line."""
    paths: list[str] = []

    for matched in _USING_PAREN_RE.finditer(text):
        paths.extend(_split_items(_paren_contents(text, matched.end() - 1)))

    comma = _find_top_level_comma(text)
    head = text if comma == -1 else text[:comma]
    tokens = _split_items(head)
    for position, token in enumerate(tokens):
        if token.lower() == "using":
            for candidate in tokens[position + 1:]:
                if candidate.startswith("("):
                    break
                paths.append(candidate)
            break

    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        if path and path not in seen:
            seen.add(path)
            unique.append(path)
    return tuple(unique)


#: Commands whose direct (non-``using``) argument is a file, URL, or
#: directory path, mapped to the maximum number of path tokens taken.
_DIRECT_PATH_COMMANDS: dict[str, int] = {
    "use": 1,
    "save": 1,
    "saveold": 1,
    "sysuse": 1,
    "webuse": 1,
    "import": 1,
    "export": 1,
    "infile": 1,
    "infix": 1,
    "insheet": 1,
    "outsheet": 1,
    "outfile": 1,
    "do": 1,
    "run": 1,
    "include": 1,
    "type": 1,
    "erase": 1,
    "rmdir": 1,
    "mkdir": 1,
    "cd": 1,
    "chdir": 1,
    "copy": 2,
}

#: Commands whose first argument is a subcommand, not a path
#: (``import delimited "x.csv"``).
_SUBCOMMAND_SKIP: dict[str, int] = {"import": 1, "export": 1}


def _strip_command_prefixes(text: str) -> str:
    """Strip stacked ``capture``/``quietly``/``by ...:`` prefixes."""
    body = text
    while True:
        stripped = _PREFIX_STRIP_RE.sub("", body)
        stripped = _BY_PREFIX_STRIP_RE.sub("", stripped)
        if stripped == body:
            return body
        body = stripped


def _extract_direct_paths(name: str, text: str) -> list[str]:
    """Direct path argument(s) of a known file command.

    Returns an empty list when the command takes a ``using`` clause on
    this line (the arguments before ``using`` are then a varlist, and
    the paths are covered by :func:`_extract_using_paths`).
    """
    limit = _DIRECT_PATH_COMMANDS.get(name)
    if limit is None:
        return []
    body = _strip_command_prefixes(text)
    comma = _find_top_level_comma(body)
    head = body if comma == -1 else body[:comma]
    tokens = _split_items(head)
    if not tokens:
        return []
    arguments = tokens[1:]
    arguments = arguments[_SUBCOMMAND_SKIP.get(name, 0):]
    if name == "webuse" and arguments and arguments[0].lower() == "set":
        arguments = arguments[1:]
    for token in arguments:
        if token.lower() == "using" or token.lower().startswith("using("):
            return []
    paths: list[str] = []
    for token in arguments:
        if token.lower() in ("if", "in"):
            break
        paths.append(token)
        if len(paths) >= limit:
            break
    return paths


def _extract_commands(out_lines: list[_Line]) -> tuple[ParsedCommand, ...]:
    """Tokenize each non-blank expanded line into a :class:`ParsedCommand`."""
    commands: list[ParsedCommand] = []
    for number, entry in enumerate(out_lines, start=1):
        stripped = entry.text.strip()
        if not stripped or stripped in ("{", "}"):
            continue
        comma = _find_top_level_comma(stripped)
        name = _command_name(stripped)
        using_paths = _extract_using_paths(stripped)
        data_paths = tuple(
            dict.fromkeys([*_extract_direct_paths(name, stripped), *using_paths])
        )
        commands.append(
            ParsedCommand(
                name=name,
                text=stripped,
                line=number,
                origins=entry.origins,
                options=stripped[comma + 1:].strip() if comma != -1 else "",
                string_literals=_extract_string_literals(stripped),
                using_paths=using_paths,
                data_paths=data_paths,
                has_unresolved_macro=_has_unresolved_macro(stripped),
            )
        )
    return tuple(commands)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "DEFAULT_MAX_OUTPUT_LINES",
    "ExpansionResult",
    "ParseDiagnostic",
    "ParsedCommand",
    "expand_code",
    "expand_code_for_security",
    "expand_dofile",
    "expand_dofile_for_security",
]
