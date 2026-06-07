---
name: stata-skill
description: |
  A packaged Stata Runner skill via official MCP-for-Stata server including stata_do, ado_package_install, help, read_log and get_data_info tools. Use it when (1) need to execute Stata do-file; (2) missing ado-packages; (3) find code error caused by syntax in Stata; (4) want to read smcl and text format log file with rich text output; (5) first encounter a data file and want to understand its structure and content.
metadata:
  version: "1.0.5"
---

# MCP-for-Stata
> Official plugin for MCP-for-Stata maintained in collaboration with [SepineTam](https://github.com/sepinetam).

[MCP-for-Stata](https://statamcp.com) is an MCP (Model Context Protocol) server that exposes Stata's statistical and econometric capabilities to LLMs. This toolset supports executing do-files, querying data file structures, installing ado packages, reading Stata logs, and looking up command documentation. 

## Prerequisites

This skill requires the MCP-for-Stata server to be installed and running. If you have not configured it yet, follow `@references/installation.md`. After installation, verify with `uvx stata-mcp doctor`. Restart your AI client after installation (required for the first-time setup).

## When to Use

Trigger this skill when the user mentions any of the following scenarios:

- Needs to execute a Stata do-file for regression or statistical analysis
- Encounters a Stata syntax error and needs to troubleshoot or verify command usage
- Needs to install third-party ado packages (e.g., outreg2, reghdfe, estout)
- First encounters a data file and wants to quickly understand its variable structure and distribution
- Needs to read a Stata execution log (.log or .smcl)
- Needs to look up the official documentation and syntax for a Stata command

## Workflow

### 1. First Encounter with Data → `get_data_info`

When the user provides a data file path (.dta, .csv, .xlsx, .sav) or says "look at this data," call `get_data_info` first.

**Key points:**
- `data_path`: absolute path to the data file
- `vars_list`: if the user only cares about specific variables, pass a list of variable names; otherwise omit (defaults to all)
- `head`: defaults to 0 (no preview rows). Only set to a positive integer when the user explicitly asks to see rows

**Return value includes:** data source, number of observations, variable list, variable types, and descriptive statistics (mean, standard error, min, max) for each variable.

**Note:** results are cached based on MD5 hash of file content. Repeated queries on the same file hit the cache.

---

### 2. Execute Stata Code → `stata_do`

When the user asks to run Stata commands, perform regression analysis, generate graphs, process data, etc., call `stata_do`.

**Pre-requisites:**
1. Write Stata code into a `.do` file (using the Write tool)
2. Confirm the file path is within an allowed directory (`<WORKING_DIR>/.statamcp/stata-mcp-dofile/` or `<WORKING_DIR>`)
3. Call `stata_do(dofile_path=..., log_file_name=...)`

**Key parameters:**
- `dofile_path`: absolute path to the do-file
- `log_file_name`: custom log filename without timestamp, optional
- `read_log_when_error`: defaults to false. When true, only returns log content when Stata returns an error code (e.g., r(198))
- `enable_smcl`: defaults to true, also generates .smcl log (Unix only)

**Return value:** `log_file_path` (text and smcl paths); may contain `log_content` on error.

**Notes:**
- Security guard is enabled by default and blocks dangerous commands (shell, erase, rm, !, etc.)
- Do-file must be within a whitelisted directory; otherwise execution is rejected
- SMCL log preserves hyperlinks from commands like findsj and getiref (Unix only)

---

### 3. Install Third-Party Packages → `ado_package_install`

Treat `ado_package_install` as a high-risk, opt-in tool. Do not call it merely
because a command is missing. First identify the exact package and source, then
ask the user to approve that package and source. The tool is available only when
the operator enabled it and started the MCP server with the unsafe profile.

**Key parameters:**
- `package`: package name. For GitHub source, use "user/repo" format
- `source`: "ssc" (default), "github", or "net"
- `is_replace`: defaults to false
- `package_source_from`: required only when source="net", specifies a validated HTTPS URL

**Authorization and validation:** SSC and net package names may contain only
ASCII letters and numbers. GitHub repositories must use `owner/repository`
format and match the exact repository allowlist.
Unknown sources, local paths, IP hosts, credentials, queries, fragments, and
non-default ports are rejected. The MCP client will ask the user to approve the
exact request during the tool call; do not attempt to bypass or pre-answer it.

**Examples:**
- `ado_package_install("outreg2")` — request approval to install an SSC package
- `ado_package_install("SepineTam/TexIV", source="github")` — request approval to install an allowlisted GitHub repository

**Note:** GitHub repository contents receive no security protection. Inspect the
repository before installation. The tool never installs the GitHub helper or refreshes help automatically.
After reviewing a successful install, call `help(cmd=..., replace=true)` only
when the user wants fresh help content.

---

### 4. Look Up Command Documentation → `help`

When the user asks about the syntax, options, or usage of a Stata command, or wants to verify a command before troubleshooting an error, call `help`.

**Key parameter:**
- `cmd`: Stata command name (e.g., "regress", "describe", "xtset")
- `replace`: defaults to false. When true, bypasses cached help and refreshes it from Stata

**Return value:** Stata help text string. A cache hit is prefixed with
`Saved result for {cmd}` or `Cached result for {cmd}`.

**Notes:**
- **Unix only** (macOS/Linux), not available on Windows
- Enabled project and global caches are considered, and the newest non-empty result is returned
- If cached content seems stale or incorrect, call `help(cmd=..., replace=true)` to refresh it

---

### 5. Read Execution Log → `read_log`

When the user asks to view a Stata execution log, analyze output results, or wants to inspect the full log after `stata_do` execution, call `read_log`.

**Key parameters:**
- `file_path`: absolute path to the log file
- `output_format`: "dict" (recommended, structured command-result pairs), "full" (all original content), "core" (removes framework lines)
- `is_beta`: defaults to false. When true, uses structured parsing (Unix only, recommended for .smcl + dict format)
- `lines`: content truncation. 0 returns all; positive returns first N items; negative returns last |N| items

**Notes:**
- File must be within the `stata-mcp-folder` directory (security boundary)
- Beta mode uses the StataLog parser and may contain parsing errors

---

### 6. Write Do-File (Deprecated)

`write_dofile` is marked as deprecated. Modern AI agents have native file-writing capabilities. Use the Write tool to create do-files instead of calling this MCP tool.

This tool is disabled by default and only available when `STATA_MCP__ENABLE_WRITE_DOFILE=true`. It will be removed in a future version.

---

## Typical Workflow

### Scenario A: Full Data Analysis Pipeline

1. `get_data_info` — explore data structure
2. Write do-file based on data characteristics (Write tool)
3. Ask for approval and use `ado_package_install`; inspect GitHub repositories first
4. `stata_do` — execute the do-file
5. `read_log` — inspect execution results if needed

### Scenario B: Troubleshooting Syntax Errors

1. `help` — look up official command documentation (Unix only)
2. Fix the code in the do-file
3. `stata_do` — re-execute to verify

### Scenario C: Install and Use a New Package

1. Confirm the exact package and source with the user
2. `ado_package_install("pkgname")` — request approval and install the package
3. `help(cmd="pkg_name", replace=true)` — explicitly refresh and check package usage
4. Use the package commands in the do-file
5. `stata_do` — execute

## Edge Cases

- **help Unix limitation**: not available on Windows; guide users to alternative documentation methods
- **write_dofile deprecated**: do not use this tool to write do-files; use the Write tool instead
- **security guard enabled by default**: dangerous commands (shell, erase, rm, !) in do-files are blocked. To disable, set `STATA_MCP__IS_GUARD=false` (not recommended)
- **RAM monitoring disabled by default**: to monitor Stata process memory, set `STATA_MCP__IS_MONITOR=true` and `STATA_MCP__RAM_LIMIT`
- **path boundary check**: do-files and log files must be within whitelisted directories; otherwise execution is rejected
- **SSC installation slow**: `ado_package_install` from SSC source may take time; skip if the package is already installed

## References

| Name | Location | Description |
|:---|:---|:---|
| Installation | `@references/installation.md` | Installation and configuration guide for MCP-for-Stata |
| stata_do | `@references/stata_do.md` | Detailed guide for the execution tool |
| get_data_info | `@references/get_data_info.md` | Detailed guide for the data exploration tool |
| help | `@references/help.md` | Detailed guide for the documentation tool |
| read_log | `@references/read_log.md` | Detailed guide for the log reader tool |
| ado_package_install | `@references/ado_package_install.md` | Detailed guide for the package installer tool |
| Documentation | [docs.statamcp.com](https://docs.statamcp.com) | Full user documentation |
| Homepage | [statamcp.com](https://statamcp.com) | Project homepage |
| Source Code | [github.com/sepinetam/mcp-for-stata](https://github.com/sepinetam/mcp-for-stata) | GitHub repository |
