# FactorAgent 因子文档验证报告（对照 `conversation_history_0121.md`）

目标：核对当前 5 份任务文档（`FactorAgent1`–`FactorAgent5`）是否 **覆盖聊天记录里的因子簇**、定义/参数是否一致、并确认与 `/home/cken/hft_projects/HftKnowledge/research_docs/` 的工程口径不冲突。

本报告结论按你提出的 3 点逐条给出，并附“覆盖映射表 + 关键口径核对 + 已修订项清单”。

---

## 结论 1：覆盖性（是否包含全部因子？）

### 1.1 v2（最终合并版）章节覆盖（1–15 + 25-A..H）

> 说明：`conversation_history_0121.md` 的 v2 是“把原 25 簇保留内容后更合理归并”的最终版本；因此以 v2 章节作为主核对清单。

| v2 章节 | 聊天记录要点 | 已落到的 FactorAgent 文档 | 关键输出（示例列名，不一定穷举） |
|---|---|---|---|
| §1 参考价格体系 | `mid` / `vwapmid(X)` / `micro_Lk` / `micro_queue_Lk` / `efficient price` / 二阶特征 | `FactorAgent1_price_and_liquidity_geometry.md` | `fa1_vwapmid_mid_diff_bps_X`, `fa1_micro_gap_bps_k`, `fa1_micro_queue_gap_bps_k`, `fa1_eff_gap_bps`, `fa1_micro_cross_flag_k` |
| §2 固定金额流动性几何 | depth-to-X / 成本曲线 slope/convex / bps 半径内可交易量 / 稀疏度 gap / tradability | `FactorAgent1_price_and_liquidity_geometry.md` | `fa1_dask_bps_X`, `fa1_buy_convex`, `fa1_thinness_R`, `fa1_grid_irregular_*`, `fa1_tradability_10bps` |
| §3 队列与激进度 | `T_deplete`（L1 + amount 版）/ passive 排队激进度（ahead_amt/expected time） | `FactorAgent2_queue_lifecycle_and_structure.md` | `fa2_Tdeplete_*`, `fa2_invTdiff`, `fa2_passive_aggr_*` |
| §4 生命周期/撤单风险 | near 定义（Amt/Bps/Lvl）/ age 结构 / cancel hazard | `FactorAgent2_queue_lifecycle_and_structure.md` | `fa2_age_mean_*`, `fa2_cancel_rate_*`, `fa2_survival_ratio_*`（可选） |
| §5 结果层 OFI | Δdepth（按价格对齐）/ near-far / exp 权重 / slope proxy / ofi_norm | `FactorAgent4_ofi_migration_dominance_consistency.md` | `fa4_ofi_near_5bps`, `fa4_ofi_exp_l0p6`, `fa4_ofi_norm_l0p6` |
| §6 距离分桶迁移 + cross-spread | dist bps 桶 / inside/join/away/cross 分类 / cross 深度分层 | `FactorAgent4_ofi_migration_dominance_consistency.md` | `net_liq_imb(bucket)`, `fa4_cross_far_ratio`（示例） |
| §7 成交聚合 + run/metaorder | micro-batch（1ms/5ms A/B）/ run 统计 / run 效率 | `FactorAgent3_trade_aggregation_penetration_toxicity.md` | `fa3_run_len`, `fa3_run_amt`, `fa3_run_efficiency` |
| §8 walk-the-book/penetration | `pen_bps` / `levels_consumed` / `pen_ratio_best` / tail/rollmax | `FactorAgent3_trade_aggregation_penetration_toxicity.md` | `fa3_pen_bps_last`, `fa3_pen_levels_last`, `fa3_pen_tail`, `fa3_pen_bps_rollmax_1s`（可选） |
| §9 吸收/毒性/逆向选择 | absorption（含 signed/burst）/ realized spread 固定延迟 / inventory pressure / impact efficiency | `FactorAgent5_adaptive_timescale_resilience_conditional.md`（absorption）+ `FactorAgent3_trade_aggregation_penetration_toxicity.md`（realized spread/inv/eff_trade）+ `FactorAgent4_ofi_migration_dominance_consistency.md`（eff_ofi/eff_netliq 可选） | `fa5_absorption_trade`, `fa5_absorption_signed_trade`, `fa3_adverse_ema_*`, `fa3_inv_pressure_5s`, `fa3_eff_trade_5s`, `fa4_eff_ofi_5s`（可选） |
| §10 时间尺度自适应 | time-EMA / per-sec/per-event（per-amount 暂不做） | `FactorAgent5_adaptive_timescale_resilience_conditional.md` | `alpha=1-exp(-dt/tau)` 的统一实现规范 |
| §11 韧性/恢复 | 连续 proxy（replenish/withdraw/depth_recovery_proxy）+ 事件型 shock-recovery | `FactorAgent5_adaptive_timescale_resilience_conditional.md` | `fa5_replenish_*`, `fa5_withdraw_*`, `fa5_depth_recovery_proxy_10bps`, `fa5_recovery_time_ema` |
| §12 墙/集中度/闪烁/大小单 | wall + erosion + break / entropy+HHI+Gini / churn+turnover / size layering | `FactorAgent2_queue_lifecycle_and_structure.md` | `fa2_wall_strength`, `fa2_entropy_*`, `fa2_churn_*`, `fa2_add_imb_large` |
| §13 事件主导权/分解 | add/cancel/trade dominance / trade_over_bookchange / aggressiveness event_rate | `FactorAgent4_ofi_migration_dominance_consistency.md` | `fa4_cancel_over_add`, `fa4_trade_over_bookchange`, `fa4_rate_cross_spread_add_5s` |
| §14 条件化动量/回归 | `mom_thin`/`mr_absorb`/`mom_x_resilience`/一致性交互 | `FactorAgent5_adaptive_timescale_resilience_conditional.md` | `fa5_mom_thin`, `fa5_mr_absorb`, `fa5_mom_x_resilience`, `fa5_trend_confirm` |
| §15 聚合/工程建议 | bar-reset/累计量写法 / 输出规范（raw + rate_fast/slow/burst；ratio agent 内算） | `FactorAgent5_adaptive_timescale_resilience_conditional.md`（工程建议）+ 各 agent 的 agg 建议段落 | 输出规范与团队统一口径一致：bar_last + gated；如需 sum/累计量在 Agent 内完成，不再维护 `signal_agg.json` |
| 25-A 一致性/冲突 | flow consistency / conflict_score | `FactorAgent4_ofi_migration_dominance_consistency.md` | `fa4_consistency`, `fa4_conflict_score` |
| 25-B 撤单驱动 vs 新增驱动 | cancel_share + net_given_cancel/add | `FactorAgent4_ofi_migration_dominance_consistency.md` | `fa4_cancel_share`, `fa4_net_given_cancel` |
| 25-C 队列拥挤度结构 | crowding_index / avg_order_size_near | `FactorAgent2_queue_lifecycle_and_structure.md` | `fa2_crowding_*`, `fa2_avg_order_size_*` |
| 25-D 价阶不规则性 | irregular grid / effective tick / large gap ratio | `FactorAgent1_price_and_liquidity_geometry.md` | `fa1_grid_irregular_*`, `fa1_effective_tick_bps_*` |
| 25-E Forward barrier change | forward_release / support_build | `FactorAgent4_ofi_migration_dominance_consistency.md` | `fa4_forward_release_10bps`, `fa4_support_build_10bps` |
| 25-F Impact efficiency | `eff_trade` /（可选）`eff_ofi`/`eff_netliq` | `FactorAgent3_trade_aggregation_penetration_toxicity.md`（trade）+ `FactorAgent4_ofi_migration_dominance_consistency.md`（可选补齐） | `fa3_eff_trade_5s`, `fa4_eff_ofi_5s`, `fa4_eff_netliq_5s` |
| 25-G Jump risk | max_gap × thinness | `FactorAgent1_price_and_liquidity_geometry.md`（可选） | `fa1_jump_asym_20bps`（示例） |
| 25-H Tradability | spread × thinness | `FactorAgent1_price_and_liquidity_geometry.md` | `fa1_tradability_10bps` |

结论：v2 的核心因子簇均已在 5 份文档中落地；此前缺失的 `micro_queue` / `efficient price` / `absorption_signed/burst` / `depth_recovery_proxy` / “bar-reset 暂不做” / “输出 time=local_ts”提醒，已补齐进对应文档（见 §2 的修订清单）。

### 1.2 v1（原 25 簇）覆盖核对（补充确认）

`conversation_history_0121.md` 前半部分的 `# 因子簇 1..25` 与 v2 的对应关系为“内容保留后归并”。当前文档对 v1 的覆盖结论：

- 簇1/2/12/13/14/15 → `FactorAgent2`（生命周期/队列/墙/熵/闪烁/大小单）
- 簇3/5/6/20 + 25-A/B/E → `FactorAgent4`（OFI/迁移/侵略性分类/主导权/一致性）
- 簇4/11/18/21 + 25-D/H/G → `FactorAgent1`（参考价体系 + fixed-amount 流动性几何 + 稀疏度）
- 簇7/8/16/17 + 25-F → `FactorAgent3`（成交聚合/run/穿透/毒性/库存压力/效率）
- 簇9/10/19/22/24/15.2 → `FactorAgent5`（absorption/resilience/time-EMA/条件化交互/输出规范）
- 簇23（bar-reset）→ **按你的明确要求：暂不推进**，已在 `FactorAgent5` 写明（bar-agnostic）

---

## 结论 2：定义一致性（是否和聊天记录完全一致？）

### 2.1 已确认一致/等价的关键定义（高风险项优先）

1) `micro_Lk`（交叉加权的 microprice-like）
- 聊天记录 v2（§1.2 C）：`p_micro_Lk = (ask1*W_bid(k) + bid1*W_ask(k))/(W_bid+W_ask)`，其中 `W_bid/ask` 为多档深度权重和。
- 文档实现（`FactorAgent1`）：用 `imb_k=(vol_bid_k-vol_ask_k)/(vol_bid_k+vol_ask_k+ε)`，`p_micro_Lk = mid + imb_k*spread/2`。
- 等价性：当 `W_bid=vol_bid_k`、`W_ask=vol_ask_k`（即 `w_i=1`）时，两式严格等价（只是不同写法）。

2) `vwapmid(X)`（固定金额 VWAP-mid）
- 聊天记录 v2（§1.2 B）：`p_vwapmid(X)=(vwap_ask(X)+vwap_bid(X))/2`。
- 文档实现（`FactorAgent1`）：按 full_book 从 best 向外累计到 `X` 金额得到 `vwap_ask/vwap_bid`，并输出与 `mid` 的差异项 + coverage。

3) realized spread / adverse selection（固定延迟法）
- 聊天记录 v2（§9.2.2）：`effective/impact/realized/adverse` 的固定延迟更新，并强调“不泄露未来”。
- 文档实现（`FactorAgent3`）：用 `deque` 缓存成交发生时刻的 `{ts0, sign, trade_px, p_ref0}`，在 `now_ts>=ts0+Δt` 时更新 EMA。

4) OFI（结果层 Δdepth）
- 聊天记录强调：必须“按价格对齐”，不能直接对 snapshot 数组下标做差。
- 文档实现（`FactorAgent4`）：维护 prev/curr price->amount map，并对 union(keys) 做 delta 汇总。

### 2.2 本轮核对中发现的“潜在歧义/易写错点”与修订

已修订（避免研究员误写）：

- `FactorAgent2`：`better_amt` 的遍历方式去掉了 `od->price±1` 这种“默认固定 tick”的表达，明确要求用 full_book/map 迭代到 `od->price`（否则在可转债稀疏盘会写错）。
- `FactorAgent3`：修正了 `fa3_pen_bps_last` 文档里重复列名的笔误；并补充了 `rolling_max`（可选）以覆盖聊天记录里“类 bar-max 但 bar-agnostic”的建议。
- `FactorAgent1`：补齐了聊天记录 v2 §1.2.D（`micro_queue_Lk`）与 §1.2（`efficient price` 简化滤波）的可落地定义与推荐参数。
- `FactorAgent5`：补齐了 v2 §9.2.1 的 `absorption_signed`/`absorption_burst`，以及 v2 §11.1 的 `depth_recovery_proxy`；并写明 v2 §15.1 “bar-reset 暂不做”。
- `FactorAgent3/4/5`：补齐了与工程规范一致的提示：输出 `time=event.local_ts`（`exchange_ts` 用于 dt/交易时段判定）。

仍需你们团队共同确认但不影响落地的“口径选择点”（可做小 A/B）：

- `T_deplete` 的 L1 队列金额 `Q_ask1_amt/Q_bid1_amt` 用事件前或事件后盘口：目前文档建议用**事件后**（更同步），但必须在实现里写死并保持一致；建议你们只做 1 套口径，避免 A/B 组合爆炸。
- “效率/吸收”类 ratio 的分子分母是“per-sec”还是“per-event”：文档统一采用 **per-sec + time-EMA**（符合 v2 §10 的主张），且避免依赖 bar-reset。

---

## 结论 3：工程可落地性（与 HftKnowledge 文档是否对得上？是否足够实现？）

总体结论：足够实现；且关键工程口径与 `HftKnowledge/research_docs/` 一致。需要特别注意的对齐点如下：

### 3.1 与 `HftKnowledge/research_docs` 的一致性要点

- 时间轴：`factor_workflow.md` 与 `data.md` 明确推荐输出 `time=event.local_ts`；当前 5 份文档均已明确写出此要求（并提醒 Playground 模板可能默认 `exchange_ts` 需改）。
- 价格单位：`PRICE_SCALE=1000`；`OrderBook::GetMidPrice/GetMicroPrice` 即便返回 `double`，单位仍是缩放价（`data.md` 已强调）。各文档均已提示避免“价格大 1000 倍”的坑。
- `OnMarketEvent` 的 book 状态：为避免事件后状态污染分类，涉及 penetration/inside/join/cross 的部分均要求维护 `prev_bid1/prev_ask1/prev_snap`（`FactorAgent2/3/4` 都强调了这点）。
- 采样/累计口径：不再维护 `signal_agg.json`，也不再使用 Analyzer2 `sum_signals`；如需累计量，必须在 Agent 内按 bar 自行维护并在采样点输出（`factor_workflow.md`）。

### 3.2 HftKnowledge 文档中的一个“容易误导”的例子（已在任务文档中规避）

- `data.md` 中有示例写法：`book->GetVolumeAhead(123)`（传入 order_id）。但实际接口需要 `OrderData&`：应先 `GetPendingOrder(order_id)` 再调用 `GetVolumeAhead(*od)`。
- `FactorAgent2` 文档已明确提醒这一点，避免研究员照抄示例导致编译/逻辑错误。

### 3.3 仍建议研究员实现时统一加上的“工程防呆”

- dt：回放排序通常按 `local_ts`，而 `exchange_ts` 可能出现相等/极少回退；用 `dt_sec=max((exchange_ts-prev_exchange_ts)/1e9, 1e-3)` 防 Inf/NaN。
- session break：午休/隔夜需要清状态（尤其 realized spread deque、time-EMA 状态机），文档已在 `FactorAgent2/3/5` 强调；`FactorAgent4` 建议也照此实现。
- crossed/空簿：所有输出必须给确定值（0 + coverage 标记），严禁 NaN/Inf（`factor_workflow.md` 的 Schema 稳定要求）。

---

## 附：本轮修订文件清单（便于你 review）

- `HFTPool/factor_agent_docs/FactorAgent1_price_and_liquidity_geometry.md`：新增 `micro_queue_Lk`、`efficient price` 定义与参数；补充 TRADE 依赖说明。
- `HFTPool/factor_agent_docs/FactorAgent2_queue_lifecycle_and_structure.md`：澄清 `better_amt` 遍历口径（不假定固定 tick）。
- `HFTPool/factor_agent_docs/FactorAgent3_trade_aggregation_penetration_toxicity.md`：补充 `time=local_ts` 提示；修正文档重复列名；新增可选 `rolling max pen`。
- `HFTPool/factor_agent_docs/FactorAgent4_ofi_migration_dominance_consistency.md`：补充 `time=local_ts` 提示；补齐 v2 §13.2 的 aggressiveness event_rate；可选补齐 25-F 的 `eff_ofi/eff_netliq`。
- `HFTPool/factor_agent_docs/FactorAgent5_adaptive_timescale_resilience_conditional.md`：写明 v2 §15.1 “bar-reset 暂不做”；补齐 `absorption_signed/burst` 与 `depth_recovery_proxy`；补充 `time=local_ts` 提示。
- `HFTPool/factor_agent_docs/factor_tasks_overview_0121_v2.md`：更新分工描述（补齐 `micro_queue/efficient price` 与 bar-reset 说明）。
