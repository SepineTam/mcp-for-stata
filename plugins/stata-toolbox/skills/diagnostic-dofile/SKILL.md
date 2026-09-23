---
name: diagnostic-dofile
description: |
  Use this skill when the user needs to inspect, audit, or diagnose the safety of a Stata do-file. Typical scenarios include: uncertainty about whether a .do file is safe; receiving a complete do-file from an unofficial source (not the Stata website, not a well-known academic institution or professor's official site); asking to check a batch of do-files; or requesting a read-only security/risk/portability diagnostic report. The skill does not modify the original file; it only emits a JSON report. Note that this is not a mandatory step for every do-file; run it only when a security review is warranted.
metadata:
  version: "0.1.0"
---

# Diagnostic do-file

This skill inspects a Stata do-file without changing the original file and outputs a JSON diagnostic report. The underlying script reuses `stata_mcp.utils.parse_dofile` and `stata_mcp.guard.blacklist`, so it handles Stata command abbreviations, prefixes (`capture` / `quietly`), macro expansion, block comments, `#delimit ;`, and other common constructs.

## When to use

Recommended situations:

- You receive a complete do-file from an unknown or unofficial source, especially one downloaded from outside the Stata website or well-known academic/professor sites.
- The code arrives as an email attachment, cloud-drive link, forum post, or chat message, and you want to verify that it contains no dangerous commands or data-overwrite risks.
- Before taking over or reproducing someone else's project, you want to audit the key do-files.
- You explicitly want a read-only diagnostic report covering security, portability, encoding, and other dimensions.

This skill is not required every time you write a do-file. For analysis code you wrote yourself, understand, and trust, you can run it directly without generating a diagnostic report each time.

## How to run

```bash
uv run plugins/stata-toolbox/skills/diagnostic-dofile/diagnose_dofile.py path/to/file.do
```

Save the report to a file:

```bash
uv run plugins/stata-toolbox/skills/diagnostic-dofile/diagnose_dofile.py path/to/file.do -o report.json
```

## Current checks

### 1. File metadata
- File path, size, and modification time.
- UTC timestamp when the report was generated.
- SHA-256 hash of the file.

### 2. Encoding and format
- UTF-8 or UTF-8 with BOM.
- Non-UTF-8 encodings such as GBK/GB2312.
- Line ending: LF, CRLF, or mixed.
- Empty file or comment-only file.

### 3. Dangerous commands
Based on `src/stata_mcp/guard/blacklist.py`:
- Shell / system commands: `!`, `!!`, `shell`, `xshell`, `winexec`, `unixcmd`.
- File deletion: `erase`, `rm`, `rmdir`.
- External code execution: `do`, `run`, `include`.
- Embedded runtimes: `python`, `mata`, `java`, `plugin`.
- Package-management commands: `ssc`, `net`, `github`, `adoupdate`, `update`.
- Working-directory changes: `cd`, `chdir`.

### 4. Data-overwrite risks
- `use xxx.dta` followed by `save xxx.dta, replace` pointing to the same file.
- Memory-clearing operations such as `clear all` / `drop _all`.

### 5. Output-file overwrite
- `graph export xxx, replace`.
- `export xxx, replace`.
- Commands with `replace` such as `outreg2`, `esttab`, `estout`, `putexcel`, `putdocx`, `putpdf`, `logout`, `texdoc`.
- `log using xxx.log, replace`.
- `saveold xxx, replace`.

### 6. External commands / user-written packages
- Recognizes common external commands such as `reghdfe`, `estout`, `outreg2`, `esttab`, `coefplot`, `ivreg2`, `rdrobust`.
- Reports them so the caller can run Stata `help <command>` to verify installation.

### 7. Paths and portability
- Absolute paths such as `/Users/...` or `C:\...`.
- `webuse` or network URLs for loading data.
- `cd` / `chdir` working-directory changes.

### 8. Macro and parsing risks
- Unresolved macro variables (global macros, local macro expressions, etc.).
- Unclosed block comments, quotes, or program blocks that may affect parsing reliability.

## Report format

The report is a JSON object with the following structure:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "2026-09-22T12:34:56.789012Z",
  "file": {
    "path": "/project/analysis.do",
    "size_bytes": 1234,
    "sha256": "abc123...",
    "encoding": "utf-8",
    "has_bom": false,
    "line_ending": "lf"
  },
  "summary": {
    "total_lines": 100,
    "code_lines": 60,
    "comment_lines": 30,
    "blank_lines": 10,
    "error_count": 2,
    "warning_count": 5,
    "info_count": 3
  },
  "findings": [
    {
      "level": "error",
      "line": 12,
      "category": "dangerous_command",
      "message": "Detected dangerous command 'shell'"
    }
  ]
}
```

## Notes

- The script only reads the original file and never modifies the do-file content.
- Findings are for reference only; the final execution decision is yours.
- For Stata-MCP, dangerous commands are automatically blocked by the security guard during `stata_do`. To disable the guard, configure `~/.statamcp/config.toml`, but this is not recommended.
