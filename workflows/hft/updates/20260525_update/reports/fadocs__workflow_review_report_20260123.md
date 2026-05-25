# HFTPool 工作流审阅报告

**审阅日期**：2026-01-23
**审阅范围**：FactorAgent6 工作记录、research_docs 文档、Skills、basic_table 源码

---

## 一、核心问题总结

### 1.1 basic_table join轴问题（最严重）

**问题**：文档说 `time=event.local_ts`，但 basic_table 实际实现是 `time=event.local_ts+8h`；文档示例用 `GetMdId()`，basic_table 用 `biz_index`。

**影响**：每个按文档写因子的 agent 都会遇到 join 失败，需要返工。

**根因位置**：
- `/home/cken/hft_projects/HFTPool/pool/basic_data/code/basic_table/tick_feature_agent.hpp:110,180,204-207`

**代码证据**：
```cpp
// 第180行
static constexpr int64_t kLegacyLocalTsOffsetNs = 28800000000000LL;  // 8小时偏移

// 第110行
const int64_t time = event.local_ts + kLegacyLocalTsOffsetNs;  // 加了偏移

// 第204-207行
static int64_t ExtractMdId(const hft::MarketEvent &event) {
    if (event.order) return event.order->biz_index;  // 直接用biz_index
    if (event.trans) return event.trans->biz_index;
    return 0;
}
```

**修复方案**：详见 `TASK_fix_basic_table_axis_alignment.md`

### 1.2 其他问题（来自 FactorAgent6 反馈）

| 问题 | 原因 | 建议改进 |
|------|------|---------|
| parquet footer 损坏 | IO/落盘不完整 | 在 batch-run skill 中增加 metadata 可读性检查 |
| 合并报告内存超限 | workers 设置过高 | 在 analyzer_user_manual.md 添加内存估算公式 |
| baseline top80 合并规则分散 | 隐式知识 | 提供标准化配置文件 |

---

## 二、文档改进建议

### 2.1 data.md

1. **新增第8章**：与 basic_table 的 Join 轴对齐（关键）
2. **修改时间轴说明**：明确需要加8小时偏移
3. **修改 md_id 示例**：改用 `biz_index`

### 2.2 factor_workflow.md

1. **在 3.1 节添加警告**：强调与 basic_table 对齐的必要性
2. **添加轴对齐检查步骤**：作为 Step1 smoke test 后的必做 gate

### 2.3 analyzer_user_manual.md

1. **添加内存估算指导**：
   - 单数据集：workers × 8-12GB
   - 多数据集合并：workers × 20-25GB
2. **添加推荐并发数**：单数据集 10-15，多数据集 6-8

### 2.4 Skills 文档

| Skill | 修改内容 |
|-------|---------|
| hft-playground-factor-write | 修改 time/md_id 的说明 |
| hft-playground-factor-batch-run | 添加 parquet 可读性检查 |
| hft-analyzer2-standard-report | 添加内存估算建议 |

---

## 三、建议新增的 Skills

1. **axis-alignment-smoke**（高优先级）
   - 功能：轴对齐检查
   - 触发：Step1 smoke test 后

2. **factor-run-integrity-check-and-repair**（高优先级）
   - 功能：全历史可用性验收 + 自动修复坏日/缺日

3. **analyzer2-merge-baseline-plus-new**（中优先级）
   - 功能：一键产出 baseline+新因子集 合并报告
   - 内置内存 guard

4. **lgbm-uplift-report**（中优先级）
   - 功能：自动生成 uplift markdown

---

## 四、Prompt 模板改进建议

### 当前问题

FA6_prompt.md 的"硬性规范"虽然说了 `time=event.local_ts`，但这与 basic_table 不一致。

### 建议修改

在 Prompt 的硬性规范中添加：

```markdown
- **轴对齐（与 basic_table）**：
  - `time = event.local_ts + 28800000000000(ns)`（必须加8小时偏移）
  - `md_id = event.order/trans.biz_index`（不是 GetMdId()）
  - Step1 smoke test 后必须做轴对齐检查（overlap ratio >= 0.999），否则不得进入 Step2
```

---

## 五、问题解答

### Q1: 是不是 basic_table 的代码写的不对？

**是的**，basic_table 的实现与文档不一致：

| 方面 | basic_table 实现 | 文档说明 | 结论 |
|------|-----------------|---------|------|
| time | `local_ts + 8h` | `local_ts` | 不一致 |
| md_id | `biz_index` | `GetMdId()` | 不一致 |

但这是"历史遗留口径"（代码中变量名 `kLegacyLocalTsOffsetNs` 暗示了这一点）。

### Q2: 我们如何改进文档以不让这样的问题再次发生？

1. 在 data.md 新增第8章明确说明 basic_table 的实际口径
2. 在 Skills 中强调轴对齐要求
3. 在 Prompt 模板中添加轴对齐硬规则
4. 添加轴对齐检查脚本作为 gate

### Q3: 我需要重写代码、重刷数据、更改 Analyzer2 吗？

**短期方案（推荐）**：
- **不需要**重写 basic_table 代码
- **不需要**重刷 basic_table 数据
- **不需要**更改 Analyzer2 代码
- **只需要**修改文档和 Skills，让后续 agent 知道正确的口径

**长期方案（可选）**：
- 如果要消除历史包袱，需要修改 basic_table 代码并重刷全历史
- 详见任务文档的"方案B"部分

---

## 六、执行状态

**更新时间**：2026-01-23

| 任务 | 状态 |
|------|------|
| Task 1-4（方案A文档修改） | ✅ 已完成 |
| Task 5（轴对齐检查 Skill） | ✅ 已完成 |
| 内存估算公式添加 | ✅ 已完成 |
| 方案B（统一修正 basic_table） | ⏸️ 延后（用户另行安排） |

### 已完成的修改

1. **data.md**：新增第 8 章「与 basic_table 的 Join 轴对齐」
2. **factor_workflow.md**：添加轴对齐说明和 md_id 使用指南
3. **analyzer_user_manual.md**：添加第 11.1 节 workers 与内存估算指导
4. **hft-playground-factor-write SKILL.md**：更新轴对齐检查要求
5. **hft-analyzer2-standard-report SKILL.md**：添加内存估算快速参考
6. **FA7/FA8/FA_prompt_v3**：添加 md_id 和轴对齐检查硬规则
7. **hft-axis-alignment-check SKILL.md**：新增独立的轴对齐检查 Skill

---

## 附录：关键文件路径

| 文件 | 用途 |
|------|------|
| `/home/cken/hft_projects/HftKnowledge/research_docs/data.md` | 数据接口文档 |
| `/home/cken/hft_projects/HftKnowledge/research_docs/factor_workflow.md` | 因子工作流文档 |
| `/home/cken/hft_projects/HftKnowledge/research_docs/analyzer_user_manual.md` | Analyzer2 手册 |
| `/home/cken/hft_projects/HFTPool/pool/basic_data/code/basic_table/tick_feature_agent.hpp` | basic_table 源码 |
| `/data/share/dev/hft/sdk_tools/templates/project/tick_feature_agent.hpp` | SDK 模板 |
