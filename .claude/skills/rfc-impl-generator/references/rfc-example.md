# RFC Example: Unix do-file execution append clear before exit

```markdown
# RFC: Unix 环境下 do-file 执行前追加 `clear` 防止 r(4) 挂起

## 1. Background

在 Unix（macOS/Linux）环境下，当 do-file 修改了内存中的数据集（如 `gen`、`replace`、`drop`、`merge`、`append` 等），Stata 默认会在 `exit` 时拒绝退出并抛出错误：

```
no; dataset in memory has changed since last saved
    Save the data or specify option clear to exit anyway.
r(4);
```

在 MCP 自动化调用场景中，没有用户能响应该提示，Stata 进程会挂起，造成僵尸进程并消耗系统资源。

## 2. Problem Analysis

### 2.1 触发条件

| 场景 | 是否触发 r(4) |
|------|-------------|
| do-file 只读数据（`describe`, `summarize`） | 否 |
| do-file 修改数据（`gen`, `replace`, `drop`） | 是 |
| do-file 加载新数据（`use new.dta, clear`） | 否（已有 clear） |

### 2.2 当前流程

```
1. StataDo.execute_dofile() 构造 commands
2. 发送: do "path/to/file.do" → log close _all → exit, STATA
3. 若 do-file 改了数据，exit 时 Stata 抛出 r(4)
4. subprocess.communicate() 永远等不到进程结束 → 挂起
```

### 2.3 为什么不加在 do-file 末尾

- do-file 可能由用户自行编写，不应该侵入用户代码
- 在 `StataDo` 层统一处理，覆盖所有通过 MCP 执行的 do-file，最可控

## 3. Proposed Design

### 3.1 改动位置

**文件**: `src/stata_mcp/stata/stata_do/do.py`

在 `_execute_unix_like` 和 `_execute_unix_like_with_monitors` 两个方法构造的 Stata 命令序列中，于 `log close _all` 和 `exit, STATA` 之间插入一行 `clear`。

例如，原命令序列末尾为：

```
...
do "path/to/file.do"
log close _all
exit, STATA
```

修改为：

```
...
do "path/to/file.do"
log close _all
clear
exit, STATA
```

两处 Unix 路径（带 monitor 和不带 monitor 的）均需做相同插入。

### 3.2 为什么 Windows 不改

- Windows 使用 `/e` 批处理模式，行为不同，未报告 r(4) 挂起问题
- 缺乏 Windows 设备验证，避免引入未知风险

## 4. Files to Change

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `src/stata_mcp/stata/stata_do/do.py` | 修改 | `_execute_unix_like` 和 `_execute_unix_like_with_monitors` 的 commands 中加 `clear` |

## 5. Files NOT to Change

- Windows 执行路径（`_execute_windows`、`_execute_windows_with_monitors`）
- `execute_dofile` 方法签名和对外接口
- log 生成逻辑
- monitor 逻辑
- API 层（`api/stata_do.py`）和 MCP tool 层

## 6. Impact & Risks

- do-file 执行前无感丢弃内存数据，不影响磁盘文件
- 重复 `clear` 无害
- 无风险

## 7. Edge Cases

| 场景 | 预期行为 |
|------|---------|
| do-file 未修改数据 | `clear` 无实际影响，空数据集也安全 |
| do-file 内已有 `clear` | 重复 `clear` 无害 |
| 空数据集 | `clear` 无害 |
| 大数据集未保存 | 这正是要解决的问题，`clear` 丢弃未保存修改并正常退出 |

## 8. Verification Plan

### 8.1 功能测试

1. 准备一个修改数据集的 do-file（含 `gen` 等命令），通过 MCP 执行
2. 预期：进程正常退出，不挂起，log 文件正常生成

### 8.2 回归测试

1. 准备一个只读 do-file（仅 `describe`、`summarize`），通过 MCP 执行
2. 预期：行为与修改前完全一致，log 输出完整

### 8.3 Lint 检查

运行项目 lint 命令，预期通过。

## 9. Checking List

- [ ] `src/stata_mcp/stata/stata_do/do.py` 中 `_execute_unix_like` 的 commands 已追加 `clear`
- [ ] `src/stata_mcp/stata/stata_do/do.py` 中 `_execute_unix_like_with_monitors` 的 commands 已追加 `clear`
- [ ] Windows 路径未改动
- [ ] 修改数据集的 do-file 执行后不再挂起
- [ ] 只读 do-file 执行后行为正常
- [ ] Lint check passes
```
