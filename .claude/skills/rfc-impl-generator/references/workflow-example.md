# Example: Full RFC/IMPL Generation Flow

## Scenario: User gives a vague idea

**User**: "I want to add a feature where we can run multiple do-files at once."

**AI assessment**: Information is vague. Need to understand the user experience.

**AI asks** (via AskUserQuestion):
> "When you say 'run multiple do-files at once', do you mean:
> - Pass a list of do-files to a single tool call and run them sequentially?
> - Or run them in parallel for speed?
>
> Also, what should the output look like — one combined log or separate logs per file?"

**User answers**: "Sequential is fine. I want a single tool call that takes a list, runs them one by one, and returns a list of results."

**AI**: Re-assesses. Now understands:
- problem = repetitive tool calls for multiple do-files
- expected outcome = one call, sequential execution, list of results returned
- scope = only `stata_do` tool, no parallel execution

**AI asks**: "Any GitHub issue for this?"

**User**: "Yes, #55."

**AI**: Confirms filename: `55-batch-dofile.md`. Proceeds to Step 4.

Reads `references/rfc-template.md` and `references/impl-template.md`, generates `ai-driven/rfc/55-batch-dofile.md` and `ai-driven/impl/55-batch-dofile.md`, then presents to user.

---

## Generated RFC

```markdown
# RFC: Batch do-file execution

## 1. Background

Users often need to run multiple Stata do-files in sequence. Currently they must call `stata_do` multiple times, which wastes tokens and adds friction. A batch mode would let users pass a list of do-files in a single tool call.

## 2. Problem Analysis

Current behavior: one tool call per do-file. When a workflow has 5+ do-files, this generates 5+ round trips and log clutter.

## 3. Proposed Design

Add a new `batch` parameter to `stata_do` that accepts a list of do-file paths and runs them sequentially, collecting results into a list.

### 3.1 Files to Change

| File | Change Type | Description |
|------|-------------|-------------|
| `src/stata_mcp/api/stata_do.py` | Modify | Add `batch` parameter, loop over do-files |
| `src/stata_mcp/mcp_servers.py` | Modify | Update `stata_do` tool signature in `_TOOL_REGISTRY` |

### 3.2 Files NOT to Change

- Windows execution paths
- `StataDo` class (the core executor stays the same)
- Log format or SMCL logic

## 4. Impact & Risks

- Slightly longer execution time per tool call, but fewer round trips overall
- If one do-file fails mid-batch, subsequent files should still run (or skip — need to decide)

## 5. Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty list | Return empty results, no error |
| One do-file fails | Continue with remaining, mark failed entry with error |
| Duplicate paths in list | Run each independently (no dedup) |

## 6. Verification Plan

1. Pass 3 do-files, verify all execute and results list has 3 entries
2. Pass a list with one invalid path, verify error is captured in results
3. Lint passes
```

---

## Generated IMPL

```markdown
# IMPL: Batch do-file execution

## Summary

Modify `stata_do` API and MCP tool to accept a list of do-file paths and run them sequentially, returning a list of individual results.

## Context

The current `stata_do` function in `api/stata_do.py` takes a single `dofile_path` string. The MCP tool in `mcp_servers.py` mirrors this. The underlying `StataDo` executor is already capable of running arbitrary do-files one at a time.

## Suggested Plan

### Step 1: Modify API layer
**File**: `src/stata_mcp/api/stata_do.py`

SUGGESTED: Add a `batch` parameter (list of paths) to `stata_do()`. If `batch` is provided, loop over each path and collect results. The existing single-path logic should remain as a special case.

```
def stata_do(dofile_path=None, batch=None, ...):
    if batch:
        results = []
        for path in batch:
            # SUGGESTED: call existing logic per file
            results.append(run_single(path))
        return {"batch_results": results}
    # existing single-file logic unchanged
```

### Step 2: Update MCP tool signature
**File**: `src/stata_mcp/mcp_servers.py`

SUGGESTED: Update the `stata_do` function signature and `_TOOL_REGISTRY` description to document the new `batch` parameter. Keep `dofile_path` as primary; `batch` is optional.

## Edge Cases

- Empty batch list: return empty batch_results, no execution
- Single do-file failure: recommend continuing with remaining and tagging the failed entry
- Mixing `dofile_path` and `batch`: recommend raising an error or prioritizing `batch`

## Checking List

- [ ] `api/stata_do.py` handles both single-path and batch modes
- [ ] `mcp_servers.py` tool signature updated with `batch` parameter
- [ ] `_TOOL_REGISTRY` description mentions batch capability
- [ ] Empty batch handled gracefully
- [ ] Failed do-file in batch does not block subsequent files
- [ ] Lint check passes
```
