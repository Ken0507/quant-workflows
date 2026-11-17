# Work Order `<WO-ID>`

状态：`PLANNED`

## 目标与影响

- 目标：
- 触发与业务影响：
- 前因与已证实事实（标注 `verified/reported/agreed/proposed/deferred`）：
- 已定决策及理由：

## 来源与责任

- 原始需求/issue/文档路径及用途：
- 控制台负责人：
- 执行者：
- 独立验收者：
- 依赖工单：

## 范围与权限

- 本轮允许修改：
- 禁止操作（包括 push/merge/deploy/restart/外部消息/真实数据，如不适用写 N/A）：
- 工作目录：
- 临时目录（必须在 `/data/db/hft/temp/`）：
- 单一 writer 目标：

## 执行设置

- provider route：`codex-pool` / `lgj`（或用户明确覆盖）
- model：`gpt-6-astra`
- reasoning effort：`xhigh`
- service tier：`default`
- 用户覆盖及作用范围：
- session/thread ID（启动后回填）：

## 交付与验收

- 交付物及绝对路径：
- 回报路径：
- 可观察完成标准：
- 验收命令/证据：
- 未决问题与 owner：

## 状态约定

- `execution_state`：`PLANNED → DISPATCHED → RUNNING → WAITING/EXECUTION_REPORTED/BLOCKED`
- `acceptance_state`：`NOT_REQUESTED → PENDING → PASSED/FAILED/BLOCKED`
- timeout 或自报完成不得直接变成 `PASSED`。
