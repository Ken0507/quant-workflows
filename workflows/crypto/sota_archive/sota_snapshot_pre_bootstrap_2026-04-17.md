# Crypto 投研 SOTA Snapshot

> **用途**：记录"截至本日"的 SOTA 状态——当前 LGBM 预测信号最佳组合是哪几个因子集、多少个因子、关键指标如何、对应回测结果如何。作为后续研究的比较基线。
>
> **语义**：本文件只反映 **current**（最新 benchmark refresh 后的真相），不维护历史最佳。历史进程请查 `sota_archive/` 归档 + `research_updates.md` changelog。
>
> **维护方式**：由 `/crypto-meta-review` skill 在用户确认后覆盖。**agent 不得擅自修改**。每次覆盖前先归档旧版到 `sota_archive/sota_snapshot_{old_date}.md`。

---

## Snapshot 元数据

- **本次 snapshot 日期**：_待首次 meta-review 运行后填写_
- **上次 snapshot 日期**：—
- **最后一次 benchmark refresh 日期**：_待填_
- **研究 session 覆盖到**：`crypto_ob_research/{N}-*` 最大编号
- **FA 覆盖到**：`factor_agent_docs/FA{N}_factor_list.md` 最大编号
- **realize pool 覆盖到**：`zebra_pool/fa{N}/` 最大编号

---

## §1 当前 SOTA 组成

### 1.1 因子集构成

> SOTA 使用以下因子集合并后进入 LGBM 训练。总因子数 = 各集合贡献数之和。

| 因子集 | 因子数 | 工程状态 | 来源研究 |
|--------|--------|---------|---------|
| f001 (base30) | _待填_ | ✅ 已落地 | baseline |
| f002 | _待填_ | ✅ 已落地 | baseline |
| fa1 | _待填_ | ✅ 已落地 | _待填_ |
| fa2 | _待填_ | ✅ 已落地 | _待填_ |
| fa3 | _待填_ | _待填_ | _待填_ |
| ... | ... | ... | ... |
| **合计** | **_待填_** | — | — |

### 1.2 LGBM SOTA 指标

- **Analyzer 报告路径**：`/data/db/crypto/analyzer/...`（指向当前 benchmark 对应的 analyzer 输出）
- **Benchmark 目录**：`.../benchmark_{YYYYMMDD}/`（如已做过 benchmark refresh；否则为"合并所有已落地 FA 的最近一次 merged analyzer run"）
- **LGBM 模型路径**：_待填_
- **Horizon**：_待填_（如 next400）
- **信号模式**：_待填_（clip001 / rank / ...）
- **Train/Valid 切分**：时间顺序 80/20（train: ~YYYY-MM-DD~YYYY-MM-DD / valid: ~YYYY-MM-DD~YYYY-MM-DD）

**关键指标**：

| 指标 | Train | Valid |
|------|-------|-------|
| OOS IC | _待填_ | _待填_ |
| ICIR | _待填_ | _待填_ |

> 单因子 Top N 清单不在本文件维护。需要了解哪些因子对预测贡献最大时，直接看 Analyzer 报告路径里的 LGBM feature importance。

### 1.3 SOTA 回测结果

| 指标 | Train | Valid |
|------|-------|-------|
| Sharpe | _待填_ | _待填_ |
| MaxDD | _待填_ | _待填_ |
| Annual Return | _待填_ | _待填_ |
| Calmar | _待填_ | _待填_ |

**回测参数说明**：

- **交易模式**：_待填_（taker / maker）
- **手续费**：_待填_
- **滑点模型**：_待填_
- **持仓周期 / 换手约束**：_待填_
- **信号阈值 / 分位切分**：_待填_
- **其他关键参数**：_待填_
- **完整回测报告**：_待填_（路径）

> 本段记录的是"目前 SOTA 回测所用的配置"。如需对比其它参数组合，去 `crypto-signal-backtest` skill 的产出目录里查。

---

## §2 研究管线累计状态

> 仅反映"累计总数"快照。本期增量 → 查 `research_updates.md` 最新条目。

| 类别 | 累计数 | 备注 |
|------|--------|------|
| research session 总数 | _待填_ | `crypto_ob_research/{N}-*` |
| 完成 session（有 factor_definition.md） | _待填_ | |
| In-flight session（有 log 无 definition） | _待填_ | |
| Failed / Interrupted session | _待填_ | |
| factor list (FA) 总数 | _待填_ | `factor_agent_docs/FA*_factor_list.md` |
| realized pool 总数 | _待填_ | `zebra_pool/fa*/` |
| benchmark refresh 次数 | _待填_ | 含当前 SOTA 对应的那一次 |
| 待编译 session 数（完成但未进入 FA） | _待填_ | meta-review 建议下一次 compile 的输入 |

---

## §3 开放研究方向 / 待关注模式

> 由 meta-review skill 从最近 N 期 `research_updates.md` §6（本期观察到的模式 / 待关注方向）聚合、去重得到。用于下一期 meta-review 做定向深度分析时的议题候选。

- _待填_

---

## §4 本版 snapshot 生成说明

- **生成来源**：由 `/crypto-meta-review` skill 扫描以下路径重建后经用户确认
  - `crypto_ob_research/{N}-*/` — 所有研究目录
  - `factor_agent_docs/FA*_factor_list.md` — 所有编译后因子集
  - `zebra_pool/fa*/report/` — 所有 realize 工作区报告
  - `/data/db/crypto/analyzer/fa*/` + benchmark 目录 — 最新 benchmark refresh 对应的 analyzer 输出
  - 最新 `crypto-signal-backtest` 报告（如存在且被用户确认为"当前 SOTA 回测"）
- **归档**：每次覆盖前由 skill 将旧版本复制到 `sota_archive/sota_snapshot_{old_date}.md`
- **首次运行（bootstrap 规则）**：本文件初始为模板。首次 `/crypto-meta-review` 运行时：
  - 把"最近一次包含全部已落地 FA + baseline 的 merged analyzer run" 视为 **benchmark refresh #0**
  - 元数据中 "最后一次 benchmark refresh 日期" 填 meta-review 运行当天
  - §1.1-1.2 按正常方式填充（不做 "pre-benchmark" 特殊标注）
  - §2 中 "benchmark refresh 次数" 从 1 开始计数
  - 后续用户手工触发真正的 Stage 5 benchmark refresh（按 feature importance 选 Top N）时，计数继续递增
