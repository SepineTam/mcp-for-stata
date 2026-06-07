---
name: stata-mcp-skill
description: Execute Stata commands, install ado packages, read help documents, and analyze data. Use when working with Stata for (1) Running do-files, (2) Installing packages from SSC/GitHub, (3) Getting command help, (4) Analyzing data files (.dta, .csv, .xlsx), (5) Reading execution logs. Supports both MCP tools (Claude Code) and CLI commands (OpenClaw).
---

> The skill could install or update from https://docs.statamcp.com/skills/openclaw or 
> ```bash
> mkdir -p /path/to/skill/base/stata-mcp-skill
> curl -o /path/to/skill/base/stata-mcp-skill/SKILL.md https://github.com/SepineTam/mcp-for-stata/raw/refs/heads/master/docs/agents/openclaw.md
> ```

# MCP-for-Stata Skill

MCP-for-Stata enables LLMs to execute Stata commands. Use MCP tools when available; fall back to CLI for clients without MCP support.

If you want to know more about MCP-for-Stata, visit its [documents](https://docs.statamcp.com) or [GitHub](https://github.com/statamcp/stata-mcp).

## MCP Tools (Preferred, used by Claude Code, Codex, Cursor or others)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `help` | Get Stata command docs | `cmd` (Unix only) |
| `stata_do` | Execute .do file | `dofile_path`, `read_log_when_error` |
| `ado_package_install` | Install approved packages; GitHub requires an allowlist | `package`, `source`; client elicits approval |
| `get_data_info` | Analyze data files | `data_path`, `vars_list` |
| `read_log` | Read log files | `file_path`, `output_format` |

## CLI Tools (Fallback, mainly used by OpenClaw)

```bash
uvx stata-mcp tool ado-install <package> [-y|--yes] [--source ssc|github|net]
uvx stata-mcp tool do <dofile_path> [--log-file-name <name>]
uvx stata-mcp tool help <command>          # Unix only
uvx stata-mcp tool data-info <data_path> [--vars-list var1 var2]
uvx stata-mcp tool read-log <log_path> [--output-format full|core|dict]
```

## Iterative Workflow

1. `get_data_info` -> understand dataset structure
2. `Edit` or `Write` -> to create a do-file
3. `stata_do` -> execute analysis with capture output
4. `help` -> learn Stata commands (Unix) if there are any command error
5. After explicit approval, use `ado_package_install`; inspect GitHub repositories first

## Notes

- Requires valid Stata license
- `help` only works on macOS/Linux
- Security guard blocks dangerous commands (shell, rm, etc.)
- MCP ado installation is disabled by default and requires client-mediated approval; CLI prompts unless `-y`/`--yes` is supplied; GitHub additionally requires an exact repository allowlist
- Log location: `<cwd>/.statamcp/stata-mcp-log/`
