---
name: git-commit-and-push
description: Use when the user asks to commit and/or push Git changes in any repository. Stage only intended files, create a clear commit, append a Codex co-author trailer by default, and push to the requested upstream branch.
---

# Git Commit And Push

## Overview

Use this skill to run a safe, repeatable `git add` -> `git commit` -> `git push` flow across any Git repository. Keep commits scoped to the requested changes and include the Codex co-author trailer unless the user explicitly opts out.

## Workflow

1. Inspect state with:
   - `git status --short`
   - `git branch --show-current`
2. Determine staging scope:
   - If the user listed files, stage only those files.
   - If scope is ambiguous, ask before staging broad changes.
3. Stage with explicit paths (`git add <path...>`). Avoid `git add .` unless the user explicitly requests all changes.
4. Create commit:
   - Use a clear imperative subject line.
   - Append this trailer by default:
     - `Co-authored-by: Codex <codex@openai.com>`
   - If user provides an exact message, preserve it and append the trailer.
5. Push:
   - Default: `git push` on current branch.
   - If upstream is missing: `git push -u origin <branch>`.
   - If user provides remote/branch, follow that exactly.
6. Report outcome with commit hash, branch, and push destination.

## Rules

- Apply this skill to all Git repositories.
- Do not rewrite history (`--amend`, `--force`, `--force-with-lease`) unless explicitly requested.
- Do not stage unrelated untracked files by default.
- If hooks or tests block commit, report the exact error and ask for next instruction.
