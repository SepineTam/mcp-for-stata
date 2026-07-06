# Use in OpenClaw 🦞

> **Deprecated**: MCP-for-Stata's built-in agent mode is marked with `FutureWarning` since v1.16.x and will be removed in a future release. New workflows should use MCP server mode (`stata-mcp server` or `stata-mcp install -c <client>`) and rely on the host AI client's native agent capabilities instead.
>
> Note: To configure OpenClaw as an MCP client, please refer to `docs/clients.md`.

Since OpenClaw does not natively support the MCP tool protocol, MCP-for-Stata provides standalone CLI tool commands that OpenClaw can use through terminal tool invocation.

## Install instruction OpenClaw

Tell your OpenClaw with the following message:

```text
Install MCP-for-Stata Skills from https://sepinetam.github.io/mcp-for-stata/skills/openclaw
```

If you are OpenClaw, go to [MCP-for-Stata Skill for OpenClaw](https://sepinetam.github.io/mcp-for-stata/skills/openclaw).

## Installation Manually

```bash
# Run directly with uvx (recommended)
uvx stata-mcp tool --help

# Or install and use
uv pip install stata-mcp
stata-mcp tool --help
```

## Available Commands

### ado-install - Install Stata Packages

Install ado packages from SSC, GitHub, or network sources.

```bash
# Install an approved SSC package
stata-mcp tool ado-install outreg2 --yes

# Install from GitHub
stata-mcp tool ado-install SepineTam/TexIV --source github --yes

# Install from network
stata-mcp tool ado-install custompkg --source net --package-source-from "https://example.com/stata/" --yes

# Don't replace existing package (useful for checking installation status)
stata-mcp tool ado-install estout --yes --is-replace false
```

**Parameters**:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `package_name` | Package name (required) | - |
| `--source` | Installation source: ssc / net / github | ssc |
| `--package-source-from` | Source URL for net installations | - |
| `--is-replace` | Replace existing package files | false |
| `-y`, `--yes` | Skip the interactive installation confirmation | false |

Without `-y` or `--yes`, the CLI asks for interactive confirmation. SSC and net
package names may contain only ASCII letters and numbers. GitHub repositories
require an exact allowlist and their contents must be inspected before
installation.

---

### do - Execute Do-files

Execute Stata do-files and retrieve logs.

```bash
# Execute a do-file
stata-mcp tool do /path/to/analysis.do

# Specify log file name
stata-mcp tool do /path/to/analysis.do --log-file-name my_results

# Skip reading log content
stata-mcp tool do /path/to/analysis.do --is-read-log false

# Disable SMCL format logging
stata-mcp tool do /path/to/analysis.do --enable-smcl false

# Stop execution after five minutes
stata-mcp tool do /path/to/analysis.do --timeout 300
```

**Parameters**:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `dofile_path` | Path to do-file (required) | - |
| `--log-file-name` | Log filename without extension | auto-generated |
| `--timeout` | Maximum execution time in seconds | no timeout |
| `--is-read-log` | Read log content after execution | true |
| `--is-replace-log` | Replace existing log file | true |
| `--enable-smcl` | Generate SMCL format log | true |

---

### help - Get Stata Command Help

> macOS and Linux only

```bash
# Get command help
stata-mcp tool help regress

# Get panel data command help
stata-mcp tool help xtreg
stata-mcp tool help xtset
```

**Parameters**:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `stata_command` | Stata command name (required) | - |
| `--replace` | Skip caches and refresh help from Stata | false |

---

### data-info - Get Data Information

Analyze data files and return statistical summaries.

```bash
# Analyze a data file
stata-mcp tool data-info /path/to/data.dta

# Specify variable subset
stata-mcp tool data-info /path/to/data.csv --vars-list gdp inflation unemployment

# Specify encoding
stata-mcp tool data-info /path/to/legacy.csv --encoding latin1
```

**Supported Formats**:
- Stata: `.dta`
- CSV/Text: `.csv`, `.tsv`, `.psv`
- Excel: `.xlsx`, `.xls`
- SPSS: `.sav`, `.zsav`

**Parameters**:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `data_path` | Path to data file (required) | - |
| `--encoding` | Text encoding | utf-8 |
| `--vars-list` | Variable names to analyze | all variables |

---

### read-log - Read Log Files

Read Stata log files (.log or .smcl).

```bash
# Read log (core content)
stata-mcp tool read-log /path/to/output.log

# Read full log
stata-mcp tool read-log /path/to/output.log --output-format full

# Read as structured format
stata-mcp tool read-log /path/to/output.log --output-format dict

# Specify encoding
stata-mcp tool read-log /path/to/output.log --encoding utf-8
```

**Parameters**:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `file_path` | Path to log file (required) | - |
| `--encoding` | File encoding | utf-8 |
| `--output-format` | Output format: full / core / dict | core |

**Output Format Descriptions**:
- `full`: Raw log content
- `core`: Cleaned content without framework lines (headers, footers, log commands)
- `dict`: Structured command-result pairs

---

## Typical Workflow

```bash
# 1. Inspect data structure
stata-mcp tool data-info /project/data/raw/survey.dta

# 2. Get command help
stata-mcp tool help regress

# 3. Install an enabled and approved package
stata-mcp tool ado-install outreg2 --yes

# 4. Execute analysis script
stata-mcp tool do /project/stata-mcp-dofile/analysis.do

# 5. View execution log
stata-mcp tool read-log /project/stata-mcp-log/analysis.log --output-format core
```

## Notes

1. **Stata License**: Requires a valid Stata installation and license
2. **Path Format**: Absolute paths are recommended
3. **help Command**: Only supported on macOS and Linux
4. **Log Location**: Defaults to `<cwd>/.statamcp/stata-mcp-log/`
