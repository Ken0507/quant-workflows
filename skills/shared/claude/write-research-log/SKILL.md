---
name: write-research-log
description: "在研究任务中持续记录工作日志。每次尝试新方法、获得结果、与codex讨论或开启subagent时，都需在工作目录的 research_log.md 中追加带时间戳的日志条目。用于追踪研究过程、记录思路和决策。"
---

# Research Log Writer

## 用途

在长期研究任务中，系统化地记录每个重要步骤、尝试、结果和讨论。确保研究过程可追溯、可复现。

## 触发时机（必须记录日志的场景）

你**必须**在以下任何场景发生时立即更新 research log：

1. **开始新的尝试/实验**
   - 开始测试新的假设
   - 尝试新的参数配置
   - 运行新的分析或计算

2. **获得重要结果**
   - 命令执行完成并有输出
   - 发现异常或错误
   - 得出中间结论

3. **与 Codex 交互**
   - 向 codex 提问或请求建议前
   - 收到 codex 回复后，记录关键观点
   - 对 codex 建议提出质疑或反驳时

4. **启动 Subagent**
   - 启动 subagent 处理子任务前
   - Subagent 完成任务后，总结其输出

5. **做出关键决策**
   - 选择特定技术方案
   - 改变研究方向
   - 发现需要进一步调查的问题

6. **遇到问题或阻塞**
   - 遇到错误或异常
   - 发现数据质量问题
   - 需要用户介入的情况

## 日志格式规范

### 文件位置

- 日志文件名：`research_log.md`
- 位置：当前工作目录（通常是你的研究子目录，如 `hft_researches/your_topic_YYYYMMDD/`）
- 如果不存在，首次写入时创建

### 日志条目格式

每条日志必须包含：
1. **时间戳**（UTC+8，格式：`YYYY-MM-DD HH:MM:SS`）
2. **类型标签**（方括号包裹）
3. **内容描述**（简明扼要，必要时分点列出）

```markdown
## YYYY-MM-DD HH:MM:SS - [标签]

内容描述（1-3句话总结，或分点列出关键信息）

---
```

### 标签类型

| 标签 | 使用场景 |
|------|---------|
| `[START]` | 开始研究任务或新阶段 |
| `[TRY]` | 开始新的尝试/实验 |
| `[RESULT]` | 获得执行结果 |
| `[CODEX-ASK]` | 向 codex 提问 |
| `[CODEX-REPLY]` | 记录 codex 的回复要点 |
| `[CODEX-DEBATE]` | 对 codex 观点提出质疑或反驳 |
| `[SUBAGENT]` | 启动或完成 subagent 任务 |
| `[DECISION]` | 做出关键决策 |
| `[ISSUE]` | 发现问题或遇到阻塞 |
| `[MILESTONE]` | 完成重要里程碑 |
| `[END]` | 研究任务结束 |

## 实现方式

### 获取时间戳

使用 Bash 命令获取格式化的 UTC+8 时间：

```bash
TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S'
```

### 追加日志

使用 Bash heredoc 追加到 research_log.md：

```bash
cat >> research_log.md << 'EOF'

## $(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S') - [标签]

内容描述

---
EOF
```

### 推荐工作流

1. **初始化日志**：任务开始时创建日志文件并写入 `[START]` 条目
2. **即时记录**：每次满足触发条件时立即追加日志（不要积攒）
3. **简明扼要**：每条日志 1-3 句话，聚焦关键信息
4. **保持连贯**：日志应能串联起整个研究过程

## 示例日志

```markdown
# Research Log: 因子对齐问题排查

## 2026-01-31 14:23:15 - [START]

开始排查因子输出与 basic_table 的轴对齐问题。目标：找出 overlap ratio < 99.9% 的根因。

---

## 2026-01-31 14:25:42 - [CODEX-ASK]

向 codex 询问：如何高效检查大规模 parquet 文件的 key 唯一性？

---

## 2026-01-31 14:27:18 - [CODEX-REPLY]

Codex 建议：
- 使用 polars 的 `is_duplicated()` 方法
- 分批处理避免内存溢出
- 重点检查 md_id != -1 的子集

---

## 2026-01-31 14:28:05 - [CODEX-DEBATE]

质疑 codex 的方案：polars 在极大文件上仍可能 OOM。
建议改用 duckdb 的 SQL GROUP BY + HAVING COUNT(*) > 1，可以利用磁盘溢出。

---

## 2026-01-31 14:35:20 - [TRY]

尝试方案：使用 duckdb 查询重复 key
```sql
SELECT code, time, md_id, COUNT(*)
FROM read_parquet('factor_output/*.parquet')
WHERE md_id != -1
GROUP BY code, time, md_id
HAVING COUNT(*) > 1;
```

---

## 2026-01-31 14:37:52 - [RESULT]

发现 127 组重复 key，主要集中在 20260115 一天。初步怀疑该日数据源有问题。

---

## 2026-01-31 14:40:13 - [SUBAGENT]

启动 subagent 分析 20260115 原始数据质量（检查 md_id 分布和时间戳连续性）。

---

## 2026-01-31 14:55:30 - [SUBAGENT]

Subagent 返回：20260115 原始数据中确实存在同一 md_id 在同一 local_ts 重复出现的情况（疑似数据源推送重复）。

---

## 2026-01-31 15:02:47 - [DECISION]

决定：对 20260115 去重后重新生成因子输出。去重策略：按 (code, time, md_id) 取 exchange_ts 最新的记录。

---

## 2026-01-31 15:25:10 - [RESULT]

重新生成完成，轴对齐检查通过：overlap ratio = 99.97%。

---

## 2026-01-31 15:26:33 - [MILESTONE]

问题解决。根因：数据源在 20260115 推送了重复的 tick 数据。已修复并验证通过。

---

## 2026-01-31 15:27:00 - [END]

研究任务完成。建议：在因子生产流程中加入 key 唯一性检查。

---
```

## 执行清单

在使用本 skill 时，请遵循以下检查清单：

- [ ] 确认当前工作目录（通常是 `hft_researches/your_topic_YYYYMMDD/`）
- [ ] 任务开始时创建或打开 `research_log.md`，写入 `[START]` 条目
- [ ] 每次满足触发条件时，立即使用 Bash 追加带时间戳的日志
- [ ] 日志内容简明扼要，聚焦关键信息
- [ ] 与 codex 交互时，分别记录 `[CODEX-ASK]`、`[CODEX-REPLY]`、`[CODEX-DEBATE]`
- [ ] 启动 subagent 前后都要记录
- [ ] 任务结束时写入 `[END]` 条目
- [ ] 如果研究超过 30 分钟，确保日志能完整串联研究过程

## 注意事项

1. **即时性**：不要等到"一个阶段结束"再统一写日志，而是每次满足条件立即追加
2. **客观性**：记录事实和观点，不要夸大或美化
3. **简洁性**：每条日志 1-3 句话，避免冗长叙述
4. **连贯性**：后续日志应能与前面的日志逻辑关联
5. **时区一致**：始终使用 UTC+8（Asia/Shanghai）
6. **编码安全**：使用 `cat >> file << 'EOF'` 而非 `echo`，避免特殊字符问题
