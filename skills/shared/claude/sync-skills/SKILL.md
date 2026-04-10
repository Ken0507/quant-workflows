---
name: sync-skills
description: "扫描 quant-workflows/skills/ 全部 skill 目录，对照实际软链接做同步。缺失的软链接自动创建；孤立的软链接（指向不存在的源）只报告不删除。"
---

# Sync Skills — 软链接同步

将 quant-workflows 下的所有 skill 同步到对应的项目目录（创建缺失的软链接）。

## 使用方式

```
/sync-skills
```

无参数。可手动调用，也可由 hook 触发后自动调用。

## 执行流程

**全部工作通过 subagent 完成。**

### Step 1: 启动 subagent

使用 Agent 工具启动 subagent，prompt 中包含完整的同步逻辑（见下方模板）。

### subagent prompt 模板

```
扫描 /home/cken/crypto_world/quant-workflows/skills/ 下的所有 skill，确保对应的软链接都正确建立。

## 软链接映射规则

| Category | Agent  | 目标目录                               |
|----------|--------|----------------------------------------|
| shared   | claude | /home/cken/.claude/skills/             |
| shared   | codex  | /home/cken/.codex/skills/              |
| hft      | claude | /home/cken/hft_projects/.claude/skills/|
| hft      | codex  | /home/cken/hft_projects/.codex/skills/ |
| crypto   | claude | /home/cken/crypto_world/.claude/skills/|
| crypto   | codex  | /home/cken/crypto_world/.codex/skills/ |

## 执行步骤

1. **遍历所有 skill 源**：
   对 /home/cken/crypto_world/quant-workflows/skills/{shared,hft,crypto}/{claude,codex}/ 下的每个子目录（即每个 skill），记录其完整路径。

2. **检查目标软链接**：
   对每个 skill，根据上面的映射规则计算应有的软链接路径。
   - 如果目标位置不存在该软链接 → **创建**（缺失修复）
   - 如果目标位置已有软链接且指向正确 → 跳过
   - 如果目标位置有同名文件/目录但不是指向该 skill 的软链接 → **报告冲突**，不覆盖

3. **检查孤立软链接**：
   对每个目标目录（6 个），列出所有软链接，检查是否：
   - 指向 quant-workflows/skills/ 内
   - 目标路径仍然存在
   - 如果指向的源已不存在 → **报告孤立**，不自动删除

4. **报告**：
   输出 4 类结果：
   - **创建**：N 个新软链接已建立（列出每个）
   - **跳过**：M 个已正确（数量即可）
   - **冲突**：K 个有同名非软链接（列出每个）
   - **孤立**：L 个软链接指向已不存在的源（列出每个，提示需要手工清理）

## 关键原则

1. **只增不删**：从不删除任何文件或软链接
2. **幂等**：重复运行无害，已正确的不动
3. **绝对路径**：所有软链接用绝对路径，不用 ~ 或相对路径
```

### Step 2: 报告结果

将 subagent 返回的同步报告直接展示给用户。
