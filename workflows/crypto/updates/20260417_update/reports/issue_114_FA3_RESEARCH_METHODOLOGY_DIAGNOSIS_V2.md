# 为什么 deep-factor-research 没找到有用的因子：研究过程深度诊断 v2

**Context**: Issue #114 — 用户反馈 v1 报告走错方向（聚焦"筛选无用因子"而非"帮 agent 找到有用因子"）
**Author**: Claude Code session, 2026-04-16
**Scope**: 深读 5 项研究的 research_log.md，定位 Phase 0-2 研究过程本身的方法论缺陷
**关键事实来源**:
- Study 37 research_log.md (1595 行) — 直接读 §0.4, R1, R2 + subagent 全程分析
- Study 35 research_log.md (1954 行) — subagent 深度分析 + 直接读 §0.4
- Study 47 research_log.md + `phase1_skill_update_proposal.md` (研究员自己写的 Skill 修改提议)
- Study 31 research_log.md (821 行) + research_report.md — Issue #113 触发案例
- Study 40 vs Study 46 对比分析（null result vs 唯一 genuine find）
- Issue #113 全文 + 已应用的 8 项 skill 改动

---

## 0a. 重要校正（v2.1 — 基于用户反馈 2026-04-16 夜）

在 v2 初稿发布后，用户指出两点需要修正：

1. **关于 P0 "Phase 0 没有目标口径先测步骤"**：用户回忆已经对 claude skill 做过相关改动，让我核查并比对近期研究（≥ #53）的行为。**核查结果**：
   - SKILL.md 本身**没有**"target-caliber sanity probe"步骤，但 `friction_knowledge_base.md` 的 **FK8 条目**（Study 41 后加入）+ FK14/FK15 等事实上承担了这一角色。
   - §0.2 "读取已知陷阱"强制要求读 friction_knowledge_base.md，所以 FK8 会被研究员读到。
   - Studies 53-64 的 research_log.md 显示：Phase 0 普遍显式声明主口径 next100-200，§0.4 Related-factor scan 显式列出 fa1/fa2 具体列名，预注册 FK7 residualization 对 target，**Problem A 和 B 的典型表现不明显**（至少在 Claude-Code 跑的 12 项里）。
   - 所以 v2 原稿对"研究流程完全没有主口径意识 / baseline 意识"的批判 **过度泛化了**——近期实际研究已经部分解决。真正的 gap 是 **SKILL.md 文字 vs friction_knowledge_base.md vs 实际研究实践三者不同步**，而非"流程里完全没有这回事"。
   - 用户点到 "5.3" 相关条款类似，**我在 workflow/skills/sota 各文档里没找到 §5.3**，需要用户确认具体指向。

2. **关于 v2 的 §0.6 "Target-caliber sanity probe" 建议（写 Python 表达式 → 跑 IC → gate）**：用户明确拒绝这个范式：
   > "这种研究范式没有效率。应该是做市场观察、统计分析，然后再进行因子设想。"
   
   **收回 §0.6 目标口径 sanity probe 建议**。v2 原稿让研究员"先写 raw signal 的 Python 实现、再跑 IC"违反了 skill 的核心 philosophy——**"微观机制优先于统计拟合"**。正确的做法是：保留"观察 → 统计 → 因子设想"的自然顺序，只在 Phase 0 的**自然语言层**注入"我这个 seed 想法凭什么在主口径上有预测力"的 rationale paragraph，而不是让研究员先提供表达式。见下文修订后的 P0-fix。

3. **关于 Study 37 R4 的"三个选项全部是鸵鸟"**：用户指出：
   > "既然研究 topic 已经给定，那最好还是多做些探索，想想该 idea 下是否还有办法找到适合的构造和研究，比如更改用类似的想法因子定义、想想时序维度上有没有能创新的等等。"
   
   **部分收回**。R4 给出的三个方向（longer lookback / bring target closer / horizon-bridging transform）**确实是合理的探索尝试**，不是"鸵鸟"。R5/R6 也确实尝试了其中的 horizon bridging 并发现 cross-day sign flip。**真正的失效点不是"没有探索"，而是**：经过 R5-R8 三轮探索全部失败后，研究员没有做两件事中的任何一件：
   (a) 退回去重新审视 mechanism-to-target 的因果链条——ghost walk 真的在 h=100-200 上有预测力吗？还是 mechanism 只在 h=5-20 上成立？
   (b) 把这个 seed 正式归入 "short-horizon / regime feature family"（如果这样的 family 存在），不再以 main-caliber 姿态交付。
   
   实际做的是 (c)："LGBM enrichment" 语义改名。这是我原稿的 P7（label-smuggling）的故事，不是"没有探索"。Study 37 的研究员做了**充分的探索**，但没有选择 (a) 或 (b)——因为流程里这两条都不是 expected path。

以下 §0 TL;DR 和 §1 诊断逐条按上面三条重新表述。**v2 原稿的其余结构（P0 以外的诊断 + 改进建议）大部分仍然成立**，但 P0 要从"pre-compute IC gate"改为"mechanism-to-target rationale paragraph"，P2 的"鸵鸟 framing"要改为"exploration 完了之后 fallback 到 label-rename"的更精确故事。

---

## 0. TL;DR — 核心判断

**fa3 失效的主因不是"筛选不够严"，是"研究过程让 agent 先在错的方向上投入沉没成本，再也退不出来"。** 过程层的 10 个方法论缺陷里，最致命的是 5 个**早期锁定类缺陷**（P0-P4），它们让 agent 在 Phase 1 的前 2-3 轮就被路径依赖锁死，后面的 Phase 2/3 再怎么做都只是在局部优化。

**v2.1 TL;DR 表**（状态列反映 §0a 的校正：FK8 已进 friction_knowledge_base；Studies 53-64 显示 P0/P1 在 Claude 研究实践里已部分缓解）：

| # | 早期锁定缺陷 | fa3 案例中的后果 | 在 #53+ 是否缓解 | fix 重点 |
|---|---|---|---|---|
| **P0** | Phase 0 没有 mechanism→主口径 rationale 书面化 | Study 37 R1 基于一次 14:00 crash 形成隐式 "horizon short" 假设 | **部分缓解**：Studies 55/56/57 Phase 0 已显式写 "main caliber next100-200"；但属研究员实践，非 SKILL 模板 | SKILL 新增 §0.6 natural-language rationale paragraph（**不是** Python/IC gate）|
| **P1** | §0.4 baseline orientation 是名字匹配，未做 Spearman | Study 35 R²=1.00 vs fa1；Study 47 0.924；Study 41 0.9963 | **部分缓解**：FK8 已进 friction_knowledge_base line 229；Studies 53-64 都 explicit 列 fa1 列 | (i) SKILL.md §0.4 文字对齐 FK8；(ii) Study 47 FK8b 的 mandatory Spearman + Reviewer gate 合入 FK8 |
| **P2** | Phase 1 结束时缺 (a) rationale 修正 / (b) 归独立 short-h FA / (c) abandon 三条合法出口，流程事实上鼓励 (d) 语义改名 | Study 37 (d); Study 31 机制信心 + in-sample 污染 7x shrinkage | **未缓解** | 配合 P0 rationale + P7 独立 FA 家族 + P4 Reviewer kill gate |
| **P3** | 饱和判据是局部的，不是 target-relative | Study 37 在 h=5 饱和，主口径未作饱和判据 | **未缓解** | Phase 1 饱和条件 + rationale 验证状态 |
| **P4** | Reviewer 章程"不参与研究决策"让方向 kill 没有外部权威 | Study 37 R4 Reviewer 把 horizon mismatch "deferred to Phase 2" | **未缓解** | Reviewer 章程改动（需用户确认）+ Mode A direction fitness |

除此之外还有 5 个**晚期放大类缺陷**（P5-P9），它们让早期错误在 Phase 2/3 被放大而非被修正。

**改进总方向**：**把 FK 库沉淀的经验和 Studies 53-64 已经在做的实践，正式写入 SKILL.md 模板和 target_and_workflow**；再补 P2-P4 三条结构性缺口（合法出口 + target-relative 饱和 + Reviewer direction kill）。**不推荐在 Phase 0 写 Python + 跑 IC gate** 这种与 skill philosophy 不符的重型流程。

---

## 1. 逐缺陷诊断（带 line number 证据）

### P0. Phase 0 没有"目标口径先测"步骤 — 最致命的早期锁定

**当前 Skill 规定**（SKILL.md §Phase 0，行 213–219）：

> 1. 接收用户输入（一句话种子想法）
> 2. 产出 `research_report.md` 的 §0 部分：核心假设、直觉来源、微观行为猜测、与已有因子关系
> 3. **不需要预定义因子列表**

Phase 0 **没有任何一步**要求 agent 在 Phase 1 开始前对种子想法做一次 "raw signal × 主 horizon IC" 快速测量。

**Study 37 的实证**（research_log.md R1 Time profile，line 88 起）：

> "The pre-cascade bid erosion happened over ~30s (6 AmountBars if bar duration ≈5s), followed by an ~100ms trade cascade and price continuation over the next 30-60s. This suggests the *setup* (ghost cancel erosion) unfolds over ~5-10 bars while the *payoff* (price move) is concentrated in 1-2 bars. **If true, the predictive horizon for a ghost-cancel signal might be short (next 1-50 bars) rather than next 100-200 bars** — I should look for IC peaking at shorter horizons and watch for decay profile."

**路径依赖**：基于 n=1 case study（BTCUSDT 2025-08-15 14:00 crash）agent 形成了"horizon 应该是短的"假设，然后 R2/R3 全部围绕 h=1–50 做调查。直到 **R4**（研究_log.md line 438 的 IC table）才第一次对主 horizon h=100 做 forward_returns 测试。R4 的实际数字是：

```
| Horizon | 08-15 IC | 08-15 t | 07-15 IC | 07-15 t |
|---|---|---|---|---|
| next5   | +0.074   | +9.19   | +0.057   | +10.40  |
| next100 | +0.001   | +0.07   | +0.020   | +3.65   |
| next200 | −0.004   | −0.53   | +0.017   | +3.07   |
```

**h=100 上的 IC 不是严格零，而是 cross-day 不稳定**：07-15 有 +0.020（t=3.65），08-15 塌到 +0.001。这是一个更微妙的 failure mode：方向不是完全错的，但信号主要在 h=5 （+0.074），h=100 的弱信号还跨日不稳定。

R4 紧接着写（line 443）：

> "**Effective horizon**: the signal is strongest at h5–h20 bars... This is MUCH SHORTER than the main target (next100–next200). Either (a) the raw factor needs a longer lookback/smoothing, or (b) the main target must be brought closer to short horizons, or (c) a horizon-bridging transform is needed in Phase 2."

三个选项全部是"在承认 mismatch 的前提下救回来"，没有第四个选项"机制可能在主口径上预测力太弱，值得放弃"。那时已经投入了 3 轮观察 + 1 个 classifier (~350 LOC) 的沉没成本，pivot 的心理成本极大。

更糟的是：R1 用来建立 horizon 直觉的 sample 是**一次 flash crash**——这是 outlier event，不是 representative sample。研究员没有要求"在随机 quiet 窗口和 active 窗口各测一次"。

**为什么严重**：R1 的 horizon 直觉来自 n=1 crash；R4 的 h=100 首测来得太晚且仅覆盖 2 天（08-15 + 07-15，其中 08-15 的 h=100 近零），所以跨日不稳定性被当作"Phase 2 要解决的问题"而不是"方向本身有风险的早期信号"。

**改进建议（P0 fix — 修订版 v2.1）**：

> ⚠️ 本建议在 v2.1 中相对 v2 初稿有实质修改。v2 原稿要求"先写 Python 表达式 → 跑 IC → gate"的范式被用户明确拒绝（paradigm 不匹配"观察 → 统计 → 因子"的 skill philosophy）。**修订方向**：不要让研究员先提供表达式再验证，而是在 Phase 0 用**自然语言**建立机制→主口径的因果链条 rationale，让后续观察有明确的检验对象。

在 Phase 0 §0.5（初始化工作目录）之后、Phase 1 R1 之前，新增强制步骤 **§0.6 "Mechanism-to-main-caliber rationale paragraph"**：

```
研究员必须在 research_log 以 [PHASE 0 RATIONALE] 标记起一个章节，用自然语言
（不写表达式、不写 Python、不跑 IC）回答：

1. 种子 idea 指向什么微观现象？（简述 phenomenon）

2. 这个现象通过什么因果链条影响未来 ~5-10 分钟（主口径 h=100-200 ≈ 5-10 min）
   的价格？具体传导路径写下来。允许写"我不确定，需要 Phase 1 验证"——这也是
   一个合法答案，但它会在 R3/R6/R9 的方向适配检查点被重点关注。

3. 如果我的因果链条是对的，Phase 1 观察应该在什么场景下看到什么？
   给出 1-2 条 falsifiable expected observations（不必定量、不必涉及 IC）。
   例子：
   "如果 ghost cancel 真的预言 price formation at h=100，
    那么 cancel 密度高的 bar 后续 ~100 bar 里 volatility + drift 
    应该比平均更明显，且在 cross-coin / cross-day 上 sign-stable。"

4. 如果 Phase 1 观察显示现象在 h=5-20 有结构但 h=100-200 近零，
   我会怎么做？（候选路径：修正 mechanism → 补 horizon bridging encoding /
   归入独立 short-horizon family / 放弃 seed）必须提前选一条，Phase 1 
   可以因为新证据修改选择但必须留下修改痕迹。

Reviewer 在 Phase 0 终审时检查：
- 第 2 点的因果链条是否具体到可验证？（"observed phenomenon → price impact" 
  中间的步骤是否写了出来？）
- 第 3 点的 expected observations 是否具体到 Phase 1 能真的去看？
- 第 4 点是否做了预先选择？

这一步**不要求 agent 提供任何代码或数值**，只要求把 Phase 0 脑子里模糊的
"这个 idea 应该有用" 变成书面化的、可被 Phase 1 证据 falsify 的 commitment。
```

**P0-fix 如何配合 Phase 1 保留现有"观察→统计→因子"顺序**：

- Phase 1 R1-R3 **仍然是开放式观察**——不强加 IC 测量顺序、不要求先写表达式。
- 但 R3/R6/R9 的前置门控（现已存在）新增一项：Reviewer 对照 §0.6 的 rationale paragraph 和最近 3 轮的观察，提两个问题：
  - *"最近 3 轮的观察，是否还支持你 §0.6 第 2 点写下的因果链条？"*
  - *"你 §0.6 第 3 点的 expected observations 被验证了吗？如果没有，是观察不足 / 方法错 / 还是 rationale 需要修订？"*
- 若 rationale 被 Phase 1 观察 falsify → 研究员必须在 research_log 写一条 "rationale revision" 条目，**显式选择**是 (a) 修正机制假设继续、(b) 归入 short-horizon family、还是 (c) 放弃 seed——选了之后，Reviewer 才决定 round 是否 PASS。
- R6/R9 是 kill gate 候选：若连续两次 rationale 被 falsify 但研究员不做 (a)/(b)/(c) 任何决定，Reviewer 升级为 "direction fitness FAIL"（见 P4）。

**这套 P0-fix 杠杆率分析**：

1. 对 Study 37：R1 line 88 的"predictive horizon might be short"在 §0.6 框架下会是 **rationale 第 4 点的预选择**（i.e., "如果 h=100 null，我计划归入 short-horizon family"）。R4 发现 h=100 弱且 cross-day 不稳定时，就直接触发"已预选的路径"，研究员归入 short-horizon 或补 bridging——**不需要再等到 R10 后才被 Codex 吐槽 rhetorical dodge**。
2. 对 Study 40（psychological levels）：§0.6 第 2 点写出因果链条时，大概率会暴露"round number → 心理价位 → ??? → 未来 5 分钟价格"中间没有具体的 microstructure link，这本身就是 reviewer 的警示信号，不需要等 R6 placebo 比真 factor 还显著才发现。
3. 对 Study 35（redundancy）：§0.6 rationale 需要写机制 vs 现有 fa1。这不能直接拦住 fa3_imb_l1 = fa1_depth_imb_1 的身份重合（需要 P1 / FK8 配合），但会让"depth imbalance 到底和 fa1_depth_imb_1 有什么区别" 这个问题在 Phase 0 就显式化。

**这一步不是万能药**：它不能拦截 in-sample 污染 (P5)、冗余身份重合 (P1 / FK8)、mechanism-成立但效应太弱——这些需要其他 fix 配合。它只解决"Agent 在 Phase 0 / Phase 1 早期没把 mechanism-to-main-caliber 因果链条写下来，导致后续验证不知道在验证什么"这一个问题。

**和近期研究（53-64）实际做法的对齐度**：Studies 56/57 已经在 Phase 0 写了类似的 rationale（"Main prediction horizon discipline: focus on next100~200" + "reject unconditioned cancel_asym_raw as main research object" + "incremental direction is narrowly X × Y × Z"）——这已经是 §0.6 精神的雏形。P0-fix 的作用是把它从"研究员个人习惯"正式写入 SKILL.md 模板，让 Codex 跑和新加入的 agent 也会做。

---

### P1. §0.4 Baseline Orientation 是名字匹配，不是 Spearman 计算

**当前 Skill 规定**（SKILL.md §0.4，line 66–89）：

> **SubAgent 任务**：
> 1. 在 Zebra 因子池中搜索与本次研究方向相关的已有因子（**关键词搜索**）：
>    `zebra_pool/f001/agents/base30_agent.h` / `zebra_pool/f002/agents/f002_agent.h`
> 2. 如果发现表达式相近的因子，在历史研究目录中找到对应的研究报告
> 3. 返回：相关因子列表（名称+表达式摘要）、对应的历史研究报告路径及核心结论

**这一步是纯文字+语义判断**。没有任何一步要求"对种子 raw signal 做 Spearman vs 现有因子池"。

**三个实证案例**：

1. **Study 35**（research_log.md §0.4 around line 35 + R-later lines around 551）：§0.4 subagent 返回 "NO L2-depth-based factors. All 69 existing factors are trade/AggTrans-based" 类的判断，研究员据此开始 Phase 1。**结果**：`fa3_imb_l1` 最后被证明 R² = 1.00 vs `fa1_depth_imb_1`（Issue #114 comment 1 collinearity v2 分析）——即它就是 fa1 的一个 monotone transform。研究员在后续轮次（line 551 附近）做了一次 *内部* correlation check 发现 "`corr(d_imb_ema8, imb_L1) = +0.9039`" 并震惊——但这个 check 的对象是"自己的 Δ-EMA 变体 vs 自己的 raw level"，并没有把 `imb_L1` 与 `fa1_depth_imb_1` 做 Spearman。"candidate vs fa1 pool" 的直接比对要等到编译+落地+跑 batch 之后，外部的 collinearity v2 分析才发生。

2. **Study 47**（research_log.md R8 + `phase1_skill_update_proposal.md`）：研究员在 §0.4 时**正确地识别了 `fa1_depth_imb_1` 是潜在相关因子**，但基于语义判断做了分类：

   > "In Study 47 R5, I concluded that cost_asym_3x (a VWAP cost asymmetry across 3× bar threshold, consuming multiple L2 levels) was 'different family' from fa1_depth_imb_1 (an L1 depth imbalance snapshot). R8 later revealed they are **0.924 Spearman rank-correlated** — essentially the same signal under a monotone transform. The semantic judgment was incorrect despite being reasonable a priori."
   > (phase1_skill_update_proposal.md)

   Study 47 R8 是在投入 8 轮调查后才手动做的 Spearman check。此前所有的机制理解、残差化、IC 测试都建立在"cost_asym_3x 与 fa1 独立"的错误前提上。

3. **Study 41**（同样由 phase1_skill_update_proposal.md 引用）：

   > "Study 41 hit the same pattern at R4 where `f_l1_imb` was found to be **0.9963 Spearman correlated** with `fa1_depth_imb_1` after being assumed independent for 3 rounds."

**校正（v2.1）**：上文关于"Study 47 FK8b 提议从未 upstream" 的表述需要修正。

**实际情况**：Study 41 产出的 **FK8** 条目**已经 upstream 到 `friction_knowledge_base.md` line 229**，而 §0.2 "读取已知陷阱"强制要求所有新研究开始前读这个文件。FK8 原文明确写出了 Remediation：
- "When running the §0.4 SubAgent scan, instruct it to also search `/data/db/crypto/futures/world/world_pool/fa1/` and `/fa2/` for L2 / depth / imbalance / concentration / gradient / entropy / divergence / counter / stale / churn factors."
- "Any candidate Study-X factor should be FK7-checked against ALL relevant fa1/fa2 factors **before** Phase 2 investment, not after."

同时 FK8 也明确标注了一条"Skill template fix (upstream)": "update the skill's §0.4 instructions to include fa1/fa2/production pools alongside zebra_pool/f001/f002. Also update §Phase 1 Round 1 to recommend the FK7 check as a standard step before factor investment"——这条**upstream to SKILL.md 的行动项没被执行**。

**实证（Studies 53-64）**：所有 Studies 53-64 的 §0.4 都显式列出 fa1/fa2 具体列名并预注册 FK7 residualization（Study 55 甚至在 Phase 0 显式引用 "FK8" 标签）。这说明 FK 知识库路径**已经事实上解决了 Problem B 在 Claude-Code 跑的研究里的表现**。

**真正的 gap（修订后的 P1 主诊断）**：

1. **SKILL.md 文字 vs friction_knowledge_base.md 的内容不一致**。SKILL.md §0.4 文字仍然只让搜索 f001/f002；FK8 的 remediation 则扩展到 fa1/fa2。这种不一致会让**新 agent / Codex agent / 没认真读 FK 的 agent** 回到老路径。
2. **FK 路径的作用域限制**：FK8 是"建议性 remediation"，不是 SKILL 强制 step。研究员可以跳过 FK 建议而不触发 compliance fail。新 agent 和 Codex 跑可能 skip FK 直接走 SKILL.md。
3. **Study 47 的 FK8b（Spearman 必做 + Reviewer gate）** 提议比 FK8 原始条目更严格，但它躺在 Study 47 目录里没进 friction_knowledge_base 也没进 SKILL.md。

所以 **P1-fix 的真正内容不是"新增 Spearman 检查"**（那已经通过 FK8 在跑了），而是**三件事的对齐**：

(i) 把 FK8 的 Remediation 明文写入 SKILL.md §0.4（文字对齐 friction_knowledge_base）
(ii) 把 Study 47 FK8b 的"Spearman 必做 + 阈值 gate + Reviewer 验证"合入 FK8（升级现有 FK 条目）
(iii) 如果 Codex 跑的 skill 和 Claude 跑的 skill 对 FK 的依赖度不同，单独同步 Codex 版 SKILL.md

**校验**：用户回忆对 claude skill 做过相关改动，实际的改动应该就是 2026-04-11 那天把 FK8 加入 friction_knowledge_base.md。user 的直觉"已经做了"是对的，改动的落点是 FK 库而非 SKILL.md——所以 SKILL.md 视角看 P1 还没修，friction_knowledge_base 视角看 P1 已经部分修了。

（下面保留原来的 Study 47 FK8b 引用作为"可以进一步升级"的依据，不作为"fix 未做"的证据）

继续引用 Study 47 研究员的建议（仍然值得 upstream）：

Study 47 研究员提议的 fix（FK8b）：

> "SubAgent deliverable must include a Spearman correlation table. For each top-10 name-matched fa1/fa2 column... report `Spearman(candidate, column)` on 1 reference cell. The output includes an alert for any |Spearman| ≥ 0.60."
> "Cost: the Spearman computation on a single reference cell (~1900 sampled bars) takes < 5 seconds per column. For a typical §0.4 scan of 20-30 candidate columns, total overhead is < 3 minutes."

这条提议躺在 Study 47 的目录里一个月了，没被写入主 Skill。

**改进建议（P1 fix）**：**直接采纳 FK8b** 并把它升级为 Phase 0 Gate（不是 Phase 1 R1 check）。具体：

- Phase 0 §0.4 subagent 返回结果必须包含 `Spearman(seed_signal, each_baseline_col)` table，至少覆盖 1 个 reference cell（例如 BTCUSDT 2025-08-15）
- 任何 |Spearman| ≥ 0.70 的 baseline 列：research **阻塞**，必须 agent 在 research_log 正式说明 "为什么看起来 0.70+ 相关但机制不同" 并由 Reviewer 批准才能继续
- 任何 |Spearman| ≥ 0.95 的：**直接 abort Phase 0**，研究重定位

---

### P2. Phase 1 是"机制理解"框架，不是"预测力检验"框架

**当前 Skill 的 Phase 1 心态**（SKILL.md line 219）：

> Phase 1: 深度微观结构调查（核心阶段）
> ⚠️ 这是整个研究的重心。

产出要求（line 319）：

> 产出：微观机制理解、候选因子草案、已排除方向、信心判断。

整个 Phase 1 的语言是"理解微观结构"和"建立机制直觉"。**"预测力"这个词在 Phase 1 部分没出现过**——Phase 1 的成功标志是"看懂了机制"，而不是"验证了因子在主口径上有信号"。

**Study 31 的实证**（Issue #113 背景 + research_report.md / research_log.md 本地直读）：

Issue #113 原文记录 Study 31 (accept_reclaim vwap) 的 "研究 IC 0.025 → production RankIC 0.003，shrinkage 7x"——这是 Issue #113 作为 trigger 案例的声明，具体 production 口径来自 Issue #113 整理时 cken 所用的 analyzer run。**本地 fa2 IC 报告** (`zebra_pool/fa2/report/fa2_{2025,2026}_ic.csv`) 显示 `fa2_accept_reclaim` 在 2025 pool 的 RankIC −0.0036，2026 pool 的 RankIC +0.0124——两个数都远低于研究 IC 0.025，shrinkage 方向正确但具体倍数取决于口径。

更关键的、可直接从本地 log 验证的事实：

- Phase 1 R1–R20 的 mechanism exploration 使用了 hand-selected 高冲击事件，样本围绕 2026 年 1 月中旬的几天（research_log.md R1-R20 case study dates: 2026-01-12, 01-19, 01-22）
- Phase 2 小样本筛选的 manifest（research_report.md line 312–315 附近）：5 symbols × 10 dates，dates 是 `2026-01-02, 01-04, 01-07, 01-09, 01-12, 01-14, 01-16, 01-19, 01-22, 01-25`——**包含 01-12、01-19、01-22 这三个 Phase 1 已看过的日期**
- Phase 3 扩展到 7 symbols × ~20 dates 但仍在 `2026-01-01 ~ 2026-01-25` 范围内，**没有跨出 Phase 1 探索的月份**

这是**典型 Phase 1 → Phase 2 in-sample 污染**：机制假设来自 hand-picked 高冲击事件的观察，验证样本包含这些事件，所以"因子真的在验证集上有 IC"和"因子只是拟合了我观察时挑的 anomaly"在数据上分不开。研究员的主观信心来自"7 币种都 sign-positive"类的 robustness 叙事，但这种 robustness 只在已知分布内才成立。

**Study 37 的实证**（v2.1 修订）：R4 第一次测 h=100，发现 08-15 近零 (+0.001, t=0.07)、07-15 弱但非零 (+0.020, t=3.65)。研究员在 line 443 附近给出三个方向：

> "Either (a) the raw factor needs a longer lookback/smoothing, or (b) the main target must be brought closer to short horizons, or (c) a horizon-bridging transform (e.g. EMA of short-horizon signal) is needed in Phase 2."

**这三个方向本身是合理的 exploration**（用户原话："既然研究 topic 已经给定，那最好还是多做些探索，想想该 idea 下是否还有办法找到适合的构造和研究"）——R5/R6 确实尝试了 (c) horizon bridging，发现 cumulative-sum 和 slow EMA 都在 cross-day 上 sign-flip（line 643 "the horizon bridging by smoothing path is effectively closed"）。这是**健康的探索 + 诚实的证伪**。

**真正的失效点**不是 "只会 rescue 不会放弃"，而是**探索穷尽之后的 fallback 行为**。R6 bridging 证伪之后，研究员有 3 条合理路径：
- **(a) 修正 mechanism-to-target rationale**：也许 ghost walk 机制根本不预测 h=100-200 方向，只预测 h=5-20 volatility regime——这是**重新定义 mechanism 的边界**，是有信息价值的结论
- **(b) 归入独立 short-horizon FA 家族**：承认这些因子的目标 horizon 是 h=5-20，用独立的 benchmark 评估，不和 main-caliber FA 混在一起
- **(c) 放弃 seed**：bridging 失败 + 方向不清 → 这条路不走，下一个 seed

研究员实际做的是 **(d)**："LGBM enrichment / regime feature" 语义改名（Phase 2 framing, line 1224: "short-horizon volatility regime features for LGBM enrichment, NOT main-target directional alpha"），然后以 main-caliber FA 姿态交付给 FA3 编译。

Codex 在 Phase 1 Exit（line 1021 附近）精确指出这个选择是 rhetorical dodge：

> "If Phase 2 still headlines next100~200 and hopes tree models bridge h5 features into long-horizon alpha, that is a rhetorical dodge. Phase 2 must explicitly reframe evaluation to h5-h20 + interaction lift."

但因为流程里没有"(b) 独立 short-horizon FA 家族"这个可选出口（分流路径不存在），(d) 语义改名事实上成了沿途阻力最小的路径。

**修订后的 P2 诊断**：

Phase 1 的"机制理解"框架本身并没有错——机制理解是必要的。问题是当机制理解完成但主口径预测力不足时，流程没有**提供合法出口 (a) (b) (c)**，反而通过 "IC profile 是诊断不是 gate" 这类语言给了 (d) 语义改名合法性。修正方向不是"让 Phase 1 更强调预测"，而是：
- P0-fix (§0.6 rationale) 让 rationale 可以被 Phase 1 观察 falsify
- P7-fix（独立 short-horizon FA 家族）提供 (b) 出口
- P4-fix（Reviewer direction fitness kill gate）让 (c) 出口有外部权威
- (d) 语义改名路径被 P7 明文禁止

**为什么严重**：当"理解机制"被定位为 Phase 1 的核心产出，任何看懂了机制的 agent 都会**把机制理解误认为因子成功**。机制理解是成功的必要条件，但远远不是充分条件。

**改进建议（P2 fix）**：

把 Phase 1 的产出要求从"机制理解"改为 **"falsifiable prediction machine"**：

```
Phase 1 的产出 = 一个能在主口径上做出可测试预测的假设，而不是"理解了机制"。

每轮调查结束时必须产出一条如下格式的 falsifiable prediction（覆盖"效应时间特征"字段）：
  "If my current mechanism understanding is correct, then in a randomly sampled window
   with [observable condition X], the main-caliber (h=100 or h=200) IC should be
   in range [lower, upper] with sign [pos/neg], and cross 3 symbols should show
   consistent sign."

R1 的预测 IC 区间宽容（例如 ±0.05），R10 必须收敛到 ±0.01 以内。
每次 Reviewer check 都必须验证：这条 prediction 是否被上一轮数据 falsify？

Phase 1 退出条件从"饱和"改为：
  (a) 最近 3 轮的 falsifiable prediction 都在预测区间内（predictions 兑现）
  (b) OR 预测被数据 falsify → 必须修正机制假设后重新进入循环
  (c) OR 连续 3 轮修正都失败 → 应认定方向无效，回到 Phase 0 重定位
```

这一步把 Phase 1 从"exploratory" 改为 **"predict then test"** —— 每一轮都是一次科学实验，不是一次观察。

这也恰好对应 Issue #114 comment 初步共识里的第 2 条：

> "预言式检验（pre-registered predictions）：在看 IC 之前先写下预期（sign、regime 依赖、极值场景、跨币种一致性等），再验证预言是否兑现，而不是验证 IC 是否过阈值——防止故事叙述式的自圆其说"

但 Issue #114 只是方法论原则，没说 "在 Phase 1 每一轮都必须写"。P2 fix 是把它落到 Phase 1 循环内的强制步骤。

---

### P3. Phase 1 饱和判据是局部的，不是 target-relative

**当前 Skill 规定**（SKILL.md line 314）：

> **饱和条件（主要退出标准）**：观察开始重复，不再有意料之外的发现。必须在 research_log 中明确论证饱和原因。

这是**局部饱和判据**——它只看 agent 自己的探索是否还有新东西。它不看 "explored phenomenon 是否对主口径有预测力"。

**Study 37 的实证**：Phase 1 的 10+ 轮调查完美满足了"观察不再重复"——研究员在 h=5–h=20 上充分探索了 ghost walk、cancel cascade、regime dependency、autocorrelation control、horizon bridging attempts、跨币种稳定性、cross-day sign flip。**所有探索都是真实的新发现**。Phase 1 终审 Reviewer PASS。但这些发现对 **h=100 主口径没有预测力**——agent 饱和的是一个错的 subspace。

**改进建议（P3 fix）**：把饱和条件改为 target-relative：

```
新饱和条件（必须同时满足）：

1. 探索饱和（原条件）：最近 2-3 轮无意料之外的新观察
2. 预测收敛（P2 新增）：最近 3 轮的 falsifiable prediction 都兑现
3. **target-caliber stability**（新增）：最新保留的 raw signal / 编码组合在主口径上的 
   Spearman IC 在 3 个随机 (sym,day) 对上同号，且 |IC| ≥ [前面约定的门槛]
4. 若 3 不满足但 1 和 2 满足：进入 "dim_recovery" 模式——必须尝试 horizon bridging
   或重定位至 short-horizon family，不得以"Phase 1 完成"姿态进入 Phase 2
```

第 3 条把"主口径预测力"从一个 future concern 变成 Phase 1 内部的 gate。

---

### P4. Reviewer 是质量审计员，不是方向裁决员

**当前 Reviewer 的角色**（reviewer_prompt.md Mode A）主要检查：
- 调查设计合理性
- 现象描述完整性
- 假设与结论的一致性
- 因子设计启示
- 替代解释
- 探索深度
- 假设演化
- （由 Issue #113 新增）预测目标连接——引导性，**不是 kill gate**

**关键盲区**：Reviewer 可以指出 "cross-day sign flip"（Study 37 R6）、"autocorrelation inflation"（Study 44）、"placebo modulus contamination"（Study 40）——这些都是统计 flaw。但 Reviewer 从来不说："你现在这个方向对 main caliber 没有预测力，你应该 pivot 到另一个 seed idea"。

**Study 37 的实证**（research_log.md line 525 附近，[REVIEWER R4]）：

> "H1 cleanly falsified (momentum not reversion, cross-day stable), H5 decisively confirmed (IC 0.17-0.27 with t>27 on both days), ghost flow shown to be independent alpha (67-80% residual retention vs trade flow), **horizon mismatch acknowledged and correctly deferred to Phase 2 for bridging**; the EMA cross-day sign flip is correctly treated as a yellow flag requiring more days rather than being rationalized away."

Reviewer 亲手写了"horizon mismatch acknowledged and correctly **deferred to Phase 2 for bridging**"——把问题踢给 Phase 2，而不是 flag 为必须在 Phase 1 解决的 blocker。Reviewer 的"correctness framework"里没有 "pivot direction" 选项。

**与当前 Reviewer 角色章程的冲突**：现行 reviewer_prompt.md 明文写"你不是执行者，不参与研究决策"（line 6）。给 Reviewer kill-gate 权力直接违反这一条。所以 P4 fix 不是单纯改 prompt 模板，而是**改 Reviewer 的角色章程本身**——从"纯审计员"改为"审计员 + 方向裁决员"。这需要用户层面确认，不是纯 skill 文字修改。

**改进建议（P4 fix）**——分两步：

Step 1（角色章程改动，需用户确认）：在 reviewer_prompt.md §角色定位 加入 "当方向适配性检查触发时，Reviewer 可以对方向本身做 kill decision，不仅限于审查调查质量"。

Step 2（具体触发规则）：在 reviewer_prompt.md Mode A 增加第 9 项 **"direction fitness"**，且该项是 kill-gate：

```markdown
### 9. 方向适配性（每 3 轮 PASS 后触发，kill gate）

触发时机：R3/R6/R9 的前置门控（与 P2/P3 的 gate 一起跑）

审查内容：
- 读取最近 3 轮的 falsifiable prediction tables
- 读取最近 3 轮的 target-caliber IC 测量结果
- 判断方向是否适配：
  (a) 若 prediction converge + target-caliber IC 跨 3 (sym,day) sign-stable → PASS
  (b) 若 prediction diverge + target-caliber IC 近零 → **FAIL with direction_abort**
      此时 Reviewer 必须输出一条"建议 pivot 方向"的具体建议，
      主进程必须在 research_log 写"pivot 处置表"并决策
  (c) 若 prediction converge 但 target-caliber IC 近零 → **FAIL with reframe_required**
      强制要求 agent 重定位到 "short-horizon regime" 或 "non-predictive feature" 
      分支——不得以 main-caliber 姿态继续
```

这是 Reviewer 第一次被授予"kill a direction"的权力。Issue #113 新加的"预测目标连接"是 guidance-only；这里是 kill-gate。

---

### P5. 缺乏 in-phase holdout — 数据污染在 Phase 1 就发生

**Study 31 的实证**：

Phase 1 在 January 2026 date range 的 **hand-selected** 高冲击事件上做机制探索（research_log.md R1-R20 围绕 01-12/19/22），agent 基于这些事件的观察设计了 factor。Phase 2 small-sample 使用**相同的 date range**（5 coins × 10 dates, `2026-01-02` 到 `2026-01-25`，其中 01-12/19/22 即 Phase 1 的重点观察日）计算 IC ≈ 0.0329。Phase 3 用同一个月扩展到 20 dates 复现 ≈ 0.0323。**到 production 跨出 January 2026 之后，fa2_accept_reclaim 的 pool RankIC 显著下降**：本地 `zebra_pool/fa2/report/fa2_{2025,2026}_ic.csv` 显示 2025 pool −0.0036 / 2026 pool +0.0124——方向是明确的 shrinkage，具体倍数取决于口径。Issue #113 body 基于当时 analyzer run 记录为 "0.025 → 0.003 (7x shrinkage)"，本地独立 verify 出的数值不同但 shrinkage 现象一致。

7x shrinkage 的根本原因：**in-sample 污染从 Phase 1 就开始**。agent 看过的数据和 agent 声称的 IC 测量数据是**同一 date range**。

**当前 Skill 规定**（SKILL.md §3 数据纪律红线）：

> 研究集 A（主）：2025-07-01 ~ 2025-09-30 — Phase 1 观察 + 统计探索 + 因子设计 + 小样本筛选
> 研究集 B（辅）：2026-01-10 ~ 2026-01-20 — 跨时段风格验证 + 大样本泛化

Skill 认为"研究集 A 用于 Phase 1-2，研究集 B 用于 Phase 3" 就足够。但这对抗不了 in-sample 污染——研究集 A 内部没有再切 holdout。

**改进建议（P5 fix）**：

```
研究集 A 进一步细分（强制）：
  A_probe:      2025-07-01 ~ 2025-07-15（14 天）— Phase 0 target probe + Phase 1 观察
  A_explore:    2025-07-16 ~ 2025-08-31（47 天）— Phase 1 自主调查 + 机制确认
  A_holdout:    2025-09-01 ~ 2025-09-30（30 天）— Phase 2 小样本 IC 的唯一 holdout
  A_probe 和 A_explore 都允许 agent 看、调查、设计因子。
  A_holdout 在 Phase 2 小样本 IC 之前 AGENT 不得直接观察或 navigate，只能由 scanner
  script 读取数值输出。
研究集 B 保持不变 (Phase 3 大样本泛化)
```

这一步强制把"agent 看过的数据"和"IC 数字来源"分离，确保 Phase 2 的 IC 不是 in-sample metric。

---

### P6. Codex 咨询时机太晚

**当前 Skill 规定**（SKILL.md line 185–189）：

> 固定咨询节点（共 2 个）：
> 1. Phase 1 Exit Protocol：饱和审查的独立审查方之一
> 2. Phase 2 因子设计后：候选因子列表完成后、小样本筛选前

**Study 37 的实证**（research_log.md line 1021 附近）：Codex 第一次被咨询是 Phase 1 Exit（R10 之后）。Codex 的原文建议：

> "Phase 1 is good enough to move forward, but only under a narrower contract: this is now a **short-horizon quote-churn/regime feature family, not a directional ghost-alpha thesis**."
> "If Phase 2 still headlines next100~200 and hopes tree models bridge h5 features into long-horizon alpha, **that is a rhetorical dodge**."

**Codex 已经正确识别了问题**，但时机是 R10 之后——agent 已经投入 14 轮 + 3 个 factor 设计 + 多个 Python script。"承认这是 short-horizon feature, not main alpha" 变成了 "最小修辞调整"而不是"重定位"。Phase 2 在这个重定义下继续，最终把 3 个 h=5 因子编进 FA3。

**改进建议（P6 fix）**：

```
Codex 咨询时机改为：

1. **Phase 0 target probe 之后、Phase 1 开始之前** (NEW P0 + P1 + Codex早期)
   - 输入：§0.4 Spearman table + §0.6 target probe IC 结果
   - 提问："基于这个 raw signal 在主口径上的表现，研究方向是否值得进 Phase 1？
           如果进，什么是 Phase 1 应优先探索的 dimension？"
   - 如 Codex 建议 abort / reframe → 必须执行（或由 Reviewer 裁决）

2. Phase 1 R3（现有 R4/R7 compliance 点附近，但更早）
   - 输入：R1-R3 的 prediction table + target-caliber IC 演化
   - 提问："predictions 收敛吗？方向看起来能在主口径上形成 alpha 吗？"

3. Phase 1 Exit（保留，但弱化）— 此时大局已定，Codex 主要审因子质量

4. Phase 2 Step 1.5（保留）
```

这是把 Codex 从"晚期审查员"改为 **"早期方向顾问"**。用最便宜的资源（一次 codex 咨询 ~几分钟）在最贵的决策（方向选择）上发挥最大杠杆。

---

### P7. 路径依赖的"LGBM enrichment" 修辞逃生门

**Skill 当前语言**（SKILL.md line 497–501）：

> ⚠️ IC-vs-horizon profile 是诊断工具，不是 pass/fail gate。不同因子可能在不同 horizon 上最强——这是正常的，反映了不同信号的时间尺度。**一个因子在 next50 最强、另一个在 next400 最强，都可能是有价值的因子**
> 
> 关键是理解每个因子的 IC profile shape 意味着什么：
>   - 如果 IC 在短 horizon 强、长 horizon 快速衰减 → immediate impact 信号，**可能更适合作为 LGBM 条件分裂特征**

这段话在哲学上对的。但它被 Study 37 的 agent **精确利用**为路径依赖逃生门：

> "These factors are candidate enrichment features for tree-based models targeting short-horizon volatility regimes." (Phase 2 framing, line 1224)

**"LGBM enrichment / regime feature" 成了 h-mismatch 因子的通用出口**。没有任何对"enrichment feature 也必须过 LGBM ablation Δ valid IC ≥ X" 的硬要求，所以这个 label 不消耗因子；它只是给因子一个避免被 kill 的理由。

**改进建议（P7 fix）**：

```
在 Skill 明确：

任何因子以 "LGBM enrichment / regime feature" 姿态 exit Phase 1/2/3 时，
必须满足：
  (a) 在 Phase 3 LGBM ablation 上 Δ valid IC ≥ +0.001（具体阈值 TBD）
  (b) 或作为独立 "short-horizon FA" 家族单独成章（不混入 main caliber 的 FA）

禁止 label 式 exit：
  不接受 "我标注为 regime feature 所以 horizon gate 不适用于我" 的修辞
```

这个改动的目的**不是**把 enrichment 因子全部 kill（#46 的 lifetime-distribution 因子可能恰好是好的 enrichment），而是让 enrichment label 不再是一个免费的逃生门。

---

### P8. "3 个独立微观机制" 要求鼓励 breadth over depth

**当前 Skill**（SKILL.md line 313）：

> 结束条件（必须同时满足）：
> - ≥10 轮 Reviewer 通过的调查
> - **≥3 个独立微观机制发现**，每个有 ≥2 场景交叉验证

这个要求在 Phase 1 早期就创造了"我必须再找 2 个机制"的压力。结果是 agent 在一个可能有机制但没有主 horizon 预测力的方向上做 3-4 轮发现 → 然后匆忙转到第二个 "mechanism" → 再转到第三个。每个 mechanism 都没有被测完"它能不能在主口径上产生 alpha"。

**Study 35 的实证**：Phase 1 围绕"depth flow divergence"做了 10+ 轮，产出了 walkadj / imb_L1 / signed-walk / defense / resilience 等多个 "mechanism"，但**没有一个被测过是否和 fa1_depth_imb_1 独立**。广度被奖励，深度没有。

**改进建议（P8 fix）**：

```
把 "≥3 个独立微观机制" 改为：

"至少 1 个微观机制满足以下全部条件：
  (a) 机制在 research_log 中被 falsifiable 地描述
  (b) 最近 3 轮 predictions 收敛
  (c) target-caliber IC 在 holdout 上 sign-stable
  (d) 与 fa1+fa2 的 Spearman < 0.70

 可选：在 (a)-(d) 都过关后，额外的机制可以作为 bonus 因子候选进入 Phase 2。
 但没有 bonus 不影响 Phase 1 退出。"
```

去掉"凑 3 个"的压力。宁可产出 1 个真正通过 gate 的因子，也不要 3 个都在灰区的 "mechanism"。

---

### P9. 成功路径（Study 46）是"程序性意外"，不是设计

**Study 46 的对比发现**（subagent 分析）：

Study 46 是 fa3 source 研究里唯一产出跨币种 sign-stable 因子的一项。它的成功路径（subagent 分析 + research_log.md 直接引用 line 910 附近："null trajectory was rescued by the Compliance Monitor's mandate"）：

1. **R2 live residualization 作为 screening gate**：R2 发现候选 A/B/C 在 h=100 上 residualized IC 只剩 1.4%（被 fa1 吸收），直接 kill 这三个候选。
2. **R3 pivot to Study 17 unpromoted raw signals**（Reviewer R2 redirect）：Reviewer 明确建议去看 Study 17 没推进的原始信号。研究员照做，但也失败。
3. **R6 compliance-driven continuation → second pivot to lifetime-distribution**：Compliance Monitor 因为 round 数未达最低要求，阻止 agent 在 R5 结束时收尾。在这一约束下 agent 探索了 queue-lifetime 分支，**这个分支成功了**。

关键在第 3 步：Study 46 自己的 research_log 用的是 "rescued by the Compliance Monitor's mandate"（比我原来写的 "procedural accident" 更准确）。Compliance Monitor 没有提示方向，它只是强制了 round 数，而 round 数约束间接为 agent 创造了探索 orthogonal encoding 的空间。**这不是纯意外，但也不是有意为之的研究策略——它是合规约束创造的探索机会，agent 在这个空间里自主找到了 pivot 方向**。

**为什么严重**：现有 Skill 没有任何地方鼓励 "当前 encoding 失败时，立刻尝试 orthogonal encoding"。Skill 的机制是"探索到饱和就退出"。Study 46 在饱和前就找到了一个失败的直接方向，如果不被 compliance 强制，它就在失败处收工。

**改进建议（P9 fix）**：

```
在 Phase 1 新增循环规则 "encoding-orthogonal probe"：

若在 Round N 发现当前主 raw signal 的 target-caliber IC 近零或显著负向：
  1. 不立即退出 Phase 1
  2. 在后续 2 轮内必须尝试至少 1 个 orthogonal encoding / orthogonal mechanism
     （例如：Study 46 从 cancel-flow → queue-lifetime 是一个 orthogonal pivot）
  3. 如果 2 轮 orthogonal probe 也失败 → 正式 abort direction，不进入 Phase 2
  4. 如果 orthogonal probe 成功 → 新 raw signal 启动新的 Phase 1 循环，round 从 1 重计
```

这是把 Study 46 的 "procedural accident" 正式化为 Skill 规则。它给 agent 明确的信号："一个失败不是 Phase 1 失败，是一个 direction 失败；pivot 是受鼓励的行为，不是懒惰"。

---

## 2. Issue #113 已做了什么，为什么不够

Issue #113 已经应用了 8 项 skill 改动，主要包括：

- Phase 1 周期性"预测目标连接" review（引导性）
- Phase 1 记录新增"效应时间特征"要素
- Phase 2 新增"编码反思"环节
- Phase 2 新增 1a "编码探索" + 1b "因子设计"
- 因子数量目标 ≥10 → 5-8 sweet spot
- Phase 3 IC profile 解读指引（即 P7 的那段话）
- Reviewer Mode A 新增"预测目标连接"项（引导性，非 kill gate）
- Reviewer Mode B Phase 2 终审新增 4 项编码检查

**重要校正**：Issue #113 的改动**不全是** guidance-only。例如 SKILL.md line 383（Phase 2 步骤 0 "编码反思"）和 line 474（因子数量检查）都是 mandatory step / gate。但即便这些是 mandatory，它们都作用于**编码层和产出数量层**，不作用于**方向选择层**。

**为什么不够**（逐条对应）：

| Issue #113 改动 | 是否 mandatory | 作用在哪一层 | 对 fa3 主因的杠杆率 |
|---|---|---|---|
| 预测目标连接 review | 引导性（non-gate） | 方向层（浅） | 低——Study 37 每个触发点收到引导但方向没变，因为 review 本身就是 guidance |
| 效应时间特征记录 | mandatory（六要素之一） | 观察层 | 低——只是定性陈述，不触发任何后续 gate |
| Phase 2 编码反思 | mandatory | 编码层 | 低——fa3 主因在 Phase 1 方向选择，Phase 2 编码是下游 |
| Phase 2 编码探索 1a/1b | mandatory | 编码层 | 同上 |
| 因子数量 5-8 | mandatory | 数量层 | 低——3 个错方向因子 vs 10 个错方向因子没有本质区别 |
| Phase 3 IC profile 指引 | 非 gate | 诊断层 | **负杠杆**——它给 h-mismatch 因子提供了修辞 shield（见 P7） |
| Reviewer 编码多样性检查 | mandatory (Mode B) | 编码层 | 低——下游检查 |

**结论**：Issue #113 的 8 项改动里，有一半是 mandatory 的，但**全部作用于编码/产出数量层，不作用于方向选择层**。fa3 的失效本质是方向错误（horizon mismatch + baseline overlap + in-sample contamination），不是编码不够多样或因子数量错——所以 Issue #113 的补丁在 fa3 相关的主因上杠杆率接近零。

同时我无法从工作区独立验证 "Issue #113 的 8 项改动" 是否就是当前 SKILL.md 里的这些条目；这些条目确实存在于当前 SKILL.md，但它们被写入的时间和 Issue #113 body 描述的 8 项改动之间的映射需要 Git log 或 issue tracker 来完全 verify。以上对应关系基于 Issue #113 body 的描述和当前 SKILL.md 的直接阅读。

---

## 2.5 替代解释与自我质询（codex 同行评审要求补充）

### 2.5.1 "主口径 h=100–200 对 crypto 微结构本来就难，研究员其实是对的"

**可能性**：显著。Study 37 R4 的原始 IC 表格本身就显示 h=5 的 +0.074 远强于 h=100 的 +0.020。Study 46 的 lifetime 因子也是在长 horizon（h=800）上 residualized IC 达到 −0.161。Study 49/50 的很多观察 raw signal 是秒级或 10 秒级事件。如果 AmountBar 3 秒/bar 的 tick 下，大量微观机制的 signal 自然就在 h=5–20，那么研究员的"短 horizon 有信号"发现不是方向错，而是**发现了真实时间尺度**。错的可能是**主目标 horizon 的选择**。

**本报告的回应**：

1. 这个解释**部分正确**。Phase 0 target probe (P0 fix) 的设计就要求同时测 h=5, h=20, h=50, h=100, h=200, h=400——它不会强制"只有 h=100 有 IC 才算有用"，而是**让 agent 和 reviewer 在 round 0 就看清 raw signal 的 IC shape**，然后基于这个 shape 决定：
   - 如果 shape 在 h=100 clearly 有信号：走 main-caliber 流程
   - 如果 shape 在 h=5–20 强但 h=100 弱：走 short-horizon feature 分支（**不是 kill，是分流**）
   - 如果 shape 全零：质疑 seed idea

2. P7 fix 的目的也不是 kill short-horizon 因子，而是让 short-horizon 因子**进入独立 FA 家族**（或者过 LGBM ablation 的独立 gate），不要和 main-caliber factor 混在同一个 verdict 里。

3. 如果**真的大量 crypto 微结构信号都在短 horizon**，那应该**额外新建一个 "FA-short" 家族**，主目标改为 h=20 或 h=50，用不同的 benchmark 单独评估。这是超出本报告 scope 的 Zebra + benchmark 架构级改动，但需要作为 Issue #114 讨论的 open question 放出来——不应被本报告的 main-caliber 修辞锁死。

4. **更根本的自我质询**：v2 报告本身是否在犯"Phase 1 心态"错误？我基于 "agent 的研究产出没有在 main caliber 上增 IC" 就断言 "research process 有 bug"——但"research process 找到了真实的短 horizon 信号"也是一种成功。正确的 framing 应该是："research process 需要在 Round 0 就让 agent 知道自己的 raw signal 在什么 horizon 上有信号，然后决定对应的 FA 分流策略"，而不是"research process 一定要找到 main-caliber 因子"。P0 fix 和 P7 fix 的组合就是这个 framing 的落地。

### 2.5.2 "Issue #113 改动可能在 studies 38-47 之后的研究上已经起作用，只是 fa3 是改动前的研究"

**可能性**：有。Issue #113 创建日期是 2026-04-11。fa3 source 研究里的 Study 35/37 等一大半都是在 2026-04-03 至 2026-04-14 之间做的，其中不少**早于** #113 的修改落地。v2 报告声称 "#113 的改动对 fa3 失效无效"，但严格讲**没看到 #113 改动后的研究案例**，这个论断需要 softening。

**本报告的回应**：

1. 严格讲，v2 的诊断对象是 studies 35/37/38/40/41/47——其中部分研究的执行时间早于 #113 改动落地，所以判断"#113 改动对 fa3 相关的主因是否有效"需要**改动之后的研究作为验证样本**。这个样本目前不存在（或 v2 作者没看）。
2. 但 v2 的 P0/P1/P2/P3/P4/P5 这 6 项都是 **Phase 0 + Phase 1 方向层** 的改动——它们正交于 Issue #113 的 **Phase 2 编码层 + Reviewer guidance 层** 改动。即使 #113 的改动在后续研究上有部分正向效果，P0-P5 仍然补上的是 #113 没覆盖的层。
3. **可落地的 validation 建议**：在 P0-P5 任何一项落地之后，对一项新的研究做"A/B"——既跑当前 #113 版 skill，也跑 P0 加强版 skill，对比两者的 Phase 0 target probe 输出和最终 production shrinkage。这是未来工作。

### 2.5.3 P0-P9 改进之间的潜在冲突和优先级澄清

Codex review 指出几个内部冲突，我在这里显式解决：

**(a) P4（Reviewer direction kill）vs P9（encoding-orthogonal probe）**：

如果 Reviewer 可以在 R3 direction abort，那么 R3 之后的 "orthogonal probe" 强制规则还适用吗？澄清：
- P4 在 R3/R6/R9 触发。direction_abort = 整个 direction 死，agent 必须回 Phase 0 重定位。
- P9 是 intra-round 规则：在任一 round 发现当前 raw signal 的 target-caliber IC 近零或负向时，agent 必须在接下来 2 轮尝试 orthogonal。
- 两者的关系：P9 先发生（agent 自己决定 pivot orthogonal），P4 是兜底（agent 不 pivot 或 2 轮 orthogonal 都失败时，Reviewer 接管 kill）。
- 明确顺序：Round N raw signal 失败 → Round N+1/N+2 orthogonal probe (P9) → 若仍失败，触发最近的 Reviewer direction fitness (P4) → direction_abort 或 reframe.

**(b) P7（禁止 LGBM enrichment 修辞）vs v2 整体主张（不要下游 filter）**：

Codex 正确指出 P7 部分重新引入了下游 LGBM gating，而 v2 整体批判 v1 的 "下游 filter" 思路。澄清：
- P7 的真实目的不是"让 LGBM ablation 成为唯一 gate"——那是 v1 的思路。
- P7 的目的是**禁止 label 式逃生门**：不允许 agent 以 "我标 regime feature 就不用过 main-horizon gate" 作为理由在 Phase 1/2 留住因子。
- 实现方式：要求 short-horizon 因子必须走 **独立 FA 家族**（与 main-caliber FA 分离），不混入 main-caliber verdict。下游 LGBM ablation 是"分流后"的可选验证，不是"拦截 main-caliber"的 gate。
- 修正：P7 的表述 "必须过 Phase 3 ablation Δ valid IC gate" 应改为 "必须进入独立 short-horizon FA 家族，其评估使用该家族独立的 benchmark，不拉低也不掩盖 main-caliber 的评估"。

**(c) P8（从 3 机制改为 1 机制）是否 over-correcting**：

Codex 指出把 "≥3 独立机制" 直接改成 "≥1" 太激进，会导致 under-exploration。澄清：
- P8 的意图是**去掉凑数压力**，不是鼓励浅探索。
- 修正：改为 **"至少 1 个机制必须满足 P2/P3/P5 的全部 gate；额外的机制作为 bonus 但不是 Phase 1 退出条件"**。
- 具体：Phase 1 最低 round 数保持 ≥10，但退出必要条件是"有 1 个机制通过所有 gate"而不是"发现 3 个机制"。

---

## 3. 改进建议总表（P0 → P9）

### 3.1 必须一次落地（P0 群）

| 编号 | 改动 | 落地位置 | 成本 |
|---|---|---|---|
| **P0-fix (v2.1)** | Phase 0 §0.6 **"Mechanism-to-main-caliber rationale paragraph"**（自然语言，无 Python 无 IC）+ R3/R6/R9 rationale 验证状态检查 | SKILL.md 新增 §0.6 + reviewer_prompt.md Mode A 门控 | 低 |
| **P1-fix** | §0.4 subagent 必须返回 Spearman(seed, each_baseline) table, 阈值 0.70 阻塞 / 0.95 abort | SKILL.md §0.4 + FK8b 写入 friction_knowledge_base.md | 低（Study 47 已写好提议） |
| **P2-fix** | Phase 1 每轮必须产出 falsifiable prediction，3 轮验证 predictions 收敛 | SKILL.md Phase 1 循环 + reviewer_prompt.md Mode A | 中 |
| **P3-fix** | Phase 1 饱和条件增加 "target-caliber IC sign-stable" 项 | SKILL.md Phase 1 结束条件 | 低 |
| **P4-fix** | **需先改 Reviewer 角色章程**（从"纯审计员"变为"审计员 + 方向裁决员"，用户确认），再在 Mode A 新增第 9 项 "direction fitness" 作为 kill gate | reviewer_prompt.md §角色定位 + Mode A | 低（但前置需用户确认） |
| **P5-fix** | 研究集 A 内部细分 probe / explore / holdout，Phase 2 IC 必须用 holdout | SKILL.md §3 数据纪律 | 低 |

### 3.2 第二优先（P6–P9）

| 编号 | 改动 | 落地位置 |
|---|---|---|
| **P6-fix** | Codex 咨询时机前移：Phase 0 后、R3 检查点、Phase 1 Exit（保留）、Phase 2 Step 1.5（保留） | SKILL.md §1 Codex 节 |
| **P7-fix** | "LGBM enrichment / regime feature" 不再是 Phase 1/2 的 label 式逃生门。任何主信号在 h<50 的因子必须进入**独立 short-horizon FA 家族**，其评估使用该家族独立的 benchmark，不与 main-caliber FA 混在同一 verdict。禁止 "我贴了 regime feature 标签所以不过 main-horizon gate" 的修辞 | SKILL.md Phase 3 + target_and_workflow.md §1 FA 分流规则 |
| **P8-fix** | Phase 1 退出条件从 "3 个独立机制" 改为 "≥1 个机制通过 target-caliber gate" | SKILL.md Phase 1 结束条件 |
| **P9-fix** | Phase 1 循环新增 "encoding-orthogonal probe" 规则——当前方向失败时强制尝试 orthogonal | SKILL.md Phase 1 循环 |

### 3.3 基础设施层（支持前两层的前置条件）

必须同步补上否则 P0/P2/P3 的 gate 无法执行：

| 编号 | 改动 | 落地位置 |
|---|---|---|
| **I1** (v2.1 降级为可选) | MCP 工具 `compute_factor_ic_pool(...)` — 不再作为 P0-fix 的前置依赖（P0-fix 改为 rationale paragraph 后不需要 IC 工具）。仍对 Phase 2 / Phase 3 LGBM ablation 有用 | crypto_mcp/tools.py |
| **I2** | MCP 工具 `check_baseline_collinearity(seed_signal_code, baseline_pool, reference_cell)` — 输出 Spearman table | crypto_mcp/tools.py |
| **I3** | Skill Phase 0 helper script：一个 Python template，agent 填入 raw signal 定义后自动跑 I1+I2 并输出标准格式 | crypto-deep-factor-research/references/phase0_probe_template.py |

I1+I2 其实就是把 Study 47 研究员的手写 check 升级为一等公民工具。成本：1-2 天开发。

---

## 4. 如果只能做 3 件事

**排序的改进 ROI**：

1. **P1-fix + I2**（baseline Spearman at Phase 0）— 立即拦住 Study 35/41/47 类失效，每个失效省下 8+ 研究轮次 + 后续整个 FA 家族的沉没成本。改动成本 < 1 天。Study 47 研究员已经写好了具体方案。

2. **P0-fix v2.1（mechanism-to-main-caliber rationale paragraph）** — 让研究员在 Phase 0 用自然语言把因果链条写下来，Phase 1 R3/R6/R9 检查 rationale 是否被证据 falsify。这不是 IC gate，不需要 Python / I1 工具，和 skill philosophy（观察优先）完全兼容。对 Study 37 的效果：R1 line 88 的 "horizon might be short" 直觉会被 §0.6 第 4 点的预选择（e.g. "若 h=100 null 则归入 short-horizon family"）承接，R4 的 null 结果直接触发预选择路径，而不需要等 R10 Codex 来吐槽 rhetorical dodge。改动成本 < 半天（纯文字编辑 SKILL.md + reviewer_prompt.md）。

3. **P4-fix**（Reviewer direction kill gate）— 给 Reviewer 正式的 "kill a direction" 权力。**角色章程改动需用户确认**（现行 prompt 明文禁止 Reviewer 做研究决策），之后的 Mode A 第 9 项规则编辑成本低。这是把上面两条硬 gate 的执行权固定化的配套。

这 3 件事一起做，**完全覆盖 Study 31, 35, 37, 41, 47 五项历史失效案例**。

---

## 5. 反思：为什么 v1 报告走错了方向

v1 报告把失效归因到"筛选 gate 不够严"，主推改进是 LGBM ablation gate + compile filter。用户正确指出这是错的：

> "如果 ob 20 轮产出 200 个因子，我完全不 care 他到底有没有成功排除掉不好的因子，我只需要全部丢到 lgbm 去跑个模型自然就知道了，跑个模型并不花什么成本。我们的成本是花在研究有用的因子上面。"

**这个反馈点破了 v1 的根本错误**：LGBM ablation 作为下游 filter 是便宜的，研究作为上游生产是贵的。研究失效的根源是**生产过程中 agent 把时间花在错的方向上**——不是生产出来后没有好的过滤。

v2 报告的全部改进都集中在**生产过程本身**：

- Phase 0 增加快速预检（P0 + P1）→ 在研究开始前就拦截错方向
- Phase 1 每轮强制 falsifiable prediction（P2）→ 让 agent 知道自己在验证还是在 rationalize
- Phase 1 饱和判据包含 target-caliber 的 IC stability（P3）→ 让"饱和"这个词和主目标绑定
- Reviewer 拥有 direction kill power（P4）→ 让方向错误能被外部力量 stop
- 研究集 A 内部 holdout（P5）→ 让 in-sample 污染不再可能
- Codex 早期咨询（P6）→ 让方向选择得到外部视角
- 禁止 "LGBM enrichment" 修辞逃生门（P7）→ 让"机制理解"不等于"因子有用"
- 退出条件改为 1 个硬机制 > 3 个软机制（P8）→ 去除凑数压力
- 失败时强制 orthogonal probe（P9）→ 让 pivot 成为设计路径而不是程序意外

**核心哲学转变**：从 "帮 agent 在任何方向上做出因子" → "帮 agent 在第 0 轮就选对方向，然后在对的方向上深挖"。

---

*本报告的每一条诊断都对照了具体研究的 research_log.md line number；每一条改进建议都对应到具体 Skill 文件的修改点。下一步由 codex 做独立同行评审。*
