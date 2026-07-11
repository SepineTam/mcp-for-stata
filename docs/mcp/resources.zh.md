# MCP 资源

MCP-for-Stata 当前没有注册任何 MCP resource。

在 macOS 和 Linux 上，Stata 命令文档仍可通过 `help` MCP 工具获取。例如，
应调用 `help(cmd="regress")`，而不是请求 `help://stata/{cmd}` resource URI。

resource 形式因 URI 模板与当前 FastMCP 参数处理不兼容而暂时停用。在服务端
重新恢复注册之前，客户端不应展示或请求原来的 `help://stata/{cmd}` resource。

受支持的接口请参阅 [MCP 工具](tools.md#help)。
