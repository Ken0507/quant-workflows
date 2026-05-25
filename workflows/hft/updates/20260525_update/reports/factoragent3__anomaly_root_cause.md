# FactorAgent3｜Analyzer2 报告异常根因分析与修复说明（run_intensity 极端值）

> 时间：2026-01-22（UTC+8）  
> 结论先行：本次“Analyzer2 报告数值明显异常”的主因是 **`fa3_run_intensity*` 在 run 刚启动时 `duration≈0` 被 `ε=1e-9` 放大，产生 `1e18` 量级极端值**，进入 Analyzer2 cache（bar 聚合）后显著污染特征分布与 LGBM 训练/评估，导致报告呈现不合理。

---

## 1) 背景与异常现象

用户反馈的异常主要体现在：
- Analyzer2 标准报告中的数值/图像表现“明显不合理”（分布/收益曲线/训练稳定性异常）。
- 因子文件体量与对齐问题曾被怀疑，但后续用户复核认为“数据量看上去没太大问题”，仍需解释“报告为何异常”。

本次排查聚焦于：**因子值本身是否存在明显的数值病态**（极端值、常数化、单位/分母错误等）。

---

## 2) 定位过程（关键证据链）

### 2.1 直接从 Analyzer2 cache 侧验证（bar 口径输入）

读取 Analyzer2 生成的日 cache（示例：`20250506.parquet`），观察到：
- `fa3_run_intensity` 的量级达到 `1e18`（max），且跨多个日期普遍存在。

该量级远超“milli-yuan/sec”在可解释范围内（即便考虑 `dt_floor=1e-3`，合理上界也应在 `1e12~1e13` 量级附近），因此可以判定为**实现 bug**而非“因子效果差/参数不佳”。

### 2.2 根因回溯到代码实现

在 `FactorAgent3` 的 run 指标计算中：
- `fa3_run_duration_sec` 在 run 启动的同一个 tick 上可能为 0；
- `fa3_run_intensity = run_amt / (run_duration + ε)` 中使用了过小的 `ε=1e-9`；
- 因为 `run_amt_milli` 在 run 启动 tick 已经累加了首笔成交金额，所以 `run_amt / 1e-9` 会被放大到 `1e17~1e18`。

这类极端值在 bar 聚合（`state=last_valid`）后会频繁被采到，从而污染分位数切分与 LGBM 的训练过程，使报告呈现异常。

---

## 3) 修复方案（已落地）

修复目标：避免 `duration≈0` 时被“除以极小 epsilon”放大，同时保持原定义（run_amt/run_duration）的经济含义。

### 3.1 修复策略

- 对 run duration 使用明确的 **`dt_floor`**（与项目其他 rate 类实现保持一致），即：
  - `dur_sec = DtSec(now_ns, run_start_ts, kDtFloor)`（`kDtFloor=1e-3`）
  - `run_intensity = run_amt / dur_sec`
- 同步修复 `run_intensity_fast/slow` 的更新口径，避免 EMA 输入仍含极端值。

### 3.2 修复验证（smoke 证据）

单日单标的 smoke 复核（`20250102, 127102`）中：
- `fa3_run_intensity` 的 max 降至 `~4e11`，不再出现 `1e18` 量级；
- schema/NaN/Inf 正常。

---

## 4) 为什么 Step2“强验证”没查出来？（复盘）

之前的 Step2 强验证主要包含：
- NaN/Inf、均值方差、分位数等统计
- 点对点复算（p2p compare）

但该问题属于：
- **“公式实现本身的分母处理不当”**（0-duration 用 ε 规避但 ε 过小）；
- p2p 复算与主实现使用同一口径时，依然会逐点一致，因此 **p2p 无法发现**；
- 统计表虽能反映极端 max，但若报告撰写/关注点偏向“NaN/Inf=0、p2p=pass”，就可能漏掉“max 量级异常”这一显性信号。

---

## 5) 改进措施（已做 & 计划做）

### 5.1 已落地：验证脚本加入“极端值闸门”

在 `validate_1m.py` 中新增质量闸门：
- 若 `fa3_run_intensity*` 出现 `abs_max > 1e14`，直接 FAIL 并输出定位表，避免“统计正常但分布病态”漏检。

### 5.2 计划补强：把“数值合理性”写成硬验收项

后续强验证将把下列内容明确为硬门槛（写入验证报告）：
- 关键 rate 类信号（run_intensity/inv_pressure/eff_trade 等）的数量级上界检查；
- 对“duration=0”场景给出明确处理（dt_floor/输出置 0/延迟更新等），并用单测覆盖。

---

## 6) 下一步

在本修复基础上，将按原任务流程重新：
- 刷 1 个月全 code 数据并完成强验证；
- 刷全历史并重跑两份 Analyzer2 标准报告；
- 重跑 LGBM uplift vs baseline；
并以“最新版报告/目录”为准完成最终交付。

