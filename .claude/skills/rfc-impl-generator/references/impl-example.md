# IMPL Example: Unix do-file execution append clear before exit

```markdown
# IMPL: Unix do-file execution append clear before exit

## Summary

Insert a `clear` command before `exit, STATA` in the two Unix execution paths of `StataDo` to prevent Stata from hanging with r(4) when the in-memory dataset has been modified.

## Context

`StataDo` in `src/stata_mcp/stata/stata_do/do.py` has four execution methods:
- `_execute_unix_like` — macOS/Linux, no monitors
- `_execute_unix_like_with_monitors` — macOS/Linux, with monitors
- `_execute_windows` — Windows, no monitors
- `_execute_windows_with_monitors` — Windows, with monitors

Each constructs a multi-line commands string sent to Stata via `proc.communicate()`. The current Unix commands end with:

```
log close _all
exit, STATA
```

When a do-file modifies the dataset, `exit, STATA` triggers r(4) and the process hangs indefinitely because Stata prompts the user to save or specify `clear`.

## Suggested Plan

### Step 1: Modify `_execute_unix_like`
**File**: `src/stata_mcp/stata/stata_do/do.py`

SUGGESTED: In the `commands` f-string, add `clear` on a new line between `log close _all` and `exit, STATA`.

### Step 2: Modify `_execute_unix_like_with_monitors`
**File**: `src/stata_mcp/stata/stata_do/do.py`

SUGGESTED: Make the identical insertion in the monitored version's `commands` string.

### Step 3: Verify Windows paths unchanged
**File**: `src/stata_mcp/stata/stata_do/do.py`

SUGGESTED: Confirm neither `_execute_windows` nor `_execute_windows_with_monitors` was touched.

## Edge Cases

- Empty dataset after do-file: `clear` is harmless
- Do-file already contains `clear`: repeating it is safe
- User expects unsaved data to persist: not applicable — MCP execution is stateless and the dataset was never meant to be kept in memory across calls

## Checking List

- [ ] `_execute_unix_like` commands include `clear` before `exit, STATA`
- [ ] `_execute_unix_like_with_monitors` commands include `clear` before `exit, STATA`
- [ ] `_execute_windows` and `_execute_windows_with_monitors` unchanged
- [ ] `execute_dofile` method signature unchanged
- [ ] Test do-file that modifies data no longer hangs
- [ ] Test read-only do-file still works normally
- [ ] Lint check passes
```
