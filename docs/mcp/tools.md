# MCP.Tools

Tools are partitioned into two profiles inside `_TOOL_REGISTRY`. `stata-mcp server --core` registers only `stata_do`, `get_data_info`, and `help`. `stata-mcp server --all` (the default) registers every tool in the registry. The `help` tool carries an `unix_only` flag and is filtered out on Windows during `register_tools()`. The `write_dofile` tool is flagged deprecated and is skipped unless `ENABLE_WRITE_DOFILE` (TOML `[BETA]` section or env `STATA_MCP__ENABLE_WRITE_DOFILE`) is set to `true`.

---
## get_data_info
```python
def get_data_info(data_path: str | Path,
                  vars_list: List[str] | None = None,
                  encoding: str = "utf-8",
                  head: int = 0) -> str:
    ...
```

**Input Parameters**:
- `data_path`: Absolute filesystem path or URL to data file (required)
- `vars_list`: Optional variable subset specification for selective analysis (default: null, all variables)
- `encoding`: Character encoding for text-based formats (default: UTF-8, ignored for .dta)
- `head`: Number of preview rows to display from the dataset (default: 0, disabled to avoid context overflow on large datasets)

**Return Structure**:
Serialized JSON string containing multi-layered metadata:
```json
{
  "overview": {"source": <path>, "obs": <int>, "var_numbers": <int>, "var_list": [<array>]},
  "info_config": {"metrics": [<array>], "max_display": <int>, "decimal_places": <int>},
  "vars_detail": {<variable_name>: {"var": <str>, "type": <str>, "summary": {...}}},
  "saved_path": <cache_file_path>
}
```

**Operational Examples**:
```python
# Local file analysis
get_data_info("/data/econometrics/survey.dta")
get_data_info("~/Documents/exports/quarterly.csv", vars_list=["gdp", "inflation", "unemployment"])

# Remote data ingestion
get_data_info("https://repository.org/datasets/panel_data.xlsx")

# Encoded source handling
get_data_info("/data/legacy/latin1_data.csv", encoding="latin1")
```

**Supported Formats**:
- **Stata**: `.dta`
- **CSV/Text**: `.csv`, `.tsv`, `.psv`
- **Excel**: `.xlsx`, `.xls`
- **SPSS**: `.sav`, `.zsav`

**Implementation Architecture**:
The tool operates through a multi-layered abstraction cascade. At the foundation lies a polymorphic class hierarchy where `DataInfoBase` defines the abstract interface for format-specific handlers (`DtaDataInfo`, `CsvDataInfo`, `ExcelDataInfo`, `SpssDataInfo`). Content integrity verification employs MD5 hashing with configurable suffix length for cache identification. Configuration propagation follows a precedence chain: runtime parameters override environment variables (`STATA_MCP_DATA_INFO_DECIMAL_PLACES`, `STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`), which in turn override TOML-based configuration at `~/.statamcp/config.toml`.

Statistical computation leverages pandas DataFrame operations with NumPy backend. The metrics system implements a configurable computation pipeline where default metrics (`obs`, `mean`, `stderr`, `min`, `max`) can be extended through configuration to include quartiles (`q1`, `q3`) and distribution shape measures (`skewness`, `kurtosis`). Type dispatch separates string variables (observation counting with unique value sampling under `max_display` threshold) from numeric variables (central tendency, dispersion, and distribution shape computation with `decimal_places` precision rounding).

Caching strategy employs content-addressable storage where hash computation determines cache file naming: `data_info__<name>_<ext>__hash_<suffix>.json`. Cache resolution occurs at invocation time, with automatic regeneration on content hash divergence. The cache directory defaults to `~/.statamcp/.cache/` but can be overridden to project-specific `stata-mcp-tmp/` locations through the `cache_dir` parameter.

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

**Input Parameters**:
- `dofile_path`: Absolute or relative path to target .do file (required)
- `log_file_name`: Custom log filename without timestamp (optional, auto-generated if null)
- `read_log_when_error`: Boolean flag that gates log payload retrieval; the tool only reads the log when a Stata return-code error (e.g. `r(198)`) is detected, keeping the success path I/O-free (default: false)
- `is_replace_log`: Boolean flag controlling whether an existing log file with the same name is overwritten (default: true)
- `enable_smcl`: Boolean flag toggling SMCL formatted logging; when true the Stata CLI is invoked without the `nolog` redirection so both `.smcl` and `.log` artifacts are produced (default: true)

**Return Structure**:
Dictionary containing execution metadata and optional log payload:
```python
{
  "log_file_path": {"text": "<absolute_path_to_log>", "smcl": "<absolute_path_to_smcl>"},
  "log_content": {"text": "<error_log_text_or_placeholder>", "smcl": "<smcl_path>"}
}
```
The `log_content` key is only present when `read_log_when_error=True`. Error condition returns: `{"error": "<exception_message>"}`.

**Operational Examples**:
```python
# Standard execution; log payload skipped on success
stata_do("/Users/project/stata-mcp-dofile/20250104153045.do")

# Custom log naming
stata_do("~/analysis/regression_pipeline.do", log_file_name="quarterly_results")

# Surface log content only when Stata reports an error
stata_do("/tmp/estimation.do", read_log_when_error=True)

# Keep prior logs and disable SMCL output
stata_do("/tmp/estimation.do",
         read_log_when_error=True,
         is_replace_log=False,
         enable_smcl=False)
```

**Implementation Architecture**:
The tool encapsulates the `StataDo` executor class which implements platform-specific command invocation strategies. Cross-platform abstraction abstracts Stata executable location through the `StataFinder` class: macOS probes `/Applications/Stata/` hierarchy, Windows interrogates Program Files registry, and Linux queries system PATH for `stata-mp`. The execution pipeline involves do-file staging, Stata CLI invocation with `-b` batch mode flag, log file redirection, and exit code monitoring.

Log file management operates within the `stata-mcp-log/` directory structure with automatic timestamp generation when `log_file_name` is omitted. The `is_replace_log` flag determines whether prior logs are overwritten, and `enable_smcl` decides whether the SMCL artifact is emitted alongside the plain text log. The executor implements conditional log retrieval based on the `read_log_when_error` flag: the text log is scanned with the `r(\d+)` pattern, and only when a Stata return-code error is detected does the tool return the log payload, otherwise it returns a placeholder pointing users to the `read_log` tool.

Exception handling categorizes failures into three tiers: `FileNotFoundError` for missing do-file artifacts, `RuntimeError` for Stata execution failures or log generation issues, and `PermissionError` for insufficient execution or write permissions. Error conditions return dictionary with `"error"` key rather than raising exceptions to maintain MCP protocol compatibility.

---

## write_dofile
> **Disabled by Default**: Whether this tool is registered with the MCP server is controlled by the `ENABLE_WRITE_DOFILE` switch. Without setting it to `true`, `register_tools()` skips this entry entirely and the tool will not be exposed to the client.
>
> Modern AI agents have native file writing capabilities, making this tool redundant.
> To enable, set `STATA_MCP__ENABLE_WRITE_DOFILE=true` or add `[BETA] ENABLE_WRITE_DOFILE = true` to your config.

```python
def write_dofile(content: str,
                 encoding: str | None = None) -> str:
    ...
```

**Input Parameters**:
- `content`: Stata command sequence to persist (required)
- `encoding`: Character encoding for file output (optional, defaults to UTF-8)

**Return Structure**:
String containing absolute POSIX-compliant path to generated do-file

**Operational Examples**:
```python
# Basic regression analysis
write_dofile("""
use "/data/survey.dta", clear
regress income age education experience
outreg2 using "`output_path'/results.doc", replace
""")

# Time series analysis with encoding specification
write_dofile("""
tsset date
arima gdp, ar(1) ma(1)
predict forecast
""", encoding="latin1")

# Data transformation pipeline
write_dofile("""
gen log_gdp = ln(gdp)
gen diff_income = d(income)
xtset country_id year
xtreg diff_income log_gdp, fe
""")
```

**Implementation Architecture**:
The tool implements atomic file creation within the `stata-mcp-dofile/` directory hierarchy. File naming employs ISO 8601 basic format timestamp generation (`YYYYMMDDHHMMSS.do`) ensuring temporal uniqueness and chronological sorting. The write operation utilizes Python's built-in `open()` function with mode `"w"` and specified encoding parameter, performing implicit file creation and truncation for atomic write semantics.

Integration with output redirection commands (`outreg2`, `esttab`) requires coordination with the `results_doc_path` prompt to establish output directory paths prior to do-file generation. This separation of concerns enables deterministic output path management across multiple Stata execution cycles.

The tool does not perform syntactic validation or semantic analysis of the Stata code content. Code correctness, command sequencing, and macro expansion validity remain the responsibility of the calling context. Error handling wraps file I/O operations in try-except blocks with structured logging for success/failure tracking.

> **Deprecation Notice**: This tool is disabled by default and will be removed in a future version. Modern AI agents have native file writing capabilities, so use those instead.

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

**Input Parameters**:
- `file_path`: Absolute path to target log file (required, `.log` or `.smcl`)
- `encoding`: Character encoding for text decoding (optional, defaults to UTF-8)
- `is_beta`: Enable structured log parsing with StataLog module (optional, default: false)
  - **macOS/Linux only** - Windows users should use default behavior
  - Recommended for `.smcl` files with `dict` format
- `lines`: Content trimming control (default: 0, no trimming)
  - `> 0`: return first N items (lines for full/core, entries for dict)
  - `< 0`: return last |N| items (lines for full/core, entries for dict)
  - `0`: return full content
- `output_format`: Output format when `is_beta=true` (optional, default: "dict")
  - `full`: Raw log content without processing
  - `core`: Cleaned content with framework lines removed
  - `dict`: Structured command-result pairs (recommended)

**Return Structure**:
- Default mode (`is_beta=false`): Raw string content of the file
- Beta mode (`is_beta=true`): Depends on `output_format`:
  - `full`: Plain text log content
  - `core`: Log content without framework (headers, footers, log commands)
  - `dict`: String representation of command-result list

**Operational Examples**:
```python
# Read log file (default mode)
read_log("/Users/project/stata-mcp-log/20250104153045.log")

# Read SMCL log with structured parsing (macOS/Linux)
read_log("/Users/project/stata-mcp-log/20250104153045.smcl",
         is_beta=True,
         output_format="dict")

# Get cleaned log content without framework
read_log("~/stata-mcp-log/session.log",
         is_beta=True,
         output_format="core")

# Read with custom encoding
read_log("~/analysis/tables/results.txt", encoding="utf-8")
```

**Implementation Architecture**:
The tool implements dual-mode log reading: traditional file reading and structured parsing via the `StataLog` module.

**Traditional Mode** (`is_beta=false`): Generic file reading via Python's `open()` function with mode `"r"`. Path validation checks file existence through `Path.exists()`. Content reading uses single `file.read()` operation for complete file retrieval.

**Structured Parsing Mode** (`is_beta=true`, Unix only): Leverages the `stata_log` module which provides:
- `StataLogTEXT`: Parser for `.log` (plain text) files
- `StataLogSMCL`: Parser for `.smcl` (Stata Markup and Control Language) files
- `StataLogInfo`: Dataclass containing `command_result_list` with structured command-output pairs

The `StataLog` factory class (`from_path()` method) automatically detects file extension and returns the appropriate parser. Framework removal eliminates log headers/footers, `log using/close` commands, and do-file execution markers, preserving only actual Stata commands and their outputs.

**Output Format Details**:
- `full`: Equivalent to `read_plain_text()` - raw file content
- `core`: Equivalent to `read_without_framework()` - cleaned content
- `dict`: Returns `str(log_info.read_as_dict())` - structured mapping

Error handling covers: `FileNotFoundError` for missing files, `IOError` for I/O failures, `ValueError` for invalid `output_format`, and `UnicodeDecodeError` for encoding mismatches.

---

## ado_package_install
```python
def ado_package_install(package: str,
                        source: str = "ssc",
                        is_replace: bool = True,
                        package_source_from: str | None = None) -> str:
    ...
```

**Input Parameters**:
- `package`: Package identifier (required)
  - SSC: package name (e.g., "outreg2")
  - GitHub: "username/reponame" format (e.g., "sepinetam/texiv")
  - net: package name with `package_source_from` specifying source
- `source`: Distribution source (optional, default: "ssc")
  - Options: "ssc", "github", "net"
- `is_replace`: Force replacement flag (optional, default: true)
- `package_source_from`: Source URL or directory for 'net' installations (optional)

Inputs are validated before any Stata execution. SSC and net package names must
be Stata identifiers, GitHub packages must use a safe `owner/repository` value,
unknown sources are rejected, and net source locations cannot contain whitespace
or Stata syntax and macro delimiters.

**Return Structure**:
String containing complete Stata execution log from installation operation

**Operational Examples**:
```python
# SSC package installation
ado_package_install("outreg2", source="ssc")

# GitHub package installation
ado_package_install("sepinetam/texiv", source="github")

# Network installation
ado_package_install("custompkg", source="net", package_source_from="https://example.com/stata/")

# Force reinstall
ado_package_install("estout", source="ssc", is_replace=True)
```

**Implementation Architecture**:
The tool implements platform-divergent installation strategies. Unix systems (macOS/Linux) execute through specialized installer classes inheriting from base installer interface: `SSC_Install` invokes `ssc install <package>, replace` via Stata CLI; `GITHUB_Install` executes `github install <username/reponame>, replace`; `NET_Install` runs `net install <package> from(<source>), replace`. Windows systems bypass direct installation, instead generating temporary do-file via `write_dofile` and delegating to `stata_do` execution.

Installation verification occurs through message parsing where installer classes examine Stata output for success indicators. The `check_installed_from_msg()` method performs regex or substring matching to identify successful installation patterns. Failed installations trigger error logging with full message capture via debug-level logging.

Performance considerations advise against unnecessary invocations due to network latency, repository lookup overhead, and redundant installation attempts when packages already exist in Stata's ado directory. The tool implements no local installation cache—each invocation queries remote repositories or filesystem.

---

## help
> macOS and Linux only

```python
def help(cmd: str) -> str:
    ...
```

**Input Parameters**:
- `cmd`: Stata command name (required, e.g., "regress", "describe", "xtset")

**Return Structure**:
String containing Stata help text output with optional cache status prefix (e.g., "Cached result for regress: ...")

**Operational Examples**:
```python
# Regression command help
help("regress")

# Panel data commands
help("xtset")
help("xtreg")

# Data management
help("merge")
help("reshape")
```

**Implementation Architecture**:
The tool implements Stata command documentation retrieval through CLI invocation with caching layer. Documentation requests execute Stata in batch mode with `help <cmd>` command, capturing stdout for return value. The `StataHelp` class manages invocation through platform-specific Stata CLI paths detected by `StataFinder`.

Caching architecture maintains help text cache at `~/.statamcp/help/` directory with file-based storage keyed by command name. Cache behavior controllable via environment variables: `STATA_MCP__CACHE_HELP` (default: true) enables/disables caching; `STATA_MCP__SAVE_HELP` controls cache persistence. Cached results include prefix message indicating cache status: "Cached result for {cmd}: ..." versus live help text.

Currently registered only as an MCP tool. Resource registration (URI pattern `help://stata/{cmd}`) was disabled in v1.16.1 due to a URI template parameter mismatch with FastMCP; tool form remains fully functional. The tool is gated by the `unix_only` flag in `_TOOL_REGISTRY` and is only available on macOS and Linux.

Cache invalidation requires manual deletion of cache files or environment variable configuration; no TTL-based expiration exists. Help text language depends on Stata installation locale; multilingual support requires separate Stata installations or locale reconfiguration.
