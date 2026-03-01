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
stata-mcp --usable
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
# Check system compatibility
stata-mcp --usable

# Install to Claude Desktop
stata-mcp install

# Check version
stata-mcp --version
```

### Development with uvx
```bash
# Run without local installation
uvx stata-mcp --version
uvx stata-mcp agent run
uvx stata-mcp --usable
```

## Architecture Overview

### Core Components

1. **MCP Server (`src/stata_mcp/mcp_servers.py`)**
   - FastMCP-based server providing Stata tools and resources
   - Main entry point for LLM interactions
   - Handles cross-platform Stata execution
   - Configurable working directory via `STATA_MCP_CWD` environment variable

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
   - Command-line interface for running stata-mcp
   - Support for multiple modes: server, agent, install, version check

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

- `help`: Get Stata command documentation (macOS and Linux only)
- `stata_do`: Execute Stata do-files
- `write_dofile`: Create Stata do-files from code
- `append_dofile`: Append code to existing do-files
- `get_data_info`: Analyze data files (CSV, DTA, XLSX)
- `read_file`: Read file contents
- `ado_package_install`: Install Stata packages from SSC, GitHub, or net sources
- `load_figure`: Load Stata-generated figures

### File Structure Conventions

Working directory is configurable via `STATA_MCP_CWD` environment variable.
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
LOG_FILE = "~/"

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
- `STATA_MCP_CWD`: Working directory (defaults to current directory or `~/Documents`)

**Logging:**
- `STATA_MCP_LOGGING_ON`: Enable/disable logging (default: true)
- `STATA_MCP_LOGGING_CONSOLE_HANDLER`: Enable console logging (default: false)
- `STATA_MCP_LOGGING_FILE_HANDLER`: Enable file logging (default: true)
- `STATA_MCP_LOG_FILE`: Custom log file path

**Data Processing:**
- `STATA_MCP_CACHE_HELP`: Enable help caching (default: true)
- `STATA_MCP_DATA_INFO_DECIMAL_PLACES`: Decimal places for data info output
- `STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`: Max string values to display

**Security:**
- `STATA_MCP__IS_GUARD`: Enable security guard validation (default: true)

**Monitoring:**
- `STATA_MCP__IS_MONITOR`: Enable RAM monitoring (default: false)
- `STATA_MCP__RAM_LIMIT`: Maximum RAM in MB (default: -1, no limit)

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

A standard git workflow follows:

1. **Lint code**: Run lint tools on your code
2. **Check status**: Run `git status` to see current changes
3. **Stage files**: Run `git add <files>` to stage changes
4. **Review changes**: Run `git diff --staged` to review staged changes
5. **Commit**: Run `git commit -m "type: description"` with conventional commit message
6. **Pull rebase**: Before pushing, run `git pull --rebase` to integrate remote changes
7. **Push**: Run `git push` to push changes to remote

## Important Notes

- All Python functions must have type annotations and English docstrings
- Use descriptive variable names
- Maintain proper code indentation
- The project requires a valid Stata license
- Default data output is in `<STATA_MCP_CWD>/stata-mcp-folder/` (or auto-detected location)
- For comprehensive documentation, see the `docs/` directory
