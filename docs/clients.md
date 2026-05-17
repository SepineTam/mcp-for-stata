# Client Configuration

Different AI clients have varying configuration formats for MCP servers. This page documents the configuration specifics for each supported client.

## Quick Install

For most clients, `stata-mcp install` handles configuration automatically:

```bash
# Single client (see the table below for valid client keys)
stata-mcp install -c <client>

# All supported clients in one shot
stata-mcp install --all

# Custom config file with optional nested JSON key
stata-mcp install -c <client> --json-file /path/to/config.json
stata-mcp install -c <client> --json-file /path/to/config.json --json-index parent.child
```

Supported client keys: `claude`, `cc` (alias `claude-code`), `gemini`, `cursor`, `cline`, `codex`, `opencode`, `openclaw`, `hermes` (alias `hermes-agent`).

The manual configuration snippets below are useful when the automated installer fails, when a client is not yet supported by the installer (e.g. Cherry Studio), or when full control over the generated config is required.

## Standard Configuration Pattern

Most AI clients follow this basic JSON pattern:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

Each client may vary in file location, JSON key path, or format (JSON / TOML / YAML).

## Client-Specific Configurations

### Claude Desktop

**Configuration Method**: Manual file edit (no first-party CLI).

**Configuration File**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`
- Linux: not supported by Anthropic.

**Format**: JSON, top-level key `mcpServers`.

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/path/to/project",
        "STATA_CLI": "/Applications/Stata/StataMP"
      }
    }
  }
}
```

**Unique Features**:
- Environment variables via the `env` object.
- Requires a full client restart after edits.

### Claude Code

**Configuration Method**: Prefers the `claude mcp add` CLI; falls back to writing `~/.claude.json` when the CLI is unavailable.

**Configuration File**: `~/.claude.json` (fallback) or project-local `.mcp.json` when using `--scope project`.

**Format**: JSON, top-level key `mcpServers`.

**Global Installation**:
```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

**Project-Scoped Installation**:
```bash
cd ~/Documents/MyResearch
claude mcp add stata-mcp \
  --env STATA_MCP__CWD=$(pwd) \
  --scope project \
  -- uvx --directory $(pwd) stata-mcp
```

**Equivalent file form**:
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**Unique Features**:
- Project-scoped configuration via `--scope project`.
- Environment variable injection via `--env`.
- Directory pinning via `uvx --directory`.
- Version pinning supported (e.g. `stata-mcp==1.16.2`).

### Gemini CLI

**Configuration Method**: Manual file edit. Installer key: `gemini`.

**Configuration File**: `~/.gemini/settings.json`.

**Format**: JSON, top-level key `mcpServers`.

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**Unique Features**:
- Same JSON schema as Claude Desktop; portable across `mcpServers`-compatible clients.

### Cursor

**Configuration Method**: Manual file edit. The installer auto-injects `--directory` and `STATA_MCP__CWD` pointing to `~/Documents` to work around Cursor's sandbox.

**Configuration File**: `~/.cursor/mcp.json`.

**Format**: JSON, top-level key `mcpServers`.

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "--directory",
        "/absolute/path/to/project",
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**Known Issues / Unique Features**:
- File system sandbox may block access to `~/Documents`; absolute paths inside an allowed directory are required.
- Both `--directory` (in `args`) and `STATA_MCP__CWD` (in `env`) must point to the same path.
- Relative paths are not supported.

### Cline (VS Code Extension)

**Configuration Method**: Manual file edit inside VS Code globalStorage.

**Configuration File**:
- macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Linux: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Windows: `%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

**Format**: JSON, top-level key `mcpServers`.

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

**Unique Features**:
- Standard `mcpServers` schema; no Cline-specific extensions.

### Codex CLI

**Configuration Method**: Prefers the `codex mcp add` CLI; falls back to appending to `~/.codex/config.toml`.

**Configuration File**: `~/.codex/config.toml`.

**Format**: TOML, top-level key `mcp_servers`.

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
env = { STATA_MCP__CWD = "/path/to/project" }
```

**Unique Features**:
- Only client in this list using TOML.
- Note the underscore key `mcp_servers` (not `mcpServers`).

### OpenCode

**Configuration Method**: Manual file edit. Installer key: `opencode`.

**Configuration File**: `~/.config/opencode/opencode.json`.

**Format**: JSON with an OpenCode-specific schema, top-level key `mcp`.

```json
{
  "mcp": {
    "stata-mcp": {
      "type": "local",
      "command": ["uvx", "stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**Unique Features**:
- Uses `type: "local"` and stores `command` as an array (binary plus args combined).
- Top-level key is `mcp`, not `mcpServers`.

### OpenClaw

**Configuration Method**: Prefers the `openclaw mcp set` CLI; falls back to writing `~/.openclaw/openclaw.json`.

**Configuration File**: `~/.openclaw/openclaw.json`.

**Format**: JSON, nested key path `mcp.servers`.

```json
{
  "mcp": {
    "servers": {
      "stata-mcp": {
        "command": "uvx",
        "args": ["stata-mcp"],
        "env": {
          "STATA_MCP__CWD": "/absolute/path/to/project"
        }
      }
    }
  }
}
```

**Unique Features**:
- Added in stata-mcp v1.16.3.
- Configuration sits two levels deep (`mcp.servers.<name>`); when using `--json-file`, pass `--json-index mcp.servers`.

### Hermes Agent

**Configuration Method**: Prefers the `hermes mcp add` CLI; falls back to appending to `~/.hermes/config.yaml`. Installer keys: `hermes` and `hermes-agent`.

**Configuration File**: `~/.hermes/config.yaml`.

**Format**: YAML, top-level key `mcp_servers`.

```yaml
mcp_servers:
  stata-mcp:
    command: "uvx"
    args: ["stata-mcp"]
    env:
      STATA_MCP__CWD: "/absolute/path/to/project"
```

**Unique Features**:
- Only YAML target in this list; the installer uses a minimal text-based writer rather than a full YAML parser.
- Underscore key `mcp_servers` matches the Codex naming convention.

### Cherry Studio (manual only)

**Configuration Method**: Not covered by `stata-mcp install`; user must edit Cherry Studio's settings manually.

**Configuration File**: Cherry Studio settings directory (location varies by platform).

**Format**: JSON, compatible with the Claude Desktop schema.

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

**Unique Features**:
- Manual configuration only; no installer support.
- Re-uses the standard `mcpServers` schema.

## Configuration Options

### Command Variations

**Standard** (uses latest version):
```json
"command": "uvx",
"args": ["stata-mcp"]
```

**Pinned Version**:
```json
"command": "uvx",
"args": ["stata-mcp==1.16.2"]
```

**With Custom Directory**:
```json
"command": "uvx",
"args": [
  "--directory",
  "/path/to/project",
  "stata-mcp"
]
```

### Environment Variables

#### Core Variables

| Variable                 | Purpose                                                       | Example                         |
|--------------------------|---------------------------------------------------------------|---------------------------------|
| `STATA_MCP__CWD`         | Working directory for Stata operations                        | `"/Users/user/research"`        |
| `STATA_MCP_CWD`          | Legacy alias for `STATA_MCP__CWD` (kept for back-compat)      | `"/Users/user/research"`        |
| `STATA_CLI`              | Path to specific Stata executable                             | `"/Applications/Stata/StataMP"` |
| `STATA_MCP_MODEL`        | Used by deprecated agent mode; not needed for MCP server mode | `"gpt-4"`                       |
| `STATA_MCP_API_KEY`      | Used by deprecated agent mode; not needed for MCP server mode | `"sk-..."`                      |
| `STATA_MCP_API_BASE_URL` | Used by deprecated agent mode; not needed for MCP server mode | `"https://api.openai.com/v1"`   |

#### Security Variables

| Variable              | Purpose                          | Default | Example               |
|-----------------------|----------------------------------|---------|-----------------------|
| `STATA_MCP__IS_GUARD` | Enable security guard validation | `true`  | `"true"` or `"false"` |

#### Monitoring Variables

| Variable                | Purpose               | Default         | Example               |
|-------------------------|-----------------------|-----------------|-----------------------|
| `STATA_MCP__IS_MONITOR` | Enable RAM monitoring | `false`         | `"true"` or `"false"` |
| `STATA_MCP__RAM_LIMIT`  | Maximum RAM in MB     | `-1` (no limit) | `"8192"` for 8GB      |

#### Debug Variables

| Variable                                | Purpose                | Default                           | Example                          |
|-----------------------------------------|------------------------|-----------------------------------|----------------------------------|
| `STATA_MCP__IS_DEBUG`                   | Enable debug mode      | `false`                           | `"true"` or `"false"`            |
| `STATA_MCP__LOGGING_ON`                 | Enable logging         | `true`                            | `"true"` or `"false"`            |
| `STATA_MCP__LOGGING_CONSOLE_HANDLER_ON` | Enable console logging | `false`                           | `"true"` or `"false"`            |
| `STATA_MCP__LOGGING_FILE_HANDLER_ON`    | Enable file logging    | `true`                            | `"true"` or `"false"`            |
| `STATA_MCP__LOG_FILE`                   | Custom log file path   | `~/.statamcp/stata_mcp_debug.log` | `"/var/log/stata-mcp/debug.log"` |

**JSON Format**:
```json
"env": {
  "STATA_MCP__CWD": "/path/to/project",
  "STATA_CLI": "/path/to/stata"
}
```

**With Security and Monitoring**:
```json
"env": {
  "STATA_MCP__CWD": "/path/to/project",
  "STATA_MCP__IS_GUARD": "true",
  "STATA_MCP__IS_MONITOR": "true",
  "STATA_MCP__RAM_LIMIT": "8192"
}
```

**TOML Format** (Codex):
```toml
env = { STATA_MCP__CWD = "/path/to/project" }
```

**With All Features**:
```toml
env.STATA_MCP__CWD = "/path/to/project"
env.STATA_MCP__IS_GUARD = "true"
env.STATA_MCP__IS_MONITOR = "true"
env.STATA_MCP__RAM_LIMIT = "8192"
env.STATA_MCP__LOGGING_CONSOLE_HANDLER_ON = "true"
```

## Configuration File Locations

| Client         | Config File Location                                                                                            | Format |
|----------------|-----------------------------------------------------------------------------------------------------------------|--------|
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) / `%APPDATA%/Claude/...` (Windows)    | JSON   |
| Claude Code    | `~/.claude.json` (fallback) or project-local `.mcp.json`                                                        | JSON   |
| Gemini CLI     | `~/.gemini/settings.json`                                                                                       | JSON   |
| Cursor         | `~/.cursor/mcp.json`                                                                                            | JSON   |
| Cline          | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` | JSON   |
| Codex CLI      | `~/.codex/config.toml`                                                                                          | TOML   |
| OpenCode       | `~/.config/opencode/opencode.json`                                                                              | JSON   |
| OpenClaw       | `~/.openclaw/openclaw.json`                                                                                     | JSON   |
| Hermes Agent   | `~/.hermes/config.yaml`                                                                                         | YAML   |
| Cherry Studio  | Cherry Studio settings directory (manual only)                                                                  | JSON   |

## Troubleshooting

### Configuration Not Detected

1. **Verify file path**: Check if configuration file exists in the correct location.
2. **Validate JSON/TOML/YAML syntax**: Use online validators to check for syntax errors.
3. **Restart client**: Most clients require restart after configuration changes.
4. **Check logs**: Look for MCP server connection errors in client logs.

### Path Issues

**Problem**: Stata-MCP cannot access project files.

**Solution**:
- Use absolute paths for `STATA_MCP__CWD`.
- Ensure paths are within the client's allowed directories.
- Check the client's file system access permissions.

### Version Conflicts

**Problem**: Wrong Stata-MCP version loaded.

**Solution**:
- Clear Python package cache: `pip cache purge stata-mcp`.
- Pin a specific version: `uvx stata-mcp==1.16.2`.
- Force a refresh: `uvx --refresh stata-mcp`.

## Best Practices

1. **Use project-scoped configuration** when available (Claude Code).
2. **Pin versions** in production environments.
3. **Set absolute paths** for working directories.
4. **Test configuration** with `uvx stata-mcp doctor` before adding to a client.
5. **Document custom configurations** for team collaboration.

## Additional Resources

- [Usage Guide](usage.md) - Comprehensive usage examples
- [Overview](overview.md) - Architecture and design
- [MCP Tools](mcp/tools.md) - Available tools reference
