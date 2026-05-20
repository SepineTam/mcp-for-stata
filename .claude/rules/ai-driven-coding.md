# AI-Driven Development Workflow

## Overview

This project uses an RFC/IMPL dual-document workflow for AI-driven feature implementation. All feature work must go through this pipeline.

## Directory Structure

```
ai-driven/
├── rfc/
│   ├── {issue-number}-{short-name}.md    # e.g. 60-exit-clear-unix.md
│   └── {prefix}-{short-name}.md          # e.g. feat-batch-dofile.md, fix-log-encoding.md
└── impl/
    ├── {issue-number}-{short-name}.md    # e.g. 60-exit-clear-unix.md
    └── {prefix}-{short-name}.md          # e.g. feat-batch-dofile.md, fix-log-encoding.md
```

**Naming convention**:
- If there is a GitHub issue: use `{issue-number}-{short-name}.md`
- If there is no issue: use `{prefix}-{short-name}.md` where prefix is `feat-`, `fix-`, `refactor-`, `perf-`, or `docs-`
- `rfc/` and `impl/` filenames must match exactly

## Document Responsibilities

### RFC (`ai-driven/rfc/*.md`) — Written by Humans

RFC is a design document **for humans**, written in the user's natural language. Its purpose is to explain:

- **What to change**: problem background, pain points
- **How to change it**: change locations, design rationale
- **Consequences of the change**: impact scope, risks if unchanged, edge cases
- **What NOT to change**: explicitly scope out off-limits areas
- **Verification plan**: how to confirm the change works

**RFC must NOT contain**:
- Concrete code implementations (no diffs)
- "Future work" sections

### IMPL (`ai-driven/impl/*.md`) — Written by Humans, Read by AI

IMPL is an implementation instruction **for AI**, the prompt handed to a Coding Agent (e.g. Codex, Claude Code) to execute. Structure from top to bottom:

1. **Summary**: one-sentence goal of the task
2. **Context**: background the AI needs (relevant files, existing logic)
3. **Suggested Plan**: step-by-step recommended approach
   - Each step notes the target file path
   - Use pseudocode / mock code to describe expected changes; **do NOT write real runnable code**
   - Use "suggested", "recommended", "consider" to leave room for AI judgment
4. **Edge Cases**: situations the AI should handle with care
5. **Checking List**: self-verification checklist for the AI to complete after implementation

**IMPL must NOT contain**:
- Complete real code implementations (IMPL is a prompt, not a code file)
- Imperative tone like "you must"; use "suggested" / "recommended" instead

## Workflow Rules

1. **Never implement from RFC directly.** Always read the paired IMPL file first.
2. **If IMPL is missing**, refuse to code and ask the user to write it.
3. **After implementation**, update the IMPL checking list and mark items complete.
4. **No orphaned files**: every RFC must have a matching IMPL before coding starts.

## Example Pair

- Issue #60: rfc/60-exit-clear-unix.md → impl/60-exit-clear-unix.md
- No issue (feat): rfc/feat-batch-dofile.md → impl/feat-batch-dofile.md

## For AI Assistants

When a user asks you to implement a feature:
1. Check if `ai-driven/impl/{issue-number}-{short-name}.md` exists
2. If yes, read it and follow the prompt exactly
3. If no, check if `ai-driven/rfc/{issue-number}-{short-name}.md` exists
4. If RFC exists but IMPL does not, tell the user: "IMPL missing for this RFC. Please write the implementation prompt in ai-driven/impl/ before coding."
5. After finishing, run the checking list in the IMPL file
