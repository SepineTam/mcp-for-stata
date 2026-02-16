# CLI Reference

Stata-MCP provides a command-line interface (CLI) for various operations including starting MCP servers, running agent mode, and installing to different AI clients.

## Installation

Verify your installation:

```bash
stata-mcp --version
```

Check system compatibility:

```bash
stata-mcp --usable
```

## Commands

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

**Transport Options:**
- `stdio` - Standard input/output (default)
- `sse` - Server-Sent Events
- `http` - HTTP transport (automatically converted to streamable-http)

### Agent Mode

Run Stata-MCP in interactive agent mode:

```bash
# Start agent in current directory
stata-mcp agent run

# Start agent in specific directory
stata-mcp agent run --work-dir /path/to/project
```

### Install to AI Clients

Install Stata-MCP to various AI coding assistants:

```bash
# Install to Claude Desktop (default)
stata-mcp install

# Install to specific client
stata-mcp install -c claude    # Claude Desktop
stata-mcp install -c cc        # Claude Code
stata-mcp install -c cursor    # Cursor
stata-mcp install -c cline     # Cline
stata-mcp install -c codex     # Codex
```

**Supported Clients:**
- `claude` - Claude Desktop
- `cc` - Claude Code
- `cursor` - Cursor Editor
- `cline` - Cline (VSCode extension)
- `codex` - Codex

### Docker-based Installation (sandbox-install)

Install Docker-based Stata-MCP to AI clients. Requires Docker and a valid Stata license.

```bash
# Basic usage with default settings (StataNow 19.5 MP)
uvx stata-mcp sandbox-install -l /path/to/stata.lic

# Specify Stata version and edition
uvx stata-mcp sandbox-install \
  --version 19_5 \
  --edition mp \
  -l /path/to/stata.lic \
  -c claude

# With resource limits
uvx stata-mcp sandbox-install \
  -V 18 \
  -e se \
  -l /path/to/stata.lic \
  --cpus 2 \
  --memory 4g
```

**Stata Versions:** `19_5`, `18_5`, `18`

**Stata Editions:** `mp` (Multi-processor), `se` (Standard), `be` (Basic)

## Options

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version information |
| `--help` | `-h` | Show help message |
| `--usable` | `-u` | Check system compatibility |
| `--transport` | `-t` | MCP transport method (stdio/sse/http) |

### Agent Options

| Option | Description |
|--------|-------------|
| `--work-dir` | Working directory for agent (default: current directory) |

### Install Options

| Option | Short | Description |
|--------|-------|-------------|
| `--client` | `-c` | Target client (default: claude) |

### Sandbox-Install Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--version` | `-V` | `19_5` | Stata version (19_5, 18_5, 18) |
| `--edition` | `-e` | `mp` | Stata edition (mp, se, be) |
| `--tag` | | `latest` | Docker image tag |
| `--license-file` | `-l` | (required) | Path to Stata license file |
| `--client` | `-c` | `claude` | Target client |
| `--work-dir` | | `./` | Working directory |
| `--cpus` | | (none) | CPU core limit |
| `--memory` | | (none) | Memory limit (e.g., 4g) |

## Examples

### Basic Usage

```bash
# Check if Stata-MCP can run on your system
stata-mcp --usable

# Start MCP server for Claude Desktop
stata-mcp

# Start with SSE transport
stata-mcp -t sse
```

### Development Workflow

```bash
# 1. Check system compatibility
stata-mcp --usable

# 2. Install to Claude Desktop
stata-mcp install

# 3. Run agent for interactive analysis
stata-mcp agent run
```

### Using with uvx

If you prefer not to install Stata-MCP globally, you can use `uvx`:

```bash
# Check version
uvx stata-mcp --version

# Check compatibility
uvx stata-mcp --usable

# Run agent
uvx stata-mcp agent run

# Install to client
uvx stata-mcp install -c cursor
```

## Exit Codes

- `0` - Success
- `1` - Error (invalid client, system incompatibility, etc.)
- `2` - Command line argument error

## Environment Variables

Stata-MCP behavior can be configured through environment variables. See [Configuration](configuration.md) for details.

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
stata-mcp --usable
```

This will check if Stata can be found on your system.

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