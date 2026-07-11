# `read_log`

Read a Stata log file (`.log` or `.smcl`) and return its content.

## Parameters

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `file_path` | `str` | Yes | — | Full path to the log file |
| `encoding` | `str` | No | `"utf-8"` | File encoding |
| `output_format` | `"full" \| "core" \| "dict"` | No | `"core"` | Output format when structured parsing is enabled |
| `lines` | `int` | No | `0` | Content trimming: `0`=all, `>0`=first N, `<0`=last \|N\| |

## Returns

String content. Structured parsing is controlled by `[BETA] enable_structured_log`
in `~/.statamcp/config.toml` and is disabled by default.

### `enable_structured_log=false` (default)

Returns raw log text content.

### `enable_structured_log=true`, `output_format="full"`

Returns all original content with SMCL markup parsed.

### `enable_structured_log=true`, `output_format="core"`

Removes framework lines (log open/close headers, footers, log commands).

### `enable_structured_log=true`, `output_format="dict"` (recommended)

Returns structured command-result pairs:

```json
{
  "commands": [
    {
      "cmd": "regress y x1 x2",
      "output": "...regression output...",
      "timestamp": "..."
    }
  ]
}
```

## When to Use

- Reading execution logs after `stata_do`
- Analyzing structured output from Stata commands
- Inspecting `.smcl` files with structured parsing

## Security Boundary

The log file **must** be within `<WORKING_DIR>/<FOLDER_TAG>/`. Files outside this directory are rejected.

## Structured Parsing

Enable the `StataLog` parser in the Stata-MCP configuration:

```toml
[BETA]
enable_structured_log = true
```

This converts supported logs into structured formats on every supported platform.
If parsing looks incorrect, disable the switch to fall back to raw text.

## `lines` Parameter

| Value | Behavior |
|:---|:---|
| `0` | Return all content |
| `> 0` | Return first N items (lines for raw mode, entries for dict mode) |
| `< 0` | Return last \|N\| items |

Use negative `lines` to quickly inspect the end of a long log (e.g., final regression results).

## Example

```python
# Read full raw log
read_log(file_path="/path/to/project/stata-mcp-log/output.log")

# Read last 50 lines of a log
read_log(file_path="/path/to/project/stata-mcp-log/output.log", lines=-50)

# Structured parsing of SMCL log (requires enable_structured_log=true)
read_log(
    file_path="/path/to/project/stata-mcp-log/output.smcl",
    output_format="dict"
)
```
