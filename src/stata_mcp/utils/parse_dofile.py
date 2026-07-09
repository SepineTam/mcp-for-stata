#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : parse_dofile.py

"""Static expansion of Stata dofiles for security checking.

This module rewrites a dofile into the flat form Stata would actually
execute so that downstream validators scan real commands instead of
obfuscated source text:

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

The expansion is best-effort and fail-safe: any construct that cannot
be resolved statically (``while`` loops, ``foreach ... of varlist``,
``=`` expressions, extended macro functions, oversized loops) is
preserved verbatim, so the expanded text never contains less than the
original source did.

Usage::

    from stata_mcp.utils.parse_dofile import expand_dofile

    cleaned_dofile_context: str = expand_dofile(Path("analysis.do"))
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
_GLOBAL_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_GLOBAL_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
_MACRO_DEF_RE = re.compile(
    r"^\s*(local|global)\s+([A-Za-z_][A-Za-z0-9_]*)(.*)$", re.IGNORECASE
)
_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
_PREFIX_STRIP_RE = re.compile(
    r"^\s*(?:(?:capture|quietly|noisily):?\s+)+", re.IGNORECASE
)
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

#: Subcommands of ``program`` that do not open a program block.
_PROGRAM_NON_BLOCK_SUBCOMMANDS: frozenset[str] = frozenset({"drop", "dir", "list"})


# ============================================================================
# State containers
# ============================================================================


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


def expand_dofile(dofile: str | Path) -> str:
    """Read a dofile and return its statically expanded content.

    The result is almost equivalent to reading the file with
    ``open(...).read()``, except that comments are removed, macros and
    loops are expanded, and command abbreviations are spelled out.

    Args:
        dofile: Path to the dofile to expand.

    Returns:
        The expanded dofile content as a single string.

    Raises:
        FileNotFoundError: If ``dofile`` does not exist or is not a file.
    """
    path = Path(dofile)
    if not path.is_file():
        raise FileNotFoundError(f"dofile not found: {path}")
    return expand_code(_read_dofile(path))


def expand_code(code: str, *, max_output_lines: int = DEFAULT_MAX_OUTPUT_LINES) -> str:
    """Statically expand Stata code held in a string.

    Args:
        code: Raw dofile content.
        max_output_lines: Cap on emitted lines; loops whose expansion
            would exceed the remaining budget are preserved verbatim.

    Returns:
        The expanded code. On any unexpected internal error the
        original ``code`` is returned unchanged (fail-safe).
    """
    try:
        stripped = _strip_comments(code)
        lines = _normalize_delimiter(stripped)
        state = _MacroState()
        budget = _Budget(remaining=max_output_lines)
        expanded = _process_lines(lines, state, budget, depth=0)
        return "\n".join(expanded)
    except Exception:
        logger.error(
            "Dofile expansion failed; returning original content",
            exc_info=True,
        )
        return code


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


def _skip_simple_string(text: str, start: int) -> int:
    """Return the index just past a ``"..."`` string starting at ``start``."""
    index = start + 1
    length = len(text)
    while index < length and text[index] != '"' and text[index] != "\n":
        index += 1
    if index < length and text[index] == '"':
        return index + 1
    return index


def _skip_compound_string(text: str, start: int) -> int:
    """Return the index just past a ``` `"..."' ``` string (nesting-aware)."""
    depth = 1
    index = start + 2
    length = len(text)
    while index < length and depth:
        if text.startswith('`"', index):
            depth += 1
            index += 2
        elif text.startswith("\"'", index):
            depth -= 1
            index += 2
        else:
            index += 1
    return index


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


def _strip_comments(code: str) -> str:
    """Remove Stata comments and join continuation lines.

    Handles, with awareness of ``"..."`` and ``` `"..."' ``` strings:

    - ``*`` full-line comments (dropped, newline kept)
    - ``//`` end-of-line comments (dropped, newline kept)
    - ``///`` continuations (rest of line and the newline dropped)
    - nested ``/* ... */`` block comments (replaced by nothing, so the
      surrounding text joins — mirroring how Stata's do-file processor
      splices lines, and exposing ``she/**/ll`` obfuscation)
    """
    parts: list[str] = []
    index = 0
    length = len(code)
    line_blank = True  # only whitespace seen so far on the current line

    while index < length:
        char = code[index]

        if char == '"':
            end = _skip_simple_string(code, index)
            parts.append(code[index:end])
            index = end
            line_blank = False
            continue

        if code.startswith('`"', index):
            end = _skip_compound_string(code, index)
            parts.append(code[index:end])
            index = end
            line_blank = False
            continue

        at_boundary = line_blank or (index > 0 and code[index - 1] in " \t")

        if code.startswith("///", index) and at_boundary:
            newline = code.find("\n", index)
            index = length if newline == -1 else newline + 1
            parts.append(" ")
            continue

        if code.startswith("//", index) and at_boundary:
            newline = code.find("\n", index)
            index = length if newline == -1 else newline
            continue

        if code.startswith("/*", index):
            depth = 1
            index += 2
            while index < length and depth:
                if code.startswith("/*", index):
                    depth += 1
                    index += 2
                elif code.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            continue

        if char == "*" and line_blank:
            newline = code.find("\n", index)
            index = length if newline == -1 else newline
            continue

        parts.append(char)
        if char == "\n":
            line_blank = True
        elif char not in " \t":
            line_blank = False
        index += 1

    return "".join(parts)


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


def _normalize_delimiter(text: str) -> list[str]:
    """Convert ``#delimit ;`` regions back to one command per line."""
    output: list[str] = []
    semicolon_mode = False
    buffer = ""

    for line in text.split("\n"):
        if not semicolon_mode:
            matched = _DELIMIT_RE.match(line)
            if matched:
                argument = matched.group(1).strip()
                if argument.startswith(";"):
                    semicolon_mode = True
                    buffer = ""
                # the directive itself is dropped from the output
                continue
            output.append(line)
            continue

        if _is_delimit_cr(line):
            if buffer.strip():
                output.append(" ".join(buffer.split()))
            buffer = ""
            semicolon_mode = False
            continue

        buffer = f"{buffer} {line}" if buffer else line
        while True:
            split_at = _find_unquoted(buffer, ";")
            if split_at == -1:
                break
            command, buffer = buffer[:split_at], buffer[split_at + 1 :]
            command = " ".join(command.split())
            if command:
                output.append(command)

    if semicolon_mode and buffer.strip():
        output.append(" ".join(buffer.split()))
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
        rest = rest[matched.end() :]

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
            rest = rest[colon + 1 :]
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


def _find_block_close(lines: list[str], start: int) -> int | None:
    """Index of the line closing the block opened at ``lines[start]``."""
    depth = 0
    for index in range(start, len(lines)):
        depth += _brace_delta(lines[index])
        if depth <= 0:
            if index == start:
                return None
            if lines[index].strip() == "}":
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
            items.append(spec[index + 2 : max(inner_end, index + 2)])
            index = end
            continue
        if spec[index] == '"':
            end = _skip_simple_string(spec, index)
            inner_end = end - 1 if end > index + 1 and spec[end - 1] == '"' else end
            items.append(spec[index + 1 : inner_end])
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


def _unroll_loop(
    var: str,
    items: list[str],
    body: list[str],
    state: _MacroState,
    budget: _Budget,
    depth: int,
) -> list[str]:
    """Emit the loop body once per item with the loop variable bound."""
    output: list[str] = []
    had_value = var in state.locals_
    previous_value = state.locals_.get(var)
    was_dynamic = var in state.dynamic_locals
    state.dynamic_locals.discard(var)

    for item in items:
        if budget.exhausted:
            logger.debug("Expansion budget exhausted; truncating unrolled loop")
            break
        state.locals_[var] = item
        output.extend(_process_lines(body, state, budget, depth + 1))

    if had_value and previous_value is not None:
        state.locals_[var] = previous_value
    else:
        state.locals_.pop(var, None)
    if was_dynamic:
        state.dynamic_locals.add(var)
    return output


def _process_preserved_block(
    var: str | None,
    body: list[str],
    state: _MacroState,
    budget: _Budget,
    depth: int,
) -> list[str]:
    """Process the body of a loop kept verbatim, protecting its variable."""
    added = False
    if var is not None and var not in state.protected:
        state.protected.add(var)
        added = True
    try:
        return _process_lines(body, state, budget, depth + 1)
    finally:
        if added and var is not None:
            state.protected.discard(var)


# ============================================================================
# Core line processor
# ============================================================================


def _process_lines(
    lines: list[str],
    state: _MacroState,
    budget: _Budget,
    depth: int,
) -> list[str]:
    """Expand a list of logical lines sequentially."""
    output: list[str] = []
    index = 0
    total = len(lines)

    while index < total:
        if budget.exhausted or depth > _MAX_EXPANSION_DEPTH:
            # fail-safe: keep the remaining source verbatim
            output.extend(lines[index:])
            break

        line = _expand_macros(lines[index], state)
        line = _expand_abbreviations(line)

        program_match = _PROGRAM_START_RE.match(line)
        if (
            program_match
            and program_match.group(1).lower() not in _PROGRAM_NON_BLOCK_SUBCOMMANDS
        ):
            state.program_depth += 1
            output.append(line)
            budget.spend()
            index += 1
            continue

        if state.program_depth > 0 and _PROGRAM_END_RE.match(line):
            state.program_depth -= 1
            output.append(line)
            budget.spend()
            index += 1
            continue

        header = _match_loop_header(line)
        if header is not None:
            close = _find_block_close(lines, index)
            if close is None:
                # unbalanced block: emit the header and permanently
                # protect the loop variable so later references survive
                if header.var is not None:
                    state.protected.add(header.var)
                output.append(line)
                budget.spend()
                index += 1
                continue

            body = lines[index + 1 : close]
            items = _resolve_loop_items(header, state)
            if (
                items is not None
                and header.var is not None
                and len(items) * max(len(body), 1) <= budget.remaining
            ):
                output.extend(
                    _unroll_loop(header.var, items, body, state, budget, depth)
                )
            else:
                if items is not None:
                    logger.debug(
                        "Loop of %d iterations exceeds expansion budget; "
                        "preserving verbatim",
                        len(items),
                    )
                output.append(line)
                budget.spend()
                output.extend(
                    _process_preserved_block(header.var, body, state, budget, depth)
                )
                output.append(lines[close])
                budget.spend()
            index = close + 1
            continue

        _record_macro_definition(line, state)
        output.append(line)
        budget.spend()
        index += 1

    return output


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "DEFAULT_MAX_OUTPUT_LINES",
    "expand_code",
    "expand_dofile",
]
