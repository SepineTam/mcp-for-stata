# Beta 配置

Beta 选项是 `~/.statamcp/config.toml` 中 `[BETA]` 分区下的实验性开关。除非特别说明，默认都关闭；功能稳定前，这些配置未来可能调整。

## 推荐默认值

```toml
[BETA]
IS_ASYNC_DO = false
MAX_ASYNC_DO = 3
enable_data_info_url_guard = false
data_info_allowed_url_domains = []
enable_structured_log = false
```

## 参数表

| 参数 | 类型 | 默认值 | 环境变量 | 说明 |
| --- | --- | --- | --- | --- |
| `IS_ASYNC_DO` | Boolean | `false` | `STATA_MCP__IS_ASYNC_DO` | 为 MCP 和 API/CLI 执行路径启用异步版 `stata_do`。 |
| `MAX_ASYNC_DO` | Integer | `3` | `STATA_MCP__MAX_ASYNC_DO` | 限制 MCP 异步 `stata_do` 的并发执行数量。超过上限的 MCP 调用会等待执行槽释放。仅在 `IS_ASYNC_DO=true` 时生效。 |
| `enable_data_info_url_guard` | Boolean | `false` | 无 | 对传给 `get_data_info` 的 URL 数据源启用 URL 校验和域名白名单检查。 |
| `data_info_allowed_url_domains` | List[str] | `[]` | 无 | URL guard 启用后允许访问的主机名列表。 |
| `enable_structured_log` | Boolean | `false` | 无 | 为 `read_log` 工具和 API 启用结构化日志解析。 |


## `IS_ASYNC_DO`

`IS_ASYNC_DO` 控制加载到该配置的 `stata_do` 执行路径是否使用异步执行器。

当值为 `false` 时，`stata_do` 保持原有同步执行路径。当值为 `true` 时，MCP server 会注册基于 `AsyncStataDo` 的异步实现。工具参数和返回结构保持不变。

可以通过配置文件启用：

```toml
[BETA]
IS_ASYNC_DO = true
```

也可以通过环境变量启用：

```bash
export STATA_MCP__IS_ASYNC_DO=true
```

Boolean 字符串值必须是 `true` 或 `false`。`on`、`off` 等值不会被接受，会回退到默认值。

当 MCP 层 `stata_do` 工具以及 API/CLI 一次性执行路径加载到 `IS_ASYNC_DO=true` 的配置时，都会启用异步执行。异步路径下工具参数仍然有效，包括 `timeout`、`enable_smcl`、`is_replace_log`、`log_file_name` 和 `read_log_when_error`。

## `MAX_ASYNC_DO`

`MAX_ASYNC_DO` 限制同时运行的 MCP 异步 `stata_do` 数量。

```toml
[BETA]
IS_ASYNC_DO = true
MAX_ASYNC_DO = 3
```

只有当机器资源和 Stata 许可证可以支撑更多并行 Stata 进程时，才建议调高这个值。该值必须是正整数。

`MAX_ASYNC_DO` 是 MCP server 侧的并发限制；它不限制独立的 API 或 CLI 调用。当 RAM 监控以 `IS_MONITOR=true` 启用时，单次异步执行会使用带监控的同步回退路径。需要监控的 MCP 运行建议使用保守并发，例如将 `MAX_ASYNC_DO` 设为 `1`。

## `enable_data_info_url_guard`

`enable_data_info_url_guard` 控制传给 `get_data_info` 的 URL 数据源是否受 beta URL guard 限制。

```toml
[BETA]
enable_data_info_url_guard = true
data_info_allowed_url_domains = ["example.com", "raw.githubusercontent.com"]
```

当该开关为 `false` 时，URL 数据源保持历史行为，直接交给 data handler，不校验 scheme、host、userinfo 或域名白名单。当该开关为 `true` 时，URL 必须使用 HTTPS，不能使用 IP 主机，不能包含 URL userinfo，并且主机名必须命中 `data_info_allowed_url_domains`。

## `data_info_allowed_url_domains`

`data_info_allowed_url_domains` 是启用 `get_data_info` URL guard 后使用的主机名白名单。

条目会匹配精确主机名及其子域名。例如，`example.com` 会允许 `example.com` 和 `data.example.com`。GitHub raw 内容是独立主机名，因此需要读取 GitHub raw 数据集时，请显式加入 `raw.githubusercontent.com`。

## `enable_structured_log`

`enable_structured_log` 控制 `read_log` 是否使用结构化 `StataLog` 解析器。

```toml
[BETA]
enable_structured_log = true
```

当该开关为 `false` 时，`read_log` 返回原始文件内容。当该开关为 `true` 时，支持的日志会通过 `StataLog` 解析为结构化格式（`full`、`core` 或 `dict`）。MCP、CLI 和 API 调用都使用同一个开关和相同的处理逻辑。

Boolean 字符串值必须是 `true` 或 `false`。`on`、`off` 等值不会被接受，会回退到默认值。
