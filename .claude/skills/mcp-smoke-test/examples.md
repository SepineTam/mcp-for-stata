# MCP Smoke Test Examples

This file contains concrete examples to make the smoke test run more reliably.

## 1. Register the local MCP server

If `stata-mcp-local-smoke-test` is not already registered:

```bash
claude mcp add stata-mcp-local-smoke-test -s local -- $(pwd)/.venv/bin/stata-mcp -c ~/.statamcp/debug.toml
```

If the project virtual environment does not exist, use the globally installed binary:

```bash
claude mcp add stata-mcp-local-smoke-test -s local -- stata-mcp -c ~/.statamcp/debug.toml
```

After adding, list servers to confirm:

```bash
claude mcp list
```

If the server is still not visible, restart the Claude process and try again.

## 2. Prepare the test environment

```bash
bash .claude/skills/mcp-smoke-test/scripts/prepare_smoke_test.sh
```

Successful output looks like:

```text
Project root: /Users/sepinetam/Documents/Github/stata-mcp
Clearing cached data_info summaries...
Found auto.dta: /Applications/Stata/auto.dta
Copying test artifacts to /tmp...
Smoke test preparation complete.
```

If no system `auto.dta` is found, the script generates mock data automatically:

```text
No system auto.dta found; generating mock data...
Saved csv: tmp/auto_mock.csv
Saved dta: tmp/auto_mock.dta
```

## 3. Example tool calls

### Test A — `get_data_info` on a local file

Parameter:

```json
{
  "file_path": "/Applications/Stata/auto.dta"
}
```

Expected result contains:

```json
{
  "observations": 74,
  "variables": 12
}
```

### Test B — `get_data_info` on an allowed URL

Parameter:

```json
{
  "file_path": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
}
```

Expected result contains:

```json
{
  "observations": 150,
  "variables": 5
}
```

### Test C — `stata_do` with the legal dofile

Parameter:

```json
{
  "dofile_path": ".claude/skills/mcp-smoke-test/scripts/legal.do"
}
```

Expected result: success with paths to the generated `.log` and `.smcl` files.

### Test D — `stata_do` security boundary

Parameter:

```json
{
  "dofile_path": "/tmp/mcp_smoke_test_boundary.do"
}
```

Expected result: blocked by the security guard because the dofile is outside the allowed working directory.

### Test E — `read_log` on the generated log

Use the text log path returned by Test C. Parameter example:

```json
{
  "log_path": ".statamcp/stata-mcp-tmp/legal_20260710_120000.log",
  "output_format": "full"
}
```

Expected result: log text contains regression output.

### Test F — `help`

Parameter:

```json
{
  "command": "regress"
}
```

Expected result: Stata help text for `regress`.

### Test G — `ado_package_install` (optional)

Parameter:

```json
{
  "package_name": "estout",
  "source": "ssc"
}
```

Expected result: user approval prompt, then installation log.

## 4. Clean up

```bash
bash .claude/skills/mcp-smoke-test/scripts/cleanup.sh
```

## 5. Common issues

### Issue: `stata_do` rejects a dofile in `/tmp`

This is expected. `stata_do` only accepts dofiles inside `WORKING_DIR`. The boundary test intentionally places the dofile in `/tmp` to verify that it is rejected.

### Issue: URL dataset is rejected

Make sure `enable_data_info_url_guard = true` and the domain is listed in `data_info_allowed_url_domains` in `~/.statamcp/debug.toml`. The example config already allows `raw.githubusercontent.com`.

### Issue: Server not visible after `claude mcp add`

Restart the Claude process. MCP server changes are not always picked up immediately.

## 6. Example final report

```markdown
# Stata-MCP 冒烟测试报告

## 服务器状态
- 注册状态：已注册
- 配置文件：`~/.statamcp/debug.toml`

## 测试结果
- [x] Test A 本地 auto.dta 读取：通过
- [x] Test B URL 鸢尾花数据集读取：通过
- [x] Test C 合法 dofile 执行：通过
- [x] Test D 安全边界拦截：通过
- [x] Test E 日志读取：通过
- [x] Test F help 命令：通过
- [ ] Test G ado 包安装：跳过 — 用户未确认

## 总结
全部核心测试通过，ado 包安装因需用户确认已跳过。
```
