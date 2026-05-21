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
Cached result for regress:
----
[regress]
    ...help text...
```

## When to Use

- Understanding a command's syntax, options, or available subcommands
- Troubleshooting errors before running the command
- Verifying correct option names and their effects

## Platform Limitation

**Unix only (macOS / Linux).** This tool is automatically filtered out on Windows during tool registration. On Windows, users should consult the Stata manual or online documentation.

## Caching

Help text is cached at two levels:

1. **In-memory cache**: persists for the MCP server session
2. **Disk cache**: stored at `~/.statamcp/help/{cmd}.txt`

Caching is controlled by environment variables:

| Variable | Default | Description |
|:---|:---|:---|
| `STATA_MCP__CACHE_HELP` | `true` | Use cached help text when available |
| `STATA_MCP__SAVE_HELP` | `true` | Save fetched help text to disk cache |

If cached content seems stale or incorrect, set `STATA_MCP__CACHE_HELP=false` to force a fresh fetch, or pass `replace=true`.

## Example

```python
# Look up regress command documentation
help(cmd="regress")

# Force refresh cache
help(cmd="xtreg", replace=true)
```

## Notes

- The `replace` parameter only refreshes the in-memory cache; to also clear disk cache, manually delete `~/.statamcp/help/{cmd}.txt`
- Help text retrieval uses the Stata CLI's `help` command internally
- If the command does not exist, Stata returns an error message in the help text
