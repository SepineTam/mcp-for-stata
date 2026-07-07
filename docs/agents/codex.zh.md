# 在 Codex 中使用

> **已废弃**：MCP-for-Stata 内置的 agent 模式自 v1.16.x 起已带 `FutureWarning`，将在后续版本移除。请改用 MCP server 模式（`stata-mcp server` 或 `stata-mcp install -c <客户端>`），并使用宿主 AI 客户端自带的 agent 能力。

本文介绍如何将 MCP-for-Stata 与 [Codex](https://github.com/openai/codex) 结合使用。Codex 是 OpenAI 提供的编码智能体，支持 CLI 和 VS Code 扩展两种形态。

> 系统要求：
> - [Stata](https://www.stata.com) 17+
> - [uv](https://docs.astral.sh/uv/getting-started/installation/) 或 Python 3.11+
> - Codex CLI 或 Codex VS Code 扩展

## 快速开始

首先检查 MCP-for-Stata 是否与当前设备兼容：

```bash
uvx stata-mcp doctor
```

然后将 MCP 服务添加到 Codex。安装器会优先调用 Codex CLI，不可用时回退到编辑 `~/.codex/config.toml`。

```bash
stata-mcp install -c codex
```

生成的 TOML 配置大致如下：

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
env = { STATA_MCP__CWD = "/path/to/project", STATA_CLI = "/Applications/Stata/StataMP" }
```

> 建议：请确保工作目录路径中不包含空格、表情符号或中文字符等特殊字符。

添加完成后重启 Codex，新的 MCP 工具即可生效。

## 手工配置

如果自动安装失败，可以直接创建或编辑 `~/.codex/config.toml`：

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
env = { STATA_MCP__CWD = "/absolute/path/to/project" }
```

Codex 注意事项：

- 顶层键为 `mcp_servers`（下划线），不是 `mcpServers`。
- 配置文件路径为 `~/.codex/config.toml`。
- 环境变量以 TOML 表语法内联书写。

## 项目结构

我们建议把所有项目放在同一目录下，例如 `~/Documents/StataProjects`。设置好 `STATA_MCP__CWD` 后，MCP-for-Stata 会在该目录下生成项目文件：

```text
my_first_project/            # 项目目录
├── .statamcp/               # MCP-for-Stata 生成的所有文件
│   ├── stata-mcp-dofile/    # do 文件
│   ├── stata-mcp-log/       # 日志文件
│   ├── stata-mcp-result/    # 某些命令（如 `outreg2`）的结果保存在此
│   └── stata-mcp-tmp/       # 临时文件，如数据信息描述
│   └── .gitignore           # git 忽略文件
└── CLAUDE.md                # 项目全局指令文件
```

## 命令变体

**固定版本**：

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp==1.16.2"]
```

**使用自定义项目目录**：

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = [
  "--directory",
  "/absolute/path/to/project",
  "stata-mcp"
]
env = { STATA_MCP__CWD = "/absolute/path/to/project" }
```

## 故障排除

- **配置未生效**：确认 `~/.codex/config.toml` 存在且 TOML 语法正确，然后重启 Codex。
- **工作目录不对**：为 `STATA_MCP__CWD` 使用绝对路径，相对路径可能解析到 Codex 的运行时目录。
- **找不到 Stata**：将 `STATA_CLI` 设置为 Stata 可执行文件的绝对路径。
