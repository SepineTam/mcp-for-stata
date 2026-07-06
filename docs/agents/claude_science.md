# Using with Claude Science

Claude Science uses a stricter sandbox policy that prevents reading from and writing to the home directory (`~`) by default. This causes the MCP-for-Stata server to fail immediately on startup when configured in the usual way:

```text
Couldn't load tools: MCP error -32000: Connection closed
--- stderr ---
Traceback ...
FileNotFoundError: [Errno 2] No such file or directory
```

This error is not caused by MCP-for-Stata itself; it happens because the Claude Science sandbox cannot find the configured executable. Two solutions are described below.

## Complete Setup

### 1. Install `stata-mcp`

```bash
uv tool install stata-mcp
```

### 2. Allowlist the sandbox paths

Run the following command to write the sandbox allowlist to `~/.claude-science/config.toml`. The script checks whether a `[sandbox]` block already exists before appending, so it will not create duplicate entries.

```bash
mkdir -p ~/.claude-science
CONFIG_FILE="$HOME/.claude-science/config.toml"

if ! grep -q '^\[sandbox\]' "$CONFIG_FILE" 2>/dev/null; then
    cat >> "$CONFIG_FILE" <<'EOF'

[sandbox]
user_write_paths = [
  "$HOME/.local/bin",
  "$HOME/.local/share/uv/tools/stata-mcp",
]
EOF
    echo "Wrote $CONFIG_FILE"
else
    echo "[sandbox] already exists; please verify user_write_paths includes:"
    echo "  $HOME/.local/bin"
    echo "  $HOME/.local/share/uv/tools/stata-mcp"
fi
```

### 3. Add the MCP server in Claude Science

Open the Claude Science MCP configuration UI and enter:

- **Name**: `Stata-MCP`
- **Command**: `~/.local/bin/stata-mcp`

Save and restart Claude Science. The MCP-for-Stata tools should now load correctly.

## Option 1: Allowlist the `uv tool` installation paths

If you installed with `uv tool install stata-mcp`, the executable and its data are placed at:

- `~/.local/bin/stata-mcp`
- `~/.local/share/uv/tools/stata-mcp`

You must explicitly allow both paths in the Claude Science sandbox so they are readable and writable.

Add the following to `~/.claude-science/config.toml`:

```toml
[sandbox]
user_write_paths = [
  "~/.local/bin",
  "~/.local/share/uv/tools/stata-mcp",
]
```

Save and restart Claude Science, then try loading the MCP-for-Stata tools again.

## Option 2: Install MCP-for-Stata outside the home directory

If you prefer not to allowlist home-directory paths, you can install MCP-for-Stata in a location the sandbox already permits, such as the project directory or a dedicated tools directory. Detailed steps will be added later.
