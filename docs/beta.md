# Beta Configuration

Beta options are experimental switches under the `[BETA]` section of `~/.statamcp/config.toml`. They are disabled by default unless stated otherwise, and may change as the feature stabilizes.

## Recommended Defaults

```toml
[BETA]
ENABLE_WRITE_DOFILE = false
IS_ASYNC_DO = false
MAX_ASYNC_DO = 3
```

## Parameters

| Parameter | Type | Default | Environment Variable | Description |
| --- | --- | --- | --- | --- |
| `ENABLE_WRITE_DOFILE` | Boolean | `false` | `STATA_MCP__ENABLE_WRITE_DOFILE` | Registers the deprecated `write_dofile` MCP tool. Keep this disabled unless an older workflow still depends on that tool. |
| `IS_ASYNC_DO` | Boolean | `false` | `STATA_MCP__IS_ASYNC_DO` | Registers the async implementation of `stata_do` so concurrent MCP calls can progress without blocking the server event loop. |
| `MAX_ASYNC_DO` | Integer | `3` | `STATA_MCP__MAX_ASYNC_DO` | Limits concurrent async `stata_do` executions. Extra calls wait for an active slot. Applies only when `IS_ASYNC_DO=true`. |

## `ENABLE_WRITE_DOFILE`

`ENABLE_WRITE_DOFILE` controls whether the deprecated `write_dofile` tool is registered with the MCP server.

Modern AI agents can already write files directly, so `write_dofile` is usually redundant. Leave this option as `false` unless you need backward compatibility with an older client or workflow.

Enable it with either:

```toml
[BETA]
ENABLE_WRITE_DOFILE = true
```

or:

```bash
export STATA_MCP__ENABLE_WRITE_DOFILE=true
```

## `IS_ASYNC_DO`

`IS_ASYNC_DO` controls whether the MCP `stata_do` tool uses the async executor.

When `false`, `stata_do` keeps the synchronous execution path. When `true`, the MCP server registers the async implementation backed by `AsyncStataDo`. The tool parameters and return structure stay the same.

Enable it with either:

```toml
[BETA]
IS_ASYNC_DO = true
```

or:

```bash
export STATA_MCP__IS_ASYNC_DO=true
```

Boolean string values must be `true` or `false`. Values such as `on` and `off` are not accepted and fall back to the default.

## `MAX_ASYNC_DO`

`MAX_ASYNC_DO` limits how many async `stata_do` executions can run at the same time.

```toml
[BETA]
IS_ASYNC_DO = true
MAX_ASYNC_DO = 3
```

Set a larger value only when the machine and Stata license can safely support more parallel Stata processes. The value must be a positive integer.
