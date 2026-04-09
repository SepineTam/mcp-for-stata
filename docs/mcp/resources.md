# MCP.Resources

Stata-MCP provides MCP resources for accessing Stata documentation and help contents.

---
## help

> **Platform Support**: macOS and Linux only (Windows not supported)

```python
@stata_mcp.resource(
    uri="help://stata/{cmd}",
    name="help",
    description="Get help for a Stata command"
)
def help(cmd: str) -> str:
    ...
```

**Resource URI**: `help://stata/{cmd}`

**Input Parameters**:
- `cmd`: Stata command name (required, e.g., "regress", "describe", "xtset", "merge")

**Return Structure**:
String containing Stata help text output. May include cache status prefix:
- `"Cached result for {cmd}\n{help_text}"` - Retrieved from cache
- `"Saved result for {cmd}\n{help_text}"` - Retrieved from project cache
- `"{help_text}"` - Fresh result from Stata
- `"No help found for the command in Stata ado locally: {cmd}"` - Command not found

**Operational Examples**:
```python
# Regression commands
help("regress")
help("logit")
help("probit")

# Panel data commands
help("xtset")
help("xtreg")
help("xtmixed")

# Data management
help("merge")
help("reshape")
help("collapse")

# Time series
help("tsset")
help("arima")
help("varsoc")
```

**Implementation Architecture**:

The help resource implements a dual-registered pattern in the MCP framework, functioning as both a resource (URI-addressable via `help://stata/{cmd}`) and an executable tool. This dual registration enables flexible access patterns: clients can either invoke it as a standard tool or access it via the resource protocol.

The `StataHelp` class manages help text retrieval with a three-tier caching strategy:

1. **Project-level Cache** (`STATA_MCP__SAVE_HELP`, default: `true`):
   - Stores help text in `stata-mcp-tmp/help__{cmd}.txt`
   - Persists across sessions within the project directory
   - Highest priority for retrieval

2. **Global Cache** (`STATA_MCP__CACHE_HELP`, default: `false`):
   - Stores help text in `~/.statamcp/help/help__{cmd}.txt`
   - Shared across all projects
   - Secondary priority if project cache miss

3. **Live Stata Execution**:
   - Invokes Stata CLI with `help {cmd}` command
   - Captures stdout for return value
   - Falls back to this tier when both caches miss

**Cache Invalidation**:
No automatic TTL-based expiration exists. Cache invalidation requires:
- Manual deletion of cache files (`rm ~/.statamcp/help/help__{cmd}.txt`)
- Setting environment variable `STATA_MCP__CACHE_HELP=false` to disable caching
- Setting environment variable `STATA_MCP__SAVE_HELP=false` to disable project-level caching

**Error Detection**:
The help system detects command existence by comparing Stata output against a standard error message template:
```
help {cmd}
help for {cmd} not found
try help contents or search {cmd}
```

If the output matches this pattern, the system raises an exception indicating the command is not found in locally installed ado-files. This behavior occurs after cache miss and before caching new results.

**Platform Considerations**:
- **macOS/Linux**: Full support with caching and live Stata execution
- **Windows**: Not supported due to Stata CLI limitations on Windows platforms

**Performance Optimization**:
For frequently accessed commands (e.g., `regress`, `xtreg`), enable `STATA_MCP__CACHE_HELP=true` to avoid repeated Stata invocations. The first execution queries Stata (~50-200ms depending on Stata startup time), subsequent queries return from cache (~1-5ms file read).

**Usage Notes**:
- Help text language depends on the Stata installation locale
- Multilingual support requires separate Stata installations or locale reconfiguration
- Cache files are plain text UTF-8 encoded, allowing manual inspection or editing
- The resource URI pattern `help://stata/{cmd}` enables programmatic access via MCP resource protocol

**Environment Variables**:

| Variable | Default | Description |
|----------|---------|-------------|
| `STATA_MCP__CACHE_HELP` | `false` | Enable global caching at `~/.statamcp/help/` |
| `STATA_MCP__SAVE_HELP` | `true` | Enable project-level caching at `stata-mcp-tmp/` |

**Integration with Tools**:
The help resource integrates with Stata-MCP tools in several workflows:
- **Pre-execution validation**: Check command syntax before generating do-files
- **Error diagnosis**: Understand error messages from Stata execution
- **Learning assistance**: Provide contextual help during analysis sessions
- **Code completion**: Suggest valid command options and syntax

**Example Workflow**:
```python
# 1. Check if a command exists
help_result = help("ivregress2")
if "not found" not in help_result:
    # 2. Generate do-file using the command
    write_dofile("ivregress2 y x1 x2, robust")

    # 3. Execute the do-file
    stata_do("/path/to/do/file")
```

---
