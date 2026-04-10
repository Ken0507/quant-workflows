# Skill Management

## Overview

This document defines the rules for adding, modifying, deleting, and migrating skills in `quant-workflows`. Every agent (human or AI) that touches a skill MUST follow the rules below so that skill discovery, naming, and cross-project symlinks stay consistent.

The golden rule: **`quant-workflows` is the single source of truth. Everything else is a symlink.**

---

## Decision Tree: Classifying a New Skill

### Step 1 — Is the skill cross-project?

- **shared**: useful in more than one project. Examples: `issue-open`, `issue-search`, `write-research-log`, `git-commit-and-push`, `hft-sdk-issue-submit` (despite the name, submitting to hft-sdk-issues is done from every project).
- **project-specific**: only useful inside one project. Examples: HFT's `hft-sync-market-data`, Crypto's `crypto-zebra-factor-write`.

### Step 2 — Which project?

- **hft**: anything tied to the HFT bond stack — HFT SDK, Playground, Analyzer2, Benchmark100Trader, tick data sync, live strategy deploy, VPN tunnel, …
- **crypto**: anything tied to crypto factor research — Zebra, `crypto-research` MCP, crypto Analyzer, AmountBar factor pipeline, …
- **future**: new top-level categories (`stock/`, `poly/`, …) will be added when those projects come online.

### Step 3 — Claude or Codex version?

Each skill should eventually exist in both a Claude Code version and a Codex version (logic equivalent, wrapper format different). It's fine to implement them in two passes.

- If the `SKILL.md` uses the Claude Code frontmatter format and calls the Claude `Skill` / harness conventions → put under `claude/`.
- If the `SKILL.md` is written for Codex (typically includes `agents/openai.yaml` or follows Codex conventions) → put under `codex/`.

---

## Naming Rules

- **Directory name ≡ `name:` field in `SKILL.md`** — they must match exactly.
- **shared skills**: use the plain functional name, no project prefix. Example: `issue-search`, `write-research-log`.
- **project-specific skills**: prefix with the project name. Example: `hft-realize-factor`, `crypto-deep-factor-research`.
- **Never rename an existing skill** without updating: (1) the directory, (2) the `name:` field in `SKILL.md`, and (3) every symlink pointing at it. If you must rename, do it atomically in one commit + symlink refresh.

---

## File Layout

A new skill always lives at:

```
quant-workflows/skills/<category>/<agent>/<skill-name>/
```

Where:

- `<category>` ∈ `{shared, hft, crypto}`
- `<agent>` ∈ `{claude, codex}`
- `<skill-name>` is the prefixed (or shared-style) directory name

At minimum the directory contains a `SKILL.md`. It may also contain reference scripts, templates, prompts, `agents/openai.yaml`, etc.

---

## Symlink Rules

After creating a new skill you MUST create the matching symlink so that the agent can discover it. Use absolute paths (not `~`, not relative).

Template:

```bash
ln -s \
  /home/cken/crypto_world/quant-workflows/skills/<category>/<agent>/<skill-name> \
  <target_dir>/<skill-name>
```

Target directory by (category, agent):

| category | agent  | target_dir                                  |
|----------|--------|---------------------------------------------|
| shared   | claude | `/home/cken/.claude/skills/`                |
| shared   | codex  | `/home/cken/.codex/skills/`                 |
| hft      | claude | `/home/cken/hft_projects/.claude/skills/`   |
| hft      | codex  | `/home/cken/hft_projects/.codex/skills/`    |
| crypto   | claude | `/home/cken/crypto_world/.claude/skills/`   |
| crypto   | codex  | `/home/cken/crypto_world/.codex/skills/`    |

**Important**:

- Always use absolute source and target paths. `~` does not work reliably inside symlinks on all tools.
- The symlink name must equal `<skill-name>` (no rewriting, no dropping prefixes).
- Never edit a symlinked `SKILL.md` file from the project side — always edit the canonical file inside `quant-workflows/` so that `git` tracks it.

---

## Complete "Add a New Skill" Flow

Example: adding a new Claude skill called `hft-new-feature` for the HFT project.

```bash
# 1. Create the canonical skill directory inside quant-workflows
mkdir -p /home/cken/crypto_world/quant-workflows/skills/hft/claude/hft-new-feature

# 2. Write SKILL.md (frontmatter must include `name: hft-new-feature`)
#    …edit with your editor of choice…

# 3. Create the symlink so Claude Code can discover it from hft_projects
ln -s \
  /home/cken/crypto_world/quant-workflows/skills/hft/claude/hft-new-feature \
  /home/cken/hft_projects/.claude/skills/hft-new-feature

# 4. Verify
ls -la /home/cken/hft_projects/.claude/skills/hft-new-feature
head -5 /home/cken/hft_projects/.claude/skills/hft-new-feature/SKILL.md

# 5. Commit + push
cd /home/cken/crypto_world/quant-workflows
git add skills/hft/claude/hft-new-feature
git commit -m "feat: add hft-new-feature skill"
git push
```

If the skill also needs a Codex sibling, repeat with `codex/` in the path and `/home/cken/hft_projects/.codex/skills/` as the target.

---

## Modifying an Existing Skill

Just edit the `SKILL.md` (or any support files) inside `quant-workflows`. Because every consumer sees it through a symlink, the change takes effect immediately in every Claude Code / Codex session. Then:

```bash
cd /home/cken/crypto_world/quant-workflows
git add skills/<category>/<agent>/<skill-name>
git commit -m "chore: update <skill-name>"
git push
```

No symlink rebuild is required.

---

## Deleting a Skill

1. Remove the symlink(s): `rm <target_dir>/<skill-name>` (for every agent that linked it).
2. Remove the canonical directory: `rm -rf quant-workflows/skills/<category>/<agent>/<skill-name>`
3. Commit: `git rm -r skills/<category>/<agent>/<skill-name> && git commit -m "chore: drop <skill-name>"`
4. Push.
5. Optional: keep a backup under `~/.claude/skills_archive_<YYYYMMDD>/` if the content might be useful later.

---

## Cross-Agent Sync (claude ↔ codex)

The steady state is that every functional skill exists in both a Claude and a Codex version. Today Codex coverage lags (see the inventory in the top-level README). When mirroring a Claude skill to Codex:

1. Create `skills/<category>/codex/<same-skill-name>/` (same directory name as the Claude version).
2. Port `SKILL.md`:
   - Content / logic should be equivalent.
   - Frontmatter and tool-call conventions follow Codex's format.
   - Optionally add `agents/openai.yaml` so Codex can surface the skill as a UI entry point.
3. Create the symlink in the matching `.codex/skills/` directory from the table above.
4. Commit + push.

The `skills/shared/codex/claude-to-codex-skill-migration/` skill documents this porting process itself.

---

## Known Issues

- **Codex auto-discovery of project-level `.codex/skills/`**: it is assumed that Codex picks up skills from a per-project `.codex/skills/` directory the same way Claude Code does, but this has not been exhaustively verified. When adding the first Codex skill to a new project, manually confirm that Codex surfaces it before declaring coverage complete.
- **`poly_projects` not managed here**: ~4 poly-specific skills currently live outside this repo. When that project becomes active they should be moved in under a new `skills/poly/` category.
- **Codex coverage gap**: only 13 / 29 Claude skills currently have Codex siblings. Several Codex-only operator skills also exist. Backfilling is an ongoing task.

---

## Current Skill Inventory (snapshot)

### shared / claude (7)

- `hft-sdk-issue-submit`
- `issue-conclusion`
- `issue-open`
- `issue-search`
- `issue-update`
- `sync-skills`
- `write-research-log`

### shared / codex (9)

- `claude-to-codex-skill-sync`
- `claude-to-codex-skill-migration`
- `git-commit-and-push`
- `hft-sdk-issue-submit`
- `issue-conclusion`
- `issue-open`
- `issue-search`
- `issue-update`
- `sync-skills`

### hft / claude (14)

- `hft-analyzer2-standard-report`
- `hft-axis-alignment-check`
- `hft-daily-trading-report`
- `hft-deep-factor-research`
- `hft-factor-list-compile`
- `hft-intraday-trading-analysis`
- `hft-live-strategy-deploy`
- `hft-playground-factor-batch-run`
- `hft-playground-factor-write`
- `hft-playground-signalreplay-backtest`
- `hft-realize-factor`
- `hft-remote-backtest`
- `hft-sync-market-data`
- `hft-vpn-tunnel-restore`

### hft / codex (7)

- `hft-analyzer2-standard-report`
- `hft-axis-alignment-check`
- `hft-deep-factor-research`
- `hft-playground-factor-batch-run`
- `hft-playground-factor-write`
- `hft-playground-signalreplay-backtest`
- `ob-mode`

### crypto / claude (8)

- `crypto-analyzer-standard-report`
- `crypto-axis-alignment-check`
- `crypto-deep-factor-research`
- `crypto-factor-list-compile`
- `crypto-realize-factor`
- `crypto-signal-backtest`
- `crypto-zebra-factor-batch-run`
- `crypto-zebra-factor-write`

### crypto / codex (1)

- `crypto-deep-factor-research`

**Totals**: 29 Claude + 17 Codex = **46 skills**.
