# FA3 研究流程深度诊断：为什么"深度因子研究"产出了毫无帮助的因子集

**Context**: Issue #114 — cken 请求独立 review fa3 研究流程
**Author**: Claude Code session, 2026-04-16
**Scope**: 以 fa3 的失效为事实样本，逐层反推研究流程中的系统性缺陷，提出可落地的改进建议
**Input coverage**:
- FA3_ATTRIBUTION_v2.md + REPORT.md + Issue #114 两条 comment
- `crypto_ob_research/` 15 项来源研究（#35, #37–#41, #43–#51）
- `crypto-deep-factor-research` SKILL.md + reviewer_prompt.md + compliance_checklist.md
- `crypto-factor-list-compile` SKILL.md
- `target_and_workflow.md`
- `crypto-research` MCP README + 工具列表
- `factor_agent_docs/FA3_factor_list.md` 元数据

---

## 0. TL;DR — 结论先行

**fa3 的失效不是一个偶发事件，而是现行研究流程里 5 个系统性缺陷叠加的必然结果。**

| # | 失效环节 | 后果 | 责任方 |
|---|---|---|---|
| **D1** | 小样本 IC 筛选不对 baseline 残差化 | 冗余因子（R²≥0.2，占 fa3 的 52%）全部通过 | SKILL + MCP |
| **D2** | Horizon mismatch 不作为 kill 条件 | 只在 h=5–20 有效的因子被写进 h=100 目标的 FA | SKILL + realize flow (defer) |
| **D3** | Null-result 研究能产出 factor_definition.md | 6 项公认 null 的研究的"失败候选"被编进 FA3 | SKILL + compile skill |
| **D4** | 单因子 IC 是 Phase 2/3 的实际唯一 gate | 非线性 conditioning 价值 vs 线性 marginal effect 错配 → 按 IC 精选主动有害 | SKILL + methodology |
| **D5** | LGBM ablation Δ valid IC 不是流程内的强制 gate，只能在 C++ 落地后才看到 | 114 个因子先全部工程化再发现全部失效，sunk cost 锁死决策 | workflow + zebra framework |

所有 5 项都有 fa3 的具体实证依据，每一项都对应一条可落地的改进。

---

## 1. 事实基座：fa3 到底坏在哪

### 1.1 Ablation 层面的结论（来自 Issue #114 comment 2 + FA3_ATTRIBUTION_v2）

| run | filter | n fa3 | Valid RankIC | Δ vs baseline |
|---|---|---:|---:|---:|
| R0 | fa2+fa1 baseline | 0 | 0.0431 | +0.0000 |
| R1 | R²<0.5 | 84 | 0.0402 | **−0.0029** |
| R2 | R²<0.3 | 67 | 0.0384 | **−0.0046** |
| R3 | R²<0.2 | 55 | 0.0437 | +0.0006 |
| R5 | R²<0.2 ∧ \|IC\|≥0.005 | 19 | 0.0424 | −0.0006 |
| R7 | R²<0.2 ∧ \|IC\|≥0.010 | 7 | 0.0420 | **−0.0011** |

- 5/5 matched-recipe fair pairs (h100 clip + h400 rank) 全部 fa3 负贡献
- 最佳子集 R3 +0.0006 ≈ 0.07σ（valid σ ≈ 0.008），和零不可区分
- fa3 family 在 LGBM 中拿走 **~44–45% gain 但 valid 负贡献**（Issue #114 comment 1 原文 44.2%）→ 教科书级 gain ≠ alpha
- 至少 3 个因子（`fa3_imb_l1` R²=1.00、`fa3_imb_l1_rolling_z` R²=0.97、`fa3_d_imb_ema8` R²=0.95）是 fa1 的近复制

### 1.2 来源层面的结论（我独立 review 了全部 15 项研究）

| 类别 | 研究编号 | 共性 |
|---|---|---|
| **A. 诚实 null / retired，不应被编进 fa3** | #38, #40, #41, #44 (+ #50, #51 亦为 null) | 研究员自己在 research_report.md §7 写了 null / retired。#44 原文"no factor_definition.md → WARNING" 说明 compile 实际上比自己 SKILL.md §1.1 描述的还要宽松 |
| **B. 弱证据当强证据** | #43, #45, #47 | raw IC 0.018–0.030，fa1 残差化后 0.0086–0.018，跨币种 sign-flip，但研究员打了"CONDITIONAL PASS / MARGINAL"还是送进编译 |
| **C. 真信号但 horizon 错位** | #37 (+ #39 部分) | 核心 raw signal 在 h=5 / h=20 有结构，研究员在 factor_definition.md 自己标注为"regime feature, NOT main-target alpha"，但仍被编进以 main horizon 为验收口径的 FA |
| **D1-redundancy**（独立维度） | #35, #47 | **真实有 main-caliber 信号**但本质是 fa1 的近线性组合：#35 的 `imb_L1` R²-to-fa1 = 1.00，#47 的 `cost_asym_3x` 与 6 个 fa1 列 Spearman 0.92+。研究本身做对了，缺陷是流程没有 baseline 残差化 gate |
| **D. 真信号 + 正确编码 + 非纯冗余** | #46 (lifetime-distribution 分支), 部分 #48/#49 | #46 经过了 mechanism pivot 并跨币种 sign-stable。#48/#49 的 research_report 也给出了各自的 primary factor 定稿（#48 ships 2 factors, #49 ships 4 primary candidates），但它们在 ablation 层面的独立贡献没有被单独测量过 |

**关键事实**：在 15 项来源研究里，**公认 null / retired 的至少 4-6 项**（#38/#40/#41/#44，加上 #50/#51），**弱证据的 3 项**（#43/#45/#47），**horizon 错位的 1-2 项**（#37 主要，#39 部分），**真冗余受害者的 2 项**（#35/#47 兼类）。即使把 #46 / #48 / #49 算作"机制上有效"的研究，其合起来对 fa3 family 的净贡献也不足以抵消其余 12+ 项研究的失效——这就是为什么 matched-recipe ablation 在 5/5 fair pairs 上 fa3 家族全部负贡献的根本原因。

---

## 2. 逐层归因

### 2.1 SKILL 层（crypto-deep-factor-research）— 4 项缺陷

#### D1. Phase 2 小样本 IC 筛选不做 baseline 残差化

**证据**：

SKILL.md §Phase 2 步骤 3（line 460–467）规定：

> 样本：5 coins × 10 天
> 通道 A：线性 IC（vs ret_lag0_next100, next200）
> 通道 B：非线性预测力（quintile 形状、conditional IC）
> 拓展观察：next400, next800 表现

**完全没有"对 fa1+fa2 做残差化后重算 IC"这一步**。

compliance_checklist.md 里"Phase 2 小样本初筛"也只检查：样本规模、随机抽样、通道 A/B、主预测口径。没有"baseline 残差化"检查项。

**后果的实证**：
- Study 35 的 `imb_L1` 原始 IC 看起来很强（BTC 24 天 pooled +0.25），研究员按流程通过；但 fa3_imb_l1 在 fa3 collinearity v2 中的 R²-to-fa1 = **1.000**（Issue #114 comment 1）——它就是 fa1_depth_imb_1 换了个名字
- Study 47 的 `cost_asym_wide_gated_v1` Phase 2 自己跑 kill test 时才发现和 6 个 fa1 列 Spearman 0.92+ 相关，但这是研究员额外做的"R8 honest check"，不是 SKILL 要求的
- Study 45 的 cascade_count h200 残差化后 35% 被吸收，但研究员还是按"residualized +0.018 > 0.010 gate"通过

**结论**：D1 是 fa3 失效的第一主因。`fa3_collinearity_summary.md`（流式 Gram v2，n=28.4M）给出的分布是：

| 阈值 | 数量 | 占 114 个 fa3 因子 |
|---|---:|---:|
| R² ≥ 0.95 | 2 | 1.8% |
| R² ≥ 0.80 | 6 | 5.3% |
| R² ≥ 0.50 | 30 | **26.3%** |
| R² ≥ 0.30 | 47 | 41.2% |
| R² ≥ 0.20 | 59 | **51.8%** |
| median | — | 0.2107 |

其中 26.3% 冗余层（R²≥0.5）是 ablation 里最大的净有害来源。59 个 R²≥0.2 的因子全部是在"Phase 2 小样本 IC 筛选看不到 baseline"的盲点下通过的。

---

#### D2. Horizon mismatch 不是 kill 条件

**证据**：

`crypto-deep-factor-research/SKILL.md` line 497–500（Phase 3 IC 矩阵章节）原文：

> ⚠️ **IC-vs-horizon profile 是诊断工具，不是 pass/fail gate**。不同因子可能在不同 horizon 上最强——这是正常的，反映了不同信号的时间尺度。一个因子在 next50 最强、另一个在 next400 最强，都可能是有价值的因子
>
> 关键是**理解每个因子的 IC profile shape 意味着什么**

这句话在哲学上是对的（非线性 conditioning 因子确实可能不靠线性 IC），但在 fa3 的语境下被错误外推成了"即使主信号在 h=5 也没关系，反正 LGBM 能用"——因为流程里没有任何一步强制这类因子在主 horizon 上过额外的 gate。

**后果的实证**：

- **Study 37**：`research_report.md` §5 表格明确把最终保留的 F1/F2/F3 三个因子都定义为 "short-horizon regime/volatility features for LGBM enrichment, **NOT main-target directional alpha**"。§7 handoff 里研究员甚至主动列了一项 "realize-pipeline must-do"：*"LGBM ablation of F2 and F3 (drop if <0.005 tree-level incremental lift)"* —— 研究员清楚需要 LGBM ablation 来最终定夺，但这是一个被 defer 到 realize 阶段的 "must-do"，realize 流程没有强制执行这条。SKILL.md line 497 的"IC profile 是诊断工具"给了这类因子在研究阶段不过 main-horizon gate 的合法通道。结果是 #37 的 regime/volatility feature 作为 "short-horizon" factor 直接进入 FA3 的 h=100 验收口径，没有独立的 horizon-gate 拦截。
- **Study 35**：本身不是一个纯 horizon mismatch 案例——它的 `imb_L1` 在 main horizon h=100/200 的 BTC fwd IC 也有实证（R5 行 BTC fwd_100/200 有正 IC 记录）。**Study 35 的主 defect 是 D1（冗余，R²-to-fa1 = 1.00），不是 D2**。把它从这一层拿掉。
- **Ablation 直接反例**：Stage 2 R7（只留 |IC| ≥ 0.010 的 fa3 子集）实际上主要是 Study 40 的 `dist_*` 家族加上少量 regime feature。这 7 个"看起来 IC 最高"的因子在 matched-recipe LGBM 里比 R0 baseline 差 **0.0011**——**IC 精选即使没有 horizon mismatch 也单调退化**（D4 的直接证据），当叠加 horizon mismatch 时（fa3 R7 几乎全是短 horizon / 低频因子）结果是双重失效。

**结论**：D2 把"horizon mismatch 的因子应不应该进 FA"这个决定，从流程层甩给了 researcher 的个人判断。研究员在 `factor_definition.md` 里诚实标注了"regime feature, not main alpha"，甚至列了 LGBM ablation 的 must-do；但因为 SKILL 的"profile 是诊断不是 gate"和 realize 流程不执行 must-do，这些警示最后全部失效。Reviewer 的"non-gate" 措辞给了这条路合法性。

---

#### D3. Null-result 研究能产出 factor_definition.md，然后被 compile 吞入

**证据**：

`crypto-factor-list-compile` SKILL.md §1.1 准入规则（line 40–48）原文：

> factor_definition.md 不存在 -> 排除
> factor_definition.md 存在 -> 收录，**无论研究的 Phase gate 是否全部通过**

`crypto-deep-factor-research` SKILL.md 并没有禁止 null-result 研究产出 factor_definition.md。整体而言 crypto workflow 对 null result 持鼓励记录的态度（"失败因子也要记录"是 target_and_workflow.md §1.6 明文原则），这让研究员把 null 分支的失败因子档案写进 factor_definition.md 没有任何障碍。

**后果的实证**（来自 FA3_factor_list.md §0 原文）：

> - #38 trade_flow_price_divergence（null result，factor_definition.md 为空占位符；贡献方法论与 cross-study observations）
> - #40 psychological_price_levels（null result）
> - #41 anchor_gravity_depth_concentration（null result）
> - #44 flicker_ratio_asymmetry（null result, no factor_definition.md → WARNING）
> - #50 add_price_concentration_hhi（null result）
> - #51 frontrun_magnitude_imbalance（null result）

6/15 = **40% 的来源研究自己公开说是 null result**。其中 #40 的全部 12 个 `dist_*` 因子全部是 DISCARDED，但因为"factor_definition.md 非空占位符"被 compile 吞入；结果 fa3 ablation R7 的 IC top 7 里有 6 个就是 #40 的 `dist_*`（Stage 2 最差子集）。

FA3_factor_list.md §0 总表的原始 classification（按组累加）：**RETAINED primary 17 + RETAINED alternate 7 + TENTATIVE 2 = 26** 个"研究员自己认可的因子"，**DISCARDED ≈ 64 + RETIRED 2 + ARCHIVED 1 = 67** 个"被研究员自己淘汰的因子"——二者之和是 **93**，和因子列表原文自称的 "~97" 接近，但实际落盘到 `fa3_agent.hpp` 的 C++ 因子列是 **114**（FA3 code README）。差值（93 → 114）来自 brace-expansion：同一 factor spec 的多组参数变体（如 hl={16,32,64}）在 list 里算一条，在实现时展开为多列。因此"有多少 fa3 列是被 research 分类为 DISCARDED" 的确切数字我不能给；但一个可靠下界是：**DISCARDED 分类至少占 research 阶段因子列表项的 ~65% (64/97)**，这些条目经 brace-expansion 后占 C++ 因子列的大头。

此外，#44 本身按 factor_list 原文说明是"no factor_definition.md → WARNING"——意味着 compile 的真实行为比我前面 quote 的规则更宽松：**不仅 "factor_definition.md 存在"会被收录，"有 factor_list WARNING 标记"也足以被拉进 §3 正文**，与 compile SKILL.md §1.1 原文表述存在一致性 gap。这是 D9 的一个额外佐证。

FA3 的 `code/README.md` 也承认：

> 工程实现阶段应**只默认复现 RETAINED + TENTATIVE**；DISCARDED / RETIRED / ARCHIVED 仅作为历史档案与未来探索候选

但下一行立刻写：

> 用户要求"不丢弃各研究中被丢弃的因子"

用户的这次 override 是个局部事件，但 **compile skill 允许它发生是流程缺陷**——compile 没有"override 超过 N 个 DISCARDED 因子时拒绝执行并要求 issue 批准"的护栏。

**结论**：D3 是 fa3 规模膨胀的主要放大器（factor_list 层 65%+ 的条目来自 DISCARDED 分类，再经 brace-expansion 进入 C++ 列）。若 D3 被拦截，fa3 的可工程化规模会从 114 个因子显著缩小到接近 "RETAINED + TENTATIVE" 的 26 条 base spec 及其合法 parameter 展开——虽然不能精确给出 C++ 列数，但数量级上会小一个 factor 以上。

---

#### D4. 单因子 IC 是 Phase 2/3 的实际唯一 gate，非线性价值没有被独立检验

**证据**：

SKILL.md §Phase 2 步骤 5 原文：

> 保留规则：A类/B类/AB类/R类（研究支撑），不用 IC 作为唯一 gate

compliance_checklist 也检查 "是否未将 IC 作为唯一 gate?"。但实际上：

- 通道 B "非线性预测力（quintile 形状、conditional IC）"的检验方法没有被标准化，每个研究自己写
- 反过早收敛规则要求"所有候选因子都进入小样本 IC 筛选"，强化了 IC 的 gatekeeper 地位
- **没有任何流程要求"在 fa1+fa2 上做 LGBM ablation，看 Δ valid IC ≥ X"才能保留因子**
- Phase 3 "多 horizon × window IC 矩阵"全部是基于单因子 IC 的诊断，从头到尾都是线性 marginal effect

**后果的实证**：

Issue #114 comment 2 的 Stage 2 ablation 证明：**沿 single-factor IC 轴精选 fa3 子集是单调退化的**。R3 (no IC cut) +0.0006 → R4 (|IC|≥0.002) +0.0003 → R5 (≥0.005) −0.0006 → R7 (≥0.010) **−0.0011**。

这是一个决定性反例：LGBM 利用因子的方式是非线性 conditioning，single-factor IC 测的是线性 marginal effect。两者背离时，按 IC 精选会**主动伤害** valid IC。R7 包含了 fa3 的 IC top 7（dist_* 全家），按 SKILL 的"非 IC 但有机制"规则这是金核心，实测反而是子集里最差的。

**结论**：D4 不是 fa3 特有问题，是整个 crypto factor research 流程的一般性 bug。下游任何用 small-sample single-factor IC 做 selector 的步骤都可能踩到这个坑。

---

### 2.2 Methodology 层（target_and_workflow.md）— 1 项缺陷

#### D6. "什么是好因子"没有硬判据，benchmark refresh 是纸面流程

**证据**：

target_and_workflow.md §1.6 "方法论原则"给出的判据：

> - 微观机制优先于统计拟合
> - 时序编码多样性
> - 线性 + 非线性预测性都要
> - 数据纪律红线
> - 失败因子也要记录

**全部是定性原则，没有一条是可执行的数值 gate**。没有：
- "因子对 fa1+fa2 的 R² ≤ X"
- "主 horizon 的 residualized IC ≥ Y"
- "LGBM ablation Δ valid IC ≥ Z"
- "因子保留需要 Stage 5 benchmark refresh 确认"

**Stage 5 Benchmark Refresh Loop 虽然在流程图里**（line 174–198），但：

- "触发：每累计 2-3 个新 FA 落地后" 是建议而非强制
- 没有指定 skill（"目前无专用 skill，手工"）
- fa3 是 15 项研究合并一次编译，中间没有经过任何 benchmark refresh

fa3 在整个开发周期里**从来没有经过一次 LGBM ablation 的正式检验**，直到 fa3 代码跑完全历史数据、生成 analyzer 报告后才第一次看到"merged-vs-fa2+fa1"的数字——那时 114 个 C++ 因子已经写好，batch run 已经跑完，sunk cost 把决策锁死。

**结论**：D6 是 "什么是好因子" 从未被真正定义的原因。本次 Issue #114 的方法论改进就是在补这个缺口，方向是对的。

---

### 2.3 Zebra + MCP 层 — 2 项基础设施缺陷

#### D7. 研究期缺失"轻量 LGBM ablation"反馈闭环

**证据**：

当前流程是 `research → factor_definition → compile → C++ implement → batch run → analyzer`。LGBM ablation Δ valid IC 只能在最后一步 analyzer 阶段看到。

crypto-research MCP 提供的 27 个工具里，没有任何一个能回答"把我这个 raw signal 的 Python 实现加到 fa1+fa2 的 parquet 上，跑一个快 LGBM，报告 Δ valid IC 是多少"。Analyzer 脚本是独立工具链，不在研究会话里。

**后果**：

- 研究员在 Phase 2 小样本筛选时**无法获得** LGBM ablation 反馈
- 任何 horizon mismatch / high-collinearity / duplicate 的问题**都要等到 100+ 小时 C++ 工程化之后**才能暴露
- 研究 → 工程 → 报告的反馈周期是 **几天到一周**，而不是 Phase 2 的 **分钟级**

**结论**：D7 不是一个单点 bug，是整个"研究→工程→评估"链路的节奏问题。即使 SKILL 层加了 D1/D2/D4 的 gate，研究员也只能用 Python 手写 ad-hoc 脚本来检验；缺乏基础设施意味着这些 gate 在实操中会以不同的质量被各个研究员实现，难以保证一致性。

---

#### D8. MCP 缺少 factor pool + baseline 残差化的一等公民工具

**证据**：

crypto-research MCP 的 27 个工具里：

- `forward_returns` — 单 cursor 位置的多 horizon 前瞻收益
- `flow_analysis`, `liquidity_profile`, `analyze_sweep` — 单位置深度分析
- **没有** `compute_factor_ic_pool(expression, symbols, dates, horizons, residualize_against="fa1+fa2")`
- **没有** `check_collinearity(factor_col, baseline_pool)`
- **没有** `lgbm_ablation_delta(new_factor, baseline=fa1+fa2)`

**后果**：

- 每个研究 session 自己用 pandas / pyarrow 写 IC 计算代码，样本定义不一致（有的用 "5 coins × 10 days"，有的用 "BTC 24 days"），数据纪律靠研究员自觉
- 残差化不做或做得不一致（有的 residualize against fa1 flow only，有的 residualize against 全部 fa1+fa2，有的不做）
- 冗余检测只能 after-the-fact（Study 47 靠 R8 手动发现 0.92 rank-corr；fa3_imb_l1 的 R²=1.00 直到 Issue #114 comment 1 的 collinearity v2 分析才被发现）

**结论**：D8 是 D1/D4 在基础设施层面的镜像。没有一等公民的 IC / residualization / ablation 工具，所有上层 gate 都只能靠研究员人肉实现，质量参差。

---

### 2.4 Compile 层 — 1 项缺陷（补 D3 的另一半）

#### D9. compile 没有 pre-merge IC 抽检和 user-override 硬护栏

**证据**：

`crypto-factor-list-compile` SKILL.md §2 编译流程：

- §2.1 合并去重 — **没有一步是"每个待合并因子跑 5coin×3day 的快速 IC + residualized IC 抽检"**
- §2.1 "检查与 baseline（f001 + f002 共 69 因子）的冗余度 -> 标注已知冗余"——但只是"标注"，不是"拒绝"
- §1.1 合规分级的最严处理是 "因子**同样进入** factor_list §3 正文（保证工程可实现），但同时写入 `FA{N}_warning_factors.md`" — **warning 不阻塞工程化**

这意味着 compile 的默认态度是"先工程化再说"。user override（"不丢弃 DISCARDED 因子"）在这套逻辑下是个语义正确的扩展：既然 warning 都不阻塞，discarded 更不会。

**结论**：D9 让 compile 变成了一个语义化的 transform 工具，而不是一个质量 gate。真正的质量 gate 被推到 Stage 3 的 analyzer 阶段，也就是 fa3 的 REPORT.md 所在位置。这条路径意味着**质量问题必然以"工程化后才发现"的姿态出现**。

---

## 3. 改进建议（按改动成本由低到高排序）

### 3.1 SKILL 层（低成本，2–4 小时）

**S1. 新增 Phase 2 步骤 3.5：baseline 残差化必查（补 D1）**

在小样本 IC 筛选通过后，对每个候选因子强制执行：

```
对 5 coins × 10 days 样本：
  1. 计算 raw IC (vs ret_lag0_next100)
  2. 对 fa1+fa2 (198 因子) 做 OLS，取残差
  3. 计算 residualized IC
  4. 计算 R²-to-baseline
  5. Gate: R²-to-baseline > 0.5 → 默认淘汰（保留需独立 rationale）
           R²-to-baseline ∈ [0.2, 0.5] → 标注为"高冗余"，进入 Phase 3 重点检验
           residualized IC < 0.5 × raw IC → 标注"可能已被 fa1+fa2 吸收"
```

这一步直接拦住 D1 的 59 个冗余因子。

**S2. 新增 Phase 2 "horizon match" 检查项（补 D2）**

Reviewer_prompt.md Mode B 因子质量检查增加：

```
- 因子的主信号 horizon（IC 极大值点）是否落在 main-caliber 范围 (h=100~200)？
  - 是 → 通过
  - 否（h=5–20 或 h=400+）→ 不自动淘汰，但必须：
      (a) 研究员在 factor_definition.md 写明"本因子主信号在 h={N}，
          作为 LGBM 条件 feature 而非 main-horizon alpha"
      (b) Phase 2 步骤 3.5 的 residualized IC 必须用主信号 horizon 计算，
          而不是 main caliber horizon
      (c) Phase 3 LGBM ablation（下一条 S3）必须在 main caliber 上 Δ ≥ 0
```

这一步让 horizon mismatch 从"隐性 smuggling"变成"显性 rationale"。

**S3. 新增 Phase 3 终审门 gate：Lightweight LGBM ablation（补 D4）**

Phase 3 新增步骤：

```
1. 从 fa1+fa2 parquet 加载 5 coins × 20 days 的子集
2. 把候选因子的 Python 实现（或 Zebra Agent 的快速 Python 仿真）
   join 到 baseline 上，作为 additional column
3. 跑一个 default-params LGBM (learning_rate=0.1, num_leaves=32, 
   rounds=20), metric=rank correlation
4. 报告：Δ valid RankIC vs baseline-only, Δ top-5-feature-importance 占比
5. Gate: Δ valid RankIC ≥ +0.001 且该因子 rank 进 top 30 feature importance
         才允许进入 Phase 4 交付
```

这一步把 Issue #114 comment 2 的"正确的 selector 是 LGBM ablation Δ valid IC"从事后总结变成流程内强制 gate。成本：每个因子跑一次 20 天子集的 LGBM ≈ 1–3 min CPU。

**S4. 明确 null-result 研究的交付规则（补 D3）**

`crypto-deep-factor-research` SKILL.md 新增规则：

```
如果 Phase 2 终审判定"没有候选因子通过 gate"：
  - 研究员不产出 factor_definition.md
  - 研究员产出 null_result.md，标题为"NULL RESULT: {topic}"
  - research_report.md 的 §5 明确写"No factors delivered; 
    see null_result.md for mechanism archive"
  - quality_review.md 的 final verdict 字段为 "NULL_RESULT"
```

**S5. 明确 horizon-mismatch 研究的交付规则（补 D2）**

```
如果 Phase 2 终审判定"所有候选因子的主信号 horizon ≠ main caliber"：
  - 研究员仍可产出 factor_definition.md，但文件首部必须声明 
    "PRIMARY_HORIZON: h={N}" 元数据
  - 这类研究的因子默认不进入"main caliber" FA 家族，
    而是进入独立的 "fast-horizon" 或 "regime-feature" 子家族
    （可能是未来 FA 编号规则的扩展）
```

---

### 3.2 Compile 层（低成本，1–2 小时）

**C1. 拒绝来自 NULL_RESULT 研究的因子合并（补 D3）**

`crypto-factor-list-compile` §1.1 准入规则修正：

```
- factor_definition.md 不存在 → 排除（已有）
- null_result.md 存在 → 排除（新增）
- quality_review.md 的 final verdict = NULL_RESULT → 排除（新增）
- factor_definition.md 存在 且 非 NULL_RESULT → 收录
```

**C2. Compile 前 pre-merge 快速 IC + residualization 抽检（补 D9）**

对每个候选因子，在编译成 factor_list 之前：

```
1. 要求研究员提供 factor 的 Python 参考实现（或从 research_log 提取）
2. 在 1 coin × 3 days（BTC 2025-07-{01,08,15}）上跑：
   - raw IC @ main horizon
   - residualized IC @ main horizon (vs fa1+fa2)
   - quick Spearman vs 每个 fa1+fa2 列
3. 生成 FA{N}_precompile_check.md 报告
4. 任何 R²-to-baseline ≥ 0.95 的因子 → 自动拒绝合并
5. 任何 residualized IC 与零不可区分的因子 → 标记为 WARN，
   但仍合并（留给 Phase 3 ablation 做最终判定）
```

**C3. User-override 硬护栏（补 D3）**

```
compile 检测到用户在 invocation 里请求"保留 DISCARDED 因子"或
"overrride Phase gate"时：
  - 打印本次 override 将带入多少个 DISCARDED / RETIRED / null 因子
  - 要求用户在 issue 中正式批准 (如创建 approval issue)
  - 如未批准直接 abort compile
  - 关键 stats：DISCARDED 总数 / 受影响研究编号 / 受影响因子占比
```

fa3 的 ~65%+ DISCARDED 因子比例（factor_list 层 64/97）应该触发这道护栏。

---

### 3.3 target_and_workflow.md 层（低成本，方法论文档）

**T1. §1.6 新增"什么是好因子"的 4 条硬 gate（对齐 Issue #114 comment 1/2）**

```markdown
### 1.6a 因子必过的 4 条硬 gate

1. **Duplicate 自动拦截**：因子注册时计算 R²-to-baseline (fa1+fa2)，
   R² ≥ 0.95 直接拒绝（防 fa3_imb_l1 事件）
2. **冗余 gate**：R²-to-baseline ≥ 0.5 默认不入 LGBM benchmark，
   保留需书面 rationale（非线性 conditioning 论据）
3. **Fair-baseline matched-recipe Δ valid IC** 是唯一终极判据，
   不使用 hyperparameter mirage。新 feature 与 baseline 必须用
   同一套 LGBM hyperparams 跑
4. **不要用 single-factor IC 做 LGBM 子集 selector**。
   正确的 selector 是 LGBM ablation Δ valid IC（Stage 2 R5/R7 反例）
```

**T2. 把 Stage 5 Benchmark Refresh 从"建议"改为"强制"**

```
- 每累计 ≥3 个 FA 编译完成 → 必须触发一次 benchmark refresh
- benchmark refresh 未完成前，第 4 个 FA 不得进入 Stage 3 工程化
- benchmark refresh 结果（新旧 valid IC 对比）必须在 research_updates.md 
  记录，作为后续研究的 "待超越目标"
```

---

### 3.4 MCP 层（中成本，1–3 天开发）

**M1. 新增一等公民工具 `compute_factor_ic_pool`（补 D8）**

```python
compute_factor_ic_pool(
    expression: str,          # Python/pandas 表达式或已落盘 parquet 路径
    symbols: List[str],
    dates: List[str],
    horizons: List[int],      # bar horizons
    residualize_against: Optional[str] = None,  # e.g. "fa1+fa2"
    exclude_sym_dates: List[Tuple] = []
) -> Dict[str, IC_Result]
```

返回 raw IC / residualized IC / R²-to-baseline / ICIR / 每日 IC 分布。标准化样本定义、NaN 处理、残差化口径，所有研究用一个口径。

**M2. 新增 `check_duplicates` 工具（补 D8）**

```python
check_duplicates(
    factor_col_parquet: str,
    against_pool: str = "fa1+fa2",
    threshold_r2: float = 0.95
) -> DuplicateReport
```

返回每个超过阈值的 baseline 列 + Spearman/Pearson 相关系数。补 fa3_imb_l1 事件。

**M3. 新增 `lgbm_ablation_delta` 工具（补 D4 + D7）**

```python
lgbm_ablation_delta(
    new_factor_cols: List[str] (parquet paths),
    baseline_pool: str = "fa1+fa2",
    sample_window: Tuple[str, str] = auto,
    lgbm_recipe: str = "default_tuned"  # matched-recipe
) -> LGBM_Delta_Report
```

返回 baseline valid IC / merged valid IC / Δ / gain% / top feature importance。这是 S3 Phase 3 门 gate 的底层工具。

---

### 3.5 Zebra 层（中成本，1–2 周）

**Z1. "研究期 Python 参考实现"的规范化通道**

在 SKILL 的 Phase 2 编码探索阶段，研究员已经在 Python 里实现了因子原型。当前这些 Python 代码分散在 research code/ 目录里，和 zebra C++ 实现没有对齐机制。

改进：

- 规定每个 factor_definition.md 附带的 Python 参考实现必须能 join 到 fa1+fa2 的 parquet 上并作为 pandas DataFrame column 提供
- 提供一个 `zebra-python-ref-runner` 工具，接受 Python 实现 + 日期范围，输出因子列 parquet
- 这样 S3 Phase 3 LGBM ablation 可以跑在 Python 参考实现上，不需要等 C++ 工程化

这条改动打通了 D7 的"研究 → LGBM 反馈"的分钟级闭环。

---

## 4. 改进建议的优先级矩阵

| 改动 | 成本 | 阻止 fa3 的杠杆率 | 优先级 |
|---|---|---|---|
| **S1 baseline 残差化** | 低 | **极高**（直接拦 51.8% 冗余因子） | P0 |
| **C1 null_result 排除** | 低 | 高（拦 4–6 项来源研究） | P0 |
| **T1 4 条硬 gate 写入文档** | 低 | 高（给所有下游角色共同语言） | P0 |
| **S2 horizon match check** | 低 | 中-高（#37 类因子的入口） | P0 |
| **S3 Phase 3 LGBM ablation** | 中（需 M3） | **极高**（唯一终极判据） | P0 |
| **M3 lgbm_ablation_delta MCP 工具** | 中 | 极高（支撑 S3） | P0 |
| **C3 user-override 硬护栏** | 低 | 中（防 DISCARDED override） | P1 |
| **S4 null_result 交付规则** | 低 | 中（上游切断 D3） | P1 |
| **M1 compute_factor_ic_pool** | 中 | 高（标准化 IC 计算） | P1 |
| **S5 horizon mismatch 规则** | 低 | 中 | P1 |
| **S2 horizon check** | 低 | 中 | P1 |
| **M2 check_duplicates** | 低（基于 M1） | 中 | P2 |
| **T2 benchmark refresh 强制化** | 中 | 高（但需要 M3） | P2 |
| **C2 pre-merge IC 抽检** | 中（需 M1） | 中 | P2 |
| **Z1 Python 参考实现规范化** | 中 | 高（支撑 S3/M3 的 infrastructure） | P2 |

**最关键的 P0 应该一次落地**：

- S1（Phase 2 残差化 gate） → 覆盖 D1
- S2（horizon match check） → 覆盖 D2
- C1（null_result 合并排除） → 覆盖 D3
- T1（4 条硬 gate 写入 target_and_workflow.md） → 覆盖 D6 + 总括
- S3 + M3（Phase 3 LGBM ablation + MCP 工具） → 覆盖 D4 + D7

这 5 项组合起来直接覆盖了 fa3 失效的所有 5 个主因（D1/D2/D3/D4/D6），剩余 D7/D8/D9 分别由 M1/M2/C2/C3 以 P1/P2 优先级逐步补上。

---

## 4.5 替代解释与自我质询（codex 同行评审要求补充）

为避免"归因过度"，这里显式列出几个可能的替代解释，以及本报告对它们的回应。

### 4.5.1 "fa1+fa2 本身已接近饱和，任何新 family 都救不了"

**可能性**：非零。Issue #114 comment 2 的 statistical caveat 明确承认 "42 天 valid 的均值 σ ≈ 0.008"，R3 vs R0 的 +0.0006 是 0.07σ 纯噪声。如果 ceiling 就在这里，即使 fa3 所有改进都落地，Δ valid RankIC 的上限也可能被 baseline 已经充分捕获的事实压住。

**本报告的回应**：

1. 这个解释不解释"为什么 fa3 在 5 个 matched pairs 上全部 **负贡献**" —— 饱和假说预期的是 "净效应 ≈ 0 在噪声内"，而不是"系统性落在负侧 0.002–0.005"。fa3 净负向是冗余把 split capacity 吞掉导致的具体损害。
2. 即使 fa1+fa2 已近饱和，现有流程中的 D1/D3 问题仍然是独立 bug——它们会让下一个 family 重蹈覆辙，即使 headline Δ IC 只能在噪声内。
3. 所以"饱和假说"不 override 本报告的改进建议；反而强化一条额外结论：**新 FA family 的立项门槛应该更高**，需要先论证 "和 baseline 有独立的 alpha 信源"而不是"能做出一个新的 114-factor 集合"。

### 4.5.2 "AmountBar 时间尺度本身就不适合 fa3 里很多研究的 raw signal"

**可能性**：显著。Study 37 的原文就写 "signal strongest at h5–h20 bars (AmountBar axis, ~25–100 seconds wall-clock), MUCH SHORTER than main target next100–200"。Study 40/41/44 的 mechanism 很多是秒级到 10 秒级事件，AmountBar (~3s/bar) 的 h=100 (~5 min) 天然离它们几个尺度远。

**本报告的回应**：这正是 D2 的骨架，不是替代解释。我承认 D2 的权重应该更高——在改进建议中，S2 应该从 P1 升级到 P0（已在上表调整）。更根本地，也许需要引入"**多 bar family**"概念：除了 AmountBar 28800，也支持更细粒度的 AmountBar 或直接 wall-clock bar 作为一些 fa family 的自然容器。但这是 Zebra 架构级改动，超出本报告 scope。

### 4.5.3 "Study 48/49 并没有被我正确评价"

**可能性**：有。codex peer review 指出 #48 ships 2 factors, #49 ships 4 primary candidates，它们本身 research_report 结论是 PASS。本报告前版"只有 #46 是 genuine find"是过度简化。

**本报告的回应**：已在 §1.2 修正为多元类别。#48/#49 的因子可能确实有机制价值，但它们在 fa3 ablation 层面的**单因子**贡献从未被隔离测量过——Stage 1/2 ablation 都是按 R² / IC 切片，没有按"来自哪个 source study"切片。这意味着：(a) 我不能声称 #48/#49 是 fa3 失效的主因，(b) 但我也不能 exonerate 它们。**正确的做法是 Phase 3 LGBM ablation gate (S3) 对每个研究的因子独立测**——这恰好也是本报告主推的改进。

### 4.5.4 "early_stopping on valid 造成 LGBM 数字本身有轻微 leakage"

**可能性**：是，但量级小。REPORT.md §7 第 6 条自己承认了这一点 —— "valid IC 略乐观 because 早停选择的 best round 在 valid 上做的"。

**本报告的回应**：对横向比较影响接近零（所有 runs 都有这个 bias），对 headline 0.0431 number 影响有限。它不 invalidate fa3 负贡献的结论——如果有 leakage，fa3 在**相对**比较上的负贡献反而更加 robust（leakage 是加性 bias）。值得在 Issue #114 的 comment 里一笔带过，不影响结论。

---

## 5. 回答原问题

> **"deep-factor-research 为什么会产出毫无帮助的因子集？是 skill 应该改进吗？是方法论问题吗？是 zebra 框架问题吗？是 MCP 设计/功能问题吗？"**

**全部都有问题，但权重不同**：

1. **SKILL 是第一主因**（D1, D2, D3, D4）。它的 Phase 2/3 gates 在三个关键维度上缺失或松弛：baseline 残差化、horizon match、LGBM ablation。**这是可以在几小时内通过修改 SKILL.md + reviewer_prompt.md 拦下 fa3 的大部分失效的。**

2. **方法论是第二主因**（D6）。"什么是好因子"在 target_and_workflow.md 里只有定性原则，没有可执行的数值 gate。Issue #114 的 4 条硬 gate 刚好填这个缺口。

3. **MCP 是第三主因**（D8）。缺少一等公民的 IC pool / residualization / LGBM ablation 工具意味着即使 SKILL 要求这些 gate，研究员也只能人肉实现，质量参差。这是**需要 1-3 天开发**的基础设施补强，但它是长期投入，不做这块的话 D1/D4 的 SKILL 层改动会变成负担。

4. **Zebra framework 本身没有第一性的 bug**。fa3 的 C++ 实现是正确的，join key 对齐、chunk 模式、EMA 口径都对。问题是 Zebra 工程化环节位于反馈链路的末端（需要 batch_runner + analyzer 才能看到 LGBM 效果），这让 D7 "研究期无 LGBM 反馈"的问题暴露成了系统性的 sunk cost 陷阱。改进方向是 Z1 "Python 参考实现规范化"，把 LGBM ablation 前移到 Phase 3。

5. **Compile skill 是最后一道防线**（D3, D9），但默认态度是"让它过"。应该升级为质量 gate：pre-merge 快速 IC 抽检 + null_result 排除 + override 硬护栏。

---

## 6. 三个反直觉发现（写入 meta-lesson）

1. **"研究员诚实"不够**。#38/#40/#41/#44 的研究员诚实地标注了 null result，但流程里的 compile step 还是把它们的"失败因子档案"当成可用因子吞入。**诚实的研究员 + 不挑剔的下游 = 失效的整体**。

2. **"更多时序编码变体"不是解药**。Issue #113 刚给 skill 加了编码反思 + 编码探索机制，鼓励研究员产出多样化的时序编码。fa3 里确实有很多 EMA / diff / ratio / rolling / z-score 变体。但 fa3 失效的主因不是编码缺乏多样性，而是 **baseline 冗余 + horizon mismatch + 无 LGBM ablation**。编码多样性只在这些更基础的 gate 通过后才有价值。

3. **"Gain 看起来很高"是陷阱**。fa3 在 LGBM 中拿到 44.2% total gain，feature importance 表上看似主角，但 matched-recipe valid RankIC 反而负 0.0019。**LGBM 会系统性地偏好与 baseline 高度相关但加了少许 noise 的"轻微变体"特征，把原信号 double-count**。这不是 fa3 特有问题，是所有"先工程化再看 gain%"的方法论都会踩的坑。唯一可信的 selector 是 fair matched-recipe 的 Δ valid IC。

---

## 7. 下一步建议

**对 Issue #114 的直接贡献**：

把第 3 节的 P0 五项（S1, S2, C1, T1, S3+M3）作为"fa3 归因后的 actionable 改进清单"，落地到：

- `quant-workflows/skills/crypto/claude/crypto-deep-factor-research/SKILL.md` — S1 (Phase 2 残差化 gate) + S2 (horizon match check) + S3 (Phase 3 LGBM ablation gate step)
- `quant-workflows/skills/crypto/claude/crypto-deep-factor-research/references/reviewer_prompt.md` — S2 reviewer 模板中增加 horizon match 检查项
- `quant-workflows/skills/crypto/claude/crypto-factor-list-compile/SKILL.md` — C1 (null_result 排除规则)
- `quant-workflows/workflows/crypto/target_and_workflow.md` §1.6 — T1 (4 条硬 gate 明文化)
- `crypto_mcp/tools.py` — M3 新增 `lgbm_ablation_delta` 工具

**对 fa3 family 的处理**：

对齐 Issue #114 comment 2 的建议：正式退役 fa3 family，不再做 v2，也不从中挑子集。fa3 作为"反例库"写入 target_and_workflow.md §1 作为未来研究的参照。

---

*本报告的每一条论点都已对照 fa3 的具体实证数据或 SKILL/workflow 文档的原文引用。下一步由 codex 做独立同行评审，检查是否存在归因错误或遗漏的替代解释。*
