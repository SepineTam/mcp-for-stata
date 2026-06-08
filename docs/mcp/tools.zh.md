# MCP.Tools

工具在 `_TOOL_REGISTRY` 中按三种 profile 划分。`stata-mcp server --core` 只注册 `stata_do`、`get_data_info`、`help`；`stata-mcp server --all`（默认）注册标准工具，但不包含高风险第三方安装；`stata-mcp server --unsafe` 会额外注册 `ado_package_install`。`help` 在 Windows 上会被过滤。已弃用的 `write_dofile` 仅在 `ENABLE_WRITE_DOFILE=true` 时注册。

---
## get_data_info
```python
def get_data_info(data_path: str | Path,
                  vars_list: List[str] | None = None,
                  encoding: str = "utf-8",
                  head: int = 0) -> str:
    ...
```

**输入参数**：
- `data_path`：数据文件的绝对文件系统路径或 URL（必填）
- `vars_list`：可选变量子集规范，用于选择性分析（默认：null，所有变量）
- `encoding`：文本格式文件的字符编码（默认：UTF-8，.dta 格式忽略）
- `head`：预览数据集时显示的行数（默认：0，禁用预览以避免大样本上下文溢出）

**返回结构**：
包含多层元数据的序列化 JSON 字符串：
```json
{
  "overview": {"source": <path>, "obs": <int>, "var_numbers": <int>, "var_list": [<array>]},
  "info_config": {"metrics": [<array>], "max_display": <int>, "decimal_places": <int>},
  "vars_detail": {<variable_name>: {"var": <str>, "type": <str>, "summary": {...}}},
  "saved_path": <cache_file_path>
}
```

**操作示例**：
```python
# 本地文件分析
get_data_info("/data/econometrics/survey.dta")
get_data_info("~/Documents/exports/quarterly.csv", vars_list=["gdp", "inflation", "unemployment"])

# 远程数据获取
get_data_info("https://repository.org/datasets/panel_data.xlsx")

# 编码源处理
get_data_info("/data/legacy/latin1_data.csv", encoding="latin1")
```

**支持格式**：
- **Stata**：`.dta`
- **CSV/文本**：`.csv`、`.tsv`、`.psv`
- **Excel**：`.xlsx`、`.xls`
- **SPSS**：`.sav`、`.zsav`

**实现架构**：
该工具通过多层抽象级联运行。基础是多态类层次结构，其中 `DataInfoBase` 定义了格式特定处理器（`DtaDataInfo`、`CsvDataInfo`、`ExcelDataInfo`、`SpssDataInfo`）的抽象接口。内容完整性验证使用 MD5 哈希，可配置后缀长度用于缓存标识。配置传播遵循优先级链：运行时参数覆盖环境变量（`STATA_MCP_DATA_INFO_DECIMAL_PLACES`、`STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`），环境变量又覆盖 `~/.statamcp/config.toml` 中的 TOML 配置。

统计计算利用 pandas DataFrame 操作，后端为 NumPy。指标系统实现可配置的计算流水线，默认指标（`obs`、`mean`、`stderr`、`min`、`max`）可通过配置扩展以包含四分位数（`q1`、`q3`）和分布形状度量（`skewness`、`kurtosis`）。类型分派将字符串变量（在 `max_display` 阈值下的观测计数和唯一值采样）与数值变量（带 `decimal_places` 精度舍入的中心趋势、离散度和分布形状计算）分开。

缓存策略采用内容可寻址存储，哈希计算决定缓存文件命名：`data_info__<name>_<ext>__hash_<suffix>.json`。缓存解析在调用时进行，当内容哈希分歧时自动重新生成。缓存目录默认为 `~/.statamcp/.cache/`，但可通过 `cache_dir` 参数覆盖为项目特定的 `stata-mcp-tmp/` 位置。

---

## stata_do
```python
def stata_do(dofile_path: str,
             log_file_name: str | None = None,
             read_log_when_error: bool = False,
             is_replace_log: bool = True,
             enable_smcl: bool = True) -> Dict[str, Union[str, None]]:
    ...
```

**输入参数**：
- `dofile_path`：目标 .do 文件的绝对或相对路径（必填）
- `log_file_name`：不带时间戳的自定义日志文件名（可选，如为 null 则自动生成）
- `read_log_when_error`：仅在 Stata 返回错误码（如 `r(198)`）时才读取并返回日志内容的开关，用以降低成功路径的 I/O 开销（默认：false）
- `is_replace_log`：是否覆盖同名 log 文件的开关（默认：true）
- `enable_smcl`：是否启用 SMCL 格式日志输出的开关，true 时 Stata CLI 不附加 `nolog` 重定向参数,同时产出 `.smcl` 和 `.log`（默认：true）

**返回结构**：
包含执行元数据和可选日志负载的字典：
```python
{
  "log_file_path": {"text": "<absolute_path_to_log>", "smcl": "<absolute_path_to_smcl>"},
  "log_content": {"text": "<error_log_text_or_placeholder>", "smcl": "<smcl_path>"}
}
```
仅在 `read_log_when_error=True` 时才会包含 `log_content` 键。错误情况返回：`{"error": "<exception_message>"}`。

**操作示例**：
```python
# 标准执行,成功路径不读 log
stata_do("/Users/project/stata-mcp-dofile/20250104153045.do")

# 自定义日志命名
stata_do("~/analysis/regression_pipeline.do", log_file_name="quarterly_results")

# 仅在 Stata 报错时返回日志内容
stata_do("/tmp/estimation.do", read_log_when_error=True)

# 保留历史日志并关闭 SMCL 输出
stata_do("/tmp/estimation.do",
         read_log_when_error=True,
         is_replace_log=False,
         enable_smcl=False)
```

**实现架构**：
该工具封装了实现平台特定命令调用策略的 `StataDo` 执行器类。跨平台抽象通过 `StataFinder` 类抽象 Stata 可执行文件位置：macOS 探测 `/Applications/Stata/` 层级，Windows 查询 Program Files 注册表，Linux 在系统 PATH 中查询 `stata-mp`。执行流水线涉及 do 文件暂存、带 `-b` 批处理模式标志的 Stata CLI 调用、日志文件重定向和退出代码监控。

日志文件管理在 `stata-mcp-log/` 目录结构内运行，当省略 `log_file_name` 时自动生成时间戳。`is_replace_log` 标志决定是否覆盖既有日志,`enable_smcl` 决定是否一并产出 SMCL 制品。执行器根据 `read_log_when_error` 标志实现条件式日志返回：先以 `r(\d+)` 模式扫描文本日志,只有检测到 Stata 返回码错误时才返回日志负载,否则返回一个占位提示,引导用户改用 `read_log` 工具。

异常处理将失败分为三个层级：缺失 do 文件产物的 `FileNotFoundError`，Stata 执行失败或日志生成问题的 `RuntimeError`，以及执行或写入权限不足的 `PermissionError`。错误情况返回带 `"error"` 键的字典而非抛出异常，以保持 MCP 协议兼容性。

---

## write_dofile
> **默认禁用**：该工具是否被注册到 MCP server 完全由 `ENABLE_WRITE_DOFILE` 配置开关决定。未设置为 `true` 时,`register_tools()` 会直接跳过这个条目,工具不会暴露给客户端。
>
> 现代 AI 智能体具有原生文件写入能力，使该工具变得多余。
> 要启用，请设置 `STATA_MCP__ENABLE_WRITE_DOFILE=true` 或在配置中添加 `[BETA] ENABLE_WRITE_DOFILE = true`。

```python
def write_dofile(content: str,
                 encoding: str | None = None) -> str:
    ...
```

**输入参数**：
- `content`：要持久化的 Stata 命令序列（必填）
- `encoding`：文件输出的字符编码（可选，默认为 UTF-8）

**返回结构**：
包含生成的 do 文件绝对 POSIX 兼容路径的字符串

**操作示例**：
```python
# 基本回归分析
write_dofile("""
use "/data/survey.dta", clear
regress income age education experience
outreg2 using "`output_path'/results.doc", replace
""")

# 带编码规范的时间序列分析
write_dofile("""
tsset date
arima gdp, ar(1) ma(1)
predict forecast
""", encoding="latin1")

# 数据转换流水线
write_dofile("""
gen log_gdp = ln(gdp)
gen diff_income = d(income)
xtset country_id year
xtreg diff_income log_gdp, fe
""")
```

**实现架构**：
该工具在 `stata-mcp-dofile/` 目录层级内实现原子文件创建。文件命名采用 ISO 8601 基本格式时间戳生成（`YYYYMMDDHHMMSS.do`），确保时间唯一性和按时间排序。写入操作使用 Python 内置的 `open()` 函数，模式为 `"w"` 和指定的编码参数，执行隐式文件创建和截断以实现原子写入语义。

与输出重定向命令（`outreg2`、`esttab`）的集成需要在 do 文件生成之前与 `results_doc_path` 提示协调以建立输出目录路径。这种关注点分离使得跨多个 Stata 执行周期的确定性输出路径管理成为可能。

该工具不执行 Stata 代码内容的语法验证或语义分析。代码正确性、命令序列和宏展开有效性仍然是调用上下文的责任。错误处理将文件 I/O 操作包装在 try-except 块中，并进行结构化日志记录以跟踪成功/失败。

> **弃用通知**：此工具默认禁用，将在未来版本中移除。现代 AI 智能体具有原生文件写入能力，请使用那些功能替代。

---

## read_log
```python
def read_log(file_path: str,
             encoding: str = "utf-8",
             is_beta: bool = False,
             lines: int = 0,
             *,
             output_format: Literal["full", "core", "dict"] = "dict") -> str:
    ...
```

**输入参数**：
- `file_path`：目标日志文件的绝对路径（必填，`.log` 或 `.smcl`）
- `encoding`：文本解码的字符编码（可选，默认为 UTF-8）
- `is_beta`：启用结构化日志解析（可选，默认：false）
  - **仅限 macOS/Linux** - Windows 用户请使用默认行为
  - 推荐用于 `.smcl` 文件配合 `dict` 格式
- `lines`：内容裁剪控制（默认：0，不裁剪）
  - `> 0`：返回前 N 项（full/core 模式为行数，dict 模式为条目数）
  - `< 0`：返回后 |N| 项
  - `0`：返回完整内容
- `output_format`：`is_beta=true` 时的输出格式（可选，默认："dict"）
  - `full`：未经处理的原始日志内容
  - `core`：去除框架行的清洁内容
  - `dict`：结构化的命令-结果对（推荐）

**返回结构**：
- 默认模式（`is_beta=false`）：文件的原始字符串内容
- Beta 模式（`is_beta=true`）：取决于 `output_format`：
  - `full`：纯文本日志内容
  - `core`：不含框架（页眉、页脚、日志命令）的日志内容
  - `dict`：命令-结果列表的字符串表示

**操作示例**：
```python
# 读取日志文件（默认模式）
read_log("/Users/project/stata-mcp-log/20250104153045.log")

# 使用结构化解析读取 SMCL 日志（macOS/Linux）
read_log("/Users/project/stata-mcp-log/20250104153045.smcl",
         is_beta=True,
         output_format="dict")

# 获取去除框架的清洁日志内容
read_log("~/stata-mcp-log/session.log",
         is_beta=True,
         output_format="core")

# 仅读取前 50 行
read_log("~/stata-mcp-log/session.log", lines=50)

# 读取最后 20 个命令结果（dict 格式）
read_log("~/stata-mcp-log/session.log",
         is_beta=True,
         output_format="dict",
         lines=-20)

# 使用自定义编码读取
read_log("~/analysis/tables/results.txt", encoding="utf-8")
```

**实现架构**：
该工具实现双模式日志读取：传统文件读取和通过 `StataLog` 模块的结构化解析。

**传统模式**（`is_beta=false`）：通过 Python 的 `open()` 函数进行通用文件读取，模式为 `"r"`。路径验证通过 `Path.exists()` 检查文件是否存在。内容读取使用单次 `file.read()` 操作获取完整文件内容。

**结构化解析模式**（`is_beta=true`，仅 Unix）：利用 `stata_log` 模块，提供：
- `StataLogTEXT`：`.log`（纯文本）文件解析器
- `StataLogSMCL`：`.smcl`（Stata 标记与控制语言）文件解析器
- `StataLogInfo`：包含 `command_result_list` 结构化命令-输出对的数据类

`StataLog` 工厂类（`from_path()` 方法）自动检测文件扩展名并返回相应的解析器。框架移除消除日志页眉/页脚、`log using/close` 命令和 do 文件执行标记，仅保留实际的 Stata 命令及其输出。

**`lines` 裁剪**：通过 `_trim_lines()` 辅助函数实现。正数取前 N 项，负数取后 |N| 项，0 返回完整内容。对于 `dict` 格式，裁剪作用于列表条目而非文本行。

错误处理覆盖：缺失文件的 `FileNotFoundError`、I/O 失败的 `IOError`、无效 `output_format` 的 `ValueError`，以及编码不匹配的 `UnicodeDecodeError`。

---

## ado_package_install
```python
def ado_package_install(package: str,
                        source: str = "ssc",
                        is_replace: bool = False,
                        package_source_from: str | None = None) -> str:
    ...
```

**输入参数**：
- `package`：包标识符（必填）
  - SSC：包名（如 "outreg2"）
  - GitHub："username/reponame" 格式（如 "sepinetam/texiv"）
  - net：包名，`package_source_from` 指定来源
- `source`：分发源（可选，默认："ssc"）
  - 选项："ssc"、"github"、"net"
- `is_replace`：强制替换标志（可选，默认：false）
- `package_source_from`：`net` 安装使用的 HTTPS URL

默认 `all` profile 不提供此高风险工具。运维人员必须启用安装功能并使用 `unsafe`
profile。SSC 和 net 包名只能包含 ASCII 字母与数字。GitHub 必须使用
`owner/repository` 格式并命中精确仓库白名单。每次 MCP 调用还会通过客户端向用户发起批准请求；
无法请求批准或用户拒绝时会失败关闭。本地路径、IP 主机、凭据、查询参数、片段、
点路径段、重复斜杠和非默认端口都会被拒绝。

GitHub 仓库内容没有安全防护，安装前必须人工查验。

**返回结构**：
包含安装操作完整 Stata 执行日志的字符串

**操作示例**：
```python
# SSC 包安装
ado_package_install("outreg2", source="ssc")

# GitHub 包安装
ado_package_install("sepinetam/texiv", source="github")

# 网络安装
ado_package_install("custompkg", source="net", package_source_from="https://example.com/stata")

# 强制重新安装
ado_package_install("estout", source="ssc", is_replace=True)
```

**实现架构**：
该工具实现平台差异化的安装策略。Unix 使用内部专用安装器；Windows 生成经过预先
校验的临时 dofile，并使用内部可信执行路径。通过 `stata_do` 提交的直接包管理命令
在所有平台上都会被阻止。

Unix 下，安装成功以交互式 Stata Controller 正常返回为准。Controller 遇到
Stata `r(n)` 返回码错误、超时或会话异常退出时会抛出异常，因此成功判断不依赖
匹配提示性输出文本。Windows 使用保守的日志兜底判断；其中 GitHub 安装只接受
明确的终态成功文本，任何错误信号都会使其失败，并且连接成功或仓库存在不能证明
安装完成。

系统不会隐式安装 GitHub helper。任意来源安装成功后，共用安装器都会尝试用
`replace=True` 刷新最可能的命令名：SSC/net 使用包名，GitHub 使用仓库名部分。
刷新失败只会记录日志，不会把已经完成的安装改判为失败。如果包提供的是其他命令名，
需要对那些命令显式调用 `help(cmd, replace=True)`。

---

## help
> 仅限 macOS 和 Linux

```python
def help(cmd: str) -> str:
    ...
```

**输入参数**：
- `cmd`：Stata 命令名（必填，如 "regress"、"describe"、"xtset"）

**返回结构**：
包含 Stata 帮助文本输出的字符串，可选缓存状态前缀（如 "Cached result for regress: ..."）

**操作示例**：
```python
# 回归命令帮助
help("regress")

# 面板数据命令
help("xtset")
help("xtreg")

# 数据管理
help("merge")
help("reshape")
```

**实现架构**：
该工具通过带缓存层的 CLI 调用实现 Stata 命令文档检索。文档请求以 `help <cmd>` 命令在批处理模式下执行 Stata，捕获 stdout 作为返回值。`StataHelp` 类通过 `StataFinder` 检测的平台特定 Stata CLI 路径管理调用。

缓存架构在 `~/.statamcp/help/` 目录维护帮助文本缓存，使用基于命令名的文件存储。缓存行为可通过环境变量控制：`STATA_MCP__CACHE_HELP`（默认：true）启用/禁用缓存；`STATA_MCP__SAVE_HELP` 控制缓存持久化。缓存结果包含指示缓存状态的前缀消息："Cached result for {cmd}: ..." 与实时帮助文本。

目前仅以 MCP 工具形式注册。资源注册（URI 模式 `help://stata/{cmd}`）已在 v1.16.1 因 FastMCP 的 URI 模板参数不匹配问题被禁用,工具形态保持完整可用。该工具通过 `_TOOL_REGISTRY` 中的 `unix_only` 标志进行限制，仅在 macOS 和 Linux 上可用。

缓存失效需要手动删除缓存文件或环境变量配置；不存在基于 TTL 的过期。帮助文本语言取决于 Stata 安装区域设置；多语言支持需要单独的 Stata 安装或区域设置重新配置。
