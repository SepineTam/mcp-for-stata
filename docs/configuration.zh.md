# 配置系统

Stata-MCP 使用具有三个优先级的分层配置系统：

1. **环境变量**（最高优先级）
2. **配置文件**（`~/.statamcp/config.toml`）
3. **默认值**（最低优先级）

## 配置文件

### 位置

配置文件位于：
```
~/.statamcp/config.toml
```

在不同平台上：
- **macOS/Linux**：`/home/username/.statamcp/config.toml`
- **Windows**：`C:\Users\Username\.statamcp\config.toml`

### 示例配置

```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = false
LOGGING_FILE_HANDLER_ON = true
LOG_FILE = "~/"

MAX_BYTES = 10_000_000
BACKUP_COUNT = 5

[SECURITY]
IS_GUARD = true

[PROJECT]
WORKING_DIR = ""

[MONITOR]
IS_MONITOR = false
MAX_RAM_MB = -1

[STATA]
# 可选：覆盖自动 Stata 检测
# STATA_CLI = "/path/to/stata-mp"

[BETA]
# Beta 功能 - 谨慎使用
ENABLE_WRITE_DOFILE = false  # 控制 write_dofile MCP 工具是否注册
```

## 配置分区

### DEBUG 分区

控制调试和日志行为。

#### `DEBUG.IS_DEBUG`

启用调试模式以获得详细输出。

- **类型**：Boolean
- **默认值**：`false`
- **环境变量**：`STATA_MCP__IS_DEBUG`
- **示例**：
  ```bash
  export STATA_MCP__IS_DEBUG=true
  ```

#### `DEBUG.logging.LOGGING_ON`

启用或禁用所有日志记录。

- **类型**：Boolean
- **默认值**：`true`
- **环境变量**：`STATA_MCP__LOGGING_ON`
- **示例**：
  ```bash
  export STATA_MCP__LOGGING_ON=false
  ```

#### `DEBUG.logging.LOGGING_CONSOLE_HANDLER_ON`

启用日志控制台输出。

- **类型**：Boolean
- **默认值**：`false`
- **环境变量**：`STATA_MCP__LOGGING_CONSOLE_HANDLER_ON`
- **示例**：
  ```bash
  export STATA_MCP__LOGGING_CONSOLE_HANDLER_ON=true
  ```

#### `DEBUG.logging.LOGGING_FILE_HANDLER_ON`

启用文件日志记录。

- **类型**：Boolean
- **默认值**：`true`
- **环境变量**：`STATA_MCP__LOGGING_FILE_HANDLER_ON`
- **示例**：
  ```bash
  export STATA_MCP__LOGGING_FILE_HANDLER_ON=true
  ```

#### `DEBUG.logging.LOG_FILE`

指定日志文件位置。

- **类型**：Path（string）
- **默认值**：`~/.statamcp/stata_mcp_debug.log`
- **环境变量**：`STATA_MCP__LOG_FILE`
- **示例**：
  ```bash
  export STATA_MCP__LOG_FILE="/var/log/stata-mcp/debug.log"
  ```

#### `DEBUG.logging.MAX_BYTES`

轮换前单个日志文件的最大大小。

- **类型**：Integer（bytes）
- **默认值**：`10_000_000`（10 MB）
- **环境变量**：`STATA_MCP__LOGGING__MAX_BYTES`
- **示例**：
  ```bash
  export STATA_MCP__LOGGING__MAX_BYTES=50_000_000
  ```

#### `DEBUG.logging.BACKUP_COUNT`

保留的备份日志文件数量。

- **类型**：Integer
- **默认值**：`5`
- **环境变量**：`STATA_MCP__LOGGING__BACKUP_COUNT`
- **示例**：
  ```bash
  export STATA_MCP__LOGGING__BACKUP_COUNT=10
  ```

### SECURITY 分区

控制安全功能。

#### `SECURITY.IS_GUARD`

为 Stata dofile 启用安全守卫验证。

- **类型**：Boolean
- **默认值**：`true`
- **环境变量**：`STATA_MCP__IS_GUARD`
- **描述**：启用时，在执行前针对危险命令和模式验证所有 dofile 代码
- **示例**：
  ```bash
  export STATA_MCP__IS_GUARD=true
  ```

更多详情请参阅[安全守卫文档](security.md)。

### PROJECT 分区

控制项目特定设置。

#### `PROJECT.WORKING_DIR`

设置 Stata-MCP 操作的工作目录。

- **类型**：Path（string）
- **默认值**：当前目录（如果可写）或 `~/Documents`
- **环境变量**：`STATA_MCP__CWD`（双下划线）
- **描述**：
  - 如果设置且可写，所有输出文件将组织在 `<WORKING_DIR>/stata-mcp-folder/` 下
  - 如果未设置或不可写，回退到当前目录或 `~/Documents`
  - **遗留支持**：`STATA_MCP_CWD`（单下划线）仍受支持但已弃用
- **示例**：
  ```bash
  export STATA_MCP__CWD="/projects/my-research"
  ```

工作目录结构：
```
<WORKING_DIR>/stata-mcp-folder/
├── stata-mcp-log/      # Stata 执行日志
├── stata-mcp-dofile/   # 生成的 do 文件
├── stata-mcp-result/   # 分析结果
└── stata-mcp-tmp/      # 临时文件
```

### MONITOR 分区

控制性能监控功能。

#### `MONITOR.IS_MONITOR`

为 Stata 进程启用 RAM 监控。

- **类型**：Boolean
- **默认值**：`false`
- **环境变量**：`STATA_MCP__IS_MONITOR`
- **描述**：启用时，在执行期间监控 Stata 子进程 RAM 使用
- **示例**：
  ```bash
  export STATA_MCP__IS_MONITOR=true
  ```

更多详情请参阅[监控文档](monitoring.md)。

#### `MONITOR.MAX_RAM_MB`

最大 RAM 限制（兆字节）。

- **类型**：Integer
- **默认值**：`-1`（无限制）
- **环境变量**：`STATA_MCP__RAM_LIMIT`
- **描述**：
  - `-1` 表示无限制（默认）
  - 设置为正值时，超过此限制的 Stata 进程将被终止
- **示例**：
  ```bash
  export STATA_MCP__RAM_LIMIT=8192  # 8 GB 限制
  ```

### BETA 分区

控制 Beta/实验性功能。

#### `BETA.ENABLE_WRITE_DOFILE`

控制 `write_dofile` MCP 工具是否注册。

- **类型**：Boolean
- **默认值**：`false`
- **环境变量**：`STATA_MCP__ENABLE_WRITE_DOFILE`
- **描述**：
  - 当为 `false`（默认）时，`write_dofile` MCP 工具不会注册
  - 现代 AI 智能体具有原生文件写入能力，使该工具变得多余
  - 仅在需要与旧工作流程向后兼容时设置为 `true`
- **示例**：
  ```bash
  export STATA_MCP__ENABLE_WRITE_DOFILE=true
  ```

> **注意**：此配置标记为 BETA，可能在未来版本中移除。

### STATA 分区

控制 Stata 可执行文件检测。

#### `STATA.STATA_CLI`

覆盖自动 Stata 检测。

- **类型**：Path（string）
- **默认值**：基于平台自动检测
- **描述**：
  - **macOS**：`/Applications/Stata/StataMP.app/Contents/MacOS/stata-mp`
  - **Windows**：`C:\Program Files\Stata18\StataMP-64.exe`
  - **Linux**：`stata-mp`（来自 PATH）
- **示例**：
  ```toml
  [STATA]
  STATA_CLI = "/usr/local/stata17/stata-mp"
  ```

## 使用环境变量

### 快速设置

```bash
# 启用调试模式
export STATA_MCP__IS_DEBUG=true

# 设置工作目录
export STATA_MCP__CWD="/projects/my-analysis"

# 启用监控，设置 8GB RAM 限制
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=8192

# 禁用安全守卫（不推荐）
export STATA_MCP__IS_GUARD=false

# 启用控制台日志
export STATA_MCP__LOGGING_CONSOLE_HANDLER_ON=true
```

### 优先级示例

如果在多个位置设置同一选项：

```bash
# 配置文件：IS_GUARD = true
# 环境变量：STATA_MCP__IS_GUARD=false
export STATA_MCP__IS_GUARD=false

# 结果：安全守卫被禁用（环境变量优先）
```

## 配置验证

配置系统包含内置验证：

- **布尔值**：必须是 `true` 或 `false`（不区分大小写）
- **整数值**：必须是有效整数
- **路径值**：自动展开 `~`（主目录）
- **无效值**：自动回退到默认值

## 常见配置模式

### 开发设置

```toml
[DEBUG]
IS_DEBUG = true

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = true
LOGGING_FILE_HANDLER_ON = false
```

### 生产设置

```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = false
LOGGING_FILE_HANDLER_ON = true
MAX_BYTES = 50_000_000
BACKUP_COUNT = 10

[SECURITY]
IS_GUARD = true

[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 16384
```

### 高性能计算

```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = false

[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 65536  # 64 GB
```

## 故障排除

### 配置未加载

1. 检查配置文件是否存在：
   ```bash
   ls ~/.statamcp/config.toml
   ```

2. 验证 TOML 语法：
   ```bash
   python3 -c "import tomllib; tomllib.load(open('~/.statamcp/config.toml', 'rb'))"
   ```

3. 检查环境变量冲突：
   ```bash
   env | grep STATA_MCP
   ```

### 工作目录问题

如果工作目录不可写，Stata-MCP 将回退到 `~/Documents`。解决方法：

1. 检查目录权限：
   ```bash
   ls -la /your/working/directory
   ```

2. 创建具有正确权限的目录：
   ```bash
   mkdir -p /your/working/directory
   chmod u+w /your/working/directory
   ```

### 日志文件未创建

1. 检查是否启用日志：
   ```bash
   echo $STATA_MCP__LOGGING_ON
   ```

2. 验证日志文件路径是否可写：
   ```bash
   touch ~/.statamcp/stata_mcp_debug.log
   ```

3. 检查磁盘空间：
   ```bash
   df -h
   ```
