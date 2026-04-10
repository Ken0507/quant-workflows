# Claude -> Codex Fidelity Audit

迁移完成后，按以下顺序审计。任何一项失败，都不应交付。

## 1. File Tree Parity

- [ ] Claude 源 skill 的 `SKILL.md` 已迁移
- [ ] Claude 源 skill 的 `references/` 已完整迁移
- [ ] Claude 源 skill 的 `scripts/` 已完整迁移
- [ ] Claude 源 skill 的 `assets/` 已完整迁移
- [ ] 目标 Codex skill 多出来的文件只有平台适配所必需的内容，如 `agents/openai.yaml`

## 2. Frontmatter And Metadata

- [ ] 目标 `SKILL.md` 保留了正确的 `name`
- [ ] 目标 `SKILL.md` 保留了与 Claude 源一致的 `description`
- [ ] Claude 的 `short-description` 已迁移到 `agents/openai.yaml.short_description`
- [ ] Claude 的 `argument-hint` 没有被静默丢失，已经体现在 `default_prompt` 或 `SKILL.md` 输入说明中
- [ ] `agents/openai.yaml` 已存在且内容与 skill 语义一致

## 3. SKILL.md Structure Parity

- [ ] 一级和二级章节结构没有被随意重写
- [ ] Phase 数量、顺序、边界、进入条件与退出条件保持一致
- [ ] 核心表格、门槛、样本规模、阈值、日期范围保持一致
- [ ] 异常终止协议、审查协议、边界检查协议没有丢失
- [ ] 所有高优先级规则都仍然存在

## 4. Prompt And Reference Parity

- [ ] `references/` 中的 prompt template 没有无故删段
- [ ] 审查 rubric、checklist 维度、输出格式要求保持一致
- [ ] 任何 reference 的修改都能解释为平台绑定替换
- [ ] 不存在把长 prompt 改写成概述性摘要的情况

## 5. Agent Orchestration Mapping

- [ ] 源 skill 中明确的持久化角色，在 Codex 中仍是持久化 subagent
- [ ] 持久化角色的后续交互语义是“复用同一 agent id”，而非重复新建
- [ ] 源 skill 中明确要求独立咨询或独立审查的节点，在 Codex 中仍保留独立角色
- [ ] Claude 中调用 Codex 的外部咨询节点，已迁移为 fresh consultant subagent
- [ ] 没有把独立审查偷换成主进程自审

## 6. Backend Defaults

- [ ] 如果 skill 依赖 reviewer / compliance / logger / consultant subagent，默认模型已明确为 `gpt-5.4`
- [ ] 对应 reasoning 已明确为 `xhigh`
- [ ] 如果没有这样设置，存在明确且经用户确认的理由

## 7. Platform Residue Scan

逐条扫描以下残差并判定：

- [ ] `Claude`
- [ ] `claude`
- [ ] `mcp__codex__codex`
- [ ] `Agent(`
- [ ] `SendMessage(`
- [ ] `run_in_background`
- [ ] `~/.claude`
- [ ] `/ob_mode`

判定标准：

- 如果残留是为了描述历史来源或兼容关系，保留可以接受
- 如果残留影响执行语义，必须清理

## 8. No Semantic Weakening

- [ ] 没有把 `must` / `必须` 改成 `should` / `建议`
- [ ] 没有把 `禁止` 改成软性提醒
- [ ] 没有删掉 gate、审查者、退出条件或数量门槛
- [ ] 没有把双层或多层审查压缩成更弱流程，除非用户明确批准该映射

## 9. Existing Codex Skill Reconciliation

如果目标目录原本已存在：

- [ ] 已以 Claude 源 skill 为基线重新对齐
- [ ] 已区分“平台适配”与“历史漂移”
- [ ] 历史漂移没有被无脑保留

## 10. Final Human-Facing Summary

- [ ] 最终差异摘要只包含三类信息：平台绑定替换、agent 编排替换、待确认项
- [ ] 摘要没有把语义改动包装成“优化”
- [ ] 如果仍有不确定映射，已明确标出来而不是自行定案
