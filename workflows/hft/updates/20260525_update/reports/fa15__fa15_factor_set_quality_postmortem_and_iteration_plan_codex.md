# FA15 因子集质量复盘：哪些“应该 work 但不 work”？为什么？怎么改？怎么证明？（Codex）

> 时间：2026-02-21（UTC+8）  
> 评审范围：  
> - 设计规格：`/home/cken/hft_projects/HFTPool/factor_agent_docs/FA15_factor_list.md`  
> - 设计审阅：`/home/cken/hft_projects/hft_researches/FA15_research/review_report.md`  
> - 实证质量评估：`/home/cken/hft_projects/HFTPool/pool/FA15/report/fa15_quality_review.md` 及其溯源中间报告（`/data/db/hft/temp/fa15_review_*.md`）  
> - 数据与口径：bar 模式，`bar_col=bar_aggtrans_time_1`，universe=bond_sz（166 codes），日期 2025-01-02 ~ 2025-07-30（139 交易日）  

---

## 0. 一句话结论（带批判）

FA15 的“参与者风格指纹”命题成立：B/E/C/D 组出现稳定且可解释的信号（尤其 B 组在 h100-h200）。但**FA15 作为一个“可直接合入 baseline 的因子集”质量不够**：冗余严重、A 组不稳定、部分因子在 merged 模型中完全被替代；此外，E 组 buy-side 的经济解释与最初假设相反，导致“看起来不 work”，但其实是“work 在另一个机制上”。  

---

## 1. 我们如何定义“work / 不 work”（避免语义争论）

本报告将“work”拆成四个层次（越往后越难）：

1. **统计上 work**：单因子 Rank IC（或分位收益）显著、方向稳定、不过度依赖极少数标的。  
2. **机制上 work**：方向/条件效应与微观结构解释自洽，不是纯粹的实现或口径伪影。  
3. **工程上 work**：数值健康、轴对齐正确、鲁棒（极端值、稀疏、低活跃度）。  
4. **增量上 work（最关键）**：与 BL150 合并后仍有边际贡献（gain/IC uplift），而不是被 baseline 直接替代。

“本来 suppose work 但不 work”的讨论，主要针对 **(1)(2)(4)**。

---

## 2. 哪些因子（或因子组）“本来 suppose work，但不 work”？

下面按“失败类型”而非按组罗列——因为很多问题是跨组共性。

### 2.1 失败类型 A：**设计假设方向错（看似不 work，其实是换个机制在 work）**

**对象：E 组 buy-side 执行精准度因子**
- `fa15_perfect_match_ratio_buy`：设计直觉是“买侧完美匹配高 → 知情买/机构执行 → 未来涨”，应正 IC。  
  实证：在多个 horizon 上稳定为负（例如 h100 ≈ -0.027，h200 ≈ -0.032），且 per-code 约 75% 为负（见 `fa15_quality_review.md` §3.1）。  
- `fa15_bite_depth_ratio_buy` 同方向同现象（与 perfect_match 高相关）。

**根因（机制解释）**  
这两个因子更像 **ask 侧薄弱/流动性差的代理变量**：薄 ask → 更容易出现“at_best 成交/深度咬合看起来精准”，但薄流动性本身预测未来收益更差（慢 alpha、截面维度），因此出现稳定负 IC。  
结论：这不是“因子失效”，而是“经济解释需要改写”，并且它在 merged 中被 baseline 的流动性/成交流信息部分替代，导致边际贡献偏弱。

**改进方向**  
把它从“知情买”重命名为 `ask_side_thinness_proxy`（或等价概念），并将其作为**条件特征**：与 spread/depth/flow regime 交互，而非全局线性主效应。

**如何证明（最小闭环）**  
1) 做分桶：按 `fa7_eff_spread_bps_1m`（或相近流动性代理）分位数分组，比较 `perfect_match_ratio_buy` 的分组 IC / 分位收益斜率是否显著不同。  
2) 做残差 IC：对每个交易日、每个截面回归 `pm_buy ~ spread + flow + activity`，取残差 `pm_buy_resid`，比较 resid 的 IC 是否仍显著（若显著 → 说明不是简单替代）。  

---

### 2.2 失败类型 B：**时间不稳定 / 漂移（最典型：A 组 Nice/Round Lot）**

**对象：A 组 Nice Lot / Round Lot**
- 组级表现：h20 组平均 |IC| ≈ 0.0036，且 6 个“前后半段方向翻转”因子里有 4 个来自 A 组（见 `fa15_quality_review.md` §6.1/§6.4）。  
- 组内冗余：nice_lot 与 round_lot 相关度普遍 >0.85，导致“多写了很多列，但信息维度没变”（见 `fa15_quality_review.md` §4.2-§4.3）。  

**为什么会这样**（批判性的两条假设）
1. **参与者行为随时间漂移**：nice set 是离散枚举（50/100/200/…/10000），如果市场风格或最优拆单粒度变化，枚举会失配，导致方向/强度漂移。  
2. **A 组实际上在测“活跃度/流动性/散户占比”的混合物**：不同 regime 下，该混合物与未来收益的相关可能反转（例如活跃提升 → 同时带来短期动量与长期回撤等）。

**改进方向**
- **把 nice set 变成“数据驱动可更新”**：用全市场订单手数分布的“相对邻居超额频率”重选集合，并明确纳入/剔除阈值（review_report.md 里已经提出 10 张与 300 张的边界验证）。  
- **引入连续型补充指标**：例如“末尾 0 的个数（trailing zeros）/手数对数分桶熵”等，作为对离散枚举的 out-of-set 检验，减少漂移风险。  
- **在模型侧显式做正交化/消融**：先以 round_lot 为主，nice_lot 只保留“超出 round_lot 的增量”，否则直接删。

**如何证明**  
1) 在 3-5 天全市场数据上，比较：旧 nice set vs 新 nice set 的（a）正例率（b）与 round_lot 的相关（c）IC 稳定性（分日、分月）。  
2) 做时间分段一致性：将样本按月或按前后半段切分，对比因子方向与强度是否显著更稳定。  

---

### 2.3 失败类型 C：**方差/有效样本不足（或被硬阈值/稀疏性“杀死”）**

**对象（代表）**：
- `fa15_nice_lot_imb_slow`：唯一不显著（t≈0.80）。  
- `fa15_price_coarse_vol_share`：弱且出现方向翻转（见 `fa15_quality_review.md` §6.1）。  
- `fa15_micro_order_intensity`：均值 IC 小、且前后半段翻转（见 `fa15_quality_review.md` §6.1）。

**为什么**  
这类因子往往同时满足：  
1) 触发事件偏稀疏或被 EMA 平滑过度；2) 与同组/跨组变量高度共线；3) 对低活跃标的衰减导致信息被“冲掉”。  

**改进方向**
- 对“稀疏事件”采用“双通道表达”而不是单个 EMA 比率：`time_since_last_event` + `event_intensity`（或 fast/slow 差分）。  
- 对“vol_share”类，增加 gating（`min_total`）或对数变换，避免在 `ema_total` 很小的区间噪声爆炸（review_report.md 里也指出了这一点）。  

**如何证明**  
针对每个“疑似死因子”，先做**分布体检**（正例率、有效样本数、分位数跨度、在低活跃 code 上的 near-zero run length），再决定是否改造或删除。`/data/db/hft/temp/fa15_review_distribution_analysis.md` 已给出 E 组近零误判纠正的范例口径。

---

### 2.4 失败类型 D：**“在 FA15-only 里看起来很强，但合入 baseline 后边际贡献为 0”（内卷效应）**

**对象：多数学 E 组 imb / A 组对照 / 部分 C 组密度类**  
现象：FA15-only 模型 Top10 中，8 个在 merged 模型 gain=0（见 `fa15_quality_review.md` §5.2）。  

**为什么**  
两类情况：
1) **真正被替代**：例如 `perfect_match_imb` 与 baseline 的 `trade_flow_imb` 相关达 |ρ|≈0.40，方向性信息被更强的 baseline 覆盖。  
2) **主效应弱但交互强**：FA15-only 环境下 LGBM 被迫挖交互，导致 gain 虚高；一旦 baseline 加入，交互不再“稀缺”，gain 归零。

**改进方向**
- 以“baseline 缺失维度”为目标做差异化：例如强化 sell-side、新增“变化率/突变”而不是水平值。  
- 用残差/正交化把 FA15 从 baseline 轴上挪开：`x_resid = x - Proj(x | baseline)`，再看增量。

**如何证明**  
做三组对照（严格同样时间切分、同样超参/种子）：
1) BL-only；2) BL+FA15(original)；3) BL+FA15(refined/orthogonalized)。  
观察：valid rank IC uplift、gain 分布变化、以及“FA15 存活因子”是否从 5/35 提升到更合理水平。

---

## 3. 我们建议的迭代路线（按投入产出排序）

### 3.1 低投入高确定性（1-3 天）

1) **评价口径对齐**：FA15 标准评估 target 至少采用 h100/h200（B/G 组的优势在长 horizon 才显现）。  
2) **精简为“可维护的非冗余子集”**：按 `fa15_quality_review.md` 的 35→18 精简表执行，并补做消融确认。  
3) **文档修订（避免误解）**：把 E 组 buy-side 的解释改成“流动性薄弱代理”，并在因子说明里明确“IC 方向可能与直觉相反但可用于模型”。  
4) **输入侧鲁棒处理**：D 组做 winsorize/log1p（kurtosis>200），避免模型被极端值牵引。

### 3.2 中投入（需要刷数/改代码，3-10 天）

5) **A 组重标定（nice set 数据驱动 + 连续型补充）**：解决时间漂移与冗余问题。  
6) **E 组重构**：从 7 列压到 3 列主干（pm_buy/pm_sell/pm_imb），并尝试 soft-match 与 delta 表达；对低活跃标的做 activity-conditional halflife 或 decay floor。  
7) **B 组增强（最优先的扩展方向）**：增加“整数偏好变化率”、按价格/流动性分段的偏好、以及与大单/小单的交互。  
8) **tick-EMA vs time-decay EMA 对比**：解决跨标的语义不一致（活跃度差异）的问题（review_report.md 已给出 R8）。  

### 3.3 长期（>2 周）

9) **卖方偏向深化**：merged 存活因子 3/5 为 sell 后缀，说明 baseline 在 sell-side 有覆盖盲区；后续 FA15 的新增优先围绕 sell-side 行为。  
10) **非线性/表示学习（谨慎推进）**：FA15 的边际信息更可能藏在“条件效应/交互/序列形态”里，建议从“显式交互特征 + Mixture-of-Experts”开始，再上序列模型。

---

## 4. “怎么证明”的标准实验模板（建议直接照抄执行）

### 4.1 单因子层（统计 + 机制）

- IC：h20/h100/h200 分日 Rank IC 均值、t-stat、IC>0%（或与预期方向一致的比例）、前后半段一致性、按月稳定性。  
- 分位收益：Q0~Q4 的单调性与经济意义（不要只看均值，必须看 monotonic）。  
- 条件化：按活动度（bar 数分位）、流动性（spread 分位）、波动（ret/sigma 分位）分组，比较斜率/强度是否显著不同。  

### 4.2 增量层（最关键）

做两条线：  
1) **残差 IC**：`x_resid = x - Proj(x | baseline_features)`，看 resid 是否仍有显著 IC（证明“不是纯替代”）。  
2) **模型消融**：BL-only vs BL+FA15(original) vs BL+FA15(refined)，比较 valid rank IC uplift 与 gain 分配；同时检查 train-valid gap（过拟合风险）。

### 4.3 稳健性层（防过拟合）

- 时间切分：至少做前/后半段；最好按月滚动。  
- 标的切分：高/低活跃度两端都要看。  
- 变换敏感性：winsorize、zscore、rank-normalize、对数变换的稳定性。  

---

## 5. 附：本次评审引用的关键事实（便于追溯）

- “FA15 merged 仅贡献 1.75% gain，存活 5/35”：见 `fa15_quality_review.md` §1/§5。  
- “B/G 组随 horizon 增长显著增强（h100-h200）”：见 `fa15_quality_review.md` §2.2/§9.2。  
- “E 组 buy-side 方向反转且系统性”：见 `fa15_quality_review.md` §3.1。  
- “A 组 4 个因子方向翻转、整体最不稳定”：见 `fa15_quality_review.md` §6.1/§6.4。  
- “11 对 |ρ|>0.85 的冗余结构与精简 35→18 建议”：见 `fa15_quality_review.md` §4.2/§4.5。  
- “分布/近零误判纠正、低活跃度差异”：见 `/data/db/hft/temp/fa15_review_distribution_analysis.md`。  

---

*报告完。*

