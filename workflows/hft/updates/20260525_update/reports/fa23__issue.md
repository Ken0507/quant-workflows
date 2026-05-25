# FA23 Issue Log

## Issue 1: ref26_consensus_score 值域
- **描述**：§8 定义值域为 {-1, -1/3, 0, +1/3, +1}（5值），但公式 (sign(x)+sign(y)+sign(z))/3 可产生 ±2/3（当 2 个非零+1 个零时）
- **结论**：实现严格遵循公式，±2/3 是数学上正确的结果。§8 值域定义有遗漏。
- **影响**：无需修改代码

## Issue 2: Group 1 (ref26) FA7 依赖
- **描述**：Group 1 因子依赖 FA7 的 eff_gap_bps, micro_gap_bps_3, vwapmid_mid_diff_bps_50k/1m
- **处理**：在 FA23 agent 内部重新实现 FA7 的计算逻辑（eff_price EMA, micro_gap_3, DepthToXMulti）
- **风险**：与 FA7 独立运行的数值可能有微小差异（由于事件处理顺序、浮点精度），但计算逻辑完全一致
- **来源代码**：FA7 实现在 workspace/FactorAgent7/projects/fa7_factor_project/src/

## Issue 3: R-class 因子定义不完整
- **tr32_run_depth_ratio**：pre_run_near_depth_L5 定义补充为"run 方向同侧前 5 档 Σ(px×vol)"
- **tr32_run_vol_accel**：batch 简化为"每笔 FILL 的 volume"，EMA α=0.02
