# FA15 质量复盘补充量化证据（Codex Addendum）

> 时间：2026-02-21（UTC+8）  
> 目的：为主报告 `fa15_factor_set_quality_postmortem_and_iteration_plan_codex.md` 中关于“哪些因子本来以为会 work 但不 work、为什么、如何证明”的论断补充**更可复现的量化证据**与后续实验清单。  
> 说明：本文件只使用现有 merged cache/统计结果做轻量计算，产物均为小型 csv，落盘于本目录 `_codex_tmp/`，未刷新大规模数据。

---

## 1. 新增产物一览（可复现证据）

都位于：`/home/cken/hft_projects/HFTPool/pool/FA15/report/_codex_tmp/`

- `daily_rank_ic_stats_merged_fa15_h100.csv`：merged（BL150+FA15）下，FA15 相关信号的 **分日 RankIC 统计**（含 t-stat、同号比例、前后半段均值等）。  
- `mean_rank_ic_distribution_merged_h100.csv`：merged 下，BL150 vs FA15 的 **mean_rank_ic 绝对值分布对比**。  
- `liq_bucket_ic_codelevel_merged_h100.csv`：按 `spread_bps` 分桶（Q0 最液 ~ Q4 最不液）的 **按 code 聚合口径** Spearman IC（提示“条件效应/分段”）。  
- `daily_rank_ic_stats_fa15_only_h20.csv`：FA15-only（h20）分日 RankIC 统计（用于对照“短 horizon 弱”）。

---

## 2. 关键补充结论

### 2.1 E 组 buy-side “方向反了但非常稳定”（不是噪声，也不太像实现 bug）

在 merged（label=`ret_lag0_next100`，h100，139 天）下，E 组 buy-side / imb 的 mean RankIC 显著为负且同号比例高（节选自 `daily_rank_ic_stats_merged_fa15_h100.csv`）：

| signal | mean_rank_ic | t_rank_ic | same_sign_ratio |
|---|---:|---:|---:|
| `fa15__fa15_perfect_match_imb` | -0.0201 | -11.83 | 0.863 |
| `fa15__fa15_perfect_match_ratio_buy` | -0.0178 | -9.32 | 0.806 |
| `fa15__fa15_bite_depth_imb` | -0.0174 | -11.24 | 0.856 |
| `fa15__fa15_bite_depth_ratio_buy` | -0.0159 | -9.73 | 0.820 |

**解释口径建议（与主报告一致）**：把 “buy 侧完美匹配/咬合深度” 从“知情买”改述为 **ask 侧薄/流动性状态代理**；其“看起来不 work”主要来自经济解释错位，而不是统计失效。

---

### 2.2 merged 下 FA15 整体强度显著弱于 BL150：边际贡献更容易被吸收/替代

`mean_rank_ic_distribution_merged_h100.csv` 给出了 merged 下两组信号强度的绝对值对比：

| group | n_signals | mean(|mean_rank_ic|) | median(|mean_rank_ic|) |
|---|---:|---:|---:|
| BL150 | 150 | 0.0169 | 0.0115 |
| FA15 | 35 | 0.0078 | 0.0065 |

这与主报告的判断一致：**FA15 的“信息维度”可能是正交的，但“主效应偏弱 + 冗余偏强”**，使其在 merged 模型里容易被更强的 baseline 特征吸收。

---

### 2.3 强烈的“流动性分段/交互”迹象（但当前口径较粗，需要行级验证）

在 `liq_bucket_ic_codelevel_merged_h100.csv`（按 code 均值聚合口径）中，E 组 buy-side 在不同流动性桶出现**符号切换**的迹象（节选）：

| signal | Q0(最液) mean_ic | Q4(最不液) mean_ic |
|---|---:|---:|
| `fa15__fa15_perfect_match_imb` | -0.0461 | +0.0350 |
| `fa15__fa15_bite_depth_imb` | -0.0388 | +0.0382 |
| `fa15__fa15_perfect_match_ratio_buy` | -0.0401 | +0.0184 |
| `fa15__fa15_bite_depth_ratio_buy` | -0.0463 | +0.0259 |

同时，对照 baseline 的 `bl__a1b_trade_flow_imb` 在各桶均稳定为正（约 0.19~0.24），说明不是简单的“桶定义失效”。  

**注意**：这份结果是“按 code 聚合”的粗口径，存在辛普森悖论风险；它更适合作为“强提示”，需要进一步用 Analyzer2 同口径（行级 RankIC）复核。

---

## 3. 建议的 4 个最小可验证实验（不刷新大数据）

1) **行级条件 RankIC（按 `spread_bps` 分桶）**  
目标：验证 2.3 的“分段符号切换”是否在行级 RankIC 仍成立。  
产物建议：`cond_rank_ic_by_spread_bin_merged_h100.csv`（只输出小表）。

2) **残差/正交增量 IC（E 组 vs baseline）**  
做法：对每个交易日截面回归 `E_group_feature ~ spread + trade_flow_imb (+ activity)`，用残差算 RankIC。  
判据：若残差 RankIC 仍显著，说明 E 组不仅是 baseline 代理；若≈0，则说明主要是替代关系。  
产物建议：`residual_rank_ic_e_group_vs_baseline.csv`。

3) **替代效应对照（模型层面）**  
做法：在 merged 训练里分别 “去掉/只保留”强替代 baseline（如 `trade_flow_imb`），观察 FA15(E) gain 是否回升。  
判据：若回升明显，则属于“被覆盖”而非“失效”。

4) **显式交互/门控（简单 MoE）**  
做法：按 `spread_bps`（或活跃度）分段训练/评估，或加入 `E * I(liq_bucket=k)` 的交互项。  
判据：若分段/交互显著提升稳定性与 uplift，则证明“条件效应”是主因。

---

这份 addendum 的定位是“把主报告里的假设做成可以复核的证据链”。如果你希望我把上述 4 个实验进一步写成可直接运行的脚本/命令块（仍只输出小型 csv），我可以继续在 `HFTPool/pool/FA15/report/_codex_tmp/` 下补齐。

