# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stata-MCP is an MCP (Model Context Protocol) server that enables LLMs to execute Stata commands and perform regression analysis. It supports both MCP server mode and agent mode for interactive Stata analysis.

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

## Architecture Overview

### Core Components

1. **MCP Server (`src/stata_mcp/mcp_servers.py`)**
   - FastMCP-based server providing Stata tools and resources
   - Main entry point for LLM interactions
   - Handles cross-platform Stata execution
   - Configurable working directory via `STATA_MCP__CWD` environment variable
   - Tool registration via `_TOOL_REGISTRY` + `register_tools(server, profile)` pattern
   - Two profiles: `core` (stata_do, get_data_info, help) and `all` (all tools)
   - Tools are no longer registered at import time; `register_tools()` must be called explicitly

2. **Stata Integration (`src/stata_mcp/core/stata/`)**
   - `StataFinder`: Locates Stata executable on different platforms (macOS, Windows, Linux)
   - `StataController`: Manages Stata command execution
   - `StataDo`: Handles do-file execution with logging
   - `builtin_tools/`: Built-in Stata tools
     - `ado_install/`: Package installation (SSC, GitHub, net)
     - `stata_help.py`: Stata command documentation

3. **Data Processing (`src/stata_mcp/core/data_info/`)**
   - `_base.py`: Base class for data info handlers
   - `csv.py`: CSV file analysis and statistics
   - `dta.py`: Stata .dta file analysis
   - `xlsx.py`: Excel file analysis
   - Automatic data type detection and summary statistics

4. **CLI Interface (`src/stata_mcp/cli/`)**
   - Command-line interface with modular parser/handler architecture
   - `_cli.py`: Entry point and subcommand routing
   - `_parsers.py`: Argument parser definitions for all subcommands
   - `_handlers.py`: Command handler implementations
   - Subcommands: `agent`, `server`, `doctor`, `tool`, `config`, `install`, `sandbox-install`, `update`

5. **Configuration System (`src/stata_mcp/config.py`)**
   - Unified configuration management via TOML config file
   - Priority: environment variables > config file > defaults
   - Sections: DEBUG, SECURITY, PROJECT, MONITOR
   - Supports hot-reload of configuration changes

6. **Security Guard (`src/stata_mcp/guard/`)**
   - `GuardValidator`: Validates Stata dofiles against dangerous commands
   - `blacklist.py`: Maintains list of prohibited commands and patterns
   - Prevents execution of destructive operations (e.g., `shell`, `rm`, `! del`)
   - Configurable via `IS_GUARD` setting

7. **Monitoring System (`src/stata_mcp/monitor/`)**
   - `MonitorBase`: Abstract base class for extensible monitors
   - `RAMMonitor`: Tracks Stata process RAM usage with psutil
   - Automatic process termination when RAM exceeds limit
   - Configurable via `IS_MONITOR` and `MAX_RAM_MB` settings

### MCP Tools Provided

Tools are registered based on profile selection (`--core` / `--all`):

| Profile | Tool | Description |
|---------|------|-------------|
| core, all | `stata_do` | Execute Stata do-files |
| core, all | `get_data_info` | Analyze data files (CSV, DTA, XLSX) |
| core, all | `help` | Get Stata command documentation (Unix only) |
| all | `read_log` | Read log file contents |
| all | `ado_package_install` | Install Stata packages from SSC, GitHub, or net sources |
| all | `write_dofile` | Create Stata do-files from code (deprecated) |

### File Structure Conventions

Working directory is configurable via `STATA_MCP__CWD` environment variable.
- If not set, tries current directory (if writable) or falls back to `~/Documents`

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

The project supports:
- **macOS**: Uses Stata MP from `/Applications/Stata/`
- **Windows**: Uses Stata MP from `Program Files`
- **Linux**: Uses `stata-mp` from system PATH

### Configuration

The project uses a hierarchical configuration system with priority: **environment variables > config file > defaults**.

#### Configuration File

Location: `~/.statamcp/config.toml`

Example configuration (see `config.example.toml` in repository root):

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

#### Environment Variables

**Working Directory:**
- `STATA_MCP__CWD`: Working directory (defaults to current directory or `~/Documents`)
- `STATA_MCP_CWD`: Legacy alias for backward compatibility

**Logging:**
- `STATA_MCP__LOGGING_ON`: Enable/disable logging (default: true)
- `STATA_MCP__LOGGING_CONSOLE_HANDLER_ON`: Enable console logging (default: false)
- `STATA_MCP__LOGGING_FILE_HANDLER_ON`: Enable file logging (default: true)
- `STATA_MCP__LOG_FILE`: Custom log file path
- `STATA_MCP__LOGGING__MAX_BYTES`: Max log file size in bytes (default: 10_000_000)
- `STATA_MCP__LOGGING__BACKUP_COUNT`: Number of backup log files (default: 5)

**Data Processing:**
- `STATA_MCP_CACHE_HELP`: Enable help caching (default: false)
- `STATA_MCP_SAVE_HELP`: Save help text to cache (default: true)
- `STATA_MCP_DATA_INFO_DECIMAL_PLACES`: Decimal places for data info output (default: 3)
- `STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`: Max string values to display (default: 10)
- `STATA_MCP_DATA_INFO_HASH_LENGTH`: Hash length for cache filename (default: 12)

**Security:**
- `STATA_MCP__IS_GUARD`: Enable security guard validation (default: true)

**Monitoring:**
- `STATA_MCP__IS_MONITOR`: Enable RAM monitoring (default: false)
- `STATA_MCP__RAM_LIMIT`: Maximum RAM in MB (default: -1, no limit)

**Agent Mode:**
- `STATA_MCP_API_KEY`: API key for LLM (falls back to `OPENAI_API_KEY`)
- `STATA_MCP_API_BASE_URL`: API base URL for LLM
- `STATA_MCP_MODEL`: Model name for LLM

**Stata Path:**
- Stata executable path detection via `StataFinder` (or set platform-specific environment variable)

## Git Commit Standards

This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

**Key points:**
- Use format: `<type>[optional scope]: <description>`
- Common types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
- Subject under 50 characters, imperative mood, lowercase
- Reference issues with `Closes #` or `Fixes #`
- **Important:** No co-author information in commits
- Breaking changes: use `!` after type/scope or `BREAKING CHANGE:` footer

**Examples:**
```bash
feat: add user authentication
fix(api): resolve null response issue
docs: update installation guide
```

## Branch Protection Policy

**All changes MUST be submitted via Pull Request.** Direct commits to `master` are NOT allowed.

### Branch Naming

- Feature: `feat/feature-name` or `dev/v1.2.3`
- Fix: `fix/bug-name`
- Docs: `docs/doc-name`

### Standard Workflow

1. **Create branch**: `git checkout -b dev/v1.13.42`
2. **Lint code**: Run `precommit`
3. **Stage files**: `git add <files>`
4. **Review changes**: `git diff --staged`
5. **Commit**: `git commit -m "type: description"`
6. **Push branch**: `git push -u origin dev/v1.13.42`
7. **Create PR**: `gh pr create --title "..." --body "..."`

## Important Notes

- All Python functions must have type annotations and English docstrings
- Use descriptive variable names
- Maintain proper code indentation
- The project requires a valid Stata license
- Default data output is in `<STATA_MCP__CWD>/stata-mcp-folder/` (or auto-detected location)
- For comprehensive documentation, see the `docs/` directory
