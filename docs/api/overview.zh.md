# Python API 参考

MCP-for-Stata 提供了 Python SDK，用于在 Python 中直接调用 Stata 功能。这对于构建自定义 Agent、集成到其他 Python 应用或编写 Stata 工作流脚本非常有用。

## 安装

```bash
pip install stata-mcp
```

## 快速开始

```python
from stata_mcp.api import (
    stata_do,
    get_data_info,
    ado_package_install,
    read_log,
    stata_help,
    write_dofile,
)

# 获取数据信息
info = get_data_info("/path/to/data.dta")

# 安装已启用且批准的包
result = ado_package_install("outreg2", source="ssc")

# 执行 do 文件
log = stata_do("/path/to/analysis.do")

# 读取日志文件
content = read_log("/path/to/output.log")
```

## 运行时上下文

`RuntimeContext` 为所有 API 调用提供配置和路径管理。

```python
from stata_mcp.api import RuntimeContext, create_runtime_context

# 创建运行时上下文
runtime = create_runtime_context()

# 使用自定义配置文件
runtime = create_runtime_context(config_file="/path/to/config.toml")

# 要求 Stata CLI（找不到则报错）
runtime = create_runtime_context(require_stata=True)

# 访问运行时属性
print(runtime.cwd)              # 当前工作目录
print(runtime.stata_cli)        # Stata 可执行文件路径
print(runtime.log_base_path)    # 日志目录
print(runtime.dofile_base_path) # do 文件目录
print(runtime.is_unix)          # 是否为 macOS/Linux
```

**RuntimeContext 属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `config` | `Config` | 配置对象 |
| `cwd` | `Path` | 当前工作目录 |
| `stata_cli` | `str \| None` | Stata 可执行文件路径 |
| `output_base_path` | `Path` | 基础输出目录 |
| `log_base_path` | `Path` | 日志文件目录 |
| `dofile_base_path` | `Path` | do 文件目录 |
| `tmp_base_path` | `Path` | 临时文件目录 |
| `is_unix` | `bool` | 是否为 Unix 系统（macOS/Linux） |

---

## API 函数

### stata_do()

执行 Stata do 文件并可选返回日志内容。

```python
def stata_do(
    dofile_path: str,
    log_file_name: str = None,
    read_log_when_error: bool = False,
    is_replace_log: bool = True,
    enable_smcl: bool = True,
    config_file: str | Path | None = None,
    timeout: float | None = None,
) -> Dict[str, Any]:
    ...
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dofile_path` | `str` | 必填 | do 文件路径 |
| `log_file_name` | `str` | `None` | 自定义日志文件名（不含扩展名） |
| `read_log_when_error` | `bool` | `False` | Stata 报错时才读取日志 |
| `is_replace_log` | `bool` | `True` | 替换已存在的日志文件 |
| `enable_smcl` | `bool` | `True` | 生成 SMCL 格式日志 |
| `config_file` | `str \| Path` | `None` | 自定义配置文件路径 |
| `timeout` | `float \| None` | `None` | 最大执行秒数；`None` 表示不限制执行时间 |

**返回值**：`Dict[str, Any]`

```python
{
    "log_file_path": {
        "text": "/path/to/output.log",
        "smcl": "/path/to/output.smcl"  # 如果 enable_smcl=True
    },
    "log_content": {
        "text": "..."  # 如果 read_log_when_error=True 且发生错误时的日志内容
    }
}
```

**示例**：

```python
# 基本执行
result = stata_do("/project/analysis.do")
print(result["log_content"]["text"])

# 自定义日志名
result = stata_do(
    "/project/analysis.do",
    log_file_name="my_results",
    enable_smcl=False,
)

# 执行超过五分钟时终止 Stata
result = stata_do("/project/analysis.do", timeout=300)

# 错误处理
if "error" in result:
    print(f"执行失败: {result['error']}")
```

---

### get_data_info()

返回支持的数据集的描述性统计信息。

```python
def get_data_info(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
) -> str:
    ...
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data_path` | `str` | 必填 | 数据文件路径 |
| `vars_list` | `List[str]` | `None` | 要分析的变量（None 表示全部） |
| `encoding` | `str` | `"utf-8"` | 文本文件的编码 |
| `config_file` | `str \| Path` | `None` | 自定义配置文件路径 |

**返回值**：`str`（JSON 字符串）

**支持格式**：
- Stata：`.dta`
- CSV/文本：`.csv`、`.tsv`、`.psv`
- Excel：`.xlsx`、`.xls`
- SPSS：`.sav`、`.zsav`

**示例**：

```python
import json

# 获取所有变量
info_json = get_data_info("/project/data/survey.dta")
info = json.loads(info_json)

# 获取特定变量
info_json = get_data_info(
    "/project/data/panel.csv",
    vars_list=["gdp", "inflation", "unemployment"],
    encoding="utf-8",
)

# 访问结果
print(info["overview"]["obs"])  # 观测值数量
print(info["vars_detail"].keys())  # 变量名
```

---

### ado_package_install()

从 SSC、net 或 GitHub 安装 ado 包。

```python
def ado_package_install(
    package: str,
    source: str = "ssc",
    is_replace: bool = False,
    package_source_from: str = None,
    config_file: str | Path | None = None,
    timeout: int = 300,
) -> str:
    ...
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `package` | `str` | 必填 | 包名或 GitHub 的 `user/repo` |
| `source` | `str` | `"ssc"` | 安装源：`ssc` / `net` / `github` |
| `is_replace` | `bool` | `False` | 替换已存在的包 |
| `package_source_from` | `str` | `None` | `net` 安装使用的经过校验的 HTTPS URL |
| `config_file` | `str \| Path` | `None` | 自定义配置文件路径 |
| `timeout` | `int` | `300` | 超时时间（秒） |

**输入校验**：
- Python API 不要求调用方确认
- SSC 和 net 包名只能包含 ASCII 字母与数字
- GitHub 仓库必须使用 `owner/repository` 格式并命中精确仓库白名单
- GitHub 仓库内容没有安全防护，安装前必须人工查验
- `source` 必须严格为 `ssc`、`net` 或 `github`；未知值会被拒绝
- 本地路径、IP 主机、凭据、查询参数、片段、点路径段、重复斜杠和非默认端口都会被拒绝

安装成功后，API 会尝试调用 `stata_help(..., replace=True)` 刷新 help 缓存。
SSC 和 net 使用包名；GitHub 使用仓库名部分。如果包实际提供的是其他命令名，
需要再对那些命令显式调用 `stata_help(command, replace=True)`。

**返回值**：`str`（安装日志或错误信息）

**示例**：

```python
# 从 SSC 安装
result = ado_package_install("outreg2")

# 从 GitHub 安装
result = ado_package_install("SepineTam/TexIV", source="github")

# 从网络安装
result = ado_package_install(
    "custompkg",
    source="net",
    package_source_from="https://example.com/stata",
)

# 检查安装状态
result = ado_package_install("estout", is_replace=False)
```

---

### read_log()

读取 Stata 日志文件。

```python
def read_log(
    file_path: str,
    encoding: str = "utf-8",
    is_beta: bool = False,
    *,
    output_format: Literal["full", "core", "dict"] = "dict",
    config_file: str | Path | None = None,
) -> str:
    ...
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `file_path` | `str` | 必填 | 日志文件路径（.log 或 .smcl） |
| `encoding` | `str` | `"utf-8"` | 文件编码 |
| `is_beta` | `bool` | `False` | 启用结构化解析 |
| `output_format` | `str` | `"dict"` | 输出格式：`full` / `core` / `dict` |
| `config_file` | `str \| Path` | `None` | 自定义配置文件路径 |

**返回值**：`str`

**输出格式**：
- `full`：原始日志内容
- `core`：去除框架行的干净内容
- `dict`：结构化的命令-结果对（字符串表示）

**示例**：

```python
# 读取日志内容
content = read_log("/project/logs/analysis.log")

# 获取干净输出
content = read_log(
    "/project/logs/analysis.log",
    is_beta=True,
    output_format="core",
)
```

---

### stata_help()

获取 Stata 命令文档。

> 仅支持 macOS 和 Linux

```python
def stata_help(
    cmd: str,
    config_file: str | Path | None = None,
    replace: bool = False,
) -> str:
    ...
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `cmd` | `str` | 必填 | Stata 命令名 |
| `config_file` | `str \| Path` | `None` | 自定义配置文件路径 |
| `replace` | `bool` | `False` | 跳过缓存并从 Stata 刷新帮助 |

**返回值**：`str`（帮助文本）

**示例**：

```python
# 获取命令帮助
help_text = stata_help("regress")
print(help_text)

# 面板数据命令
help_text = stata_help("xtreg")

# 强制实时查询 Stata 并覆盖缓存
help_text = stata_help("xtreg", replace=True)
```

---

### write_dofile()

创建包含 Stata 命令的 do 文件。

> **注意**：这是一个工具函数。现代 Agent 具有原生文件写入能力。

```python
def write_dofile(
    content: str,
    encoding: str | None = None,
    config_file: str | Path | None = None,
) -> str:
    ...
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `content` | `str` | 必填 | Stata 命令 |
| `encoding` | `str` | `None` | 文件编码（默认 UTF-8） |
| `config_file` | `str \| Path` | `None` | 自定义配置文件路径 |

**返回值**：`str`（创建的 do 文件路径）

**示例**：

```python
# 创建 do 文件
dofile_path = write_dofile("""
use "/data/survey.dta", clear
regress income age education
estat hettest
""")

# 执行它
result = stata_do(dofile_path)
```

---

## 错误处理

所有 API 函数返回错误信息而不是抛出异常：

```python
# 检查 stata_do 中的错误
result = stata_do("/path/to/analysis.do")
if "error" in result:
    print(f"错误: {result['error']}")
    # 处理错误
else:
    print(result["log_content"]["text"])

# get_data_info 返回错误字符串
info = get_data_info("/path/to/data.xyz")
if info.startswith("Unsupported") or info.startswith("Failed"):
    print(f"错误: {info}")
else:
    data = json.loads(info)
```

## 集成示例

### 构建自定义 Agent

```python
from stata_mcp.api import stata_do, get_data_info

def analyze_dataset(data_path: str, dofile_path: str):
    # 1. 检查数据
    info = get_data_info(data_path)

    # 2. 执行分析
    result = stata_do(dofile_path, read_log_when_error=True)

    # 3. 返回结果
    return {
        "data_info": info,
        "analysis_log": result.get("log_content", {}).get("text", ""),
    }
```

### 批量处理

```python
from stata_mcp.api import stata_do, write_dofile

datasets = ["wave1.dta", "wave2.dta", "wave3.dta"]

for dataset in datasets:
    # 为每个数据集生成 do 文件
    dofile = write_dofile(f"""
        use "/data/{dataset}", clear
        regress y x1 x2 x3
        outreg2 using "/output/{dataset}.xls", replace
    """)

    # 执行
    stata_do(dofile, log_file_name=f"analysis_{dataset}")
```
