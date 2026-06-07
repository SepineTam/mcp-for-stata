# 配置系统

MCP-for-Stata 使用具有三个优先级的分层配置系统：

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
LOG_FILE = "~/.statamcp/stata_mcp_debug.log"
MAX_BYTES = 10_000_000
BACKUP_COUNT = 5

[BETA]
ENABLE_WRITE_DOFILE = false

[HELP]
IS_CACHE = true
IS_SAVE = true

[SECURITY]
IS_GUARD = true
ENABLE_ADO_INSTALL = false
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = []

[PROJECT]
WORKING_DIR = ""
CLEAN_LOG_DAYS = -1
FOLDER_TAG = ".statamcp"

[MONITOR]
IS_MONITOR = false
MAX_RAM_MB = -1

[STATA]
# 可选：覆盖自动 Stata 检测
# STATA_CLI = "/path/to/stata-mp"

[data_info]
metrics = ["obs", "mean", "stderr", "min", "max", "q1", "q3", "skewness", "kurtosis"]
string_keep_number = 10
decimal_places = 3
hash_length = 12
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

### HELP 分区

控制 `help` 工具的缓存行为。

#### `HELP.IS_CACHE`

启用 `help` 工具结果的内存缓存。

- **类型**：Boolean
- **默认值**：`true`
- **环境变量**：`STATA_MCP__CACHE_HELP`
- **描述**：启用后，对同一命令的重复 help 请求将从缓存读取，减少会话内对 Stata 的重复调用。
- **示例**：
  ```bash
  export STATA_MCP__CACHE_HELP=true
  ```

#### `HELP.IS_SAVE`

将 help 缓存持久化到磁盘（`~/.statamcp/help/`）。

- **类型**：Boolean
- **默认值**：`true`
- **环境变量**：`STATA_MCP__SAVE_HELP`
- **描述**：启用后，help 响应会写入文件，可跨会话复用。如果只需要内存缓存，请关闭此项。
- **示例**：
  ```bash
  export STATA_MCP__SAVE_HELP=false
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

#### 第三方 Ado 包安装

`ado_package_install` 默认禁用，因为安装后的 ado 包会在 Stata 中执行第三方代码。
启用时必须同时满足以下条件：

- 设置 `SECURITY.ENABLE_ADO_INSTALL = true`
- 将每个已批准的 GitHub `owner/repository` 加入精确仓库白名单
- MCP server 必须通过 `stata-mcp server --unsafe` 启动
- 每次 MCP 调用接受客户端弹出的用户批准请求；每次 API 调用传入 `confirm=True`；
  每次 CLI 调用传入 `--yes`

```toml
[SECURITY]
ENABLE_ADO_INSTALL = true
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["SepineTam/TexIV"]
```

对应环境变量为 `STATA_MCP__ENABLE_ADO_INSTALL`、
和 `STATA_MCP__ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES`。GitHub 白名单环境变量
使用逗号分隔。SSC 和 net 包名只能包含 ASCII 字母与数字。net 来源必须使用经过
校验的 HTTPS URL；本地路径、IP 地址主机、凭据、查询参数、片段、点路径段、
重复斜杠和非默认端口都会被拒绝。

GitHub 白名单只校验仓库名称，不会检查或保护仓库内容。安装前必须人工查验仓库。

### PROJECT 分区

控制项目特定设置。

#### `PROJECT.WORKING_DIR`

设置 MCP-for-Stata 操作的工作目录。

- **类型**：Path（string）
- **默认值**：当前目录（如果可写）或 `~/Documents`
- **环境变量**：`STATA_MCP__CWD`（双下划线）
- **描述**：
  - 如果设置且可写，所有输出文件将组织在 `<WORKING_DIR>/<FOLDER_TAG>/` 下（默认 `.statamcp/`）
  - 如果未设置或不可写，回退到当前目录或 `~/Documents`
  - **遗留支持**：`STATA_MCP_CWD`（单下划线）仍受支持但已弃用
- **示例**：
  ```bash
  export STATA_MCP__CWD="/projects/my-research"
  ```

#### `PROJECT.CLEAN_LOG_DAYS`

工作目录下 Stata 日志的保留天数。

- **类型**：Integer
- **默认值**：`-1`（不清理）
- **环境变量**：`STATA_MCP__CLEAN_LOG_DAYS`
- **描述**：
  - `-1` 表示关闭自动清理
  - 设置为正整数后，`stata-mcp doctor` 的 cleanup 检查会删除超过指定天数的 Stata 日志文件
- **示例**：
  ```bash
  export STATA_MCP__CLEAN_LOG_DAYS=30
  ```

#### `PROJECT.FOLDER_TAG`

`WORKING_DIR` 下 stata-mcp 子目录的名称。

- **类型**：String
- **默认值**：`.statamcp`（隐藏目录）
- **环境变量**：`STATA_MCP__FOLDER_TAG`
- **描述**：
  - 决定存放日志、do 文件、结果与临时文件的目录名
  - 自 v1.16.0 起，默认名称从 `stata-mcp-folder` 迁移到 `.statamcp`
  - 如需保留旧的目录布局，可将其设置为 `stata-mcp-folder`
- **示例**：
  ```bash
  export STATA_MCP__FOLDER_TAG=stata-mcp-folder
  ```

工作目录结构：
```
<WORKING_DIR>/<FOLDER_TAG>/        # 默认：.statamcp/
├── stata-mcp-log/      # Stata 执行日志
├── stata-mcp-dofile/   # 生成的 do 文件
├── stata-mcp-result/   # 分析结果
└── stata-mcp-tmp/      # 临时文件
```

**迁移说明（v1.16.0）**：
- 默认目录名从 `stata-mcp-folder` 改为 `.statamcp`。
- 若检测到工作目录下仍存在旧的 `stata-mcp-folder`，MCP-for-Stata 会在该目录中写入一个 `README` 警告并创建 `.migrated` 标记，避免重复提示。
- 如需回滚旧布局，设置 `export STATA_MCP__FOLDER_TAG=stata-mcp-folder` 即可。

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

### data_info 分区

控制 `get_data_info` 工具的行为：返回哪些描述性统计、如何处理字符串变量，以及缓存文件名的构造方式。

#### `data_info.metrics`

每个变量返回的默认数值指标列表。

- **类型**：List of strings
- **默认值**：`["obs", "mean", "stderr", "min", "max", "q1", "q3", "skewness", "kurtosis"]`
- **描述**：
  - 支持的取值包括 `obs`、`mean`、`stderr`、`min`、`max`、`q1`、`q3`、`skewness`、`kurtosis`
  - 可裁剪列表缩减返回体积，也可补充更多指标以获得更详尽的摘要
- **示例**：
  ```toml
  [data_info]
  metrics = ["obs", "mean", "stderr", "min", "max"]
  ```

#### `data_info.string_keep_number`

字符串变量保留的唯一值数量上限。

- **类型**：Integer
- **默认值**：`10`
- **环境变量**：`STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`
- **描述**：唯一值数量超过该上限的分类字符串只保留若干代表值。
- **示例**：
  ```bash
  export STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER=20
  ```

#### `data_info.decimal_places`

格式化数值统计时使用的小数位数。

- **类型**：Integer
- **默认值**：`3`
- **环境变量**：`STATA_MCP_DATA_INFO_DECIMAL_PLACES`
- **示例**：
  ```bash
  export STATA_MCP_DATA_INFO_DECIMAL_PLACES=4
  ```

#### `data_info.hash_length`

data-info 缓存文件名所附加的哈希后缀长度。

- **类型**：Integer
- **默认值**：`12`
- **环境变量**：`STATA_MCP_DATA_INFO_HASH_LENGTH`
- **描述**：data-info 层用它区分基于相同源文件生成的不同缓存条目。
- **示例**：
  ```bash
  export STATA_MCP_DATA_INFO_HASH_LENGTH=8
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

如果工作目录不可写，MCP-for-Stata 将回退到 `~/Documents`。解决方法：

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
