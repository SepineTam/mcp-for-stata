# CLI Reference

MCP-for-Stata provides a command-line interface (CLI) for various operations including starting MCP servers and installing to different AI clients.

## Installation

Verify your installation:

```bash
stata-mcp --version
```

Run diagnostics to check system health:

```bash
stata-mcp doctor
```

> **Note:** `--usable` has been deprecated since v1.14.3. It still works in current releases but `stata-mcp doctor` is the recommended replacement in v1.16+ and may be removed in a later major release.

## Commands

### Global Config Override

Most users should use `~/.statamcp/config.toml` and optional
`./.statamcp/config.toml` project files. For developer debugging, the CLI also
accepts a config override:

```bash
stata-mcp -c /path/to/debug-config.toml server
stata-mcp server --config /path/to/debug-config.toml
```

> **Note:** `-c/--config` is not recommended for normal use. When provided,
> Stata-MCP reads only that file and ignores the user/project config stack.
> On Linux, `/etc/statamcp/config.toml` still has the highest priority and can
> override this debug config.
> The `install` and `verify` subcommands keep their existing `-c/--client`
> meaning; use `--config` there if a debug config path is needed.

### Start MCP Server

Start the MCP server with different transport methods:

```bash
# Start with stdio transport (default)
stata-mcp

# Explicitly specify transport method
stata-mcp -t stdio
stata-mcp -t sse
stata-mcp -t http
```

#### Server Subcommand

Use the `server` subcommand to control which MCP tools are registered:

```bash
# Standard tools, stdio transport (same as bare command)
stata-mcp server

# Core tools only (stata_do, get_data_info, help)
stata-mcp server --core

# Standard tools with HTTP transport
stata-mcp server --all -t http

# Standard tools plus high-risk ado installation
stata-mcp server --unsafe

# Core tools with SSE transport
stata-mcp server --core -t sse
```

**Tool Profiles:**
- `--all` - Register standard tools, excluding high-risk installation (default)
- `--core` - Register only core tools: `stata_do`, `get_data_info`, `help`
- `--unsafe` - Add the high-risk `ado_package_install` tool

**Transport Options:**
- `stdio` - Standard input/output (default)
- `sse` - Server-Sent Events
- `http` - HTTP transport (automatically converted to streamable-http)

### Doctor Diagnostics

Run health checks to diagnose potential issues:

```bash
# Run all checks
stata-mcp doctor

# Show detailed information for each check
stata-mcp doctor --verbose

# Output in JSON format
stata-mcp doctor --json

# Run only specific checks (repeatable)
stata-mcp doctor --check stata --check python

# Preview cleanup actions without deleting (cleanup checks only)
stata-mcp doctor --check cleanup --dry-run
```

Common check names include `stata`, `python`, and `cleanup`. The `--dry-run` flag is interpreted by cleanup-style checks and previews destructive operations instead of executing them; other checks ignore it.

### Verify Installation

Check whether `stata-mcp` is already installed in a target MCP client or config file. This subcommand is read-only and never modifies configuration files.

```bash
# Check a supported client
stata-mcp verify -c claude

# Check a custom JSON config file
stata-mcp verify -f ~/.cursor/mcp.json

# Check a nested config path
stata-mcp verify -f ~/.openclaw/openclaw.json --index mcp.servers

# Use a custom entry key
stata-mcp verify -f ~/.codex/config.toml --index mcp_servers --key stata-mcp
```

`-c` takes precedence over `-f` when both are provided.

### Update

Update stata-mcp to the latest version:

```bash
# Auto-detect install method and update
stata-mcp update

# Check if a newer version is available
stata-mcp update --check

# Show detected method and available update without executing
stata-mcp update --dry-run

# Force specific update method
stata-mcp update --method pip       # pip install
stata-mcp update --method uv-tool   # uv tool upgrade
stata-mcp update --method homebrew  # brew upgrade
```

**Update Methods:** `auto` (default), `pip`, `uv-tool`, `homebrew`

> **Note for uv tool users on versions before 1.17.2:** Due to a detection bug in earlier versions, `stata-mcp update` may incorrectly detect pip and fail. Run `uv tool upgrade stata-mcp` once manually to reach 1.17.2 or later, after which `stata-mcp update` will work correctly.

### Local Tool Commands

Run API-backed Stata tools directly from the CLI:

```bash
# Install an approved ado package from SSC
stata-mcp tool ado-install reghdfe --yes

# Run a do-file and only read the log when execution fails
stata-mcp tool do /path/to/analysis.do --is-read-log true

# Stop a do-file if execution exceeds five minutes
stata-mcp tool do /path/to/analysis.do --timeout 300

# Read Stata help through the one-shot API helper
stata-mcp tool help regress

# Inspect a supported dataset
stata-mcp tool data-info /path/to/data.dta

# Read a generated log file
stata-mcp tool read-log /path/to/output.log
```

Tool subcommands:
- `stata-mcp tool ado-install <package_name> [-y|--yes] [--source ssc|net|github]`
- `stata-mcp tool do <dofile_path> [--is-read-log true|false] [--enable-smcl true|false] [--timeout <seconds>]`
- `stata-mcp tool help <command> [--replace true|false]`
- `stata-mcp tool data-info <data_path> [--vars-list var1 var2 ...]`
- `stata-mcp tool read-log <log_path> [--output-format full|core|dict]`

> Note: `--is-read-log true` returns log content only when the underlying execution reports a Stata return-code error.

> Without `-y` or `--yes`, `ado-install` asks for interactive confirmation.
> SSC and net package names may contain only ASCII letters and numbers. GitHub
> repositories require an exact repository allowlist and must be inspected
> before installation.

### Config Management

Inspect and update local CLI configuration stored in `~/.statamcp/config.toml`:

```bash
# Print the entire config file
stata-mcp config

# Show a single value (cli is shorthand for STATA.STATA_CLI)
stata-mcp config show cli
stata-mcp config show STATA.STATA_CLI
stata-mcp config show SECURITY.IS_GUARD

# Set STATA_CLI explicitly
stata-mcp config set cli /path/to/stata

# Auto-detect STATA_CLI via StataFinder and persist it
stata-mcp config set cli

# Edit an existing key by dot-notation
stata-mcp config edit STATA.STATA_CLI /path/to/stata
stata-mcp config edit SECURITY.IS_GUARD false
```

The `set` subcommand currently accepts only the `cli` key. The `edit` subcommand accepts any existing `Section.Key` in the config file and rejects keys that are not already defined.

### Install to AI Clients

Install MCP-for-Stata to various AI coding assistants:

```bash
# Install to all supported clients (no -c, no --json-file)
stata-mcp install

# Install to a specific client
stata-mcp install -c claude-code
stata-mcp install -c cursor

# Install to all clients explicitly
stata-mcp install --all

# Install into a custom JSON config file
stata-mcp install --json-file /path/to/config.json

# Install into a nested key inside a custom JSON config file
stata-mcp install --json-file /path/to/config.json --json-index mcp.servers
```

**Supported Clients:**

| Client ID | Target | Aliases |
|-----------|--------|---------|
| `claude` | Claude Desktop | |
| `claude-code` | Claude Code | `cc` |
| `cursor` | Cursor Editor | |
| `cline` | Cline (VS Code extension) | |
| `codex` | Codex | |
| `gemini` | Gemini CLI | |
| `opencode` | OpenCode | |
| `openclaw` | OpenClaw | |
| `hermes` | Hermes | `hermes-agent` |

## Options

### Server Options

| Option | Description |
|--------|-------------|
| `--core` | Register only core tools (stata_do, get_data_info, help) |
| `--all` | Register standard tools, excluding high-risk installation (default) |
| `--unsafe` | Add high-risk ado installation; requires explicit security configuration |
| `-t`, `--transport` | MCP transport method (stdio/sse/http) |

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version information |
| `--help` | `-h` | Show help message |
| `--usable` | `-u` | *(Deprecated)* Check system compatibility, use `stata-mcp doctor` instead |
| `--transport` | `-t` | MCP transport method (stdio/sse/http) |

### Config Options

| Command | Description |
|---------|-------------|
| `stata-mcp config` | Print the raw `~/.statamcp/config.toml` content |
| `stata-mcp config show <dot_key>` | Show one value. `cli` is shorthand for `STATA.STATA_CLI`; otherwise use `Section.Key` |
| `stata-mcp config set cli [value]` | Set `STATA.STATA_CLI`. Auto-detect via StataFinder when value is omitted |
| `stata-mcp config edit <dot_key> <value>` | Edit an existing `Section.Key` entry |

### Install Options

| Option | Short | Description |
|--------|-------|-------------|
| `--client` | `-c` | Target client. Omitting both `-c` and `--json-file` is equivalent to `--all` |
| `--all` | `-a` | Install to all supported clients |
| `--json-file` | | Custom target client config file path |
| `--json-index` | | Dot-separated nested key path (e.g. `mcp.servers`); only valid together with `--json-file` |

### Doctor Options

| Option | Description |
|--------|-------------|
| `--verbose` | Show detailed information for each check |
| `--json` | Output report in JSON format |
| `--check` | Run only specified check names (repeatable) |
| `--dry-run` | Preview cleanup actions without deleting files (cleanup-style checks only) |

### Verify Options

| Option | Short | Description |
|--------|-------|-------------|
| `--client` | `-c` | Target client key (e.g. `claude`, `cursor`, `codex`) |
| `--file` | `-f` | Path to a custom JSON or TOML config file |
| `--index` | | Dot-separated nested key path, used with `-f` (e.g. `mcp.servers`) |
| `--key` | | Entry key inside the target dict (default: `stata-mcp`) |

### Update Options

| Option | Description |
|--------|-------------|
| `--method` | Force specific update method (auto/pip/uv-tool/homebrew) |
| `--dry-run` | Show detected method without updating |
| `--check` | Only check if a newer version is available |

## Examples

### Basic Usage

```bash
# Check if MCP-for-Stata can run on your system
stata-mcp doctor

# Start MCP server for Claude Desktop
stata-mcp

# Start with SSE transport
stata-mcp -t sse
```

### Development Workflow

```bash
# 1. Run diagnostics
stata-mcp doctor

# 2. Install to Claude Code
stata-mcp install -c claude-code

# 3. Inspect a dataset before writing the analysis
stata-mcp tool data-info /path/to/data.dta
```

### Using with uvx

If you prefer not to install MCP-for-Stata globally, you can use `uvx`:

```bash
# Check version
uvx stata-mcp --version

# Run diagnostics
uvx stata-mcp doctor

# Run a do-file directly
uvx stata-mcp tool do /path/to/analysis.do

# Start the MCP server
uvx stata-mcp server

# Install to a client
uvx stata-mcp install -c cursor
```

## Self-contained Install Scripts

The project root ships a set of self-contained installer scripts for users who do not already have `uv` or `pip` available. They bootstrap a Python toolchain and bring up `stata-mcp` in one step.

| Script | Target platform | Typical use |
|--------|-----------------|-------------|
| `install.sh` | Unix shells (Linux, macOS, WSL) | `bash install.sh` |
| `install.command` | macOS Finder | double-click to launch in Terminal |
| `install.ps1` | Windows PowerShell | `powershell -ExecutionPolicy Bypass -File install.ps1` |
| `install.bat` | Windows command line | double-click or run from `cmd.exe` |

These scripts are intended for first-time bootstrap on machines without a Python package manager. On machines that already have `uv` or `pip`, the standard `uv tool install stata-mcp` / `pip install stata-mcp` flow is preferred.

## Exit Codes

- `0` - Success
- `1` - Error (system incompatibility, file not found, etc.)
- `2` - Command line argument error, or missing/invalid config key in `verify`
- `3` - Failed to parse JSON/TOML file in `verify`
- `4` - Invalid MCP server entry in `verify` (missing `command` or wrong type)
- `5` - `verify` subcommand argument error (missing `-c`/`--client`, invalid client, or missing `-f`/`--file`)

## Environment Variables

MCP-for-Stata behavior can be configured through environment variables. See [Configuration](configuration.md) for details.

Key environment variables:

- `STATA_MCP_CWD` - Working directory for Stata operations
- `STATA_MCP_LOGGING_ON` - Enable/disable logging
- `STATA_MCP__IS_GUARD` - Enable security guard validation
- `STATA_MCP__IS_MONITOR` - Enable RAM monitoring

See the [Configuration](configuration.md) document for the complete list.

## Troubleshooting

### "Stata not found" Error

Ensure Stata is installed and accessible:

```bash
stata-mcp doctor
```

This will run diagnostics and check if Stata can be found on your system.

### Permission Errors

Some operations may require appropriate permissions:
- Installing to Claude Desktop may need admin/user privileges
- Working directories must be writable

### Transport Issues

If you encounter issues with specific transport methods:
- Default to `stdio` for most use cases
- Use `--transport stdio` explicitly if auto-detection fails

## See Also

- [Usage Guide](usage.md) - Detailed usage examples
- [Configuration](configuration.md) - Environment variables and settings
- [Security](security.md) - Security guard and validation
- [Monitoring](monitoring.md) - Resource monitoring configuration
