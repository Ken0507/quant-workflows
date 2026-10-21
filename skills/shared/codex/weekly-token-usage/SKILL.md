---
name: weekly-token-usage
description: 当用户要看最近一周每天 codex-pool 和 DeepSeek 花了多少钱、token 消费金额、上周费用或指定区间账单时使用。默认返回每日金额、币种和费用合计；token 数只作为可选附录，缺少实际账单时明确标注。
metadata:
  short-description: 最近一周 codex-pool 与 DeepSeek 每日费用
---

# 每日模型费用

> 你是费用核对助手。用户所说的“消费”指花了多少钱；先给每日金额和合计，清楚区分已取得账单、缺失账单与估算。保留 skill 原名作为兼容入口。

## 查询流程

默认按 `Asia/Shanghai` 统计今天及前 6 天，含首尾共 7 天。今天尚未结束。用户说“上周”时用上一个完整周一至周日。

```bash
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --last-week
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --days 7 --end 2026-10-20
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --format json
```

直接返回“日期 / codex-pool 费用 / DeepSeek 费用”表和各自合计。默认不展示 token 表。`$` 为美元，`¥` 为人民币，不跨币种相加；保留 JSON 的原精度，显示金额通常用两位小数。pool 使用每日日桶的 `actual_cost`，不是 `cost`、余额或 `usage.total`。

`exit 2` 表示一个费用来源查询失败或账单尚未接入。仍展示另一个来源已有金额，明确没完成的部分；不能声称两个平台费用均已查全。只有用户要 token 分项时使用：

```bash
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --metric tokens --format json
```

## DeepSeek 实际费用入口

默认读取 `~/.config/weekly-token-usage/deepseek-bill.csv`，或用 `--deepseek-bill PATH` 指定**从官方账单核对整理**的逐日费用文件。CSV 字段为：

```csv
date,actual_cost,currency,timezone
2026-10-20,12.34,CNY,Asia/Shanghai
```

上行金额只是格式示例，不是真实账单。该格式是本工具的规范化输入，不声称是官网原始导出格式。每个日期一行；保留账单币种与原日桶时区，缺日不补零。导入记录不是实时查询，今天的数据截至账单导出时点；刷新的前提是取得新账单。不得把示例或 token 推算值写入此文件。

如果文件不存在，默认费用列显示“账单未接入”。本机 DeepSeek API key 只能通过已核实的 `/user/balance` 查询余额；`/user/usage` 实测为 404。本机 DSH 结算日志也只有 token，没有货币费用。继续读取用户已授权、已登录的官方用量后台或账单导出；如果缺浏览器入口，完成可用来源与本地修改后向用户索取入口或文件路径，不请求用户粘贴 key/cookie。

公开价目包含峰谷价，历史价格、模型、请求计费时点都会影响金额。未经确认的价格乘总 token 不能叫实际扣费。若用户另外接受估算，应另列“估算”，逐请求核对模型、缓存、历史价格和峰谷时段，不写入实际账单列。

## 数据源与依赖

- Python 3.11+。费用模式只查询 pool 并读取费用 CSV，不扫描本机会话；可选 token 模式还需 `zstandard` 模块或 `zstd` 命令。
- pool 从 `~/.codex/lgj.config.toml` 读取现有 provider/base URL 及 `/bin/cat` 指向的专用 key。可用 `--pool-profile PATH` 指定已有配置，不执行任意认证命令。
- pool 日桶由 `days/timezone` 控制，最大回溯90天。`start_date/end_date` 只影响其他统计；脚本取足够范围后在本地截取，不能用历史累计代替目标区间费用。
- token 模式的 DSH 只读适配、归档去重和缺记录处理见 [README.md](README.md)。这些记录不能证明账户实际花费。

## 硬性规则

1. **先给钱数**：默认每日费用与合计，用户未要求时不拿 token 表替代。
2. **依据实际金额**：pool 使用 `actual_cost`；DeepSeek 使用获授权的官方费用原件。当前余额、今日价格和本机 token 不等于历史扣费。
3. **未知不填零**：未接入、缺日、缺金额、未知币种、查询失败均需显式展示；无法取得两者时报告部分完成。
4. **日期与币种明确**：按所选自然日筛选；不同币种不加总，导入日桶不跨时区硬转换，当日不是完整一天。
5. **刷新来源明确**：pool 每次实时请求；DeepSeek 导入数据标明截至导出时点，不伪装实时。
6. **只读与凭据保全**：不调用模型、不修改会话和服务、不输出密钥/cookie/正文/原始HTTP错误体；账单原件不提交Git。

## 反模式

❌ 用户问消费却只给 token 数。→ 2026-10-21 用户已明确纠正为“花了多少钱”，默认给费用表。

❌ 按总 token 乘一个单价，写成 DeepSeek 实际花费。→ 缓存、模型与峰谷价格不同；要实际费用须拿账单，估算必须另列。

❌ pool 历史起止日期传入后直接信任日桶或历史总量。→ 按 days 取回溯窗后筛选，再对已取得的日费用求和。

## 常见问题

| 现象 | 处理 |
|---|---|
| pool 网络失败 | 若为沙箱网络限制，按宿主流程重跑同一只读命令；不启动模型探测。 |
| pool HTTP 401/403 | 核对已有 profile 与 key 文件是否有效可读，不打印key。 |
| DeepSeek 账单未接入 | 需要官方账单导出路径或已登录后台入口；这是尚未完成项，不是零消费。 |
| CSV 重复日期、混币种或时区不符 | 回官方原件核对后整理成一致的逐日记录，不在代码中猜测合并。 |
| 用户另要 token | 显式使用 `--metric tokens`，保留本机覆盖限制。 |

离线回归命令：

```bash
python3 -m unittest discover -s ~/.codex/skills/weekly-token-usage/scripts -p 'test_*.py' -v
```
