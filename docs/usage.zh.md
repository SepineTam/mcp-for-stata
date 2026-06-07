# 使用指南

> **希望未来不再有[star war](https://www.aeaweb.org/articles?id=10.1257/app.20150044)。** - 让科研从 reg monkeys 变成有价值的研究。

本指南介绍如何在不同环境和智能体中集成和使用 MCP-for-Stata。

## 前提条件

在使用 MCP-for-Stata 之前，请确保你有：
- 已安装 **Stata** 17+ 并具有有效许可证
- **uv** 包管理器或 Python 3.11+
- 已安装或可通过 `uvx` 使用 **MCP-for-Stata**

验证你的设置：
```bash
uvx stata-mcp doctor
```

## 新功能
<details markdown="1">
<summary><strong>点击展开</strong></summary>

### 🔒 安全守卫系统

MCP-for-Stata 现在包含自动安全验证以防止危险命令：

```python
# 默认自动启用
# 阻止：!, shell, erase, rm, run, do, include 等

# 安全代码正常执行
result = stata_mcp.stata_do("""
    sysuse auto
    regress price mpg weight
""")

# 危险代码被阻止
result = stata_mcp.stata_do("""
    ! rm -rf /  # ❌ 被安全守卫阻止
""")
# Error: Security validation failed
```

**配置**：
```toml
# ~/.statamcp/config.toml
[SECURITY]
IS_GUARD = true  # 默认：true
```

**环境变量**：
```bash
export STATA_MCP__IS_GUARD=true
```

详情请参阅[安全文档](security.md)。

### 📊 RAM 监控系统

监控和控制 Stata 进程内存使用：

```python
# 启用监控，设置 8GB 限制
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=8192

# 如果 RAM 超过限制，进程将被自动终止
result = stata_mcp.stata_do(large_analysis_code)
```

**配置**：
```toml
[MONITOR]
IS_MONITOR = false   # 默认：false
MAX_RAM_MB = -1      # -1 = 无限制，正值 = 以 MB 为单位的限制
```

详情请参阅[监控文档](monitoring.md)。

### ⚙️ 统一配置系统

通过 TOML 文件或环境变量配置所有设置：

**优先级**：环境变量 > 配置文件 > 默认值

```bash
# 使用环境变量快速设置
export STATA_MCP__CWD="/projects/my-analysis"
export STATA_MCP__IS_GUARD=true
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=16384
```

**或使用配置文件**（`~/.statamcp/config.toml`）：
```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = false
LOGGING_FILE_HANDLER_ON = true

[SECURITY]
IS_GUARD = true

[PROJECT]
WORKING_DIR = ""

[MONITOR]
IS_MONITOR = false
MAX_RAM_MB = -1
```

详情请参阅[配置文档](configuration.md)。

</details>

## CLI 命令

MCP-for-Stata 在 MCP 服务器之外还提供了多个实用命令。

```bash
# 运行诊断
stata-mcp doctor

# 安装已启用并加入白名单的 ado 包
stata-mcp tool ado-install reghdfe --yes

# 查看数据集
stata-mcp tool data-info /path/to/data.dta

# 更新到最新版本
stata-mcp update

# 基于 Docker 的沙盒安装
stata-mcp sandbox-install -l /path/to/stata.lic
```

完整文档请参阅 [CLI 参考](cli.md)。

## 在 Python 中使用

### 使用 OpenAI Agents SDK

MCP-for-Stata 可以使用 OpenAI Agents SDK 与 Python 智能体集成。

#### 方法 1：直接 MCP 服务器集成

```python
# !uv pip install openai-agents
from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams

# 创建 MCP 服务器连接
stata_mcp_server = MCPServerStdio(
    name="MCP-for-Stata",
    params=MCPServerStdioParams(
        command="uvx",
        args=["stata-mcp"]
    )
)

# 使用 MCP 服务器初始化智能体
agent = Agent(
    name="Research Assistant",
    instructions="You are a helpful economics research assistant.",
    mcp_servers=[stata_mcp_server]
)

# 运行分析
result = await Runner.run(
    agent,
    input="Run a regression: log(wage) ~ age, educ, exper with nlsw88 data and report coefficients."
)

print(f"Result: \n> {result.final_output}")
```

## 在编码智能体中使用

MCP-for-Stata 设计用于与现代 AI 编码智能体无缝集成。以下是流行平台的测试配置。

### Claude 插件（推荐）

我们推荐使用官方插件以获得最佳体验。因此在 Claude Code 中使用 MCP-for-Stata 的最简单方式是通过官方插件，它同时提供 MCP 服务器和 LSP 集成：

```bash
# 添加市场注册表
claude plugin marketplace add sepinetam/stata-mcp

# 全局安装插件
claude plugin install stata-toolbox -s user
```

如果你想与合作伙伴一起工作，也可以这样安装：
```bash
# claude plugin marketplace add sepinetam/stata-mcp

claude plugin install stata-toolbox@stata-plugin-lib -s project
```

然后，你可以在 `.claude/settings.json` 中找到该插件
```json
{
  "enabledPlugins": {
    "stata-toolbox@stata-plugin-lib": true
  }
}
```

**插件功能：**
- ✅ 一键安装
- ✅ MCP 服务器 + LSP 一起配置
- ✅ 预配置的最优 Stata LSP 设置

完整的插件文档请参阅 [Claude 插件指南](claude-plugin.md)。

### Claude Code 的手动 MCP 配置

或者，手动配置 MCP 服务器：

Claude Code 是我们推荐的 AI 辅助实证研究解决方案。

#### 全局安装

```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

#### 基于项目的配置

对于研究项目，使用项目范围配置：

```bash
cd ~/Documents/MyResearchProject
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

#### 指定版本

要使用特定版本：

```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp==1.16.3
```

**验证安装：**
```bash
claude mcp list
```

**基于项目配置的优势：**
- 每个研究项目隔离 MCP-for-Stata 环境
- 项目目录内自动路径管理
- 无全局配置冲突

### Codex（VS Code 扩展）

对于使用 Codex 扩展的 VS Code 用户，编辑 `~/.codex/config.toml`：

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
```

### Cline

对于 Cline 用户，编辑位于 `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json` 的 MCP 配置文件：

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### Cursor

**注意：** Cursor 的文件系统访问受限。默认情况下 MCP 服务器可能无法访问 `Documents` 目录。如果遇到问题，请尝试此配置：

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP__CWD": "/path/to/your/project"
      }
    }
  }
}
```

将 `/path/to/your/project` 替换为你的实际研究目录。

## 在 AI 客户端中使用

大多数 AI 客户端遵循标准的 MCP 服务器配置格式。以下是通用配置模式：

### 标准配置（Claude Desktop、Cherry Studio 等）

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### 带自定义工作目录的配置

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP__CWD": "/path/to/working/directory"
      }
    }
  }
}
```

### 带环境变量的配置

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP__CWD": "/path/to/working/directory",
        "STATA_MCP_MODEL": "gpt-4",
        "STATA_MCP_API_KEY": "your-api-key",
        "STATA_MCP_API_BASE_URL": "https://api.openai.com/v1"
      }
    }
  }
}
```

## 环境变量

MCP-for-Stata 支持多个环境变量进行自定义：

| 变量 | 描述 | 默认值 |
|----------|-------------|---------|
| `STATA_MCP__CWD` | Stata 操作的当前工作目录 | `./` |
| `STATA_MCP_API_BASE_URL` | API 请求的基础 URL | `https://api.openai.com/v1` |
| `STATA_MCP_CLIENT` | 客户端类型标识符 | - |

## 故障排除

### 常见问题

**"Stata not found"**
- 验证 Stata 安装：`which stata`（macOS/Linux）或检查 PATH
- 使用 `StataFinder` 配置指南设置自定义路径

**"Module not found" 错误**
- 确保依赖已安装：`uv pip install openai-agents stata-mcp`
- 检查 Python 版本：需要 3.11+

**MCP 服务器无法连接**
- 验证 `uvx stata-mcp doctor` 通过所有检查
- 检查客户端的 MCP 服务器日志
- 使用 stdio 传输（默认）测试

### 调试模式

启用详细日志：
```bash
export STATA_MCP__IS_DEBUG=true
uvx stata-mcp doctor --verbose
```

## 最佳实践

1. **项目结构**：使用项目范围的 MCP 配置以获得更好的隔离
2. **版本固定**：在生产环境中指定确切版本：`stata-mcp==1.16.3`
3. **数据管理**：保持原始数据不可变；使用 processing/ 目录
4. **API 密钥**：使用环境变量，切勿硬编码凭证

## 其他资源

- [概述](overview.md) - 架构和设计
- [工具文档](tools.md) - 可用的 MCP 工具
- [客户端指南](agents/index.md) - 客户端特定文档
- [GitHub 仓库](https://github.com/sepinetam/mcp-for-stata) - 源代码和问题

## 贡献

发现错误或有功能请求？请[提交 issue](https://github.com/sepinetam/mcp-for-stata/issues/new) 或发送 pull request。
