# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stata-MCP is an MCP (Model Context Protocol) server that enables LLMs to execute Stata commands and perform statistical/regression analysis. It supports:
- **MCP server mode**: FastMCP-based server exposing Stata tools to LLMs
- **Agent mode**: Interactive Stata analysis via OpenAI Agents SDK
- **CLI tools**: Direct command-line access to all Stata capabilities

Current version: **1.15.1** | License: **AGPL-3.0** | Python: **>=3.11**

## Common Development Commands

### Environment Setup
```bash
# Install dependencies and create virtual environment
uv sync

# Install the package in development mode
uv pip install -e .

# Verify installation
stata-mcp --version

# Run diagnostics to check system health
stata-mcp doctor

# NOTE: --usable is deprecated since v1.14.3, use "stata-mcp doctor" instead
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_server_parser.py
pytest tests/test_server_registration.py
```

### Building and Distribution
```bash
# Build source distribution and wheels
uv build

# Build specific formats
uv build --sdist    # Source distribution only
uv build --wheel    # Wheel only

# Specify output directory
uv build --out-dir dist/
```

### Running the Application

#### MCP Server Mode (default)
```bash
# Start MCP server with stdio transport (default)
stata-mcp

# Start with specific transport
stata-mcp -t http    # HTTP transport
stata-mcp -t sse     # SSE transport

# Start with tool profile selection
stata-mcp server                     # All tools, stdio (same as bare command)
stata-mcp server --core              # Core tools only (stata_do, get_data_info, help)
stata-mcp server --all -t http       # All tools, HTTP transport
stata-mcp server --core -t http      # Core tools, HTTP transport
```

#### Agent Mode
```bash
# Run interactive agent mode
stata-mcp agent run

# Or use uvx for direct execution
uvx stata-mcp agent run
```

#### Utility Commands
```bash
# Run diagnostics to check system health (replaces deprecated --usable)
stata-mcp doctor
stata-mcp doctor --verbose          # Detailed output
stata-mcp doctor --json             # JSON output
stata-mcp doctor --check stata      # Run specific check(s)

# Update stata-mcp to latest version
stata-mcp update
stata-mcp update --check            # Check if update is available
stata-mcp update --dry-run          # Show detected method without updating
stata-mcp update --method pip       # Force specific update method (auto/pip/uv-tool/homebrew)

# Manage configuration
stata-mcp config                    # Show current config
stata-mcp config cli set            # Auto-detect and set STATA_CLI path
stata-mcp config cli set /path/to/stata  # Set specific STATA_CLI path

# Run local Stata tools via CLI
stata-mcp tool ado-install <package> [--source ssc|net|github]
stata-mcp tool do <dofile_path> [--log-file-name NAME]
stata-mcp tool help <command>
stata-mcp tool data-info <data_path> [--vars-list var1 var2]
stata-mcp tool read-log <file_path> [--output-format full|core|dict]

# Install to MCP clients
stata-mcp install                   # Default: Claude Desktop
stata-mcp install -c cc             # Claude Code
stata-mcp install -c gemini         # Gemini CLI
stata-mcp install -c cursor         # Cursor
stata-mcp install -c cline          # Cline
stata-mcp install -c codex          # Codex
stata-mcp install -c opencode       # OpenCode
stata-mcp install --all             # Install to all supported clients
stata-mcp install --json-file PATH  # Install to custom config file

# Docker-based sandbox installation
stata-mcp sandbox-install -l /path/to/stata.lic
stata-mcp sandbox-install -l /path/to/stata.lic -c cursor --cpus 2 --memory 4g

# Check version
stata-mcp --version
```

### Development with uvx
```bash
# Run without local installation
uvx stata-mcp --version
uvx stata-mcp agent run
uvx stata-mcp doctor
```

## Source Layout

```
src/stata_mcp/
├── __init__.py              # Lazy-loading exports: stata_mcp (server), main (CLI)
├── mcp_servers.py           # FastMCP server with _TOOL_REGISTRY and register_tools()
├── config.py                # Unified config management (TOML + env vars)
├── api/                     # Tool API wrappers (thin layer over core logic)
│   ├── _runtime.py          # RuntimeContext dataclass for execution contexts
│   ├── stata_do.py          # stata_do() with security guard + RAM monitor
│   ├── get_data_info.py     # Data file analysis dispatcher
│   ├── read_log.py          # Log file reader (text and SMCL formats)
│   ├── stata_help.py        # Stata command documentation
│   ├── ado_install.py       # Package installer (SSC/GitHub/net)
│   └── write_dofile.py      # Do-file creator (deprecated)
├── cli/                     # Command-line interface
│   ├── _cli.py              # Entry point and subcommand routing
│   ├── _parsers.py          # Argument parser definitions for all subcommands
│   └── _handlers.py         # Command handler implementations
├── stata/                   # Stata integration layer
│   ├── stata_finder/        # Platform-specific Stata executable locator
│   │   ├── finder.py        # Factory dispatcher
│   │   ├── base.py          # Abstract base
│   │   ├── macos.py         # macOS implementation
│   │   ├── windows.py       # Windows implementation
│   │   └── linux.py         # Linux implementation
│   ├── stata_controller/    # Interactive pexpect-based Stata session
│   ├── stata_do/            # Batch do-file execution with subprocess
│   └── builtin_tools/
│       ├── ado_install/     # SSC_Install, NET_Install, GITHUB_Install
│       ├── help/            # StataHelp with disk caching
│       └── stata_log/       # Log readers: text and SMCL formats
├── data_info/               # Data file analysis handlers
│   ├── base.py              # DataInfoBase ABC, Series dataclasses
│   ├── csv.py               # CSV handler
│   ├── dta.py               # Stata .dta handler
│   ├── xlsx.py              # Excel handler
│   └── spss.py              # SPSS .sav handler
├── guard/                   # Security validation
│   ├── validator.py         # GuardValidator, RiskItem, SecurityReport
│   └── blacklist.py         # DANGEROUS_COMMANDS, DANGEROUS_PATTERNS
├── monitor/                 # Process monitoring
│   ├── base.py              # MonitorBase ABC
│   └── ram_monitor.py       # RAMMonitor (threading + psutil)
├── agent_as/                # Agent-mode components
│   ├── agent_base.py        # AgentBase ABC (OpenAI Agents SDK)
│   ├── repl_agents.py       # REPLAgent with SQLiteSession + MCP server
│   ├── set_model.py         # Model configuration helpers
│   ├── agent_as_tool/       # stata_agent, adversarial_thinking_agent, any_as_tools
│   └── agent_as_rag/        # RAG-based agent with handoff capability
├── evaluate/                # Evaluation and scoring
│   ├── _model.py            # OpenAI client config (DEFAULT/CHAT/THINKING models)
│   ├── score_it.py          # Scoring module
│   ├── advice.py            # Advice generation
│   └── agent_runner.py      # Evaluation agent runner
├── utils/                   # Utility modules
│   ├── doctor.py            # Diagnostics: CheckStatus, DoctorReport
│   ├── update.py            # Version checking and update orchestration
│   ├── usable.py            # Legacy usability check (deprecated)
│   └── Installer/           # MCP client integration installer
└── core/
    └── types/
        └── _error.py        # Custom exceptions: StataCLINotFoundError, RAMLimitExceededError
```

## Architecture Overview

### 1. MCP Server (`src/stata_mcp/mcp_servers.py`)

FastMCP-based server. Key design points:
- Tools are **not** registered at import time — `register_tools(server, profile)` must be called explicitly
- `_TOOL_REGISTRY` dict maps tool names to metadata (description, func, profiles, flags)
- Two profiles: `core` (3 tools) and `all` (6 tools)
- Platform filters: `unix_only=True` for `help` tool
- Deprecated flag: `write_dofile` is flagged deprecated
- Profile lock-in: switching profiles after registration raises an error

### 2. API Layer (`src/stata_mcp/api/`)

Thin wrappers that compose core logic. Each function:
- Accepts a `RuntimeContext` (config, paths, stata CLI info)
- Validates inputs, runs security guard if enabled, invokes core logic
- Returns structured results ready for MCP tool responses

### 3. Stata Integration (`src/stata_mcp/stata/`)

| Component | Description |
|-----------|-------------|
| `StataFinder` | Locates Stata executable per platform |
| `StataController` | pexpect-based interactive Stata sessions |
| `StataDo` | Subprocess batch do-file execution with monitor hooks |
| `StataHelp` | Help text retrieval with optional disk caching |
| `SSC_Install` / `NET_Install` / `GITHUB_Install` | Package installation from different sources |

### 4. Data Processing (`src/stata_mcp/data_info/`)

`get_data_handler()` auto-detects format and returns the appropriate handler:

| Handler | Formats |
|---------|---------|
| `CsvDataInfo` | `.csv` |
| `DtaDataInfo` | `.dta` (Stata) |
| `ExcelDataInfo` | `.xlsx`, `.xls` |
| `SpssDataInfo` | `.sav` (SPSS) |

All handlers extend `DataInfoBase` and return `Series` dataclasses with typed numeric and string statistics.

### 5. CLI Interface (`src/stata_mcp/cli/`)

Modular architecture:
- `_parsers.py` defines argument parsers for: `agent`, `server`, `doctor`, `tool`, `config`, `install`, `sandbox-install`, `update`
- `_handlers.py` implements the corresponding handler functions
- `_cli.py` routes subcommands and serves as the package entry point

### 6. Configuration System (`src/stata_mcp/config.py`)

Priority (highest to lowest): **environment variables > config file > defaults**

`Config` class uses `@cached_property` for lazy directory creation. `StataMcpFolder` helper manages the working directory structure.

Config file location: `~/.statamcp/config.toml`

```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = false
LOGGING_FILE_HANDLER_ON = true
LOG_FILE = "~/.statamcp/stata_mcp_debug.log"
MAX_BYTES = 10_000_000
BACKUP_COUNT = 5

[SECURITY]
IS_GUARD = true

[PROJECT]
WORKING_DIR = ""

[MONITOR]
IS_MONITOR = false
MAX_RAM_MB = -1  # -1 means no limit
```

### 7. Security Guard (`src/stata_mcp/guard/`)

`GuardValidator` scans do-files before execution:
- `DANGEROUS_COMMANDS`: Prohibited Stata commands (e.g., `shell`, `erase`, `rm`)
- `DANGEROUS_PATTERNS`: Regex patterns for dangerous constructs (e.g., `! del`, `! rm`)
- Returns `SecurityReport` with a list of `RiskItem` objects
- Configurable via `IS_GUARD` setting (default: `true`)

### 8. Monitoring System (`src/stata_mcp/monitor/`)

`RAMMonitor` runs in a background thread:
- Polls Stata process RAM usage via `psutil`
- Terminates process when usage exceeds `MAX_RAM_MB`
- Raises `RAMLimitExceededError` with usage details
- Configurable via `IS_MONITOR` and `MAX_RAM_MB` settings

### 9. Agent System (`src/stata_mcp/agent_as/`)

Built on the **OpenAI Agents SDK** (`openai-agents`):
- `REPLAgent`: Interactive REPL with `SQLiteSession` for persistent message history, `MCPServerStdio` for live MCP tool access
- `AgentBase`: Abstract base class for all agent types
- `agent_as_tool/`: Compose agents as tools (stata agent, adversarial thinking, generic tool wrappers)
- `agent_as_rag/`: RAG-based agent variants with handoff capability

### MCP Tools Provided

Tools are registered based on profile selection (`--core` / `--all`):

| Profile | Tool | Notes |
|---------|------|-------|
| core, all | `stata_do` | Execute Stata do-files |
| core, all | `get_data_info` | Analyze data files (CSV, DTA, XLSX, SPSS) |
| core, all | `help` | Stata command documentation (Unix only) |
| all | `read_log` | Read log files; supports `lines` param and `full`/`core`/`dict` formats |
| all | `ado_package_install` | Install packages from SSC, GitHub, or net |
| all | `write_dofile` | Create do-files (deprecated) |

### File Structure Conventions

Working directory is configurable via `STATA_MCP__CWD` environment variable.
- Falls back to current directory (if writable) or `~/Documents`

```
<cwd>/stata-mcp-folder/
├── stata-mcp-log/      # Stata execution logs
├── stata-mcp-dofile/   # Generated do-files
├── stata-mcp-result/   # Analysis results
└── stata-mcp-tmp/      # Temporary files
```

Configuration directory: `~/.statamcp/`
- `config.toml`: Configuration file
- `help/`: Cached help texts
- `stata_mcp_debug.log`: Debug log file (if logging enabled)

### Cross-Platform Support

| Platform | Stata Location |
|----------|---------------|
| macOS | `/Applications/Stata/` |
| Windows | `Program Files` |
| Linux | `stata-mp` from system PATH |

## Environment Variables Reference

### Working Directory
- `STATA_MCP__CWD`: Working directory (defaults to cwd or `~/Documents`)
- `STATA_MCP_CWD`: Legacy alias for backward compatibility

### Logging
- `STATA_MCP__LOGGING_ON`: Enable/disable logging (default: `true`)
- `STATA_MCP__LOGGING_CONSOLE_HANDLER_ON`: Enable console logging (default: `false`)
- `STATA_MCP__LOGGING_FILE_HANDLER_ON`: Enable file logging (default: `true`)
- `STATA_MCP__LOG_FILE`: Custom log file path
- `STATA_MCP__LOGGING__MAX_BYTES`: Max log file size in bytes (default: `10_000_000`)
- `STATA_MCP__LOGGING__BACKUP_COUNT`: Number of backup log files (default: `5`)

### Data Processing
- `STATA_MCP_CACHE_HELP`: Enable help caching (default: `false`)
- `STATA_MCP_SAVE_HELP`: Save help text to cache (default: `true`)
- `STATA_MCP_DATA_INFO_DECIMAL_PLACES`: Decimal places for data info output (default: `3`)
- `STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`: Max string values to display (default: `10`)
- `STATA_MCP_DATA_INFO_HASH_LENGTH`: Hash length for cache filename (default: `12`)

### Security
- `STATA_MCP__IS_GUARD`: Enable security guard validation (default: `true`)

### Monitoring
- `STATA_MCP__IS_MONITOR`: Enable RAM monitoring (default: `false`)
- `STATA_MCP__RAM_LIMIT`: Maximum RAM in MB (default: `-1`, no limit)

### Agent Mode
- `STATA_MCP_API_KEY`: API key for LLM (falls back to `OPENAI_API_KEY`)
- `STATA_MCP_API_BASE_URL`: API base URL for LLM
- `STATA_MCP_MODEL`: Model name for LLM

## Testing

Tests live in `tests/` and use **pytest**. The test suite uses `monkeypatch` and stub implementations to isolate modules from heavy dependencies (FastMCP, pexpect, etc.).

| File | What it tests |
|------|--------------|
| `test_server_parser.py` | CLI argument parsing: transport flags, profile defaults, mutual exclusion |
| `test_server_registration.py` | `register_tools()`: core/all profile filtering, platform/deprecated filters, profile lock-in |

Pattern for adding tests:
- Stub out external dependencies with `monkeypatch.setitem(sys.modules, ...)`
- Import the module under test after patching via `importlib.import_module()`
- Use a dummy `FastMCP`-like server object to assert which tools get registered

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `mcp[cli]>=1.23.0` | MCP protocol and FastMCP server |
| `pandas>=3.0.0,<4.0.0` | Data processing (lazy-loaded) |
| `pexpect>=4.9.0` | Interactive Stata sessions |
| `openai-agents>=0.3.2` | Agent mode (OpenAI Agents SDK) |
| `openai>=1.109.1` | LLM API client |
| `psutil>=6.0.0` | RAM monitoring |
| `pyreadstat>=1.2.0` | SPSS file reading |
| `openpyxl>=3.1.5` | Excel file reading |
| `tomli-w>=1.2.0` | TOML config writing |
| `pathvalidate>=3.3.1` | Path validation |

## Git Commit Standards

This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

**Key points:**
- Format: `<type>[optional scope]: <description>`
- Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`
- Subject under 50 characters, imperative mood, lowercase
- Reference issues with `Closes #` or `Fixes #`
- **No co-author information in commits**
- Breaking changes: use `!` after type/scope or `BREAKING CHANGE:` footer

**Examples:**
```
feat: add spss data handler
fix(api): resolve null response in get_data_info
docs: update cli reference for server profiles
perf: lazy-load pandas at import time
```

## Branch Protection Policy

**All changes MUST be submitted via Pull Request.** Direct commits to `master` are NOT allowed.

### Branch Naming

- Feature: `feat/feature-name` or `dev/v1.x.y`
- Fix: `fix/bug-name`
- Docs: `docs/doc-name`

### Standard Workflow

1. **Create branch**: `git checkout -b dev/v1.x.y`
2. **Lint code**: run pre-commit hooks
3. **Stage files**: `git add <files>`
4. **Review changes**: `git diff --staged`
5. **Commit**: `git commit -m "type: description"`
6. **Push branch**: `git push -u origin dev/v1.x.y`
7. **Create PR** via GitHub

## Code Conventions

- All Python functions must have **type annotations** and **English docstrings**
- Use descriptive variable names
- Maintain proper code indentation (4 spaces)
- Heavy dependencies (`pandas`, `numpy`, `requests`) must be **lazy-loaded** at function call time, not at module import
- New data format handlers go in `src/stata_mcp/data_info/` and must register in the `DATA_INFO_REGISTRY`
- New MCP tools go in `src/stata_mcp/api/` and must be added to `_TOOL_REGISTRY` in `mcp_servers.py`
- Security-sensitive code paths must go through `GuardValidator` before execution
- The project requires a valid Stata license to run Stata commands

## Important Notes

- Default data output is in `<STATA_MCP__CWD>/stata-mcp-folder/`
- The `help` tool is Unix-only; it is filtered out on Windows during `register_tools()`
- `write_dofile` is deprecated — do not extend or rely on it for new features
- `--usable` CLI flag is deprecated since v1.14.3; use `stata-mcp doctor` instead
- For comprehensive end-user documentation, see the `docs/` directory and https://docs.statamcp.com
