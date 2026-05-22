# MCP.Resources

MCP-for-Stata 提供用于访问 Stata 文档和帮助内容的 MCP 资源。

---
## help

> **平台支持**：仅限 macOS 和 Linux（不支持 Windows）

```python
@stata_mcp.resource(
    uri="help://stata/{cmd}",
    name="help",
    description="Get help for a Stata command"
)
def help(cmd: str) -> str:
    ...
```

**资源 URI**：`help://stata/{cmd}`

**输入参数**：
- `cmd`：Stata 命令名（必填，如 "regress"、"describe"、"xtset"、"merge"）

**返回结构**：
包含 Stata 帮助文本输出的字符串。可能包含缓存状态前缀：
- `"Cached result for {cmd}\n{help_text}"` - 从缓存检索
- `"Saved result for {cmd}\n{help_text}"` - 从项目缓存检索
- `"{help_text}"` - 来自 Stata 的新结果
- `"No help found for the command in Stata ado locally: {cmd}"` - 命令未找到

**操作示例**：
```python
# 回归命令
help("regress")
help("logit")
help("probit")

# 面板数据命令
help("xtset")
help("xtreg")
help("xtmixed")

# 数据管理
help("merge")
help("reshape")
help("collapse")

# 时间序列
help("tsset")
help("arima")
help("varsoc")
```

**实现架构**：

帮助资源在 MCP 框架中实现双重注册模式，既作为资源（可通过 `help://stata/{cmd}` 以 URI 寻址）又作为可执行工具。这种双重注册启用灵活的访问模式：客户端可以将其作为标准工具调用，或通过资源协议访问。

`StataHelp` 类通过三层缓存策略管理帮助文本检索：

1. **项目级缓存**（`STATA_MCP__SAVE_HELP`，默认：`true`）：
   - 将帮助文本存储在 `stata-mcp-tmp/help__{cmd}.txt`
   - 在项目目录内跨会话持久化
   - 检索优先级最高

2. **全局缓存**（`STATA_MCP__CACHE_HELP`，默认：`true`）：
   - 将帮助文本存储在 `~/.statamcp/help/help__{cmd}.txt`
   - 在所有项目间共享
   - 项目缓存未命中时的次要优先级

3. **实时 Stata 执行**：
   - 以 `help {cmd}` 命令调用 Stata CLI
   - 捕获 stdout 作为返回值
   - 当两层缓存都未命中时回退到此层

**缓存失效**：
不存在自动的基于 TTL 的过期。缓存失效需要：
- 手动删除缓存文件（`rm ~/.statamcp/help/help__{cmd}.txt`）
- 设置环境变量 `STATA_MCP__CACHE_HELP=false` 以禁用缓存
- 设置环境变量 `STATA_MCP__SAVE_HELP=false` 以禁用项目级缓存

**错误检测**：
帮助系统通过将 Stata 输出与标准错误消息模板比较来检测命令是否存在：
```
help {cmd}
help for {cmd} not found
try help contents or search {cmd}
```

如果输出匹配此模式，系统抛出异常，指示命令在本地安装的 ado 文件中未找到。此行为在缓存未命中后、缓存新结果之前发生。

**平台考虑**：
- **macOS/Linux**：完全支持缓存和实时 Stata 执行
- **Windows**：由于 Windows 平台上 Stata CLI 的限制而不支持

**性能优化**：
对于频繁访问的命令（如 `regress`、`xtreg`），启用 `STATA_MCP__CACHE_HELP=true` 以避免重复的 Stata 调用。首次执行查询 Stata（约 50-200ms，取决于 Stata 启动时间），后续查询从缓存返回（约 1-5ms 文件读取）。

**使用说明**：
- 帮助文本语言取决于 Stata 安装区域设置
- 多语言支持需要单独的 Stata 安装或区域设置重新配置
- 缓存文件是纯文本 UTF-8 编码，允许手动检查或编辑
- 资源 URI 模式 `help://stata/{cmd}` 通过 MCP 资源协议启用程序化访问

**环境变量**：

| 变量 | 默认值 | 描述 |
|----------|---------|-------------|
| `STATA_MCP__CACHE_HELP` | `true` | 在 `~/.statamcp/help/` 启用全局缓存 |
| `STATA_MCP__SAVE_HELP` | `true` | 在 `stata-mcp-tmp/` 启用项目级缓存 |

**与工具的集成**：
帮助资源在多种工作流程中与 MCP-for-Stata 工具集成：
- **执行前验证**：在生成 do 文件前检查命令语法
- **错误诊断**：理解 Stata 执行中的错误消息
- **学习辅助**：在分析会话期间提供上下文帮助
- **代码补全**：建议有效的命令选项和语法

**示例工作流程**：
```python
# 1. 检查命令是否存在
help_result = help("ivregress2")
if "not found" not in help_result:
    # 2. 使用该命令生成 do 文件
    write_dofile("ivregress2 y x1 x2, robust")

    # 3. 执行 do 文件
    stata_do("/path/to/do/file")
```

---
