# Beta Configuration

Beta options are experimental switches under the `[BETA]` section of `~/.statamcp/config.toml`. They are disabled by default unless stated otherwise, and may change as the feature stabilizes.

## Recommended Defaults

```toml
[BETA]
ENABLE_WRITE_DOFILE = false
IS_ASYNC_DO = false
MAX_ASYNC_DO = 3
enable_data_info_url_guard = false
data_info_allowed_url_domains = []
enable_structured_log = false
```

## Parameters

| Parameter | Type | Default | Environment Variable | Description |
| --- | --- | --- | --- | --- |
| `ENABLE_WRITE_DOFILE` | Boolean | `false` | `STATA_MCP__ENABLE_WRITE_DOFILE` | Registers the deprecated `write_dofile` MCP tool. Keep this disabled unless an older workflow still depends on that tool. |
| `IS_ASYNC_DO` | Boolean | `false` | `STATA_MCP__IS_ASYNC_DO` | Enables the async implementation of `stata_do` for MCP and API/CLI execution paths. |
| `MAX_ASYNC_DO` | Integer | `3` | `STATA_MCP__MAX_ASYNC_DO` | Limits concurrent async MCP `stata_do` executions. Extra MCP calls wait for an active slot. Applies only when `IS_ASYNC_DO=true`. |
| `enable_data_info_url_guard` | Boolean | `false` | None | Enables URL validation and domain allowlist checks for URL data sources passed to `get_data_info`. |
| `data_info_allowed_url_domains` | List[str] | `[]` | None | Allowed hostnames when the `get_data_info` URL guard is enabled. |
| `enable_structured_log` | Boolean | `false` | None | Enables structured log parsing for the `read_log` tool and API. |

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

`IS_ASYNC_DO` controls whether configured `stata_do` execution paths use the async executor.

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

Async execution applies to the MCP-layer `stata_do` tool and to API/CLI one-shot execution when they load a configuration with `IS_ASYNC_DO=true`. The same tool arguments still apply on the async path, including `timeout`, `enable_smcl`, `is_replace_log`, `log_file_name`, and `read_log_when_error`.

## `MAX_ASYNC_DO`

`MAX_ASYNC_DO` limits how many async MCP `stata_do` executions can run at the same time.

```toml
[BETA]
IS_ASYNC_DO = true
MAX_ASYNC_DO = 3
```

Set a larger value only when the machine and Stata license can safely support more parallel Stata processes. The value must be a positive integer.

`MAX_ASYNC_DO` is a server-side MCP concurrency limit; it does not limit standalone API or CLI invocations. When RAM monitoring is enabled with `IS_MONITOR=true`, individual async executions use the monitored synchronous fallback path. Use conservative concurrency, such as `MAX_ASYNC_DO=1`, for monitored MCP runs.

## `enable_data_info_url_guard`

`enable_data_info_url_guard` controls whether URL data sources passed to `get_data_info` are restricted by the beta URL guard.

```toml
[BETA]
enable_data_info_url_guard = true
data_info_allowed_url_domains = ["example.com", "raw.githubusercontent.com"]
```

When this switch is `false`, URL sources keep the historical behavior and are passed directly to the data handler without scheme, host, userinfo, or domain checks. When it is `true`, URL sources must use HTTPS, cannot use IP hosts, cannot contain URL userinfo, and must match `data_info_allowed_url_domains`.

## `data_info_allowed_url_domains`

`data_info_allowed_url_domains` is the hostname allowlist used when the `get_data_info` URL guard is enabled.

Entries match the exact hostname and its subdomains. For example, `example.com` allows `example.com` and `data.example.com`. GitHub raw content is a separate hostname, so add `raw.githubusercontent.com` explicitly when you need to inspect raw GitHub-hosted datasets.

## `enable_structured_log`

`enable_structured_log` controls whether `read_log` uses the structured `StataLog` parser.

```toml
[BETA]
enable_structured_log = true
```

When this switch is `false`, `read_log` returns raw file content. When it is `true`, supported logs are parsed into structured formats (`full`, `core`, or `dict`) via `StataLog`. The MCP-layer tool applies structured parsing only on macOS and Linux; the API path uses structured parsing whenever the switch is enabled.

Boolean string values must be `true` or `false`. Values such as `on` and `off` are not accepted and fall back to the default.
