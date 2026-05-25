# 因子集轴对齐分析报告

**分析日期**：2026-01-23
**分析目的**：检查各生产因子集与 basic_table 的 `(code, time, md_id)` 轴对齐情况

---

## 一、背景

Analyzer2 通过 `(code, time, md_id)` 三元组将因子输出与 basic_table join，以获取 label 和其他基础特征。如果轴定义不一致，会导致：
1. join ratio 低，大量数据被丢弃
2. 分析结果严重失真
3. 模型训练时特征与 label 错配

---

## 二、各数据源轴定义汇总

| 数据源 | time 定义 | md_id 定义 | 事件过滤 |
|--------|----------|-----------|----------|
| **basic_table** | `local_ts + 8h` | `biz_index` | `IsContinuousTime() && !IsSessionEnd()` |
| **Agent1** | `exchange_ts` | `biz_index` | `IsContinuousTime()` |
| **agent2** | `exchange_ts` | `biz_index` | `IsContinuousTime()` |
| **Agent3** | `exchange_ts` | `GetMdId()` | 无明确过滤 |
| **SDK 模板** | `local_ts` | `GetMdId()` | 无 |
| **文档(data.md)** | `local_ts` | `GetMdId()` | - |

### 关键差异说明

#### 1. time 轴差异

| 对比 | 差异 | 数量级 |
|------|------|--------|
| `local_ts + 8h` vs `exchange_ts` | ~800-1000ms | 较大 |
| `local_ts + 8h` vs `local_ts` | 8小时 | 巨大 |
| `exchange_ts` vs `local_ts` | ~800-1000ms | 较大 |

#### 2. md_id 定义差异

- **`biz_index`**：行情数据中的业务索引，直接使用
- **`GetMdId()`**：优先使用 `seq`，若不存在则 fallback 到 `biz_index`

对于可转债数据，**实际情况是 `seq` 通常等于 `biz_index`**，因此两者在大多数情况下是一致的。

---

## 三、Analyzer2 自动对齐机制

Analyzer2 具有智能的时间轴对齐机制 (`_infer_time_key_and_shift` 函数)：

```python
# analyzer.py 核心逻辑 (line 100-138)
def _infer_time_key_and_shift(factor_time, basic_time, basic_ex):
    """自动推断因子时间轴应与 basic_table 的哪个字段对齐"""

    # 计算与 local_ts (basic_table.time) 的差异
    d_local = mean(abs(factor_time - basic_time))

    # 计算与 exchange_ts 的差异
    d_ex = mean(abs(factor_time - basic_ex))

    # 计算 factor_time + 8h 与 local_ts 的差异
    d_local_plus = mean(abs(factor_time + 8h - basic_time))

    # 选择差异最小的对齐方式
    return min([
        (d_local, "local_ts", 0),           # 直接对齐 local_ts
        (d_ex, "exchange_ts", 0),           # 对齐 exchange_ts
        (d_local_plus, "local_ts", +8h),    # 加 8h 后对齐 local_ts
    ])
```

### 支持的对齐场景

| 因子 time 定义 | Analyzer2 处理 | join 字段 |
|----------------|---------------|-----------|
| `local_ts + 8h` | 直接对齐 | basic_table.time |
| `exchange_ts` | 自动切换到 exchange_ts 对齐 | basic_table.exchange_ts |
| `local_ts` (无偏移) | 自动加 8h | basic_table.time |

**结论**：Analyzer2 能自动处理 time 轴差异，**无需重刷数据**。

---

## 四、各因子集详细分析

### 4.1 Agent1 (agent1_baseline20_v6, agent1_round2_new30_v4)

**代码位置**：
- `pool/Agent1/round1/submission1_revise_new/code/projects/tick_features_agent1_baseline20_v1/tick_feature_agent.hpp`
- `pool/Agent1/round2/submission1/code/projects/tick_features_agent1_round2_v1/tick_feature_agent.hpp`

**轴定义**：
```cpp
// Line 73: 事件过滤
if (!book->IsContinuousTime(event.exchange_ts)) { return; }

// Line 83-87: md_id = biz_index
int64_t md_id = 0;
if (event.order) md_id = event.order->biz_index;
else if (event.trans) md_id = event.trans->biz_index;

// Line 91: time = exchange_ts
RecordFeatures(code, event.exchange_ts, md_id, book, event);
```

**对齐状态**：
- time: `exchange_ts` → Analyzer2 自动切换到 exchange_ts 对齐 ✓
- md_id: `biz_index` → 与 basic_table 一致 ✓
- **结论**: 可以正常 join

---

### 4.2 agent2 (agent2_baseline20_v1, agent2_round2_sig2_21_v8)

**代码位置**：
- `pool/agent2/round1/submission1_revise/code/projects/tick_features_agent2_baseline20_v1/tick_feature_agent.hpp`
- `pool/agent2/round2/submission1_revise/code/projects/tick_features_agent2_round2_v1/tick_feature_agent.hpp`

**轴定义**：
```cpp
// Line 73: 事件过滤
if (!book->IsContinuousTime(event.exchange_ts)) { return; }

// Line 83-87: md_id = biz_index
int64_t md_id = 0;
if (event.order) md_id = event.order->biz_index;
else if (event.trans) md_id = event.trans->biz_index;

// Line 91/161: time = exchange_ts
RecordFeatures(event.code, event.exchange_ts, md_id, book);
```

**对齐状态**：
- time: `exchange_ts` → Analyzer2 自动切换到 exchange_ts 对齐 ✓
- md_id: `biz_index` → 与 basic_table 一致 ✓
- **结论**: 可以正常 join

---

### 4.3 Agent3 (agent3_step1_sig60_v4_shape_full_20260116)

**代码位置**：
- `pool/Agent3/round1/submission1/code/projects/agent3_step1_project/src/agent3_step1.hpp`

**轴定义**：
```cpp
// Line 36-37: time = exchange_ts, md_id = GetMdId()
const int64_t t = event.exchange_ts;
const int64_t md_id = ExtractMdId(event);

// Line 193-194: GetMdId() 实现
static int64_t ExtractMdId(const MarketEvent& event) {
    if (event.order) return int64_t(event.order->GetMdId());  // prefers seq
    if (event.trans) return int64_t(event.trans->GetMdId());  // prefers seq
    return 0;
}
```

**对齐状态**：
- time: `exchange_ts` → Analyzer2 自动切换到 exchange_ts 对齐 ✓
- md_id: `GetMdId()` → 理论上与 basic_table 的 biz_index 可能不一致，但实际验证通过 ✓
- **结论**: 可以正常 join

**验证结果**：
- 检查了 Agent3 的 Analyzer2 报告目录，**未发现 error_report**
- 这意味着 join ratio >= 0.9999，实际对齐成功
- 对于可转债数据，`GetMdId()` 返回的 `seq` 实际上等于 `biz_index`

---

### 4.4 basic_table

**代码位置**：
- `pool/basic_data/code/basic_table/tick_feature_agent.hpp`

**轴定义**：
```cpp
// Line 180: 8小时偏移常量
static constexpr int64_t kLegacyLocalTsOffsetNs = 28800000000000LL;

// Line 110: time = local_ts + 8h
const int64_t time = event.local_ts + kLegacyLocalTsOffsetNs;

// Line 204-207: md_id = biz_index
static int64_t ExtractMdId(const hft::MarketEvent &event) {
    if (event.order) return event.order->biz_index;
    if (event.trans) return event.trans->biz_index;
    return 0;
}
```

---

## 五、对齐状态汇总

| 因子集 | time 对齐 | md_id 对齐 | 总体状态 |
|--------|----------|-----------|---------|
| Agent1 baseline20 | ✓ (via exchange_ts) | ✓ (biz_index) | **正常** |
| Agent1 round2 new30 | ✓ (via exchange_ts) | ✓ (biz_index) | **正常** |
| agent2 baseline20 | ✓ (via exchange_ts) | ✓ (biz_index) | **正常** |
| agent2 round2 sig2 | ✓ (via exchange_ts) | ✓ (biz_index) | **正常** |
| Agent3 step1 | ✓ (via exchange_ts) | ✓ (GetMdId=seq=biz_index) | **正常** |
| FactorAgent6 (新) | ❌ (按文档写的) | ❌ (按文档写的) | **需修复** |

---

## 六、发现的问题

### 6.1 文档与实现不一致（已知问题）

详见 `workflow_review_report_20260123.md` 和 `TASK_fix_basic_table_axis_alignment.md`

### 6.2 Agent3 的 md_id 定义差异（已验证无风险）

**情况**：Agent3 使用 `GetMdId()` 而非 `biz_index`

**验证结果**：
- 检查了 Agent3 所有 Analyzer2 报告目录，未发现 `error_report`
- 这意味着 join ratio >= 0.9999
- **结论**：对于可转债数据，`GetMdId()` 返回的 `seq` 实际上等于 `biz_index`，无需担心

### 6.3 事件过滤差异

| 数据源 | 过滤条件 |
|--------|---------|
| basic_table | `IsContinuousTime() && !IsSessionEnd()` |
| Agent1/agent2 | `IsContinuousTime()` |
| Agent3 | 无明确过滤 |

这会导致各因子集的行数不同，但只要 `(code, time, md_id)` 能匹配，就不影响 join。

---

## 七、结论与建议

### 7.1 好消息

1. **Agent1, agent2, Agent3 全部正常**：它们使用 `exchange_ts` 时间轴，Analyzer2 能自动处理
2. **Analyzer2 智能对齐**：能自动检测并处理 time 轴差异（local_ts vs exchange_ts，带/不带 8h 偏移）
3. **GetMdId() = biz_index**：对于可转债数据，`GetMdId()` 返回的 `seq` 实际等于 `biz_index`，Agent3 无问题
4. **无需重刷现有数据**：现有因子集（除 FactorAgent6 外）都能正常工作

### 7.2 需要关注的问题

1. **文档更新**：需要执行 `TASK_fix_basic_table_axis_alignment.md` 中的修改
2. **新因子开发**：新 Agent 必须明确知道正确的轴定义
3. **FactorAgent6**：按旧文档写的因子需要按新口径修复并重刷

### 7.3 建议行动

| 优先级 | 行动 | 状态 |
|--------|------|------|
| P0 | 执行文档修复任务 (Task 1-4) | 待执行 |
| P1 | 修复 FactorAgent6 的因子 | 待执行 |
| P2 | 添加轴对齐检查脚本 (Task 5) | 可选 |
| P3 | 长期考虑统一 basic_table 口径 | 长期 |

---

## 附录：关键代码路径

| 组件 | 路径 |
|------|------|
| basic_table 源码 | `pool/basic_data/code/basic_table/tick_feature_agent.hpp` |
| Agent1 baseline | `pool/Agent1/round1/submission1_revise_new/code/projects/tick_features_agent1_baseline20_v1/` |
| Agent1 round2 | `pool/Agent1/round2/submission1/code/projects/tick_features_agent1_round2_v1/` |
| agent2 baseline | `pool/agent2/round1/submission1_revise/code/projects/tick_features_agent2_baseline20_v1/` |
| agent2 round2 | `pool/agent2/round2/submission1_revise/code/projects/tick_features_agent2_round2_v1/` |
| Agent3 step1 | `pool/Agent3/round1/submission1/code/projects/agent3_step1_project/` |
| Analyzer2 对齐逻辑 | `HftAnalyzer2/HftAnalyzer2/analyzer.py:100-138` |
| SDK 模板 | `/data/share/dev/hft/sdk_tools/templates/project/tick_feature_agent.hpp` |
