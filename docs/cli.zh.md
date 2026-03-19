# CLI 参考

Stata-MCP 提供命令行界面（CLI）用于各种操作，包括启动 MCP 服务器、运行智能体模式以及安装到不同的 AI 客户端。

## 安装

验证您的安装：

```bash
stata-mcp --version
```

检查系统兼容性：

```bash
stata-mcp --usable
```

## 命令

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

**传输选项：**
- `stdio` - 标准输入/输出（默认）
- `sse` - Server-Sent Events
- `http` - HTTP 传输（自动转换为 streamable-http）

### 智能体模式

以交互式智能体模式运行 Stata-MCP：

```bash
# 在当前目录启动智能体
stata-mcp agent run

# 在指定目录启动智能体
stata-mcp agent run --work-dir /path/to/project
```

### 本地工具命令

直接从 CLI 运行由 API 模块驱动的 Stata 工具：

```bash
# 从 SSC 安装 ado 包（默认源）
stata-mcp tool ado-install reghdfe

# 运行 do-file 并打印生成的日志输出
stata-mcp tool do /path/to/analysis.do

# 通过一次性的 API helper 读取 Stata help
stata-mcp tool help regress --is-read-log true --enable-smcl true

# 查看支持的数据集元信息
stata-mcp tool data-info /path/to/data.dta

# 读取生成的日志文件
stata-mcp tool read-log /path/to/output.log
```

工具子命令：
- `stata-mcp tool ado-install <package_name> [--source ssc|net|github]`
- `stata-mcp tool do <dofile_path> [--is-read-log true|false] [--enable-smcl true|false]`
- `stata-mcp tool help <command> [--is-read-log true|false] [--enable-smcl true|false]`
- `stata-mcp tool data-info <data_path> [--vars-list var1 var2 ...]`
- `stata-mcp tool read-log <log_path> [--output-format full|core|dict]`

### 配置管理

查看和更新本地 CLI 配置：

```bash
# 打印当前配置文件内容（~/.statamcp/config.toml）
stata-mcp config

# 手动设置 STATA_CLI 路径
stata-mcp config cli set /path/to/stata

# 自动检测 STATA_CLI 并持久化保存
stata-mcp config cli set
```

### 安装到 AI 客户端

将 Stata-MCP 安装到各种 AI 编程助手：

```bash
# 安装到 Claude Desktop（默认）
stata-mcp install

# 安装到特定客户端
stata-mcp install -c claude    # Claude Desktop
stata-mcp install -c cc        # Claude Code
stata-mcp install -c cursor    # Cursor
stata-mcp install -c cline     # Cline
stata-mcp install -c codex     # Codex
```

**支持的客户端：**
- `claude` - Claude Desktop
- `cc` - Claude Code
- `cursor` - Cursor Editor
- `cline` - Cline（VS Code 扩展）
- `codex` - Codex

### 基于 Docker 的安装（sandbox-install）

将基于 Docker 的 Stata-MCP 安装到 AI 客户端。需要 Docker 和有效的 Stata 许可证。

```bash
# 使用默认设置的基本用法（StataNow 19.5 MP）
uvx stata-mcp sandbox-install -l /path/to/stata.lic

# 指定 Stata 版本和版本类型
uvx stata-mcp sandbox-install \
  --version 19_5 \
  --edition mp \
  -l /path/to/stata.lic \
  -c claude

# 带资源限制
uvx stata-mcp sandbox-install \
  -V 18 \
  -e se \
  -l /path/to/stata.lic \
  --cpus 2 \
  --memory 4g
```

**Stata 版本：** `19_5`、`18_5`、`18`

**Stata 版本类型：** `mp`（多处理器）、`se`（标准版）、`be`（基础版）

## 选项

### 全局选项

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--version` | `-v` | 显示版本信息 |
| `--help` | `-h` | 显示帮助信息 |
| `--usable` | `-u` | 检查系统兼容性 |
| `--transport` | `-t` | MCP 传输方式（stdio/sse/http） |

### 智能体选项

| 选项 | 描述 |
|--------|-------------|
| `--work-dir` | 智能体的工作目录（默认：当前目录） |

### 配置选项

| 命令 | 描述 |
|--------|-------------|
| `stata-mcp config` | 打印原始配置文件内容 |
| `stata-mcp config cli set [value]` | 设置 `STATA.STATA_CLI`，省略 value 时自动检测 |

### 安装选项

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--client` | `-c` | 目标客户端（默认：claude） |

### Sandbox-Install 选项

| 选项 | 简写 | 默认值 | 描述 |
|--------|-------|---------|-------------|
| `--version` | `-V` | `19_5` | Stata 版本（19_5, 18_5, 18） |
| `--edition` | `-e` | `mp` | Stata 版本类型（mp, se, be） |
| `--tag` | | `latest` | Docker 镜像标签 |
| `--license-file` | `-l` | （必填） | Stata 许可证文件路径 |
| `--client` | `-c` | `claude` | 目标客户端 |
| `--work-dir` | | `./` | 工作目录 |
| `--cpus` | | （无） | CPU 核心限制 |
| `--memory` | | （无） | 内存限制（如 4g） |

## 示例

### 基本用法

```bash
# 检查 Stata-MCP 能否在您的系统上运行
stata-mcp --usable

# 为 Claude Desktop 启动 MCP 服务器
stata-mcp

# 使用 SSE 传输启动
stata-mcp -t sse
```

### 开发工作流程

```bash
# 1. 检查系统兼容性
stata-mcp --usable

# 2. 安装到 Claude Desktop
stata-mcp install

# 3. 运行智能体进行交互式分析
stata-mcp agent run
```

### 使用 uvx

如果您不想全局安装 Stata-MCP，可以使用 `uvx`：

```bash
# 检查版本
uvx stata-mcp --version

# 检查兼容性
uvx stata-mcp --usable

# 运行智能体
uvx stata-mcp agent run

# 安装到客户端
uvx stata-mcp install -c cursor
```

## 退出代码

- `0` - 成功
- `1` - 错误（无效客户端、系统不兼容等）
- `2` - 命令行参数错误

## 环境变量

Stata-MCP 的行为可以通过环境变量配置。详见[配置](configuration.md)。

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
stata-mcp --usable
```

这将检查 Stata 是否能在您的系统上找到。

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
