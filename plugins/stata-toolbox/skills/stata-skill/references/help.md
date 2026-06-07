# `help`

Retrieve documentation and usage information for a Stata command.

## Parameters

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `cmd` | `str` | Yes | — | Stata command name (e.g., "regress", "describe", "xtset") |
| `replace` | `bool` | No | `false` | Force refresh of cached help text |

## Returns

String containing Stata help text. If the result is from cache, the prefix shows:

```
Cached result for regress
...help text...
```

Project-cache results use the prefix `Saved result for {cmd}`.

## When to Use

- Understanding a command's syntax, options, or available subcommands
- Troubleshooting errors before running the command
- Verifying correct option names and their effects

## Platform Limitation

**Unix only (macOS / Linux).** This tool is automatically filtered out on Windows during tool registration. On Windows, users should consult the Stata manual or online documentation.

## Caching

Help text is cached at two levels:

1. **Project cache**: stored at `<WORKING_DIR>/.statamcp/stata-mcp-tmp/help__{cmd}.txt`
2. **Global cache**: stored at `~/.statamcp/help/help__{cmd}.txt`

Only enabled cache locations are considered. If both contain a non-empty result,
the newest file by modification time is returned. If their timestamps match, the
project cache is preferred.

Caching is controlled by environment variables:

| Variable | Default | Description |
|:---|:---|:---|
| `STATA_MCP__CACHE_HELP` | `true` | Enable the global help cache |
| `STATA_MCP__SAVE_HELP` | `true` | Enable the project help cache |

If cached content seems stale or incorrect, pass `replace=true`. This bypasses
cache lookup, queries Stata, and overwrites both project and global cache files.

## Example

```python
# Look up regress command documentation
help(cmd="regress")

# Force refresh cache
help(cmd="xtreg", replace=true)
```

## Notes

- There is no automatic TTL-based refresh; use `replace=true` after an external package update
- Successful package installation attempts to refresh help for the likely command name, but packages may provide commands with different names
- `cmd` must be a single Stata command name that starts with a letter or underscore and otherwise contains only letters, numbers, and underscores
- Help text retrieval uses the Stata CLI's `help` command internally
- If the command does not exist, Stata returns an error message in the help text
