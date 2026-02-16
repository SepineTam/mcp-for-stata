# MCP.Tools

---
## get_data_info
```python
def get_data_info(data_path: str | Path,
                  vars_list: List[str] | None = None,
                  encoding: str = "utf-8") -> str:
    ...
```

**输入参数**：
- `data_path`：数据文件的绝对文件系统路径或 URL（必填）
- `vars_list`：可选变量子集规范，用于选择性分析（默认：null，所有变量）
- `encoding`：文本格式文件的字符编码（默认：UTF-8，.dta 格式忽略）

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

**实现架构**：
该工具通过多层抽象级联运行。基础是多态类层次结构，其中 `DataInfoBase` 定义了格式特定处理器（`DtaDataInfo`、`CsvDataInfo`、`ExcelDataInfo`）的抽象接口。内容完整性验证使用 MD5 哈希，可配置后缀长度用于缓存标识。配置传播遵循优先级链：运行时参数覆盖环境变量（`STATA_MCP_DATA_INFO_DECIMAL_PLACES`、`STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`），环境变量又覆盖 `~/.statamcp/config.toml` 中的 TOML 配置。

统计计算利用 pandas DataFrame 操作，后端为 NumPy。指标系统实现可配置的计算流水线，默认指标（`obs`、`mean`、`stderr`、`min`、`max`）可通过配置扩展以包含四分位数（`q1`、`q3`）和分布形状度量（`skewness`、`kurtosis`）。类型分派将字符串变量（在 `max_display` 阈值下的观测计数和唯一值采样）与数值变量（带 `decimal_places` 精度舍入的中心趋势、离散度和分布形状计算）分开。

缓存策略采用内容可寻址存储，哈希计算决定缓存文件命名：`data_info__<name>_<ext>__hash_<suffix>.json`。缓存解析在调用时进行，当内容哈希分歧时自动重新生成。缓存目录默认为 `~/.statamcp/.cache/`，但可通过 `cache_dir` 参数覆盖为项目特定的 `stata-mcp-tmp/` 位置。

---

## stata_do
```python
def stata_do(dofile_path: str,
             log_file_name: str | None = None,
             is_read_log: bool = True) -> Dict[str, Union[str, None]]:
    ...
```

**输入参数**：
- `dofile_path`：目标 .do 文件的绝对或相对路径（必填）
- `log_file_name`：不带时间戳的自定义日志文件名（可选，如为 null 则自动生成）
- `is_read_log`：是否获取日志内容的布尔标志（默认：true）

**返回结构**：
包含执行元数据和可选日志负载的字典：
```python
{
  "log_file_path": "<absolute_path_to_stata_log>",
  "log_content": "<full_log_text_or_'Not_read_log'>"
}
```
错误情况返回：`{"error": "<exception_message>"}`

**操作示例**：
```python
# 带日志获取的标准执行
stata_do("/Users/project/stata-mcp-dofile/20250104153045.do")

# 自定义日志命名
stata_do("~/analysis/regression_pipeline.do", log_file_name="quarterly_results")

# 不读取日志的执行
stata_do("/tmp/estimation.do", is_read_log=False)
```

**实现架构**：
该工具封装了实现平台特定命令调用策略的 `StataDo` 执行器类。跨平台抽象通过 `StataFinder` 类抽象 Stata 可执行文件位置：macOS 探测 `/Applications/Stata/` 层级，Windows 查询 Program Files 注册表，Linux 在系统 PATH 中查询 `stata-mp`。执行流水线涉及 do 文件暂存、带 `-b` 批处理模式标志的 Stata CLI 调用、日志文件重定向和退出代码监控。

日志文件管理在 `stata-mcp-log/` 目录结构内运行，当省略 `log_file_name` 时自动生成时间戳。执行器根据 `is_read_log` 标志实现差异化日志处理：启用时执行文件读取操作并返回内容；禁用时返回占位符字符串以最小化 I/O 开销。

异常处理将失败分为三个层级：缺失 do 文件产物的 `FileNotFoundError`，Stata 执行失败或日志生成问题的 `RuntimeError`，以及执行或写入权限不足的 `PermissionError`。错误情况返回带 `"error"` 键的字典而非抛出异常，以保持 MCP 协议兼容性。

---

## write_dofile
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

---

## append_dofile
```python
def append_dofile(original_dofile_path: str,
                  content: str,
                  encoding: str | None = None) -> str:
    ...
```

**输入参数**：
- `original_dofile_path`：用于内容扩展的源文件路径（可能无效或为空）
- `content`：要追加的 Stata 代码（必填）
- `encoding`：字符编码（可选，默认为 UTF-8）

**返回结构**：
包含新 do 文件绝对路径的字符串（修改后的副本或新创建的产物）

**操作示例**：
```python
# 扩展现有分析
append_dofile(
    "/Users/project/stata-mcp-dofile/base_analysis.do",
    "xtreg y x1 x2, fe robust"
)

# 源文件缺失时的故障安全创建
append_dofile(
    "/nonexistent/path.do",
    "regress y x"
)
# 返回包含提供内容的新文件路径

# 迭代分析的代码组合
append_dofile(
    previous_dofile_path,
    """
predict residuals, residuals
summarize residuals
"""
)
```

**实现架构**：
该工具通过三阶段操作实现故障安全组合策略：验证阶段通过 `Path.exists()` 探测检查 `original_dofile_path` 是否存在和可访问；组合阶段执行条件内容组装，有效源文件触发读取操作后进行连接，而无效路径触发新文件创建；持久化阶段将组合内容写入 `stata-mcp-dofile/` 层级中新的带时间戳产物。

关键设计特征：源文件保持不变。所有组合操作创建带有新时间戳的新产物，确保源不可变性和保留来源。换行完整性维护检查源文件终止；如果源内容缺少尾随换行符，则在内容追加前插入分隔符。

该工具不执行原始内容和追加内容之间的语法一致性验证。宏变量作用域、临时变量命名冲突和命令序列有效性需要调用者手动协调。与 `write_dofile` 类似，输出重定向路径管理需要在需要显式输出文件规范的命令之前调用 `results_doc_path`。

平台特定路径解析使用 `pathlib.Path` 实现跨平台兼容性。文件读取操作使用指定的编码参数，回退到 UTF-8 默认值。错误处理将 I/O 操作包装起来，读取错误时静默失败，将读取异常视为等同于缺失源文件。

---

## mk_dir
```python
def mk_dir(path: str) -> bool:
    ...
```

**输入参数**：
- `path`：目录路径规范（字符串，必填，非空）

**返回结构**：
表示创建后目录存在验证的布尔值（true：存在，false：创建失败）

**操作示例**：
```python
# 单个目录创建
mk_dir("/Users/project/outputs")
# 返回：True

# 递归层级创建
mk_dir("~/analysis/2025/q1/january")
# 创建：analysis/, analysis/2025/, analysis/2025/q1/, analysis/2025/q1/january/

# 跨平台路径
mk_dir("C:\\Users\\project\\data")  # Windows
mk_dir("/home/user/analysis")       # Unix
```

**实现架构**：
该工具通过 `pathvalidate` 库的 `sanitize_filepath()` 函数实现安全目录创建，具有平台特定验证。清理阶段移除目录遍历序列、规范化路径分隔符并验证字符编码。路径解析通过 `Path.resolve()` 将清理后的输入转换为绝对形式，消除符号链接和相对路径组件。

目录创建使用 `Path.mkdir()` 及参数 `mode=0o755`（rwxr-xr-x：所有者读/写/执行，组/其他读/执行）、`exist_ok=True`（幂等操作）和 `parents=True`（递归创建）。权限配置遵循 Unix 文件系统约定，组和他人具有读/执行权限以启用目录遍历和列表。

异常层次提供细粒度的失败诊断：通过清理阶段的 `ValidationError` 检测无效路径时抛出 `ValueError`；OS 检测到目录创建权限不足时抛出 `PermissionError`；文件系统级故障（磁盘满、配额超限、只读文件系统）时抛出 `OSError`。所有异常向调用者传播并附带描述性消息。

创建后验证通过 `Path.exists()` 结合 `Path.is_dir()` 执行布尔存在检查，以确认目录成功创建并区分同名目录和文件。

---

## load_figure
```python
def load_figure(figure_path: str) -> Image:
    ...
```

**输入参数**：
- `figure_path`：图像文件的绝对路径（必填）

**返回结构**：
包含用于 MCP 传输和显示的图像数据的 FastMCP `Image` 对象

**操作示例**：
```python
# 加载 Stata 生成的图形
load_figure("/Users/project/exports/regression_results.png")

# 加载导出的图形
load_figure("~/analysis/timeseries_plot.jpg")
```

**实现架构**：
该工具使用 FastMCP 的原生 `Image` 类包装器从本地文件系统实现图像资产加载。路径验证通过 `Path.exists()` 探测检查文件是否存在；缺失资产触发带描述性消息的 `FileNotFoundError` 异常。成功调用时，以文件路径作为初始化参数构造 `Image` 对象，使底层 MCP 框架能够自动读取文件和检测 MIME 类型。

支持的格式取决于 FastMCP 实现，但通常包括 PNG（Portable Network Graphics）和 JPEG（Joint Photographic Experts Group）。该工具不执行格式验证或转换；不支持的格式在 Image 对象构造或传输阶段生成错误。

错误日志记录在异常传播之前将结构化消息写入日志基础设施，使失败加载尝试的审计跟踪成为可能。该工具不执行图像处理、调整大小或格式转换——操作在 MCP 客户端应用的显示/渲染时进行。

---

## read_file
```python
def read_file(file_path: str,
              encoding: str = "utf-8") -> str:
    ...
```

**输入参数**：
- `file_path`：目标文件的绝对路径（必填）
- `encoding`：文本解码的字符编码（可选，默认为 UTF-8）

**返回结构**：
包含使用指定编码解码的完整文件内容的字符串

**操作示例**：
```python
# 读取 Stata 日志文件
read_file("/Users/project/stata-mcp-log/20250104153045.log")

# 带编码读取配置
read_file("~/.statamcp/config.toml", encoding="utf-8")

# 读取导出的结果
read_file("~/analysis/tables/regression_results.txt")
```

**实现架构**：
该工具使用 Python 内置的 `open()` 函数实现通用文件读取，模式为 `"r"` 和指定的编码参数。路径验证通过 `Path.exists()` 检查文件是否存在；缺失文件抛出带描述性消息（包含无效路径）的 `FileNotFoundError`。文件读取使用上下文管理器（`with` 语句）以实现自动文件句柄关闭和资源清理。

内容读取执行单次 `file.read()` 操作，将整个文件内容作为字符串检索到内存中。对于超过可用内存的大文件，此方法触发 `MemoryError`；但典型用例涉及合理大小范围内的日志文件、配置文件和结果表。

错误处理将失败分类：不存在的路径为 `FileNotFoundError`，I/O 操作失败（权限被拒绝、磁盘读取错误、文件系统损坏）为 `IOError`，编码不匹配为 `UnicodeDecodeError`（虽未显式捕获，但会向调用者传播并附带编码信息）。成功操作记录包含文件路径的结构化消息以供审计跟踪。

---

## ado_package_install
```python
def ado_package_install(package: str,
                        source: str = "ssc",
                        is_replace: bool = True,
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
- `is_replace`：强制替换标志（可选，默认：true）
- `package_source_from`：'net' 安装的源 URL 或目录（可选）

**返回结构**：
包含安装操作完整 Stata 执行日志的字符串

**操作示例**：
```python
# SSC 包安装
ado_package_install("outreg2", source="ssc")

# GitHub 包安装
ado_package_install("sepinetam/texiv", source="github")

# 网络安装
ado_package_install("custompkg", source="net", package_source_from="https://example.com/stata/")

# 强制重新安装
ado_package_install("estout", source="ssc", is_replace=True)
```

**实现架构**：
该工具实现平台差异化的安装策略。Unix 系统（macOS/Linux）通过继承自基础安装器接口的专用安装器类执行：`SSC_Install` 通过 Stata CLI 调用 `ssc install <package>, replace`；`GITHUB_Install` 执行 `github install <username/reponame>, replace`；`NET_Install` 运行 `net install <package> from(<source>), replace`。Windows 系统绕过直接安装，而是通过 `write_dofile` 生成临时 do 文件并委托给 `stata_do` 执行。

安装验证通过消息解析进行，安装器类检查 Stata 输出中的成功指示器。`check_installed_from_msg()` 方法执行正则或子字符串匹配以识别成功安装模式。失败的安装触发错误日志记录，通过调试级日志记录完整消息捕获。

性能考虑建议避免不必要的调用，因为网络延迟、仓库查找开销和包已存在时的冗余安装尝试。该工具不实现本地安装缓存——每次调用都查询远程仓库或文件系统。

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

缓存架构在 `~/.statamcp/help/` 目录维护帮助文本缓存，使用基于命令名的文件存储。缓存行为可通过环境变量控制：`STATA_MCP_CACHE_HELP`（默认：true）启用/禁用缓存；`STATA_MCP_SAVE_HELP` 控制缓存持久化。缓存结果包含指示缓存状态的前缀消息："Cached result for {cmd}: ..." 与实时帮助文本。

双重装饰模式将工具注册为 MCP 资源和可执行函数。资源 URI 模式 `help://stata/{cmd}` 通过 MCP 资源协议启用基于 URI 的访问，而函数装饰器 `@stata_mcp.tool()` 启用直接调用。这种双重注册为不同的 MCP 客户端实现提供灵活的访问模式。

缓存失效需要手动删除缓存文件或环境变量配置；不存在基于 TTL 的过期。帮助文本语言取决于 Stata 安装区域设置；多语言支持需要单独的 Stata 安装或区域设置重新配置。
