# Python API Reference

Stata-MCP provides a Python SDK for programmatic access to Stata functionality. This is useful for building custom agents, integrating with other Python applications, or scripting Stata workflows.

## Installation

```bash
pip install stata-mcp
```

## Quick Start

```python
from stata_mcp.api import (
    stata_do,
    get_data_info,
    ado_package_install,
    read_log,
    stata_help,
    write_dofile,
)

# Get data information
info = get_data_info("/path/to/data.dta")

# Install a package
result = ado_package_install("outreg2", source="ssc")

# Execute a do-file
log = stata_do("/path/to/analysis.do")

# Read log file
content = read_log("/path/to/output.log")
```

## Runtime Context

The `RuntimeContext` provides configuration and path management for all API calls.

```python
from stata_mcp.api import RuntimeContext, create_runtime_context

# Create a runtime context
runtime = create_runtime_context()

# With custom config file
runtime = create_runtime_context(config_file="/path/to/config.toml")

# With Stata CLI required (raises error if not found)
runtime = create_runtime_context(require_stata=True)

# Access runtime properties
print(runtime.cwd)              # Current working directory
print(runtime.stata_cli)        # Stata executable path
print(runtime.log_base_path)    # Log directory
print(runtime.dofile_base_path) # Do-file directory
print(runtime.is_unix)          # Is macOS/Linux
```

**RuntimeContext Properties**:

| Property | Type | Description |
|----------|------|-------------|
| `config` | `Config` | Configuration object |
| `cwd` | `Path` | Current working directory |
| `stata_cli` | `str \| None` | Stata executable path |
| `output_base_path` | `Path` | Base output directory |
| `log_base_path` | `Path` | Log file directory |
| `dofile_base_path` | `Path` | Do-file directory |
| `tmp_base_path` | `Path` | Temporary files directory |
| `is_unix` | `bool` | Is Unix-like system (macOS/Linux) |

---

## API Functions

### stata_do()

Execute a Stata do-file and optionally return log content.

```python
def stata_do(
    dofile_path: str,
    log_file_name: str = None,
    is_read_log: bool = True,
    is_replace_log: bool = True,
    enable_smcl: bool = True,
    config_file: str | Path | None = None,
) -> Dict[str, Any]:
    ...
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dofile_path` | `str` | required | Path to do-file |
| `log_file_name` | `str` | `None` | Custom log filename (without extension) |
| `is_read_log` | `bool` | `True` | Read log content after execution |
| `is_replace_log` | `bool` | `True` | Replace existing log file |
| `enable_smcl` | `bool` | `True` | Generate SMCL format log |
| `config_file` | `str \| Path` | `None` | Custom config file path |

**Returns**: `Dict[str, Any]`

```python
{
    "log_file_path": {
        "text": "/path/to/output.log",
        "smcl": "/path/to/output.smcl"  # if enable_smcl=True
    },
    "log_content": {
        "text": "..."  # log content if is_read_log=True
    }
}
```

**Example**:

```python
# Basic execution
result = stata_do("/project/analysis.do")
print(result["log_content"]["text"])

# With custom log name
result = stata_do(
    "/project/analysis.do",
    log_file_name="my_results",
    enable_smcl=False,
)

# Error handling
if "error" in result:
    print(f"Execution failed: {result['error']}")
```

---

### get_data_info()

Return descriptive statistics for a supported dataset.

```python
def get_data_info(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
) -> str:
    ...
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_path` | `str` | required | Path to data file |
| `vars_list` | `List[str]` | `None` | Variables to analyze (all if None) |
| `encoding` | `str` | `"utf-8"` | Text encoding for text-based files |
| `config_file` | `str \| Path` | `None` | Custom config file path |

**Returns**: `str` (JSON string)

**Supported Formats**:
- Stata: `.dta`
- CSV/Text: `.csv`, `.tsv`, `.psv`
- Excel: `.xlsx`, `.xls`
- SPSS: `.sav`, `.zsav`

**Example**:

```python
import json

# Get all variables
info_json = get_data_info("/project/data/survey.dta")
info = json.loads(info_json)

# Get specific variables
info_json = get_data_info(
    "/project/data/panel.csv",
    vars_list=["gdp", "inflation", "unemployment"],
    encoding="utf-8",
)

# Access the result
print(info["overview"]["obs"])  # Number of observations
print(info["vars_detail"].keys())  # Variable names
```

---

### ado_package_install()

Install an ado package from SSC, net, or GitHub.

```python
def ado_package_install(
    package: str,
    source: str = "ssc",
    is_replace: bool = True,
    package_source_from: str = None,
    config_file: str | Path | None = None,
    timeout: int = 300,
) -> str:
    ...
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `package` | `str` | required | Package name or `user/repo` for GitHub |
| `source` | `str` | `"ssc"` | Installation source: `ssc` / `net` / `github` |
| `is_replace` | `bool` | `True` | Replace existing package |
| `package_source_from` | `str` | `None` | Source URL for `net` installations |
| `config_file` | `str \| Path` | `None` | Custom config file path |
| `timeout` | `int` | `300` | Timeout in seconds |

**Returns**: `str` (installation log or error message)

**Example**:

```python
# Install from SSC
result = ado_package_install("outreg2")

# Install from GitHub
result = ado_package_install("SepineTam/TexIV", source="github")

# Install from network
result = ado_package_install(
    "custompkg",
    source="net",
    package_source_from="https://example.com/stata/",
)

# Check installation status
result = ado_package_install("estout", is_replace=False)
```

---

### read_log()

Read a Stata log file.

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

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `str` | required | Path to log file (.log or .smcl) |
| `encoding` | `str` | `"utf-8"` | File encoding |
| `is_beta` | `bool` | `False` | Enable structured parsing |
| `output_format` | `str` | `"dict"` | Output format: `full` / `core` / `dict` |
| `config_file` | `str \| Path` | `None` | Custom config file path |

**Returns**: `str`

**Output Formats**:
- `full`: Raw log content
- `core`: Cleaned content without framework lines
- `dict`: Structured command-result pairs (string representation)

**Example**:

```python
# Read log content
content = read_log("/project/logs/analysis.log")

# Get clean output
content = read_log(
    "/project/logs/analysis.log",
    is_beta=True,
    output_format="core",
)
```

---

### stata_help()

Get Stata command documentation.

> macOS and Linux only

```python
def stata_help(
    cmd: str,
    config_file: str | Path | None = None,
) -> str:
    ...
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cmd` | `str` | required | Stata command name |
| `config_file` | `str \| Path` | `None` | Custom config file path |

**Returns**: `str` (help text)

**Example**:

```python
# Get help for a command
help_text = stata_help("regress")
print(help_text)

# Panel data commands
help_text = stata_help("xtreg")
```

---

### write_dofile()

Create a do-file with Stata commands.

> **Note**: This is a utility function. Modern agents have native file writing capabilities.

```python
def write_dofile(
    content: str,
    encoding: str | None = None,
    config_file: str | Path | None = None,
) -> str:
    ...
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | required | Stata commands |
| `encoding` | `str` | `None` | File encoding (defaults to UTF-8) |
| `config_file` | `str \| Path` | `None` | Custom config file path |

**Returns**: `str` (path to created do-file)

**Example**:

```python
# Create a do-file
dofile_path = write_dofile("""
use "/data/survey.dta", clear
regress income age education
estat hettest
""")

# Execute it
result = stata_do(dofile_path)
```

---

## Error Handling

All API functions return error information rather than raising exceptions:

```python
# Check for errors in stata_do
result = stata_do("/path/to/analysis.do")
if "error" in result:
    print(f"Error: {result['error']}")
    # Handle error
else:
    print(result["log_content"]["text"])

# get_data_info returns error as string
info = get_data_info("/path/to/data.xyz")
if info.startswith("Unsupported") or info.startswith("Failed"):
    print(f"Error: {info}")
else:
    data = json.loads(info)
```

## Integration Examples

### Building a Custom Agent

```python
from stata_mcp.api import stata_do, get_data_info

def analyze_dataset(data_path: str, dofile_path: str):
    # 1. Inspect data
    info = get_data_info(data_path)

    # 2. Execute analysis
    result = stata_do(dofile_path, is_read_log=True)

    # 3. Return results
    return {
        "data_info": info,
        "analysis_log": result.get("log_content", {}).get("text", ""),
    }
```

### Batch Processing

```python
from stata_mcp.api import stata_do, write_dofile

datasets = ["wave1.dta", "wave2.dta", "wave3.dta"]

for dataset in datasets:
    # Generate do-file for each dataset
    dofile = write_dofile(f"""
        use "/data/{dataset}", clear
        regress y x1 x2 x3
        outreg2 using "/output/{dataset}.xls", replace
    """)

    # Execute
    stata_do(dofile, log_file_name=f"analysis_{dataset}")
```
