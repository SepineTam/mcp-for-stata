# Beta 配置

Beta 选项是 `~/.statamcp/config.toml` 中 `[BETA]` 分区下的实验性开关。除非特别说明，默认都关闭；功能稳定前，这些配置未来可能调整。

## 推荐默认值

```toml
[BETA]
ENABLE_WRITE_DOFILE = false
IS_ASYNC_DO = false
MAX_ASYNC_DO = 3
```

## 参数表

| 参数 | 类型 | 默认值 | 环境变量 | 说明 |
| --- | --- | --- | --- | --- |
| `ENABLE_WRITE_DOFILE` | Boolean | `false` | `STATA_MCP__ENABLE_WRITE_DOFILE` | 注册已弃用的 `write_dofile` MCP 工具。除非旧工作流仍依赖该工具，否则建议保持关闭。 |
| `IS_ASYNC_DO` | Boolean | `false` | `STATA_MCP__IS_ASYNC_DO` | 注册异步版 `stata_do`，让多个 MCP 调用可以并行推进，不阻塞 server 事件循环。 |
| `MAX_ASYNC_DO` | Integer | `3` | `STATA_MCP__MAX_ASYNC_DO` | 限制异步 `stata_do` 的并发执行数量。超过上限的调用会等待执行槽释放。仅在 `IS_ASYNC_DO=true` 时生效。 |

## `ENABLE_WRITE_DOFILE`

`ENABLE_WRITE_DOFILE` 控制 MCP server 是否注册已弃用的 `write_dofile` 工具。

现代 AI 智能体通常已经具备直接写文件的能力，因此 `write_dofile` 一般是冗余工具。除非旧客户端或旧工作流仍然依赖它，否则建议保持 `false`。

可以通过配置文件启用：

```toml
[BETA]
ENABLE_WRITE_DOFILE = true
```

也可以通过环境变量启用：

```bash
export STATA_MCP__ENABLE_WRITE_DOFILE=true
```

## `IS_ASYNC_DO`

`IS_ASYNC_DO` 控制 MCP `stata_do` 工具是否使用异步执行器。

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

## `MAX_ASYNC_DO`

`MAX_ASYNC_DO` 限制同时运行的异步 `stata_do` 数量。

```toml
[BETA]
IS_ASYNC_DO = true
MAX_ASYNC_DO = 3
```

只有当机器资源和 Stata 许可证可以支撑更多并行 Stata 进程时，才建议调高这个值。该值必须是正整数。
