---
name: rfc-impl-generator
description: Generate RFC and IMPL documents from a user-provided feature/fix description. Use when the user says something like "I want to add a feature with codex", "Implement this", "Write an RFC for...", or provides a short idea that needs to be formalized into the ai-driven/rfc + ai-driven/impl pipeline.
allowed-tools: Read Grep Write Edit AskUserQuestion
---

# RFC/IMPL Document Generator

Convert a user's feature or fix idea into a paired RFC (design document for humans) and IMPL (implementation prompt for AI) in the `ai-driven/` directory.

## When to Use

- User says "I want to add X feature"
- User describes a bug fix or improvement
- User says "write an RFC for..."
- User gives a short idea that needs formalization before coding

## Workflow

### Step 1. Receive the User's Description

The user provides a short description of what they want. This could be a sentence, a paragraph, or a reference to a GitHub issue.

### Step 2. Assess Information Completeness

Determine if the description is sufficient to write a meaningful RFC and IMPL. Ask yourself:

- Do I understand **what problem** this solves?
- Do I understand **what the user expects to happen** after the change?
- Do I understand **when/where** the user would use this?
- Do I know the **scope** (what's in, what's out)?

If any of these are unclear, proceed to Step 3. If all are clear, jump to Step 4.

### Step 3. Ask Clarifying Questions (if needed)

Use `AskUserQuestion` to gather missing information. **Focus on expected outcomes and user experience, NOT technical implementation details.**

**Good questions (ask these):**
- "What should the user see or experience after this change?"
- "When would someone use this? Can you walk through a concrete scenario?"
- "What problem does this solve for you?"
- "How important is this compared to other features you're considering?"

**Bad questions (avoid these):**
- "Should this be a new parameter or a config option?"
- "Do you want to use threading or multiprocessing?"
- "What data structure should we use?"
- "Should we cache this in Redis or a file?"

**Rules for asking:**
- Ask 1-2 questions at a time
- After each answer, re-assess if you have enough information
- If still unclear, ask follow-up questions
- Stop once you can write a coherent RFC and IMPL

### Step 4. Generate the Documents

Once you have sufficient information, generate both documents.

#### 4.1 Determine the filename

Use the naming convention from `.claude/rules/ai-driven-coding.md`:
- If there's a GitHub issue: `{issue-number}-{short-name}.md`
- If no issue: `{prefix}-{short-name}.md` (prefix = feat-, fix-, refactor-, perf-, docs-)

`short-name` should be 2-4 English words, kebab-case.

**Before writing, ask the user to confirm the filename** if you're unsure about the issue number or prefix.

#### 4.2 Write the RFC

Create `ai-driven/rfc/{filename}`. Read [references/rfc-template.md](references/rfc-template.md) for the exact structure and copy it as the starting scaffold.

**RFC rules:**
- Written in the user's natural language
- No concrete code (no diffs, no real implementation)
- No "future work" sections
- Focus on "what" and "why", not "how"

#### 4.3 Write the IMPL

Create `ai-driven/impl/{filename}`. Read [references/impl-template.md](references/impl-template.md) for the exact structure and copy it as the starting scaffold.

**IMPL rules:**
- Written in English (AI-facing)
- Pseudocode only, no real runnable code
- Use "suggested", "recommended", "consider" — leave room for AI judgment
- Must end with a Checking List

### Step 5. Present to User

After generating both files:
1. Show the user the two file paths
2. Summarize what was written in 2-3 sentences
3. Ask if they want to review or modify anything before handing off to a Coding Agent

## Reference Files

| Name | Location | Description |
|:---|:---|:---|
| RFC Template | `references/rfc-template.md` | Empty RFC scaffold to copy for new design docs |
| IMPL Template | `references/impl-template.md` | Empty IMPL scaffold to copy for new AI prompts |
| RFC Example | `references/rfc-example.md` | Filled RFC for issue #60 (exit-clear-unix) |
| IMPL Example | `references/impl-example.md` | Filled IMPL for issue #60 |
| Workflow Example | `references/workflow-example.md` | Full walkthrough from vague idea to RFC+IMPL pair |
---
