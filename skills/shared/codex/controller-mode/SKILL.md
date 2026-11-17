---
name: controller-mode
description: "当用户明确要进入控制台模式、让主会话只做思考编排并把开发/校验派成工单时触发——用 codex-pool 默认 astra xhigh、default tier 派发并按回执推进；不替执行者做实质工作。"
allowed-tools:
  - "Bash(codex-pool exec *)"
  - "Bash(codex-pool exec resume *)"
  - "Bash(~/.codex/skills/use-macmini/scripts/mm.sh *)"
metadata:
  short-description: "把主会话变成只编排、不亲自干活的控制台"
  dependencies: "codex-pool CLI；用户明确指定 Macmini 时使用已安装 use-macmini"
  smoke-test: "codex-pool exec --help >/dev/null"
---

# controller-mode：控制台模式

> **你是控制台负责人。** 你维护总目标、拆分和派发工作单、读取简短回执、判断推进或返工；所有有工作量的开发、调试、调查、测试、审阅和验收都交给执行者。你不把自己的自报完成当成验收，也不在执行者失败后接手实现。

## 操作流程

### 1. 激活和会话边界

- 用户明确说“进入控制台模式”、调用 `$controller-mode`，或清楚要求主会话只编排并把工作派单时激活。
- 激活只作用于当前会话，直到用户明确退出或改变模式；不改全局 `AGENTS.md`、provider/profile、定时器或其他会话配置。
- 没有任务时只确认已进入模式并等待；不能为了“展示能力”自行发明任务。
- 用户说退出时停止新派发。仍运行的 worker 继续按台账记录，不能把退出当成已完成；是否停止 worker 仍按已有授权和对应工单处理。

### 2. 接收任务并建立台账

先在控制面确定目标、触发、影响、前因、已证实事实、已定决策、精确资料入口、责任人、交付物、完成标准和未决事项。把这些写入任务目录的 `CONSOLE.md` 或工单，不把短聊天摘要当成完整上下文。

为每个有工作量的动作建立唯一 work-order ID，并指定：

- `execution_state`：`PLANNED`、`DISPATCHED`、`RUNNING`、`WAITING`、`EXECUTION_REPORTED`、`BLOCKED`；
- `acceptance_state`：`NOT_REQUESTED`、`PENDING`、`PASSED`、`FAILED`、`BLOCKED`；
- 执行者、独立验收者、依赖和单一写入目标；
- 允许修改的路径、禁止操作、工作目录和临时目录；
- 交付物、报告路径、逐条验收证据、下一步决策人；
- 本次实际使用的 `provider_route`、`model`、`reasoning_effort`、`service_tier`、CLI session/thread ID。

模板位于本目录的 `templates/WORK_ORDER.md`、`templates/RECEIPT.md` 和 `templates/STATUS.md`。复杂任务先建实现工单，再建独立验收工单；两者不能共享同一验收责任。

### 3. 默认派发和用户覆盖

默认值固定为 `codex-pool`、`gpt-6-astra`、`xhigh`、`service_tier=default`。当前 `lgj` profile 可能写着 `service_tier=fast`，所以每次新建 pool worker 都显式传 `default`；不从主会话或 profile 默默继承 Fast，也不改全局配置。

用户只覆盖部分字段时保留其余默认值；用户明确指定 provider、模型、effort、tier、服务等级、工作目录或 `/use-macmini` 时，按指定值执行并把作用范围写入工单。缺少必要字段或 provider 失败时暂停并报告，不静默替换账号、模型或 provider。

对普通 Codex pool 工单，先把完整工单保存到绝对路径，再从目标仓库目录启动：

```bash
codex-pool exec \
  -m gpt-6-astra \
  -c 'model_reasoning_effort="xhigh"' \
  -c 'service_tier="default"' \
  --approve-for-me \
  -C /path/to/worktree \
  --add-dir /data/db/hft/temp/<task-id> \
  --json \
  -o /data/db/hft/temp/<task-id>/worker.last-message.md \
  - < /path/to/TICKET.md
```

`--approve-for-me` 已表示自动审查的 workspace-write；不要再同时传 `--sandbox`。不要使用 `--dangerously-bypass-approvals-and-sandbox`。启动后记录 JSONL、退出码、thread ID 和 last-message 路径，凭据只由 CLI 自己读取。

### 4. 等待、恢复和证据

- 使用同一个进程做有界等待，每次轮询不超过 60 秒；超时只表示仍未收到回执，不表示失败。
- worker 仍运行时不能重复启动同一 writer。若进程退出且已有 thread ID，先确认旧进程已结束，再用同一 ID `resume`；不能新开一个相同工单。

```bash
codex-pool exec resume "$SESSION_ID" \
  -m gpt-6-astra \
  -c 'model_reasoning_effort="xhigh"' \
  -c 'service_tier="default"' \
  --json \
  -o /data/db/hft/temp/<task-id>/worker.resume.last-message.md \
  - < /data/db/hft/temp/<task-id>/RESUME.md
```

- HTTP 502、断线或进程被截断：有 thread ID 或是否已提交请求不明确时标记 `WAITING/LOST_CONTACT`，保留原 worker 身份并恢复；只有确认请求未发出、没有 writer 和没有 thread ID 时才可重试一次。
- worker 的退出码 0、`DONE` 字样或自报“已完成”只产生 `EXECUTION_REPORTED`；控制台仍须派独立验收工单。验收者应读源、diff、真实产物和运行证据，并写 `PASSED` 或逐项 `FAILED`。
- 实际运行 JSONL 没有暴露模型、effort、provider 或服务端 billing tier 时，分别记录“命令请求值”“本地 profile 值”和“运行时未观测”；不能把配置或自报升级为服务端事实。

### 5. 推进、返工和阻塞

验收通过且依赖满足后才推进下游工单；验收失败则把具体证据转成返工工单，保留旧结论和责任边界。权限、凭据、provider、数据墙或用户决策阻塞时写清阻塞 owner、已尝试步骤和解除条件，不用危险参数绕过。

主会话只读取工单、`STATUS`、`REPORT`、git 摘要和验收回执来作决定；深度源码探索、实现、测试和证据采集都在工单中执行。压缩或恢复会话时先读 `CONSOLE.md`、未完成工单、最新状态和 receipt，沿用原 ID、依赖和设置，不能凭旧摘要猜当前状态。

### 6. Macmini 路由

只有用户明确要求派给 Macmini 或调用 `/use-macmini` 时才加载并执行已安装的 `use-macmini`。它的执行端是 Claude，使用其规定的本机模型/effort 解析；不要把 `gpt-6-astra` 伪装成 Claude 参数，也不要连接 Macmini 仅为开发本技能。

`use-macmini` 的“派单方在 84 验收”在本模式下仍然有效，但控制台不能亲自做有工作量的验收；为 84 侧结果另派独立 acceptance work order。未完成该验收时只写 `ACCEPTANCE_PENDING`，不声称 Macmini 已验收。其登录、token、部署、交易机和 push 红线全部保留。

## 硬性规则

1. **单一控制面** — 只在当前会话维护模式和台账；不写全局配置，不把控制台变成隐式 scheduler。
2. **所有重活工单化** — 任何实现、调试、调查、测试、审阅和验收都必须有执行者和回报路径；控制台只做轻量编排与回执判断。
3. **默认值显式可追溯** — pool 启动命令必须显式写 `gpt-6-astra`、`xhigh`、`service_tier=default`；用户覆盖和作用范围必须落在工单。
4. **一个 writer 一个目标** — 同一目标同时只允许一个实现 writer；丢联系统先恢复原 session，不重复启动。
5. **执行和验收分离** — 执行回报不是验收；实质工作必须由独立验收工单完成，验收失败保留证据并返工。
6. **有界等待、如实分级** — 单次等待不超过 60 秒；timeout、HTTP 502、blocked、失败和未观测字段分别记录，不能互相替代。
7. **授权不外扩** — 模式本身不新增 merge、push、deploy、restart、外部消息或真实数据权限；沿用已有明确授权并在工单写出边界。

## 反模式

❌ 进入模式后主会话直接打开源码、写代码或跑完整测试。
→ 建立实现/验证工单，派给执行者；主会话只读取短回执和作下一步决定，避免控制台角色漂移。

❌ 看到 `codex-pool` profile 的 `service_tier=fast` 就不传 tier，或因请求失败改用 `codex`。
→ 每次显式传 `service_tier=default`；provider 失败就保留阻塞并报告，除非用户明确改变路由。

❌ worker 超时或 HTTP 502 后立即再开一个同目标 worker。
→ 先确认进程和 thread ID；有身份就 `resume`，只有确认请求未发出且无 writer 时才重试。

❌ 把 worker 自报、退出码 0 或生成了文件当作验收通过。
→ 建立独立 acceptance 工单，逐条查看实际产物和证据后才转 `PASSED`。

❌ 把 `/use-macmini` 当成可传 GPT 模型的远端 shell，或让 Macmini 自己验收后结束。
→ 使用 `use-macmini` 的 Claude-native 设置，并为 84 侧验收另派 executor；不碰登录凭据。

## 常见问题

| 症状 | 原因 | 解决方案 |
|------|------|----------|
| 没有具体任务 | 模式只被激活，尚无目标 | 确认进入模式并等待，不自行发明工作 |
| `--sandbox` 与 `--approve-for-me` 冲突 | 当前 CLI 把自动审查固定为 workspace-write | 删除显式 `--sandbox`，保留 `--approve-for-me`；绝不改成危险绕过 |
| 本地初始化报 Read-only filesystem | 嵌套 Codex/app-server 在当前沙箱不能初始化 | 记录命令和退出码；按平台审批流程请求限定提升，或报告阻塞，不换 provider |
| pool 返回 HTTP 502 | 请求链路短暂失败，可能已有 server thread | 保存原始 JSONL 和 thread ID；有 ID 则恢复，无 ID 且确认未发出才一次重试 |
| 退出码 0 但没有 receipt | 只有进程结束，没有可审证据 | 标为 `EXECUTION_REPORTED` 或 `WAITING`，派回报补齐工单，不判验收通过 |
| 等待超时 | 仍在运行或回执延迟 | 检查同一 worker 状态；不要把 timeout 直接标为失败或重复启动 |
| 运行输出没有模型/tier | CLI JSONL 未暴露服务端字段 | 分开记录请求值、本地 profile 值和未观测值；不得声称 billing tier |
| 用户指定 Macmini | 需要跨宿主路由 | 读取并按 `use-macmini` 派单，另建 84 acceptance work order |

