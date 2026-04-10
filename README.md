# quant-workflows

> Quantitative research workflow management — skills, MCPs, pipelines, and cross-project orchestration for HFT / Crypto factor research.

## Purpose

This repository is the single source of truth for cken's research-workflow assets:

- **Skills, MCPs, and pipeline documentation** used across all research projects.
- **Cross-project management** — unified home for HFT (high-frequency bond trading), Crypto (crypto factor research), and future asset classes (equity / polymarket / …).
- **Dual agent support** — every workflow is expressed in both Claude Code and Codex flavors (logic equivalent, frontmatter / conventions differ).
- **Workflow documentation** — end-to-end pipeline docs so that any agent (human or AI) can understand the full picture and future migration paths.

Rather than scattering skills across `~/.claude/skills/`, `~/hft_projects/.claude/skills/`, `~/crypto_world/.claude/skills/`, etc., everything lives here and is exposed to each environment via symlinks.

## Directory Structure

```
quant-workflows/
├── skills/
│   ├── shared/                 # cross-project skills (issue mgmt, git tools, research log, …)
│   │   ├── claude/
│   │   └── codex/
│   ├── hft/                    # HFT-specific skills (Playground, Analyzer2, Benchmark100Trader, …)
│   │   ├── claude/
│   │   └── codex/
│   └── crypto/                 # Crypto-specific skills (Zebra, crypto-research MCP, Analyzer, …)
│       ├── claude/
│       └── codex/
├── workflows/                  # end-to-end pipeline documentation (stitches skills together)
│   ├── hft/
│   └── crypto/
├── mcp/                        # MCP server configurations (future)
└── docs/                       # global documentation
    └── skill-management.md     # rules for adding / modifying / removing skills
```

- `skills/<category>/<agent>/<skill-name>/` is the canonical location for any skill.
- `workflows/` will hold longer-form pipeline docs that chain multiple skills into a full research flow.
- `mcp/` is reserved for MCP server configs/definitions (currently empty).
- `docs/` contains repo-level operating rules; see [`docs/skill-management.md`](docs/skill-management.md).

## Symlink Architecture

`quant-workflows` is the source of truth. Each agent discovers skills through project-scoped symlinks that point back into this repo:

| Skill category | Claude target                                | Codex target                                |
|----------------|----------------------------------------------|---------------------------------------------|
| `shared`       | `/home/cken/.claude/skills/`                 | `/home/cken/.codex/skills/`                 |
| `hft`          | `/home/cken/hft_projects/.claude/skills/`    | `/home/cken/hft_projects/.codex/skills/`    |
| `crypto`       | `/home/cken/crypto_world/.claude/skills/`    | `/home/cken/crypto_world/.codex/skills/`    |

Symlink naming rule: use the skill's directory name verbatim (including any `hft-` / `crypto-` prefix). Do **not** rename — the symlink name, the directory name under `skills/…`, and the `name:` field in `SKILL.md` must all match exactly.

Editing a `SKILL.md` in this repo automatically updates every consumer (Claude Code sessions, Codex sessions, every project) through the symlinks — no rebuild or copy step needed.

## Current Skill Inventory

| Category   | Claude | Codex | Total |
|------------|-------:|------:|------:|
| shared     |      7 |     9 |    16 |
| hft        |     14 |     7 |    21 |
| crypto     |      8 |     1 |     9 |
| **Total**  | **29** |**17** |**46** |

Codex coverage still lags Claude (this is expected — Codex skills are being backfilled from the Claude versions one by one; see `skills/shared/codex/claude-to-codex-skill-migration/`).

## Adding a New Skill (TL;DR)

1. Decide **category** (`shared` / `hft` / `crypto`) and **agent** (`claude` / `codex`).
2. Create `skills/<category>/<agent>/<skill-name>/SKILL.md` inside this repo.
3. Create the corresponding symlink into the matching `.claude/skills/` or `.codex/skills/` directory from the table above.
4. `git add` → commit → push.

Full rules (naming, decision tree, deletion, cross-agent sync, known issues): see [`docs/skill-management.md`](docs/skill-management.md).

## Related Projects

- **HFT research**: `/home/cken/hft_projects/`
- **Crypto research**: `/home/cken/crypto_world/`
- **Issue tracker**: `ligenjian001-ai/hft-sdk-issues` (managed via the `issue-*` shared skills)
