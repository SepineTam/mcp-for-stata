# `stata_do`

Execute a Stata do-file and return the log file paths and optionally the log content.

## Parameters

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `dofile_path` | `str` | Yes | — | Absolute path to the `.do` file to execute |
| `log_file_name` | `str` | No | auto-generated | Custom log filename without timestamp |
| `read_log_when_error` | `bool` | No | `false` | Only return log content when a Stata return-code error is detected |
| `is_replace_log` | `bool` | No | `true` | Overwrite existing log files |
| `enable_smcl` | `bool` | No | `true` | Also generate `.smcl` log (Unix only) |

## Returns

```json
{
  "log_file_path": {
    "text": "/path/to/logfile.log",
    "smcl": "/path/to/logfile.smcl"
  },
  "log_content": {
    "text": "...",
    "smcl": "..."
  }
}
```

`log_content` is only present when `read_log_when_error=true` **and** a Stata error is detected.

## When to Use

- Running Stata commands, performing regression or statistical analysis
- Executing any pre-written do-file
- Re-running a do-file after fixing errors

## Security Boundary

The do-file **must** be within one of the following directories:
- `<WORKING_DIR>/.statamcp/stata-mcp-dofile/`
- `<WORKING_DIR>` (the configured working directory)

Files outside these directories are rejected.

## Security Guard

Enabled by default (`STATA_MCP__IS_GUARD=true`). The guard scans the do-file before execution and blocks dangerous commands including:

- `shell` / `sh`, `xshell`, `winexec`, `unixcmd`
- `erase` / `era`, `rm`, `rmdir`
- `!` (system command prefix)
- `copy`, `run`, `do`, `include` (when used to execute external files)

The guard also detects macro expansion bypasses where dangerous commands are hidden inside local macros.

## SMCL Log

When `enable_smcl=true` (default) on Unix systems, a `.smcl` log is generated alongside the `.log` file. SMCL preserves hyperlinks from commands like `findsj` and `getiref`. On Windows, SMCL generation is silently skipped.

## Example

```python
# Step 1: Write the do-file
stata_code = """
use "data.dta", clear
regress y x1 x2 x3
esttab using "results.csv", replace
"""
# Use Write tool to save to /path/to/project/stata-mcp-dofile/analysis.do

# Step 2: Execute
stata_do(dofile_path="/path/to/project/stata-mcp-dofile/analysis.do")
```

## Environment Variables

| Variable | Default | Description |
|:---|:---|:---|
| `STATA_MCP__IS_GUARD` | `true` | Enable security guard validation |
| `STATA_MCP__IS_MONITOR` | `false` | Enable RAM monitoring |
| `STATA_MCP__RAM_LIMIT` | `-1` | Maximum RAM in MB (`-1` = no limit) |
