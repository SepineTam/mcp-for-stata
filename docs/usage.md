# Usage Guide

> **Hope no [Star War](https://www.aeaweb.org/articles?id=10.1257/app.20150044) future.** - Let's evolve from reg monkeys to causal thinkers.

This guide covers how to integrate and use MCP-for-Stata across different environments and agents.

## Prerequisites

Before using MCP-for-Stata, ensure you have:
- **Stata** 17+ installed with a valid license
- **uv** package manager or Python 3.11+
- **MCP-for-Stata** installed or available via `uvx`

Verify your setup:
```bash
uvx stata-mcp doctor
```

## New Features
<details markdown="1">
<summary><strong>Click to expand</strong></summary>

### 🔒 Security Guard System

MCP-for-Stata now includes automatic security validation to prevent dangerous commands:

```python
# Automatically enabled by default
# Blocks: !, shell, erase, rm, run, do, include, etc.

# Safe code executes normally
result = stata_mcp.stata_do("""
    sysuse auto
    regress price mpg weight
""")

# Dangerous code is blocked
result = stata_mcp.stata_do("""
    ! rm -rf /  # ❌ Blocked by security guard
""")
# Error: Security validation failed
```

**Configuration**:
```toml
# ~/.statamcp/config.toml
[SECURITY]
IS_GUARD = true  # Default: true
```

**Environment Variable**:
```bash
export STATA_MCP__IS_GUARD=true
```

For details, see [Security Documentation](security.md).

### 📊 RAM Monitoring System

Monitor and control Stata process memory usage:

```python
# Enable monitoring with 8GB limit
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=8192

# Process is automatically terminated if RAM exceeds limit
result = stata_mcp.stata_do(large_analysis_code)
```

**Configuration**:
```toml
[MONITOR]
IS_MONITOR = false   # Default: false
MAX_RAM_MB = -1      # -1 = no limit, positive value = limit in MB
```

For details, see [Monitoring Documentation](monitoring.md).

### ⚙️ Unified Configuration System

Configure all settings via TOML file or environment variables:

**Priority**: Environment variables > config file > defaults

```bash
# Quick setup with environment variables
export STATA_MCP__CWD="/projects/my-analysis"
export STATA_MCP__IS_GUARD=true
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=16384
```

**Or use config file** (`~/.statamcp/config.toml`):
```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = false
LOGGING_FILE_HANDLER_ON = true

[SECURITY]
IS_GUARD = true

[PROJECT]
WORKING_DIR = ""

[MONITOR]
IS_MONITOR = false
MAX_RAM_MB = -1
```

For details, see [Configuration Documentation](configuration.md).

</details>

## CLI Commands

MCP-for-Stata provides several utility commands beyond the MCP server.

```bash
# Run diagnostics
stata-mcp doctor

# Install an enabled and approved ado package
stata-mcp tool ado-install reghdfe --yes

# Inspect a dataset
stata-mcp tool data-info /path/to/data.dta

# Update to latest version
stata-mcp update
```

See [CLI Reference](cli.md) for complete documentation.

## Usage in Python

## Usage in Coding Agents

MCP-for-Stata is designed for seamless integration with modern AI coding agents. Below are tested configurations for popular platforms.

### Claude Plugin (Recommended)

We recommend using the official plugin for the best experience. Therefore the simplest way to use MCP-for-Stata with Claude Code is through the official plugin, which provides both MCP server and LSP integration:

```bash
# Add marketplace registry
claude plugin marketplace add sepinetam/stata-mcp

# Install plugin globally
claude plugin install stata-toolbox -s user
```

If you want to work with your partners, also could install it with: 
```bash
# claude plugin marketplace add sepinetam/stata-mcp

claude plugin install stata-toolbox@stata-plugin-lib -s project
```

Then, you can find the plugin in `.claude/settings.json` with
```json
{
  "enabledPlugins": {
    "stata-toolbox@stata-plugin-lib": true
  }
}
```

**Plugin Features:**
- ✅ One-command installation
- ✅ MCP server + LSP configured together
- ✅ Pre-configured optimal Stata LSP settings

For complete plugin documentation, see [Claude Plugin Guide](claude-plugin.md).

### Manual MCP Configuration for Claude Code

Alternatively, configure MCP server manually:

Claude Code is our recommended solution for AI-assisted empirical research.

#### Global Installation

```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

#### Project-based Configuration

For research projects, use project-scoped configuration:

```bash
cd ~/Documents/MyResearchProject
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

#### Specify Version

To use a specific version:

```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp==1.16.3
```

**Verify installation:**
```bash
claude mcp list
```

**Benefits of project-based configuration:**
- Isolates MCP-for-Stata environment per research project
- Automatic path management within project directory
- No global configuration conflicts

### Codex (VS Code Extension)

For VS Code users with the Codex extension, edit `~/.codex/config.toml`:

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
```

### Cline

For Cline users, edit the MCP configuration file at `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### Cursor

**Note:** Cursor has limited file system access. MCP servers may not access `Documents` directory by default. If you encounter issues, try this configuration:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP__CWD": "/path/to/your/project"
      }
    }
  }
}
```

Replace `/path/to/your/project` with your actual research directory.

## Usage in AI Clients

Most AI clients follow the standard MCP server configuration format. Below is the universal configuration pattern:

### Standard Configuration (Claude Desktop, Cherry Studio, etc.)

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### Configuration with Custom Working Directory

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP__CWD": "/path/to/working/directory"
      }
    }
  }
}
```

### Configuration with Environment Variables

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP__CWD": "/path/to/working/directory",
        "STATA_MCP_MODEL": "gpt-4",
        "STATA_MCP_API_KEY": "your-api-key",
        "STATA_MCP_API_BASE_URL": "https://api.openai.com/v1"
      }
    }
  }
}
```

## Environment Variables

MCP-for-Stata supports several environment variables for customization:

| Variable | Description | Default |
|----------|-------------|---------|
| `STATA_MCP__CWD` | Current working directory for Stata operations | `./` |
| `STATA_MCP_API_BASE_URL` | Base URL for API requests | `https://api.openai.com/v1` |
| `STATA_MCP_CLIENT` | Client type identifier | - |

## Troubleshooting

### Common Issues

**"Stata not found"**
- Verify Stata installation: `which stata` (macOS/Linux) or check PATH
- Use `StataFinder` configuration guide for custom paths

**"Module not found" errors**
- Ensure dependencies: `uv pip install stata-mcp`
- Check Python version: 3.11+ required

**MCP server not connecting**
- Verify `uvx stata-mcp doctor` passes all checks
- Check client's MCP server logs
- Test with stdio transport (default)

### Debug Mode

Enable verbose logging:
```bash
export STATA_MCP__IS_DEBUG=true
uvx stata-mcp doctor --verbose
```

## Best Practices

1. **Project Structure**: Use project-scoped MCP configuration for better isolation
2. **Version Pinning**: Specify exact versions in production: `stata-mcp==1.16.3`
3. **Data Management**: Keep raw data immutable; use processing/ directories
4. **API Keys**: Use environment variables, never hardcode credentials

## Additional Resources

- [Overview](overview.md) - Architecture and design
- [Tools Documentation](tools.md) - Available MCP tools
- [GitHub Repository](https://github.com/sepinetam/mcp-for-stata) - Source code and issues

## Contributing

Found a bug or have a feature request? Please [open an issue](https://github.com/sepinetam/mcp-for-stata/issues/new) or submit a pull request.
