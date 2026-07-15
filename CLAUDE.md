# CLAUDE.md

Guidance for Claude Code when changing this repository. Keep this file concise and
project-specific; derive volatile details such as dependency versions and complete
file listings from the codebase.

## Project

Stata-MCP is a Python 3.11+ MCP server and CLI for running Stata do-files and
inspecting statistical data. It uses FastMCP and is licensed under AGPL-3.0.

## Essential commands

```bash
# Install/sync the development environment
uv sync

# Run tests
uv run pytest tests/
uv run pytest tests/cli/test_server_registration.py

# Inspect or run the CLI
uv run stata-mcp --help
uv run stata-mcp doctor
uv run stata-mcp server --all

# Build distributions
uv build
```

Use `stata-mcp doctor`, not the deprecated `--usable` flag. Run targeted tests
while developing, then the full suite before handing off a substantive change.

## Architecture

- `src/stata_mcp/cli/`: argument parsing and command handlers. The CLI exposes
  `doctor`, `server`, `tool`, `config`, `install`, `update`, and `verify`.
- `src/stata_mcp/mcp_servers.py`: FastMCP server, tool wrappers, and
  `_TOOL_REGISTRY`. Tools are registered explicitly by `register_tools()`.
- `src/stata_mcp/api/`: one-shot Python APIs built around `RuntimeContext`.
- `src/stata_mcp/stata/`: Stata discovery, execution, log parsing, help, and
  controlled ado-package installation.
- `src/stata_mcp/data_info/`: registered handlers for CSV/TSV/PSV, DTA,
  XLSX/XLS, and SPSS SAV/ZSAV data.
- `src/stata_mcp/guard/`: command validation, package-management blocking, and
  local path/URL auditing.
- `src/stata_mcp/monitor/`: process monitors such as the RAM limit monitor.
- `src/stata_mcp/utils/`: diagnostics, installation, updates, and do-file parsing.
- `src/stata_mcp/evaluate/`: optional evaluation code that requires the `agents`
  dependency group; it is not part of the core runtime path.

The package root lazily exposes the default server and CLI entry point. Preserve
that lightweight import behavior.

## MCP tool profiles

| Profile | Tools |
|---|---|
| `core` | `stata_do`, `get_data_info`, `help` |
| `all` (default) | all `core` tools plus `read_log` |
| `unsafe` | all standard tools plus `ado_package_install` |

`help` is filtered out on Windows. A process cannot switch profiles after tools
have been registered; start a new process instead.

`write_dofile` remains a direct Python API helper but is not registered as an MCP
tool. Do not add it back to `_TOOL_REGISTRY` without an explicit security review.

## Security invariants

- Do-files may execute only from the configured working directory or the
  Stata-MCP do-file directory.
- `PackageManagementGuardValidator` blocks package-management commands in normal
  `stata_do` calls even when the general guard is disabled. Installation must use
  the controlled ado-install path.
- `GuardValidator` scans do-files when `IS_GUARD` is enabled. Preserve fail-closed
  behavior for unresolved or dangerous input.
- `DataPathAuditor` is the shared authority for local dataset boundaries and URL
  rules. Do not duplicate weaker checks in individual data handlers.
- URL guarding requires HTTPS, rejects IP-literal hosts and URL user information,
  and enforces the configured domain allowlist when enabled.
- GitHub ado installation requires an allowlisted repository and explicit
  confirmation. Treat it as third-party code execution.
- `read_log` is restricted to the Stata-MCP folder when its strict boundary is
  enabled.
- Never log secrets, raw do-file contents, or unredacted URL user information,
  query strings, or fragments. Use `[SECURITY VIOLATION]` for rejected security
  events.

Security checks must cover both the MCP wrappers and the direct APIs. Add or update
tests whenever changing path handling, command parsing, package installation, or
configuration security.

## Configuration

`src/stata_mcp/config.py` is the source of truth. Configuration can come from
environment variables, the user file (`~/.statamcp/config.toml`), the project file
(`.statamcp/config.toml`), and on Linux the system file
(`/etc/statamcp/config.toml`). `--config`/`STATA_MCP_CONFIG_FILE` selects a
debug-only file path.

Do not restate the complete precedence rules here: security settings deliberately
merge differently from ordinary settings. Use `Config` and its tests when changing
or documenting precedence.

## Change guidelines

- Use type annotations and English docstrings for new or changed public Python
  functions. Use descriptive English names and English code comments.
- Add CLI behavior in `_parsers.py` and `_handlers.py`; keep dispatch in `_cli.py`
  small.
- Add MCP tools to `src/stata_mcp/api/` and register them explicitly in
  `_TOOL_REGISTRY`, including their intended profiles and platform constraints.
- Add data handlers under `src/stata_mcp/data_info/`, declare their extensions,
  and ensure the module is imported so `DATA_INFO_REGISTRY` is populated.
- Route do-file execution through the existing guard and monitor layers. Do not
  bypass them for convenience.
- Keep security rejection summaries useful without exposing sensitive content.
- For new modules, prefer `logging.getLogger(__name__)`. Preserve intentional
  root-logger use in `mcp_servers.py` unless performing a dedicated logging
  refactor.
- Follow `CONTRIBUTING.md` for branch, pull-request, and commit conventions. Do
  not commit directly to `master`.

## Tests

Tests mirror the source layout:

- `tests/cli/`: parsers, registration, installation, and verification
- `tests/api/`: direct API security behavior
- `tests/data_info/`: format handlers and data access security
- `tests/guard/`: validators and path auditing
- `tests/stata/`: execution, timeout, help, and log behavior
- `tests/utils/`: do-file parsing and utilities

Shared fixtures live in `tests/conftest.py`; dataset fixtures live in
`tests/fixtures/dataset/` and may be downloaded/generated at runtime. See
`tests/README.md` for fixture details.

## Sources of truth

When documentation and code disagree, verify against these files and update this
document in the same change:

| Concern | Source |
|---|---|
| Dependencies and Python versions | `pyproject.toml` |
| CLI commands and flags | `src/stata_mcp/cli/_parsers.py` |
| MCP tools and profiles | `src/stata_mcp/mcp_servers.py` |
| Configuration behavior | `src/stata_mcp/config.py` |
| Test organization | `tests/README.md` and `tests/` |
