# 客户端配置

不同的 AI 客户端对 MCP 服务器有不同的配置格式。本文档记录了每个受支持客户端的配置细节。

## 一键安装

绝大多数客户端可以由 `stata-mcp install` 自动写入配置：

```bash
# 单个客户端（合法的 client key 见下表）
stata-mcp install -c <client>

# 一次安装到所有受支持的客户端
stata-mcp install --all

# 自定义配置文件路径，可选嵌套 JSON 键
stata-mcp install -c <client> --json-file /path/to/config.json
stata-mcp install -c <client> --json-file /path/to/config.json --json-index parent.child
```

支持的 client key：`claude`、`cc`（别名 `claude-code`）、`gemini`、`cursor`、`cline`、`codex`、`opencode`、`openclaw`、`hermes`（别名 `hermes-agent`）。

下方手工配置示例仅在自动安装失败、客户端尚未被 installer 支持（例如 Cherry Studio），或者需要完全控制最终配置时使用。

## 标准配置模式

大多数 AI 客户端遵循以下基本 JSON 模式：

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

每个客户端可能在文件位置、JSON 键路径或格式（JSON / TOML / YAML）上略有不同。

## 客户端特定配置

### Claude Desktop

**配置方式**：手动编辑配置文件（无官方 CLI）。

**配置文件**：
- macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows：`%APPDATA%/Claude/claude_desktop_config.json`
- Linux：Anthropic 暂未提供 Linux 版。

**格式**：JSON，顶层键 `mcpServers`。

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/path/to/project",
        "STATA_CLI": "/Applications/Stata/StataMP"
      }
    }
  }
}
```

**独有功能**：
- 通过 `env` 对象注入环境变量。
- 编辑后需要彻底重启客户端。

### Claude Code

**配置方式**：优先调用 `claude mcp add` CLI；CLI 不可用时回退写入 `~/.claude.json`。

**配置文件**：`~/.claude.json`（回退）或项目目录下的 `.mcp.json`（使用 `--scope project`）。

**格式**：JSON，顶层键 `mcpServers`。

**全局安装**：
```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

**项目范围安装**：
```bash
cd ~/Documents/MyResearch
claude mcp add stata-mcp \
  --env STATA_MCP__CWD=$(pwd) \
  --scope project \
  -- uvx --directory $(pwd) stata-mcp
```

**对应的文件形式**：
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**独有功能**：
- 通过 `--scope project` 实现项目范围配置。
- 通过 `--env` 注入环境变量。
- 通过 `uvx --directory` 固定工作目录。
- 支持版本固定（如 `stata-mcp==1.16.2`）。

### Gemini CLI

**配置方式**：手动编辑配置文件。Installer key：`gemini`。

**配置文件**：`~/.gemini/settings.json`。

**格式**：JSON，顶层键 `mcpServers`。

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**独有功能**：
- 与 Claude Desktop 共享同一 JSON schema，可在 `mcpServers` 兼容客户端间复用。

### Cursor

**配置方式**：手动编辑配置文件。Installer 会自动注入 `--directory` 和 `STATA_MCP__CWD`，并指向 `~/Documents`，以绕过 Cursor 沙箱。

**配置文件**：`~/.cursor/mcp.json`。

**格式**：JSON，顶层键 `mcpServers`。

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
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**已知问题 / 独有功能**：
- 文件系统沙箱可能阻止访问 `~/Documents`，必须使用允许目录内的绝对路径。
- `--directory`（位于 `args`）与 `STATA_MCP__CWD`（位于 `env`）必须指向同一路径。
- 不支持相对路径。

### Cline（VS Code 扩展）

**配置方式**：手动编辑 VS Code globalStorage 内的配置文件。

**配置文件**：
- macOS：`~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Linux：`~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Windows：`%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

**格式**：JSON，顶层键 `mcpServers`。

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
- 标准 `mcpServers` schema，无 Cline 专属扩展。

### Codex CLI

**配置方式**：优先调用 `codex mcp add` CLI；CLI 不可用时回退追加到 `~/.codex/config.toml`。

**配置文件**：`~/.codex/config.toml`。

**格式**：TOML，顶层键 `mcp_servers`。

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
env = { STATA_MCP__CWD = "/path/to/project" }
```

**独有功能**：
- 本表中唯一使用 TOML 的客户端。
- 注意键为下划线写法 `mcp_servers`，不是 `mcpServers`。

### OpenCode

**配置方式**：手动编辑配置文件。Installer key：`opencode`。

**配置文件**：`~/.config/opencode/opencode.json`。

**格式**：JSON，使用 OpenCode 自定义 schema，顶层键 `mcp`。

```json
{
  "mcp": {
    "stata-mcp": {
      "type": "local",
      "command": ["uvx", "stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

**独有功能**：
- 使用 `type: "local"`，并将 `command` 写成数组（命令与参数合并）。
- 顶层键为 `mcp`，而非 `mcpServers`。

### OpenClaw

**配置方式**：优先调用 `openclaw mcp set` CLI；CLI 不可用时回退写入 `~/.openclaw/openclaw.json`。

**配置文件**：`~/.openclaw/openclaw.json`。

**格式**：JSON，嵌套键路径 `mcp.servers`。

```json
{
  "mcp": {
    "servers": {
      "stata-mcp": {
        "command": "uvx",
        "args": ["stata-mcp"],
        "env": {
          "STATA_MCP__CWD": "/absolute/path/to/project"
        }
      }
    }
  }
}
```

**独有功能**：
- 在 stata-mcp v1.16.3 中新增。
- 配置位于两层嵌套（`mcp.servers.<name>`）；使用 `--json-file` 时需配合 `--json-index mcp.servers`。

### Hermes Agent

**配置方式**：优先调用 `hermes mcp add` CLI；CLI 不可用时回退追加到 `~/.hermes/config.yaml`。Installer key：`hermes`、`hermes-agent`。

**配置文件**：`~/.hermes/config.yaml`。

**格式**：YAML，顶层键 `mcp_servers`。

```yaml
mcp_servers:
  stata-mcp:
    command: "uvx"
    args: ["stata-mcp"]
    env:
      STATA_MCP__CWD: "/absolute/path/to/project"
```

**独有功能**：
- 本表中唯一的 YAML 目标；installer 采用简化的文本写入而非完整 YAML 解析器。
- 下划线键 `mcp_servers` 与 Codex 命名风格一致。

### Cherry Studio（仅手动配置）

**配置方式**：`stata-mcp install` 不支持，用户需自行编辑 Cherry Studio 的设置文件。

**配置文件**：Cherry Studio 设置目录（路径因平台而异）。

**格式**：JSON，与 Claude Desktop schema 兼容。

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
- 仅支持手工配置，无 installer 支持。
- 复用标准 `mcpServers` schema。

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
"args": ["stata-mcp==1.16.2"]
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

| 变量                     | 用途                                                       | 示例                            |
|--------------------------|------------------------------------------------------------|---------------------------------|
| `STATA_MCP__CWD`         | Stata 操作的工作目录                                       | `"/Users/user/research"`        |
| `STATA_MCP_CWD`          | `STATA_MCP__CWD` 的旧别名（保留向后兼容）                  | `"/Users/user/research"`        |
| `STATA_CLI`              | 特定 Stata 可执行文件路径                                  | `"/Applications/Stata/StataMP"` |
| `STATA_MCP_MODEL`        | 仅 deprecated 的 agent 模式使用，MCP server 模式无需配置   | `"gpt-4"`                       |
| `STATA_MCP_API_KEY`      | 仅 deprecated 的 agent 模式使用，MCP server 模式无需配置   | `"sk-..."`                      |
| `STATA_MCP_API_BASE_URL` | 仅 deprecated 的 agent 模式使用，MCP server 模式无需配置   | `"https://api.openai.com/v1"`   |

#### 安全变量

| 变量                  | 用途              | 默认值 | 示例                  |
|-----------------------|-------------------|--------|-----------------------|
| `STATA_MCP__IS_GUARD` | 启用安全守卫验证  | `true` | `"true"` 或 `"false"` |

#### 监控变量

| 变量                    | 用途           | 默认值          | 示例                  |
|-------------------------|----------------|-----------------|-----------------------|
| `STATA_MCP__IS_MONITOR` | 启用 RAM 监控  | `false`         | `"true"` 或 `"false"` |
| `STATA_MCP__RAM_LIMIT`  | 最大 RAM（MB） | `-1`（无限制）  | `"8192"` 表示 8GB     |

#### 调试变量

| 变量                                    | 用途             | 默认值                            | 示例                             |
|-----------------------------------------|------------------|-----------------------------------|----------------------------------|
| `STATA_MCP__IS_DEBUG`                   | 启用调试模式     | `false`                           | `"true"` 或 `"false"`            |
| `STATA_MCP__LOGGING_ON`                 | 启用日志         | `true`                            | `"true"` 或 `"false"`            |
| `STATA_MCP__LOGGING_CONSOLE_HANDLER_ON` | 启用控制台日志   | `false`                           | `"true"` 或 `"false"`            |
| `STATA_MCP__LOGGING_FILE_HANDLER_ON`    | 启用文件日志     | `true`                            | `"true"` 或 `"false"`            |
| `STATA_MCP__LOG_FILE`                   | 自定义日志路径   | `~/.statamcp/stata_mcp_debug.log` | `"/var/log/stata-mcp/debug.log"` |

**JSON 格式**：
```json
"env": {
  "STATA_MCP__CWD": "/path/to/project",
  "STATA_CLI": "/path/to/stata"
}
```

**带安全和监控**：
```json
"env": {
  "STATA_MCP__CWD": "/path/to/project",
  "STATA_MCP__IS_GUARD": "true",
  "STATA_MCP__IS_MONITOR": "true",
  "STATA_MCP__RAM_LIMIT": "8192"
}
```

**TOML 格式**（Codex）：
```toml
env = { STATA_MCP__CWD = "/path/to/project" }
```

**带所有功能**：
```toml
env.STATA_MCP__CWD = "/path/to/project"
env.STATA_MCP__IS_GUARD = "true"
env.STATA_MCP__IS_MONITOR = "true"
env.STATA_MCP__RAM_LIMIT = "8192"
env.STATA_MCP__LOGGING_CONSOLE_HANDLER_ON = "true"
```

## 配置文件位置

| 客户端         | 配置文件位置                                                                                                    | 格式 |
|----------------|-----------------------------------------------------------------------------------------------------------------|------|
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）/ `%APPDATA%/Claude/...`（Windows）   | JSON |
| Claude Code    | `~/.claude.json`（回退）或项目目录下的 `.mcp.json`                                                              | JSON |
| Gemini CLI     | `~/.gemini/settings.json`                                                                                       | JSON |
| Cursor         | `~/.cursor/mcp.json`                                                                                            | JSON |
| Cline          | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` | JSON |
| Codex CLI      | `~/.codex/config.toml`                                                                                          | TOML |
| OpenCode       | `~/.config/opencode/opencode.json`                                                                              | JSON |
| OpenClaw       | `~/.openclaw/openclaw.json`                                                                                     | JSON |
| Hermes Agent   | `~/.hermes/config.yaml`                                                                                         | YAML |
| Cherry Studio  | Cherry Studio 设置目录（仅手动）                                                                                | JSON |

## 故障排除

### 配置未检测到

1. **验证文件路径**：检查配置文件是否存在于正确位置。
2. **验证 JSON/TOML/YAML 语法**：使用在线验证器检查语法错误。
3. **重启客户端**：大多数客户端在配置更改后需要重启。
4. **检查日志**：在客户端日志中查找 MCP 服务器连接错误。

### 路径问题

**问题**：Stata-MCP 无法访问项目文件。

**解决方案**：
- 为 `STATA_MCP__CWD` 使用绝对路径。
- 确保路径在客户端允许的目录内。
- 检查客户端的文件系统访问权限。

### 版本冲突

**问题**：加载了错误的 Stata-MCP 版本。

**解决方案**：
- 清除 Python 包缓存：`pip cache purge stata-mcp`。
- 固定特定版本：`uvx stata-mcp==1.16.2`。
- 强制刷新：`uvx --refresh stata-mcp`。

## 最佳实践

1. **使用项目范围配置**（如可用）（Claude Code）。
2. **在生产环境中固定版本**。
3. **为工作目录设置绝对路径**。
4. **在添加到客户端之前用 `uvx stata-mcp doctor` 测试配置**。
5. **为团队协作文档化自定义配置**。

## 其他资源

- [使用指南](usage.md) - 全面使用示例
- [概述](overview.md) - 架构和设计
- [MCP 工具](mcp/tools.md) - 可用工具参考
