---
name: mcp-smoke-test
description: Run a local smoke test for the Stata-MCP server.
---

# MCP Smoke Test for Stata-MCP

This skill performs an end-to-end smoke test of the local Stata-MCP server.
It checks installation, runs representative data and Stata commands, and reports
pass/fail status for each tool.

## When to use

- The user asks whether Stata-MCP is working.
- The user wants to verify a new MCP server configuration.
- The user says a tool is broken or unavailable.
- The user asks for a smoke test, sanity check, or end-to-end test.

## Before you start

1. Make sure the current working directory is the project root.
2. Confirm whether the project virtual environment exists at `./.venv/bin/stata-mcp`.
   If it does not exist, use the globally installed `stata-mcp` command instead.
3. Ensure `~/.statamcp/debug.toml` exists and enables beta security.
   Use `.claude/skills/mcp-smoke-test/config/debug.example.toml` as a template.

## Step 1: Ensure the MCP server is registered

Check whether the MCP server `stata-mcp-local-smoke-test` is available by listing
Claude MCP servers:

```bash
claude mcp list
```

If `stata-mcp-local-smoke-test` is missing, add it with the debug configuration:

```bash
claude mcp add stata-mcp-local-smoke-test -s local -- $(pwd)/.venv/bin/stata-mcp -c ~/.statamcp/debug.toml
```

If `./.venv` does not exist, use:

```bash
claude mcp add stata-mcp-local-smoke-test -s local -- stata-mcp -c ~/.statamcp/debug.toml
```

After adding, if the server is still not available, tell the user:

> MCP server was added but is not yet visible. Please restart the Claude process
> and then invoke the smoke test again.

## Step 2: Run smoke tests

Run the preparation script. It clears cached summaries, locates or generates a
suitable `auto.dta`, and copies the boundary test files to `/tmp`:

```bash
bash .claude/skills/mcp-smoke-test/scripts/prepare_smoke_test.sh
```

Then use the `mcp__stata-mcp-local-smoke-test` tools (or the server name registered above)
to execute each test below. Record the result for each item.

For concrete tool-call parameters, expected outputs, and troubleshooting, see
`.claude/skills/mcp-smoke-test/examples.md`.

### Test A — `get_data_info` on a local Stata sample file

Try the first existing file from this list:

- `/Applications/Stata/auto.dta`
- `/Applications/StataNow/auto.dta`

Expected result: JSON summary with 74 observations and 12 variables.

### Test B — `get_data_info` on an allowed URL

Use this URL (already in the allowlist):

```
https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv
```

Expected result: JSON summary with 150 observations and 5 variables.

### Test C — `stata_do` with a legal dofile

Run the bundled dofile `.claude/skills/mcp-smoke-test/scripts/legal.do` with `stata_do`.

Expected result: execution succeeds and returns log file paths.

### Test D — `stata_do` security boundary (negative test)

Run the copied dofile `/tmp/mcp_smoke_test_boundary.do` with `stata_do`.

Expected result: blocked by the security guard because the dofile is outside the
allowed working directory.

### Test E — `read_log` on the generated log

Read the text log returned by Test C. Expected result: log content includes
regression output.

### Test F — `help` for a Stata command

Run `help` with argument `regress`. Expected result: Stata help text for `regress`.

### Test G — `ado_package_install` (optional, requires user approval)

If the user confirms, attempt to install a small SSC package such as `estout`.
Expected result: user approval prompt, then installation log.

If the user declines or the tool is not registered (non-unsafe profile), mark
this test as skipped.

## Step 3: Clean up

Run the cleanup script to remove temporary files and cached summaries:

```bash
bash .claude/skills/mcp-smoke-test/scripts/cleanup.sh
```

Do not delete log files or data summaries; they are useful for diagnosis.

## Step 4: Report results

Return a concise Chinese report using this template:

```markdown
# Stata-MCP 冒烟测试报告

## 服务器状态
- 注册状态：<已注册 / 新注册 / 需重启>
- 配置文件：`~/.statamcp/debug.toml`

## 测试结果
- [ ] Test A 本地 auto.dta 读取：<通过 / 失败 / 跳过> — 原因
- [ ] Test B URL 鸢尾花数据集读取：<通过 / 失败 / 跳过> — 原因
- [ ] Test C 合法 dofile 执行：<通过 / 失败 / 跳过> — 原因
- [ ] Test D 安全边界拦截：<通过 / 失败 / 跳过> — 原因
- [ ] Test E 日志读取：<通过 / 失败 / 跳过> — 原因
- [ ] Test F help 命令：<通过 / 失败 / 跳过> — 原因
- [ ] Test G ado 包安装：<通过 / 失败 / 跳过> — 原因

## 总结
<一句话结论：全部通过 / 部分失败 / 需要用户操作>
```

Only mark a test as passed when you observed the expected result. For failures,
include the exact error message or tool response.

## Resources

| Resource | Path | Purpose |
|----------|------|---------|
| Example config | `.claude/skills/mcp-smoke-test/config/debug.example.toml` | Template for `~/.statamcp/debug.toml` with beta security enabled |
| Usage examples | `.claude/skills/mcp-smoke-test/examples.md` | Concrete tool calls, expected outputs, and troubleshooting |
| Legal dofile | `.claude/skills/mcp-smoke-test/scripts/legal.do` | Valid dofile for Test C |
| Boundary dofile | `.claude/skills/mcp-smoke-test/scripts/boundary.do` | Dofile that references `/tmp/auto.dta` for Test D |
| Mock data generator | `.claude/skills/mcp-smoke-test/scripts/gen_mock_data.py` | Generates `auto.dta` when the system sample is unavailable |
| Prepare script | `.claude/skills/mcp-smoke-test/scripts/prepare_smoke_test.sh` | Sets up all test artifacts |
| Cleanup script | `.claude/skills/mcp-smoke-test/scripts/cleanup.sh` | Removes temporary test artifacts |
