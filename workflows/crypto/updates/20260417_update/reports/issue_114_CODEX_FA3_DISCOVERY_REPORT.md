# Issue 114 深度研究报告：为什么 deep-factor-research 没有把 agent 推向真正有用的因子

**作者**: Codex  
**日期**: 2026-04-16  
**主题**: 以 `fa3` 为失败样本，回溯 `crypto_ob_research` 来源研究、`crypto-deep-factor-research` skill、`target_and_workflow.md`、`crypto_mcp`、`zebra` 工程链路，回答一个严格限定的问题：

> 我们怎样改进研究流程，才能在研究阶段更高概率地找到真正有用的因子，而不是产出一大批“研究上有意思、工程上可实现、但对当前 baseline 没增量”的因子？

---

## 0. 结论先行

### 0.1 最终判断

`deep-factor-research` **不是完全失效**。它已经证明自己能做三件事：

1. 产生高质量的**负结果研究**和方法论资产；
2. 在少数方向上确实能挖到**有价值的 production family**；
3. 让 agent 形成一套相对诚实的研究文档与审查轨迹。

但如果问题是：

> “它为什么没有把 agent 系统性地推向对当前 `fa1+fa2` 有增量的 100~200 bar 因子？”

那么答案是：

**主因在 research workflow / skill / methodology，而不在 Zebra C++ 实现正确性。**

更具体地说，当前流程优化的是：

- “把一个 seed 做成一项完整研究”
- “从 Phase 1 现象里衍生出多个编码候选”
- “在文档上诚实记录 null / retired / alternate / gate / reserve”

它**没有同等强度地优化**：

- “这是不是当前 production frontier 外的新方向？”
- “这是不是当前主目标槽位需要的因子，而不是别的槽位？”
- “这在研究阶段是否已经证明对当前 baseline 有增量？”

这三点缺失，才是 `fa3` 最后变成“研究很多、文档很完整、模型里 gain 很高、但 valid 增量为负”的根因。

### 0.2 归因层级

**第一主因：Skill / workflow 方法论不完整**

- `§0.4` 的 related-factor scan 还停留在 `zebra_pool/f001/f002`，没有扫描真实生产池 `fa1/fa2`；
- workflow 文档口头上要求考虑“与 baseline 的 LGBM 联合表现”，但 skill 没有把这件事变成研究阶段的强制步骤；
- 对“main-target alpha / conditional gate / volatility feature / control-only / null-result”没有显式 outcome taxonomy；
- Phase 2 的编码探索改进能增加候选多样性，但**不能自动提高增量 alpha 密度**。

**第二主因：研究目标槽位管理缺失**

- 多个 study 最终产出的其实是 `h5-h20` 波动率 / regime feature、`high-vol only` 条件因子、symbol-specific marginal alpha，或纯负结果；
- 这些结果本身不一定错，但它们不等于“当前主目标的有效因子”；
- 当前流程没有强约束让 agent 在 Phase 1/2 尽早确认“自己到底在为哪个 production slot 工作”。

**第三主因：研究阶段没有 baseline-aware incrementality gate**

- 研究里大量使用 single-factor IC、small-sample screen、cross-day sign-stability；
- 这些对“微观机制是否存在”有价值，但对“加入当前 baseline 是否增量”不够；
- 对于 nonlinear / regime / conditional features，缺少研究阶段的轻量 LGBM matched-recipe ablation，导致 agent 只能把判断推迟到 realize 后。

**放大器，而非本题主答案**

- factor-list compile 把 `DISCARDED / RETIRED / null-result placeholder` 大量带下去；
- 部分 study 在最终 Phase 3 / Phase 4 完成前就被工程化；
- Analyzer 初版比较口径错误，把 `merged vs fa3_only` 误当成 `merged vs fa1+fa2` 的增量结论。

这些当然会让 `fa3` 更差，但它们不是“如何在研究阶段更容易找到有用因子”的根答案。

---

## 1. 证据范围

本报告只使用以下证据：

1. GitHub issue 背景：
   - `#114` Crypto 投研方法论改进：小样本 IC 不可信 + fa3 评估流程漏洞归因
   - `#113` `crypto-deep-factor-research` skill 框架级改进：预测目标意识 + 编码探索机制
   - `#115` meta-review 文档架构，与 `#113/#114` 的收口关系
2. `fa3` 直接结果：
   - `zebra_pool/fa3/experiments/stage1/REPORT.md`
   - `zebra_pool/fa3/report/analyzer_summary.md`
   - `zebra_pool/fa3/report/code_review_report.md`
3. `fa3` 来源研究：
   - `crypto_ob_research/{35,37,38,39,40,41,43,44,45,46,47,48,49,50,51}/`
4. 最近 workflow 改动与后续研究复核：
   - `crypto_ob_research/{53,54,55,56,57,58,59,60,61,62,63,64}/`
4. workflow / skill：
   - `quant-workflows/workflows/crypto/target_and_workflow.md`
   - `quant-workflows/skills/crypto/claude/crypto-deep-factor-research/SKILL.md`
   - `quant-workflows/skills/crypto/codex/crypto-deep-factor-research/SKILL.md`
   - `quant-workflows/skills/crypto/claude/crypto-factor-list-compile/SKILL.md`
5. 工具边界：
   - `crypto_mcp/README.md`
6. friction KB：
   - `crypto_ob_research/friction_knowledge_base.md`

---

## 2. 顶层约束：`fa3` 的失败必须先被正确表述

在归因之前，必须先承认一个事实：

- `fa3` 在公平比较里**没有带来增量 alpha**；
- 最佳公平 baseline 是 `fa2+fa1`，`Valid RankIC = 0.0431`；
- 最佳 fa3-inclusive 配置只有 `0.0413`，仍落后 `-0.0018`；
- 即使只保留 top-20 fa3 特征，仍然比纯 baseline 更差。

证据：

- `zebra_pool/fa3/experiments/stage1/REPORT.md:13-18`
- `zebra_pool/fa3/experiments/stage1/REPORT.md:167-177`

同时也必须承认另一个事实：

- 最初的 analyzer 总结之所以会得出“fa3 增量很强”，是因为它比较的是 `merged vs fa3_only`，不是 `merged vs fa1+fa2`；
- 这不是 Zebra 计算错，而是**评估口径错**。

证据：

- `zebra_pool/fa3/report/analyzer_summary.md:133-143`
- `zebra_pool/fa3/experiments/stage1/REPORT.md:13-18`

因此，本报告的任务不是证明 `fa3` 好或不好，而是解释：

> 为什么研究阶段没有把 agent 稳定推向“对当前 `fa1+fa2` 有增量”的候选空间？

---

## 3. 15 个来源研究逐个 review：它们到底产出了什么

下面这张表只看每个 study **最终交付物的真实类型**，而不看它在 `FA3_factor_list.md` 里被怎样展开。

| Study | 最终交付类型 | 对主目标 `next100~200` 的关系 | 结论 |
|---|---|---|---|
| `35` | **未完成最终定稿 / provisional family** | 有潜力，但 `imb_L1` 明显处于 baseline 邻域，`walkadj` 仍待 Phase 3 与工程口径闭合 | 不能当成熟生产 family 使用 |
| `37` | **短 horizon 波动率 / regime feature** | 明确写了 `h5-h20`、`NOT main-target alpha` | 研究诚实，但 target slot 错 |
| `38` | **null-result + cross-study observation** | 无 production factor | 这是成功的负结果研究，不是失败研究 |
| `39` | **high-vol only 条件因子** | 只在高波 regime 有意义 | 可以做 conditional feature，不等于主目标 alpha |
| `40` | **negative-result / empty-list** | 无 production factor | 健康负结果 |
| `41` | **pure negative result** | 无 production factor；同时发现 `FK8` | 研究本身有价值，暴露了 skill bug |
| `43` | **最终 retired** | Phase 3 fail promotion；边际、symbol-specific、被 baseline 吸收 | 真实 observable，但不够格独立部署 |
| `44` | **retired / no factor** | 无 production factor | 健康负结果 |
| `45` | **1 个 main-caliber incremental factor** | h200 最强，h100/h400 明显被 baseline 吸收 | 少数真实有效的增量 family |
| `46` | **强机制 family，但并非所有分支都稳健** | 核心 ratio form 强；部分原始分支对 residualization 方法敏感 | 属于真正成功研究 |
| `47` | **Phase 2 kill test retire** | 与 baseline 高重叠，严格 kill | 也是成功的“及时止损型研究” |
| `48` | **1 个线性旗舰 + 1 个 conditional gate** | 真正可 shipping 的 family | 属于真正成功研究 |
| `49` | **4 个 primary production candidates** | 明确经过 Phase 3 collapse 后保留 | 属于真正成功研究 |
| `50` | **negative-result / empty-list** | 无 production factor | 健康负结果 |
| `51` | **null-study / no retained factor** | 无 production factor | 健康负结果 |

### 3.1 分类统计

按“对当前主目标是否直接有用”来分：

- **明确 production-ready / incremental 的 study**：`45`, `46`, `48`, `49`
- **条件成立才有意义、但不是主目标主线的 study**：`35`, `37`, `39`
- **最终 retired 的 study**：`43`, `47`
- **明确 null / negative-result 的 study**：`38`, `40`, `41`, `44`, `50`, `51`

也就是说，在 `fa3` 的 15 个来源研究里：

- 真正清晰落到 production-ready 主线的，只有 **4 项**；
- 另有 **3 项**更像条件特征、短 horizon feature 或未完成定稿；
- 剩下 **8 项**不是退休就是负结果。

这本身就说明：

> 当前研究流程产出的大部分“研究成果”，并不天然属于“可以直接提升当前 baseline 的主目标因子”这一类。

### 3.2 支持性证据摘录

#### `37` 明确不是主目标 alpha

- `37-ghost_walk_and_cancel_driven_mid/factor_definition.md:13-18`
- `37-ghost_walk_and_cancel_driven_mid/research_report.md:1224`
- `37-ghost_walk_and_cancel_driven_mid/research_report.md:1368`

Study 37 的结论并不是“找到 next100 alpha”，而是：

- quote-driven ghost stream 是短 horizon 波动率特征；
- 最合适目标是 `realized_vol_next_5_bars`；
- 只能作为 LGBM enrichment feature，而不是主目标方向因子。

这说明研究本身是诚实的，但**槽位不对**。

#### `39` 是 high-vol only

- `39-depth_depletion_imbalance/factor_definition.md:12-25`
- `39-depth_depletion_imbalance/factor_definition.md:114-118`

Study 39 的三个幸存因子都明确写成：

- `high-vol only`
- 低波 regime 近乎无效

这不是错因子，但它更像 conditional state feature，而不是默认可并入主线的通用 alpha。

#### `43` 最终被 honest retire

- `43-spread_replenishment_latency_asymmetry/factor_definition.md:394`
- `43-spread_replenishment_latency_asymmetry/research_report.md:708-726`
- `43-spread_replenishment_latency_asymmetry/quality_review.md:567-585`

Study 43 非常有代表性：

- 现象是真的；
- 编码也不差；
- 但 magnitude、CI、跨符号稳定性和 baseline residual 后的结果都不够；
- 最终 honest retire。

这说明：**“研究现象成立” ≠ “该方向值得继续占用 production 因子预算”。**

#### `45` 是少数真正 main-caliber incremental family

- `45-information_toxicity_term_structure/research_report.md:376`
- `45-information_toxicity_term_structure/factor_definition.md:66-72`
- `45-information_toxicity_term_structure/quality_review.md:337-360`

Study 45 的 primary factor 在 h200 上 residual 后仍有 `+0.018`，这才是“当前 baseline 上的 incremental factor”应有的表述方式。

#### `46`, `48`, `49` 是当前流程真正成功的案例

- `46-proximal_liquidity_churn/factor_definition.md:21-50`
- `48-market_physics_path_statistics/factor_definition.md:14-45`
- `49-intraday_volume_zscore/factor_definition.md:3-18`

这三项说明：

- 流程不是完全失效；
- 但它只在一部分 seed 上，能够把研究推进到真正有用的 production family。

---

## 4. 第一主因：Skill 在最关键的地方没有面对真实 frontier

这是本报告最确定、证据最强的一条。

### 4.1 `§0.4` 的 related-factor scan 过时了

当前 `crypto-deep-factor-research` skill 的 `§0.4` 仍然要求 subagent 只扫描：

- `zebra_pool/f001/agents/base30_agent.h`
- `zebra_pool/f002/agents/f002_agent.h`
- `zebra_pool/README.md`

证据：

- `quant-workflows/skills/crypto/claude/crypto-deep-factor-research/SKILL.md:73-83`

但真实生产池不是这 69 因子，而是：

- `fa1_v1` 123 因子
- `fa2_v1` 75 因子
- 总计 198 因子

证据：

- `zebra_pool/fa3/report/analyzer_summary.md:24`
- `crypto_ob_research/friction_knowledge_base.md:229-246`

### 4.2 这个 bug 直接浪费了研究预算

Study 41 是最清楚的例子。

它在早期因为按 skill 文字执行，只看了 `f001/f002`，于是得出：

- “L2 resting-book 因子在现有池里是新方向”

后来在 `FK8` 检查时才发现：

- `f_l1_imb` 与 `fa1_depth_imb_1` 的 Spearman 相关高达 `0.9963`；
- residualized IC 大幅塌缩；
- 整个 fast channel 其实是已存在 production factor 的重述。

证据：

- `crypto_ob_research/friction_knowledge_base.md:233-246`
- `41-anchor_gravity_depth_concentration/research_log.md:1048`
- `41-anchor_gravity_depth_concentration/factor_definition.md:21`

### 4.3 这不是 compile 问题，而是 discovery-stage bug

这个 bug 会让 agent 在 Phase 0 就把一个本该当场降级或转向的方向，误判为“值得深挖的新方向”。

这正是你最在意的成本：

- 不是后面有没有筛掉；
- 而是前面**花了很多研究轮次去重新发现已存在的东西**。

### 4.4 结论

`§0.4` 的 related-factor scope bug 是当前 deep-factor-research 最明确的 discovery-stage 缺陷。  

它不是“可能有帮助”的建议，而是必须修的 P0。

---

## 5. 第二主因：workflow 没有强约束 agent 先回答“我到底在做哪个 slot”

### 5.1 workflow 的北极星是 `100~200 bar` 预测因子

`target_and_workflow.md` 说得很清楚：

- 单次 deep-factor-research 的子目标，是找对 `100~200 bar horizon` 有预测性的因子；
- 非线性价值也算，但仍然必须服务于整体 LGBM 预测信号。

证据：

- `quant-workflows/workflows/crypto/target_and_workflow.md:19-26`
- `quant-workflows/workflows/crypto/target_and_workflow.md:83-86`

### 5.2 但 skill 没有让 agent 显式声明“交付槽位”

当前流程里，agent 可以在研究过程中自然漂移到这些不同槽位：

- main-target linear alpha
- main-target nonlinear conditional gate
- short-horizon volatility/regime feature
- symbol-specific niche feature
- research control / mechanism readout
- null-result / retired

但 skill 没有要求 agent 在 Phase 0 或 Phase 1 Exit 明确写：

- 本 study 当前最可能属于哪一类；
- 如果 drift 到另一类，是否应当**重命名目标**、**降级为 control**，或者**直接收口为负结果**。

### 5.3 结果：agent 会把“研究上有意义的东西”继续包装成“可能进入因子池的东西”

Study 37 是最典型的：

- 研究结论非常清楚地说它是 `h5-h20` 的 volatility/regime feature；
- 明确不是 `next100-200` 的 main-target alpha；
- 但它仍然形成了可 realize 的 factor_definition 并进入后续工程链路。

证据：

- `37-ghost_walk_and_cancel_driven_mid/factor_definition.md:13-18`
- `37-ghost_walk_and_cancel_driven_mid/research_report.md:1224`

Study 39、43 也一样：

- `39` 是 `high-vol only`
- `43` 是 mid-liquidity / symbol-specific / marginal observable

这些都不是“没研究好”，而是**没有被及时重新归类**。

### 5.4 为什么这对“找到有用因子”很关键

如果 slot 不清楚，agent 的后续动作会全错：

- 它会继续做 encoding exploration，而不是先确认 target fit；
- 它会把 short-horizon 现象桥接成 main-target 候选；
- 它会把 conditioning variable 当作候选 alpha；
- 它会把“很适合进别的 model objective 的 feature”误送到当前主线。

这就是研究成本浪费。

### 5.5 最近的 `53+` 研究说明：target awareness 有改善，但 slot discipline 仍未落地为硬门

这一步很重要，因为它能区分：

- `fa3` 暴露的问题，后来到底有没有被修；
- 以及这些修补是“真正进入 workflow”了，还是只是研究者临场更谨慎了。

对 `53-64` 的补充复核结论是：

1. **主目标意识确实在变强**
   - `56` 明确把 `next100~200` 当主目标，`next400/800` 只是 supporting horizon：
     - `56-cancel_side_asymmetry_fragility/research_report.md:28`
   - `60` 明确把 `next100` 写成 “front side of the main horizon”，并把 `next200/400` 当 decay / re-merge diagnostics：
     - `60-bite_ratio_perfect_probe/research_report.md:1177`
     - `60-bite_ratio_perfect_probe/research_log.md:1619`
   - `63` 明确把 `ret_lag0_next100..200` 当 primary，`next400/800` 只当 extension checks：
     - `63-hidden_vacuum_probe/research_report.md:64-84`

2. **也出现了正确的“因目标槽位不匹配而退休”的例子**
   - `61` 识别出信号主要活在 `h400/800`，与主槽位 `h100~200` 冲突，于是直接退休；
   - 这是正确的 main-slot discipline，而不是失败：
     - `61-event_grammar_attack_outcome/research_report.md:204`
     - `61-event_grammar_attack_outcome/factor_definition.md:1-18`

3. **但 slot drift 并没有完全消失**
   - `54` 在最终设计里仍把 `next10 bars` 当 primary target horizon，并明确拒绝 `100-bar carry` 作为主锚点：
     - `54-cancel_repost_recovery_concentration/research_report.md:1249`
     - `54-cancel_repost_recovery_concentration/factor_definition.md:121-125`
   - 这类研究可以成立，但它不该和 `100~200` 主线候选处在同一个默认交付槽位里。

4. **旧的数量门仍会把 conditional / fragile family 推过边界**
   - `64` 仍按旧的 `>=10` quantity gate 通过 Phase 2；
   - 但 Phase 3 的最终结论却是：没有 universal production-ready factor，`13` 个 retained 因子全部是 fragile，只剩 `1` 个 conditional finalist：
     - `64-convexity_liquidity_density/research_report.md:871-873`
     - `64-convexity_liquidity_density/research_report.md:944-985`

所以，最近研究的真实状态不是“问题已经解决”，而是：

- 研究者开始更清楚地谈主目标；
- 但 workflow 还没有把 slot discipline 变成一个硬性、可执行、会阻止错误交付的门。

---

## 6. 第三主因：workflow 口头要求 baseline LGBM 联合表现，但 skill 没把它操作化

### 6.1 workflow 已经承认“联合表现”是关键

`target_and_workflow.md` 明确写了：

- Phase 2/3 不能只看线性 IC；
- 要考虑 conditional IC、分位形状、与已有 baseline 的 **LGBM 联合表现**。

证据：

- `quant-workflows/workflows/crypto/target_and_workflow.md:25`
- `quant-workflows/workflows/crypto/target_and_workflow.md:95`

### 6.2 但 skill 里没有任何研究阶段的 LGBM proxy step

在实际 `crypto-deep-factor-research` skill 中：

- 有 Phase 1 观察；
- 有 Phase 2 编码探索、小样本/大样本 IC；
- 有 Phase 3 horizon 矩阵；
- 也允许把某些因子解释为“可能更适合 LGBM 条件分裂特征”；

但**没有任何一步**要求：

1. 把当前候选因子 join 到当前 baseline 因子上；
2. 在 research 阶段跑一个 matched-recipe baseline-vs-baseline+candidate 的轻量 LGBM delta；
3. 对 nonlinear / regime feature 给出最基本的增量证据。

证据：

- `quant-workflows/skills/crypto/claude/crypto-deep-factor-research/SKILL.md` 全文没有研究阶段的 `LGBM`/`ablation`/`incremental` 实操步骤；
- 只有 Phase 3 里一句解释性语句：短 horizon 强、长 horizon 弱的因子“可能更适合作为 LGBM 条件分裂特征”，但只是记录在 `factor_definition.md` 里，供下游参考。
- `quant-workflows/skills/crypto/claude/crypto-deep-factor-research/SKILL.md:499-502`

### 6.3 这会把最关键的判断推迟到 realize 后

Study 37 再次说明问题：

- 它在 research 阶段已经知道自己不是 main-target alpha；
- 也已经知道真正需要的是 tree-level / LGBM ablation；
- 但这件事被 defer 到 realize pipeline 的 must-do。

证据：

- `37-ghost_walk_and_cancel_driven_mid/factor_definition.md:18`
- `37-ghost_walk_and_cancel_driven_mid/factor_definition.md:137-145`（文中 deferred items）

这意味着：

- agent 在研究阶段并不知道这个方向是否值得继续投入；
- 只能先把文档做完、再实现、再刷数、再看 analyzer；
- 反馈太晚。

这里要特别澄清一件事：

**这不等于“研究阶段必须完整地看下游 LGBM / benchmark refresh”，也不等于当前手动 batch compile / realize 设计本身就是 bug。**

当前流程本来就是按批次积累研究，再周期性地 compile / realize / benchmark refresh。这个总体节奏可以是合理的。真正的问题是：

- 在两次 batch 之间，研究阶段几乎没有 baseline-aware proxy feedback；
- agent 也没有被强制先回答“我现在做的是不是主线 slot”；
- 于是很多应该在研究阶段就降级、转槽、或退休的方向，被继续 formalize 到 realization 前。

### 6.4 这不是“产出后筛选”，而是 discovery-stage feedback

这点必须和你不接受的那种“后面筛掉 bad factor”分析区分开。

这里说的不是：

- “先产 200 个因子，再慢慢做 feature selection”

而是：

- **在研究阶段就给 agent 一个能反映当前 baseline 增量价值的近似反馈**；
- 让它更早知道某个 regime feature 值不值得继续；
- 让它把研究时间集中到真正有 marginal lift 的方向上。

这正是你关心的“如何提高找到有用因子的概率”。

---

## 7. 第四主因：Issue 113 的“编码探索增强”是有益改动，但不是主解

### 7.1 我同意 `#113` 的方向

`#113` 的改动解决了真实问题：

- 防止默认 EMA 套一切；
- 要求编码反思；
- 要求编码探索；
- 引入 sweet spot，减少“必须 ≥10 因子”的硬压力；
- 把 IC-horizon profile 降级为诊断工具，而不是简单 gate。

这对研究质量确实有帮助。

### 7.1a 但从当前仓库状态看，`#113` 更像“已提出并写入工作区”，还不能算“稳定 landed”

这点必须写清楚，否则会误判“为什么最近研究里还看不到这些改动的执行痕迹”。

我复核当前 `quant-workflows` 工作区时看到：

- `target_and_workflow.md` 目前是工作区里的新文件；
- Claude 版 `crypto-deep-factor-research/SKILL.md` 和 `reviewer_prompt.md` 是工作区修改；
- Codex 版 skill 仍停在更早的迁移状态。

因此，关于 `#113` 更准确的表述应该是：

- **方向已经明确提出，文本也已存在于当前工作区；**
- **但不能简单说它已经以稳定 commit / 稳定基线的方式完全落地。**

这也解释了为什么下面这条现象成立：

- 在最近 `53-64` 的研究产物里，仍然看不到这些新结构被系统性执行。

### 7.2 但它主要解决的是“浅探索”，不是“低增量”

Issue 113 的改动，本质上是在问：

- “同一个 raw signal，还有哪些编码？”

它没有直接回答：

- “这个 raw signal 本身是不是在当前 frontier 外？”
- “这个 raw signal 属不属于我们正在争取的 delivery slot？”
- “它对 baseline 是否有边际增益？”

### 7.3 Study 49 是最好反例

Study 49 说明：

- 编码探索多样性在**强 seed** 上可以产生很好的结果；
- 但 Phase 2 还是保留了 `11 A/AB + 1 reserve`；
- 最后 Phase 3 还要把它 collapse 回 `4 primary + 1 tighter variant + alternates`。

证据：

- `49-intraday_volume_zscore/factor_definition.md:4-9`
- `49-intraday_volume_zscore/quality_review.md:295-298`

这说明：

- 编码探索不是坏事；
- 但如果没有更强的 frontier / slot / incrementality 约束，它仍然会**扩大候选集，而不一定提高有效因子密度**。

### 7.4 结论

`#113` 是正确修补，但只解决了“探索浅”这一层。  

`#114` 真正暴露的问题，在更上游：

- 研究方向是否站在真实 frontier 之外；
- 研究结果是否属于正确槽位；
- 研究阶段是否已经拿到 baseline-aware 增量反馈。

### 7.5 更关键的是：最近研究里并没有真正落地 `#113` 的新 Phase 2 结构

我逐个扫描了 `53-64` 的 `research_log.md`，没有一个 study 真正写出：

- `[PHASE 2 编码反思]`
- `[PHASE 2 编码探索]`

这意味着：

- 最近研究的改进，更多来自研究者自己变得更谨慎；
- 而不是 workflow 已经把 `#113` 的新要求变成了稳定、可重复执行的流程。

这也是为什么我不接受“`#113` 改完了，所以后续问题应该已经消失”这种推断。  
目前更接近的事实是：**方向对了，但还没有被稳定执行。**

---

## 8. 第五主因：study outcome type 不清晰，导致研究产出语义混杂

### 8.1 现在的 `factor_definition.md` 语义太宽

在当前生态里，`factor_definition.md` 可能表示：

- 真正 ship-ready 的 production factor
- conditional gate
- research-support alternate
- retired historical spec
- null-result placeholder
- Phase 2/3 pending draft

例子：

- `38`：`NULL RESULT. Zero novel factor deliverables.`
- `47`：`RETIRED`
- `35`：Phase 2/3 pending
- `45`：文件抬头仍写 `Phase 2 screening in progress`，但 quality review 已认定 primary factor ship-ready

证据：

- `38-trade_flow_price_divergence/factor_definition.md:3-18`
- `47-effective_spread_state_machine/factor_definition.md:1-8`
- `35-depth_flow_divergence/factor_definition.md:305-307`
- `45-information_toxicity_term_structure/factor_definition.md:4`
- `45-information_toxicity_term_structure/quality_review.md:351`

### 8.2 这会让 agent 的研究目标变得模糊

如果一个研究即使最终是：

- negative-result
- retired
- control-only
- symbol-specific marginal

也仍然自然地生成 `factor_definition.md`，那么对 agent 来说，“把 seed 研究到一个结论文档”与“找到一个值得投入生产预算的因子”就会混在一起。

这会影响 Phase 1/2 的决策习惯：

- 更倾向把弱方向继续 formalize；
- 更倾向写更多 encoding；
- 更不倾向早收口为 `NULL_RESULT` 或 `CONTROL_ONLY`。

### 8.3 downstream compile 只是把这个问题放大

`FA3_factor_list.md` 里明确写了：

- 本次因子集把 `RETAINED / TENTATIVE / ARCHIVED / DISCARDED / RETIRED` 全部收录；
- 这是由于用户给了“不要丢弃各研究中被丢弃的因子”的特殊指令。

证据：

- `factor_agent_docs/FA3_factor_list.md:39-46`

但这只是**放大器**。更早的问题是：

> 上游研究产物的语义本来就没有被严格分层。

---

## 9. Zebra 不是第一性 bug，但它有一个真实问题：反馈太晚

### 9.1 我没有看到 Zebra C++ 实现上的一阶错误

`fa3` 的 code review 给出的结论是：

- 114 因子逐一对齐；
- critical / major issue = 0；
- 只有 minor issue；
- schema、state、guard、跨天行为都正确。

证据：

- `zebra_pool/fa3/report/code_review_report.md:8-13`

所以不能把 `fa3` 的失败归因成：

- “C++ 实现错了”
- “Zebra 公式落地扭曲了研究”

### 9.2 但 Zebra 的工程位置确实在反馈链路末端

当前真实路径是：

`research -> factor_definition -> compile -> C++ -> full-history parquet -> analyzer -> fair baseline correction`

这意味着：

- 研究阶段看不到真实 baseline incrementality；
- realize 之后才知道这条线到底有没有 marginal lift；
- sunk cost 已经发生。

这不是 Zebra 的算法 bug，而是**系统架构上的 feedback latency**。

### 9.3 正确改法不是责怪 Zebra，而是把 proxy 提前

如果在 Phase 2/3 就有：

- baseline overlap check
- per-day residual IC against top-K absorbers
- 小规模 matched-recipe LGBM delta

那么 Zebra 仍然负责最终工程化，但不会再承担“首次发现方向值不值得做”的职责。

---

## 10. MCP 不是主因，但它确实缺了一类关键工具

### 10.1 现有 MCP 很擅长 observation / narrative / event forensics

`crypto_mcp` 的 27 个工具覆盖：

- session
- navigation
- status / book / events
- analyze_sweep / explain_move / flow_analysis / liquidity_profile
- visualization

证据：

- `crypto_mcp/README.md:22-27`
- `crypto_mcp/README.md:45-56`

### 10.2 但它不覆盖 factor incrementality tooling

README 的 27 个工具里，没有提供研究阶段最缺的这些能力：

- current baseline column enumeration / overlap scan
- candidate-vs-baseline residual IC
- per-day / same-day residualization helper
- quick matched-recipe LGBM ablation
- outcome lint / study outcome type check

所以当前研究在 Phase 2/3 的关键量化判断，几乎都要靠每个 study 自己重写脚本。

这带来两个问题：

1. 每个 study 的 baseline-aware methodology 不统一；
2. skill 也就很难把它写成真正可执行的强制步骤。

### 10.3 结论

MCP **不是** `fa3` 失败的第一主因。  

但它确实缺少“从观察走向增量验证”的工具层，这使得 skill 很难把“joint baseline performance”操作化。

---

## 11. 归纳：当前流程到底哪里“花了很多研究时间，但不增加找到好因子的概率”

综合上面的证据，当前流程最浪费研究预算的地方有四个：

1. **在过时的 frontier map 上选题**
   - 只看 `f001/f002`，不看真实 `fa1/fa2`
   - 结果是把已存在邻域当新方向研究

2. **不明确 delivery slot**
   - 研究走着走着从 main-target alpha 漂成了 regime / vol / conditional / marginal observable
   - 但没有被及时重分类或终止

3. **没有 research-stage incrementality feedback**
   - 只知道“这个现象有 IC / 有结构”
   - 不知道“加到当前 baseline 上有没有增量”

4. **把编码探索当作主要杠杆，而不是辅助杠杆**
   - 这能提高候选多样性
   - 但不能替代 frontier awareness、slot discipline、incrementality proof

---

## 12. 改进建议：按优先级排序

下面只列**真正会提高 agent 在研究阶段找到有用因子的概率**的建议。

### P0-1. 修 skill `§0.4`，把 novelty 判断切到真实 production frontier

**改动**：

- `§0.4` 扫描范围必须从 `zebra_pool/f001/f002` 升级到：
  - 当前 production pools：`fa1`, `fa2`, 以及最近 benchmark 的实际因子列
  - 历史研究 `crypto_ob_research/`
  - 最新 benchmark top-N / most-important families
- novelty 判断以 **parquet 列名 + 小样本相关 / residualization** 为准，而不是 source code 文件为准

**强制规则**：

- 每个 candidate raw signal 在 Phase 1 Exit 前，必须对 top-3 相近 baseline 因子做 residualization；
- 若 target horizon 下 residual drop 超过预设阈值，例如 `>50%`，则：
  - 要么明确 reframe 为 overlap-zone control；
  - 要么直接 retire；
  - 不能继续当“新方向主候选”。

**理由**：

- 这是当前最确定的 discovery-stage bug；
- 修完就能直接减少重复研究。

### P0-2. 在 Phase 0 增加 `delivery slot hypothesis`

每个新 study 在 Phase 0 必须显式声明自己最初要争取的是哪一类：

- `MAIN_ALPHA_LINEAR`
- `MAIN_ALPHA_NONLINEAR`
- `CONDITIONAL_GATE`
- `VOL_REGIME_FEATURE`
- `CONTROL_ONLY`
- `NULL_RESULT_CANDIDATE`

然后在 Phase 1 Exit 强制复核：

- 如果结论已经明显 drift 到别的 slot：
  - 要么改 slot；
  - 要么结束 study；
  - 不能继续沿原 slot 叙事硬推进。

**理由**：

- 这样 Study 37/39/43 这类方向不会再被默认推进到主目标因子池；
- agent 会更早停止在错误槽位上的编码扩张。

### P0-3. 把 baseline-aware incrementality test 前移到研究阶段

这一步不是 realize 后筛因子，而是研究阶段的**探索反馈**。

建议在 Phase 2 或 Phase 3 增加标准动作：

1. 构建一个轻量 panel：
   - 候选因子列
   - 当前 benchmark / fa1 / fa2 相近列
   - 同样的 target horizon
2. 对每个 candidate：
   - 做 per-day residual IC vs top-K absorbers
   - 做 same-day pooled robustness
3. 对任何声称自己是 `CONDITIONAL_GATE` / `VOL_REGIME_FEATURE` / `nonlinear value` 的候选：
   - 跑一个 matched-recipe 小型 LGBM：
     - baseline only
     - baseline + candidate
   - 只看相对 delta，不追求绝对值

**理由**：

- 这一步直接回答“继续投入这个方向是否有意义”；
- 它比后面 realize 完再看 analyzer，前移了整整一个工程阶段；
- 这正好回答你关心的“如何让 agent 更容易找到真正有用的因子”。

### P0-4. 引入明确的 study outcome taxonomy

建议统一在 study closeout 写：

```text
outcome_type:
  - MAIN_ALPHA_READY
  - CONDITIONAL_LGBM_READY
  - RESEARCH_CONTROL_ONLY
  - NULL_RESULT
  - RETIRED
  - PROVISIONAL_PENDING
```

并强制规定：

- 只有 `MAIN_ALPHA_READY` / `CONDITIONAL_LGBM_READY` 才能进入 factor-list compile 主体；
- `NULL_RESULT` / `RETIRED` / `CONTROL_ONLY` 不生成对 realize 有歧义的 `factor_definition.md`；
- `PROVISIONAL_PENDING` 明确禁止 realize。

**理由**：

- 这不是“后面筛掉”，而是让上游研究产物语义清楚；
- agent 也更容易在研究阶段做早停。

### P0-5. 如果要做 long-run skill，前提是先修 `slotting / mainline admission`

我同意 long-run skill 可能是正确方向，但**不能直接做成**：

- “多个 idea 并行 / 串行自动研究”
- “累计到 100 个因子自动 compile / realize”
- “跑一次 benchmark refresh，再继续下一轮”

如果在此之前不先修 study-level admission rule，自动化只会更快地放大坏方向。

更合理的顺序是：

1. **先修 slotting**
   - 每个 study 在 Phase 0 明确自己争取的是：
     - `MAINLINE`
     - `CONDITIONAL`
     - `DIAGNOSTIC`
     - `RETIRED / NULL`
2. **再修 mainline admission**
   - 只有 `MAINLINE` survivor 才进入 compile / realize / benchmark refresh 主流程；
   - `CONDITIONAL` 不和主线 alpha 混槽累计；
   - `DIAGNOSTIC / RETIRED / NULL` 不进入自动 realization 计数。
3. **最后再做 long-run automation**
   - 这样自动化放大的是“更高质量的方向选择”，而不是“更多错误 formalization”。

换句话说：

- long-run skill **可以更好**；
- 但它的前提不是“把现有流程跑得更长”；
- 而是先把“什么能进主线、什么必须转槽或退休”这件事做硬。

### P1-1. 把 Phase 2 的核心指标从“数量”改成“value density”

Issue 113 已经把硬性的 `≥10` 改成更柔性的 `5-8 sweet spot`，这是进步。  

但还需要再推进一步：

- 不要再把“候选数量”当成默认正向指标；
- 每新增一个同 family encoding，都必须说明它贡献的是哪一维新信息：
  - 新 raw mechanism
  - 新 conditioning axis
  - 新 horizon bridge
  - 已用 proxy test 证明有 marginal lift

否则就停。

**理由**：

- Study 49 说明编码扩张可以有意义；
- 但如果没有 value-density discipline，它会持续消耗研究时间。

### P1-2. 把 `43/46/47` 的 methodology lessons 固化成默认模板

要固化的不是具体因子，而是这些默认方法：

- per-day residualization 优先于粗暴 pooled residualization
- broader baseline 比 top-5 baseline 更重要
- serial dependence aware uncertainty（moving-block bootstrap / effective-N）
- `kill-test-first` 适用于弱证据 watchlist item
- CI / residual / same-day robustness 必须在 main-target 口径上看，而不是只看 pooled point estimate

**理由**：

- 这些 study 的最大价值不是“差点成了的因子”，而是把什么样的方法更靠谱说明白了。

### P1-3. 建一个 live frontier map，而不是只靠 agent 临场扫代码

建议用 meta-review 或 benchmark refresh 产出一个长期维护的文档：

- 当前 benchmark top-N 因子家族
- 已经被证明饱和 / 高吸收的邻域
- 当前强势槽位：趋势、stale、cascade、vol regime、same-price、lifetime、path stats 等
- 不建议再开的新 seed 邻域

**理由**：

- 让 agent 一开始就在对的地形图上行动；
- 避免重复进入“已被 production pool 吃掉的区域”。

### P2-1. 为 research 阶段补一组标准工具

这组能力可以先做脚本，未必非要先进 MCP：

- `baseline_overlap_check`
- `residual_ic_scan`
- `quick_lgbm_ablation`
- `study_outcome_lint`
- `frontier_neighbor_lookup`

如果后续要做进 MCP，也应该作为一组新的 factor-research layer，而不是塞进现有 event-observation 工具。

### P2-2. 同步 Codex skill

当前 Codex 版 `crypto-deep-factor-research` 仍明显落后于 Claude 版：

- 没有 `Phase 2 编码反思`
- 没有 `编码探索 1a`
- 还保留更老的数量压力与更弱的 Phase 3 说明

证据：

- `quant-workflows/skills/crypto/codex/crypto-deep-factor-research/SKILL.md:382-423`
- 对照：
  `quant-workflows/skills/crypto/claude/crypto-deep-factor-research/SKILL.md:383-480`

这不是 `fa3` 历史失败的主因，因为历史研究主要是 Claude 做的。  

但如果你希望以后让 Codex 参与这类研究，这个同步必须做。

---

## 13. 对四个问题的直接回答

### 13.1 是 skill 需要改进吗？

**是，且这是第一主因。**

最需要改的是：

1. `§0.4` frontier scan scope
2. delivery slot discipline
3. research-stage incrementality gate
4. outcome taxonomy
5. `#113` 改动真正落地为稳定 workflow，而不是只停留在工作区文本

### 13.2 是方法论有问题吗？

**是。**

更准确地说，不是“微观结构研究”这件事有问题，而是：

- novelty 判断的方法论
- slot 管理的方法论
- incrementality 验证的方法论
- long-run automation 的 admission / slotting 方法论

这三块目前都不完整。

### 13.3 是 Zebra 框架有问题吗？

**没有看到一阶实现 bug。**

但它目前承担了本不该由它承担的职责：

- 第一次告诉我们这条研究线是否值得做

应该把这部分反馈前移到研究阶段的 Python / panel / quick-ablation 层。

### 13.4 是 MCP 设计或功能有问题吗？

**不是第一主因，但有真实 capability gap。**

它现在强在：

- observation
- event forensics
- narrative inspection

它弱在：

- baseline-aware factor incrementality
- cross-study / cross-baseline panel tooling

这会拖累 skill 的可执行性。

---

## 14. 最终建议：如果只做 5 件事，就做这 5 件

1. **修 `§0.4` frontier scan**：把 `fa1/fa2/current benchmark` 纳入 Phase 0 必扫范围。
2. **加 `delivery slot hypothesis`**：Phase 0 建档，Phase 1 Exit 强制复核，不允许模糊漂移。
3. **加 research-stage quick incrementality test**：baseline residual + matched-recipe mini-LGBM。
4. **加 outcome taxonomy**：`MAIN_ALPHA_READY / CONDITIONAL_LGBM_READY / CONTROL_ONLY / NULL_RESULT / RETIRED / PROVISIONAL_PENDING`。
5. **把数量目标改成 value-density discipline**：编码探索保留，但不再默认鼓励扩张。

---

## 15. 最后一条判断

如果你的问题是：

> “为什么 `fa3` 最后混出了一个没用的因子集？”

那最直接的回答可以是：

- compile 把 null / retired / discarded 也一起带下去了；
- analyzer 早期比较口径错了；
- baseline 冗余很高。

但如果你的问题是：

> “怎样改研究流程，才能让 agent 更容易找到有用因子，而不是把研究时间花在低增量方向上？”

那更准确的回答是：

**当前 deep-factor-research 的最大问题，不是不会研究，也不是不会记录失败，而是它还没有把“真实 frontier awareness + 正确 target slot + baseline-aware incrementality”变成研究阶段的硬约束。**

这三件事补上，编码探索、负结果诚实记录、Reviewer / Compliance 这些优点才会真正开始服务于“找到有用因子”这个目标，而不是只服务于“完成一项研究”。

如果后续要把这个 skill 做成 long-run agent，也应该先把这三件事固化，再谈自动 compile / realize / benchmark refresh。  
否则你自动化的不是“找到有用因子”，而只是“更快地把更多不该进入主线的东西推进工程链路”。
