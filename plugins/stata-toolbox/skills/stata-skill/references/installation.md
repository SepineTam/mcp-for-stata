# Installation

## Overview

MCP-for-Stata runs via `uvx` without system installation. You only need to register it as an MCP server in your AI client.

## Automatic Registration (Recommended)

### One-Line Install (with uv auto-detection)

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.ps1 | iex
```

This script auto-installs `uv` if missing, then registers MCP-for-Stata to all supported AI clients.

### If uv is already installed

```bash
uvx stata-mcp install --all          # All supported clients at once
```

Or install to a specific client:

```bash
uvx stata-mcp install -c codex       # Codex
uvx stata-mcp install -c claude      # Claude Desktop
uvx stata-mcp install -c cc          # Claude Code
uvx stata-mcp install -c cursor      # Cursor
uvx stata-mcp install -c cline       # Cline
uvx stata-mcp install -c gemini      # Gemini CLI
uvx stata-mcp install -c opencode    # OpenCode
uvx stata-mcp install -c openclaw    # OpenClaw
uvx stata-mcp install -c hermes      # Hermes
```

Restart your AI client after installation.

## Manual Registration

If automatic registration fails, manually add the following configuration to your AI client's MCP settings:

```json
{
  "stata-mcp": {
    "command": "uvx",
    "args": ["stata-mcp"]
  }
}
```

### Client-Specific Config Locations

| Client | Config File | Format | Key |
|:---|:---|:---|:---|
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | JSON | `mcpServers` |
| Claude Code | `~/.claude.json` | JSON | `mcpServers` |
| Codex | `~/.codex/config.toml` | TOML | `mcp_servers` |
| Cursor | `~/.cursor/mcp.json` | JSON | `mcpServers` |
| Gemini | `~/.gemini/settings.json` | JSON | `mcpServers` |
| Cline | VS Code `globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` | JSON | `mcpServers` |
| OpenCode | `~/.config/opencode/opencode.json` | JSON | `mcp` |
| OpenClaw | `~/.openclaw/openclaw.json` | JSON | `mcp.servers` |
| Hermes | `~/.hermes/config.yaml` | YAML | `mcp_servers` |

## Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (installs automatically with `uvx`)
- A valid Stata license (Stata/BE, Stata/SE, or Stata/MP)

## Verify

```bash
uvx stata-mcp doctor
```

Checks:
- Stata executable is found
- MCP-for-Stata is properly configured
- Required directories are writable
