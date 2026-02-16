# 客户端配置

不同的 AI 客户端对 MCP 服务器有不同的配置格式。本文档记录了每个受支持客户端的配置细节。

## 标准配置模式

大多数 AI 客户端遵循以下基本模式：

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

但是，每个客户端在文件位置、格式或支持的功能方面可能略有不同。

## 客户端特定配置

### Claude Code

**配置方法**：CLI 命令或 `.mcp.json`

**全局安装**：
```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

**基于项目的安装**（推荐）：
```bash
cd ~/Documents/MyResearch
claude mcp add stata-mcp \
  --env STATA_MCP_CWD=$(pwd) \
  --scope project \
  -- uvx --directory $(pwd) stata-mcp
```

**配置文件**：`.mcp.json`（在项目目录中创建）

**格式**：JSON
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP_CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**独有功能**：
- ✅ 项目范围配置（`--scope project`）
- ✅ 环境变量注入（`--env`）
- ✅ 目录指定（`--directory`）
- ✅ 版本固定支持（`stata-mcp==1.13.0`）

### Claude Desktop

**配置文件**：`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

**格式**：JSON
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP_CWD": "/path/to/project",
        "STATA_CLI": "/Applications/Stata/StataMP"
      }
    }
  }
}
```

**独有功能**：
- ✅ 通过 `env` 对象支持环境变量
- ✅ 需要手动编辑配置文件

### Codex（VS Code 扩展）

**配置文件**：`~/.codex/config.toml`

**格式**：TOML
```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
```

**带环境变量**：
```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
env = { STATA_MCP_CWD = "/path/to/project" }
```

**独有功能**：
- ⚠️ 使用 TOML 格式而非 JSON
- ✅ 通过 `env` 表支持环境变量

### Cline

**配置文件**：`~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json`

**格式**：JSON
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

**独有功能**：
- ⚠️ 标准 JSON 格式
- ⚠️ 无特殊功能或扩展

### Cursor

**配置文件**：Cursor 设置（位置因操作系统而异）

**格式**：JSON
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "--directory",
        "/absolute/path/to/project",
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP_CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**已知问题**：
- ⚠️ 文件系统访问限制（可能无法访问 `Documents` 目录）
- ⚠️ **需要同时**在 args 中设置 `--directory` **和** `STATA_MCP_CWD` 环境变量（两者必须指向同一路径）
- ⚠️ 必须使用绝对路径（不支持相对路径）
- ✅ 支持环境变量

### Cherry Studio

**配置文件**：Cherry Studio 设置

**格式**：JSON（与 Claude Desktop 相同）

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

**独有功能**：
- ✅ 标准 MCP 配置
- ✅ 与 Claude Desktop 格式兼容

## 配置选项

### 命令变体

**标准**（使用最新版本）：
```json
"command": "uvx",
"args": ["stata-mcp"]
```

**固定版本**：
```json
"command": "uvx",
"args": ["stata-mcp==1.13.0"]
```

**带自定义目录**：
```json
"command": "uvx",
"args": [
  "--directory",
  "/path/to/project",
  "stata-mcp"
]
```

### 环境变量

#### 核心变量

| 变量                 | 用途                                | 示例                         |
|--------------------------|----------------------------------------|---------------------------------|
| `STATA_MCP_CWD`          | Stata 操作的工作目录 | `"/Users/user/research"`        |
| `STATA_CLI`              | 特定 Stata 可执行文件路径      | `"/Applications/Stata/StataMP"` |
| `STATA_MCP_MODEL`        | 智能体模式的 LLM 模型               | `"gpt-4"`                       |
| `STATA_MCP_API_KEY`      | LLM 提供商的 API 密钥               | `"sk-..."`                      |
| `STATA_MCP_API_BASE_URL` | 自定义 API 端点                    | `"https://api.openai.com/v1"`   |

#### 安全变量

| 变量              | 用途                          | 默认值 | 示例               |
|-----------------------|----------------------------------|---------|-----------------------|
| `STATA_MCP__IS_GUARD` | 启用安全守卫验证 | `true`  | `"true"` 或 `"false"` |

#### 监控变量

| 变量                | 用途               | 默认值         | 示例               |
|-------------------------|-----------------------|-----------------|-----------------------|
| `STATA_MCP__IS_MONITOR` | 启用 RAM 监控 | `false`         | `"true"` 或 `"false"` |
| `STATA_MCP__RAM_LIMIT`  | 最大 RAM（MB）     | `-1`（无限制） | `"8192"` 表示 8GB      |

#### 调试变量

| 变量                                | 用途                | 默认值                           | 示例                          |
|-----------------------------------------|------------------------|-----------------------------------|----------------------------------|
| `STATA_MCP__IS_DEBUG`                   | 启用调试模式      | `false`                           | `"true"` 或 `"false"`            |
| `STATA_MCP__LOGGING_ON`                 | 启用日志         | `true`                            | `"true"` 或 `"false"`            |
| `STATA_MCP__LOGGING_CONSOLE_HANDLER_ON` | 启用控制台日志 | `false`                           | `"true"` 或 `"false"`            |
| `STATA_MCP__LOGGING_FILE_HANDLER_ON`    | 启用文件日志    | `true`                            | `"true"` 或 `"false"`            |
| `STATA_MCP__LOG_FILE`                   | 自定义日志文件路径   | `~/.statamcp/stata_mcp_debug.log` | `"/var/log/stata-mcp/debug.log"` |

**JSON 格式**：
```json
"env": {
  "STATA_MCP_CWD": "/path/to/project",
  "STATA_CLI": "/path/to/stata"
}
```

**带安全和监控**：
```json
"env": {
  "STATA_MCP_CWD": "/path/to/project",
  "STATA_MCP__IS_GUARD": "true",
  "STATA_MCP__IS_MONITOR": "true",
  "STATA_MCP__RAM_LIMIT": "8192"
}
```

**TOML 格式**（Codex）：
```toml
env = { STATA_MCP_CWD = "/path/to/project" }
```

**带所有功能**：
```toml
env.STATA_MCP_CWD = "/path/to/project"
env.STATA_MCP__IS_GUARD = "true"
env.STATA_MCP__IS_MONITOR = "true"
env.STATA_MCP__RAM_LIMIT = "8192"
env.STATA_MCP__LOGGING_CONSOLE_HANDLER_ON = "true"
```

## 配置文件位置

| 客户端         | 配置文件位置                                                                                           | 格式 |
|----------------|----------------------------------------------------------------------------------------------------------------|--------|
| Claude Code    | `.mcp.json`（项目）或全局配置                                                                         | JSON   |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json`                                              | JSON   |
| Codex          | `~/.codex/config.toml`                                                                                         | TOML   |
| Cline          | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json` | JSON   |
| Cursor         | Cursor 设置目录                                                                                      | JSON   |
| Cherry Studio  | Cherry Studio 设置目录                                                                               | JSON   |

## 故障排除

### 配置未检测到

1. **验证文件路径**：检查配置文件是否存在于正确位置
2. **验证 JSON/TOML 语法**：使用在线验证器检查语法错误
3. **重启客户端**：大多数客户端在配置更改后需要重启
4. **检查日志**：在客户端日志中查找 MCP 服务器连接错误

### 路径问题

**问题**：Stata-MCP 无法访问项目文件

**解决方案**：
- 为 `STATA_MCP_CWD` 使用绝对路径
- 确保路径在客户端允许的目录内
- 检查客户端的文件系统访问权限

### 版本冲突

**问题**：加载了错误的 Stata-MCP 版本

**解决方案**：
- 清除 Python 包缓存：`pip cache purge stata-mcp`
- 固定特定版本：`uvx stata-mcp==1.13.0`
- 使用 `uvx --refresh stata-mcp` 强制刷新

## 最佳实践

1. **使用项目范围配置**（如果可用）（Claude Code）
2. **在生产环境中固定版本**
3. **为工作目录设置绝对路径**
4. **在添加到客户端之前用 `uvx stata-mcp --usable` 测试配置**
5. **为团队协作文档化自定义配置**

## 其他资源

- [使用指南](usage.md) - 全面使用示例
- [概述](overview.md) - 架构和设计
- [MCP 工具](mcp/tools.md) - 可用工具参考
