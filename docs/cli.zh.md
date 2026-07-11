# CLI 参考

MCP-for-Stata 提供命令行界面（CLI）用于各种操作，包括启动 MCP 服务器以及安装到不同的 AI 客户端。

## 安装

验证您的安装：

```bash
stata-mcp --version
```

运行诊断检查系统健康状况：

```bash
stata-mcp doctor
```

> **注意：** `--usable` 自 v1.14.3 起已弃用。在当前版本中仍可使用，但 v1.16+ 起推荐改用 `stata-mcp doctor`，该选项可能在后续主版本中被移除。

## 命令

### 全局配置覆盖

大多数用户应使用 `~/.statamcp/config.toml`，并按需添加
`./.statamcp/config.toml` 项目配置。CLI 也提供一个面向开发调试的配置覆盖参数：

```bash
stata-mcp -c /path/to/debug-config.toml server
stata-mcp server --config /path/to/debug-config.toml
```

> **注意：** 不建议在日常使用中使用 `-c/--config`。提供该参数后，
> Stata-MCP 只读取这个文件，并忽略用户级/项目级配置栈。
> 在 Linux 上，`/etc/statamcp/config.toml` 仍然拥有最高优先级，可以覆盖这个调试配置。
> `install` 和 `verify` 子命令保留原有的 `-c/--client` 含义；
> 如果这些子命令需要调试配置路径，请使用 `--config`。

### 启动 MCP 服务器

使用不同的传输方式启动 MCP 服务器：

```bash
# 使用 stdio 传输启动（默认）
stata-mcp

# 明确指定传输方式
stata-mcp -t stdio
stata-mcp -t sse
stata-mcp -t http
```

#### Server 子命令

使用 `server` 子命令控制注册哪些 MCP 工具：

```bash
# 标准工具，stdio 传输（与裸命令相同）
stata-mcp server

# 仅核心工具（stata_do、get_data_info、help）
stata-mcp server --core

# 标准工具，HTTP 传输
stata-mcp server --all -t http

# 标准工具加高风险 ado 安装
stata-mcp server --unsafe

# 核心工具，SSE 传输
stata-mcp server --core -t sse
```

**工具配置（Profile）：**
- `--all` - 注册标准工具，但不包含高风险安装（默认）
- `--core` - 仅注册核心工具：`stata_do`、`get_data_info`、`help`
- `--unsafe` - 增加高风险工具 `ado_package_install`

**传输选项：**
- `stdio` - 标准输入/输出（默认）
- `sse` - Server-Sent Events
- `http` - HTTP 传输（自动转换为 streamable-http）

### 诊断检查（doctor）

运行健康检查以诊断潜在问题：

```bash
# 运行所有检查
stata-mcp doctor

# 显示每项检查的详细信息
stata-mcp doctor --verbose

# 以 JSON 格式输出
stata-mcp doctor --json

# 仅运行特定检查（可重复）
stata-mcp doctor --check stata --check python

# 仅预览清理动作但不实际删除（仅 cleanup 类检查）
stata-mcp doctor --check cleanup --dry-run
```

常见的检查名包括 `stata`、`python` 和 `cleanup`。`--dry-run` 仅对 `cleanup` 类检查生效，用于预览将要清理的内容而不真正删除；其他检查会忽略该参数。

### 验证安装（verify）

检查 `stata-mcp` 是否已安装在目标 MCP 客户端或配置文件中。该子命令只读，不会修改任何配置文件。

```bash
# 检查支持的客户端
stata-mcp verify -c claude

# 检查自定义 JSON 配置文件
stata-mcp verify -f ~/.cursor/mcp.json

# 检查嵌套配置路径
stata-mcp verify -f ~/.openclaw/openclaw.json --index mcp.servers

# 使用自定义条目键
stata-mcp verify -f ~/.codex/config.toml --index mcp_servers --key stata-mcp
```

同时传入 `-c` 和 `-f` 时，`-c` 优先。

### 更新（update）

将 stata-mcp 更新到最新版本：

```bash
# 自动检测安装方式并更新
stata-mcp update

# 检查是否有新版本可用
stata-mcp update --check

# 显示检测到的方式和可用更新但不执行
stata-mcp update --dry-run

# 强制指定更新方式
stata-mcp update --method pip       # pip install
stata-mcp update --method uv-tool   # uv tool upgrade
stata-mcp update --method homebrew  # brew upgrade
```

**更新方式：** `auto`（默认）、`pip`、`uv-tool`、`homebrew`

> **1.17.2 之前通过 uv tool 安装的用户注意：** 早期版本存在检测 bug，`stata-mcp update` 可能误判为 pip 导致更新失败。请先手动运行一次 `uv tool upgrade stata-mcp` 升级到 1.17.2 或更高版本，之后 `stata-mcp update` 即可正常使用。

### 本地工具命令

直接从 CLI 运行由 API 模块驱动的 Stata 工具：

```bash
# 从 SSC 安装已批准的 ado 包
stata-mcp tool ado-install reghdfe --yes

# 运行 do-file，仅在执行失败时读取 log
stata-mcp tool do /path/to/analysis.do --is-read-log true

# 使用自定义日志名，并保留已有同名日志
stata-mcp tool do /path/to/analysis.do --log-file-name quarterly_results --is-replace-log false

# 执行超过五分钟时终止 do-file
stata-mcp tool do /path/to/analysis.do --timeout 300

# 通过一次性的 API helper 读取 Stata help
stata-mcp tool help regress

# 查看支持的数据集元信息
stata-mcp tool data-info /path/to/data.dta

# 读取生成的日志文件
stata-mcp tool read-log /path/to/output.log
```

工具子命令：
- `stata-mcp tool ado-install <package_name> [-y|--yes] [--source ssc|net|github]`
- `stata-mcp tool do <dofile_path> [--log-file-name <name>] [--is-read-log true|false] [--is-replace-log true|false] [--enable-smcl true|false] [--timeout <seconds>]`
- `stata-mcp tool help <command> [--replace true|false]`
- `stata-mcp tool data-info <data_path> [--vars-list var1 var2 ...]`
- `stata-mcp tool read-log <log_path> [--output-format full|core|dict]`

> 说明：`--is-read-log true` 只会在底层执行报告 Stata 返回码错误时返回日志内容。

> `ado-install` 未传入 `-y` 或 `--yes` 时会进行交互确认。SSC 和 net 包名只能
> 包含 ASCII 字母与数字。GitHub 仓库必须命中精确仓库白名单，并在安装前人工查验。

### 配置管理

查看和更新本地 CLI 配置（位于 `~/.statamcp/config.toml`）：

```bash
# 打印整个配置文件内容
stata-mcp config

# 查看单个键值（cli 是 STATA.STATA_CLI 的简写）
stata-mcp config show cli
stata-mcp config show STATA.STATA_CLI
stata-mcp config show SECURITY.IS_GUARD

# 显式设置 STATA_CLI
stata-mcp config set cli /path/to/stata

# 自动检测 STATA_CLI 并持久化保存
stata-mcp config set cli

# 通过 dot-notation 编辑已存在的键
stata-mcp config edit STATA.STATA_CLI /path/to/stata
stata-mcp config edit SECURITY.IS_GUARD false
```

`set` 子命令目前只接受 `cli` 这一个键。`edit` 子命令接受配置文件中任意已存在的 `Section.Key`，对未定义的键会拒绝写入。

### 安装到 AI 客户端

将 MCP-for-Stata 安装到各种 AI 编程助手：

```bash
# 安装到所有支持的客户端（不带 -c 和 --json-file 时等价于 --all）
stata-mcp install

# 安装到特定客户端
stata-mcp install -c claude-code
stata-mcp install -c cursor

# 显式安装到所有客户端
stata-mcp install --all

# 安装到自定义 JSON 配置文件
stata-mcp install --json-file /path/to/config.json

# 安装到自定义 JSON 配置文件的嵌套键路径
stata-mcp install --json-file /path/to/config.json --json-index mcp.servers
```

**支持的客户端：**

| 客户端 ID | 目标 | 别名 |
|-----------|------|------|
| `claude` | Claude Desktop | |
| `claude-code` | Claude Code | `cc` |
| `cursor` | Cursor Editor | |
| `cline` | Cline（VS Code 扩展） | |
| `codex` | Codex | |
| `gemini` | Gemini CLI | |
| `opencode` | OpenCode | |
| `openclaw` | OpenClaw | |
| `hermes` | Hermes | `hermes-agent` |

## 选项

### Server 选项

| 选项 | 描述 |
|--------|-------------|
| `--core` | 仅注册核心工具（stata_do、get_data_info、help） |
| `--all` | 注册标准工具，但不包含高风险安装（默认） |
| `--unsafe` | 增加高风险 ado 安装；要求显式安全配置 |
| `-t`, `--transport` | MCP 传输方式（stdio/sse/http） |

### 全局选项

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--version` | `-v` | 显示版本信息 |
| `--help` | `-h` | 显示帮助信息 |
| `--usable` | `-u` | *（已弃用）* 检查系统兼容性，请改用 `stata-mcp doctor` |
| `--transport` | `-t` | MCP 传输方式（stdio/sse/http） |
| `--config` | `-c` | 仅调试用的 `config.toml` 路径，面向开发者 |

### 配置选项

| 命令 | 描述 |
|--------|-------------|
| `stata-mcp config` | 打印 `~/.statamcp/config.toml` 的全部内容 |
| `stata-mcp config show <dot_key>` | 查看单个值，`cli` 为 `STATA.STATA_CLI` 的简写，其他使用 `Section.Key` |
| `stata-mcp config set cli [value]` | 设置 `STATA.STATA_CLI`，省略 value 时由 StataFinder 自动检测 |
| `stata-mcp config edit <dot_key> <value>` | 通过 `Section.Key` 修改已存在的配置项 |

### 安装选项

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--client` | `-c` | 目标客户端；若同时省略 `-c` 和 `--json-file`，等价于 `--all` |
| `--all` | `-a` | 安装到所有支持的客户端 |
| `--json-file` | | 自定义目标客户端配置文件路径 |
| `--json-index` | | dot-notation 的嵌套键路径（如 `mcp.servers`），仅在与 `--json-file` 一起使用时有效 |

### 诊断选项（doctor）

| 选项 | 描述 |
|--------|-------------|
| `--verbose` | 显示每项检查的详细信息 |
| `--json` | 以 JSON 格式输出报告 |
| `--check` | 仅运行指定检查（可重复） |
| `--dry-run` | 仅预览清理动作但不实际删除文件（仅 cleanup 类检查生效） |

### 验证选项（verify）

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--client` | `-c` | 目标客户端 key（如 `claude`、`cursor`、`codex`） |
| `--file` | `-f` | 自定义 JSON 或 TOML 配置文件路径 |
| `--index` | | 与 `-f` 配合使用的 dot-notation 嵌套键路径（如 `mcp.servers`） |
| `--key` | | 目标字典内的条目键（默认：`stata-mcp`） |

### 更新选项（update）

| 选项 | 描述 |
|--------|-------------|
| `--method` | 强制指定更新方式（auto/pip/uv-tool/homebrew） |
| `--dry-run` | 显示检测到的方式但不执行更新 |
| `--check` | 仅检查是否有新版本可用 |

## 示例

### 基本用法

```bash
# 检查 MCP-for-Stata 能否在您的系统上运行
stata-mcp doctor

# 为 Claude Desktop 启动 MCP 服务器
stata-mcp

# 使用 SSE 传输启动
stata-mcp -t sse
```

### 开发工作流程

```bash
# 1. 运行诊断检查
stata-mcp doctor

# 2. 安装到 Claude Code
stata-mcp install -c claude-code

# 3. 在写分析之前先查看数据
stata-mcp tool data-info /path/to/data.dta
```

### 使用 uvx

如果您不想全局安装 MCP-for-Stata，可以使用 `uvx`：

```bash
# 检查版本
uvx stata-mcp --version

# 运行诊断
uvx stata-mcp doctor

# 直接执行一个 do-file
uvx stata-mcp tool do /path/to/analysis.do

# 启动 MCP 服务器
uvx stata-mcp server

# 安装到客户端
uvx stata-mcp install -c cursor
```

## 自包含安装脚本

项目的 `scripts/` 目录提供了一组自包含的安装脚本，适合机器上尚未安装 `uv` 或 `pip` 的用户使用。脚本会自动拉起所需的 Python 工具链，并以一键方式启动 `stata-mcp`。

| 脚本 | 适用平台 | 典型用法 |
|------|----------|----------|
| `scripts/install.sh` | Unix shell（Linux、macOS、WSL） | `bash scripts/install.sh` |
| `scripts/install.command` | macOS Finder | 双击在终端中启动 |
| `scripts/install.ps1` | Windows PowerShell | `powershell -ExecutionPolicy Bypass -File scripts/install.ps1` |
| `scripts/install.bat` | Windows 命令行 | 双击或在 `cmd.exe` 中运行 |

这些脚本主要面向无 Python 包管理器的首次安装场景。对于已经装好 `uv` 或 `pip` 的机器，仍然推荐使用 `uv tool install stata-mcp` / `pip install stata-mcp` 的标准流程。

## 退出代码

- `0` - 成功
- `1` - 错误（系统不兼容、文件不存在等）
- `2` - 命令行参数错误，或 `verify` 中缺少/无效的配置键
- `3` - `verify` 解析 JSON/TOML 文件失败
- `4` - `verify` 中 MCP 服务器条目无效（缺少 `command` 或类型错误）
- `5` - `verify` 子命令参数错误（缺少 `-c`/`--client`、客户端无效，或缺少 `-f`/`--file`）

## 环境变量

MCP-for-Stata 的行为可以通过环境变量配置。详见[配置](configuration.md)。

关键环境变量：

- `STATA_MCP_CWD` - Stata 操作的工作目录
- `STATA_MCP_LOGGING_ON` - 启用/禁用日志
- `STATA_MCP__IS_GUARD` - 启用安全守卫验证
- `STATA_MCP__IS_MONITOR` - 启用 RAM 监控

完整列表请参见[配置文档](configuration.md)。

## 故障排除

### "Stata not found" 错误

确保 Stata 已安装并可访问：

```bash
stata-mcp doctor
```

这将运行诊断检查并确认 Stata 是否能在您的系统上找到。

### 权限错误

某些操作可能需要适当的权限：
- 安装到 Claude Desktop 可能需要管理员/用户权限
- 工作目录必须可写

### 传输问题

如果遇到特定传输方式的问题：
- 大多数用例默认使用 `stdio`
- 如果自动检测失败，明确使用 `--transport stdio`

## 另请参阅

- [使用指南](usage.md) - 详细使用示例
- [配置](configuration.md) - 环境变量和设置
- [安全](security.md) - 安全守卫和验证
- [监控](monitoring.md) - 资源监控配置
