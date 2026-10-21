---
name: weekly-token-usage
description: 当用户要看最近一周每天 codex-pool 和 DeepSeek 花了多少钱、token 消费金额、上周费用或指定区间账单时使用。默认返回 pool 服务端费用与 DeepSeek 本机用量按官方价估算的人民币费用，保留币种和估算标记；token 数只作可选附录。
metadata:
  short-description: 最近一周 codex-pool 与 DeepSeek 每日费用
---

# 每日模型费用

> 你是费用核对助手。用户所说的“消费”指花了多少钱；先给每日金额和合计，默认完成两者的费用查询，清楚区分平台记账金额与按记录估算的金额。保留 skill 原名作为兼容入口。

## 查询流程

默认按 `Asia/Shanghai` 统计今天及前 6 天，含首尾共 7 天。今天尚未结束。用户说“上周”时用上一个完整周一至周日。

```bash
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --last-week
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --days 7 --end 2026-10-20
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --format json
```

直接返回“日期 / codex-pool 费用 / DeepSeek 费用”表和各自合计。DeepSeek 的 `≈¥` 表示按记录和官方价估算；不要因没有官方扣费流水而阻断本机费用计算。默认不展示 token 表。`$` 为美元，`¥` 为人民币，不跨币种相加；保留 JSON 的原精度，显示金额通常用两位小数。pool 使用每日日桶的 `actual_cost`，不是 `cost`、余额或 `usage.total`。

`exit 2` 表示一个费用来源失败；显式指定账单文件但文件不存在也返回2。仍展示另一个来源已有金额，明确没完成的部分；不能声称两个平台费用均已查全。只有用户要 token 分项时使用：

```bash
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --metric tokens --format json
```

## DeepSeek 默认计价

脚本先实时核对[官方价目表](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)，再读取本机 DSH 请求结算元数据，沿用已有计价脚本的方式按每次请求计算人民币费用。请求先按归档、fork 和重试规则去重。

- 未缓存输入、缓存命中、输出分别计价；Flash 每百万 token 高峰价为 2 / 0.04 / 8 元，空闲价减半。Pro 为 9 / 0.30 / 27 元，空闲价减半。旧 Flash 别名按官方映射处理。
- 峰谷按北京时间：周一至周五（不含法定节假日）09:00–12:00、14:00–18:00 为高峰，其余为空闲。日历已核对2026年；补班的周末仍按官方“周末全天空闲”规则处理。
- 使用本机结算事件时刻作为计费时点近似；跨峰谷边界、账户折扣、赠送余额等可能使结果与账单不同。只统计模型 token 费用，不包括独立 Search/Fetch 计费。
- 历史价卡从2026-09-10开始；10月17日官方更新确认价格不变。价目页、模型、历史日期或日历超出已验证范围时明确缺项，不猜价格。
- 已删除日志、缺 usage、其他机器用量无法覆盖；缺日期显示“无记录”，不表示零消费。

这是用户要的可用费用估算路径，**无需先索取官方后台登录态或要求用户另行同意估算**。同时必须保留 `≈` 和本机覆盖说明，不能称为实际扣费流水。细节与已用脚本入口见 [README.md](README.md)。

## 可选官方账单替代

用户已有官方逐日费用时，可用 `--deepseek-bill PATH` 替代默认估算。格式是本工具的规范化输入，不声称是官网导出原格式：

```csv
date,actual_cost,currency,timezone
2026-10-20,12.34,CNY,Asia/Shanghai
```

上行只是格式示例。每个日期一行；只能从官方原件核对整理，不能将估算值填入 `actual_cost`。缺日不补零，不跨币种加总、不跨时区硬转换。导入记录截至导出时点，不能冒充实时查询。普通费用查询不依赖此文件。

## 数据源与依赖

- Python 3.11+。默认费用模式还需 `zstandard` 模块或 `zstd` 命令，以流式读取本机会话；不自动安装或升级环境。
- pool 从 `~/.codex/lgj.config.toml` 读取现有 provider/base URL 及 `/bin/cat` 指向的专用 key。可用 `--pool-profile PATH` 指定已有配置，不执行任意认证命令。
- pool 日桶由 `days/timezone` 控制，最大回溯90天。`start_date/end_date` 只影响其他统计；脚本取足够范围后在本地截取，不能用历史累计代替目标区间费用。
- 本机默认根为 `~/.ae/workbench/home/sessions`、`sessions-archive`、`~/.dsh/sessions`；`--dsh-root PATH` 可重复，指定后替换默认列表。只读适配和去重见 README。

## 硬性规则

1. **先给钱数**：默认每日费用与合计，用户未要求时不拿 token 表替代。
2. **来源与标记一致**：pool 使用 `actual_cost`；DeepSeek 默认 `estimated_cost` 并显示 `≈`。官方账单替代必须有真实原件，不能把估算写成实际扣费。
3. **未知不填零**：缺日、缺用量、未知模型/价格/日历/币种、查询失败均需显式展示；保留可用的小计和遗漏数量。
4. **日期与币种明确**：按所选自然日筛选；不同币种不加总，导入日桶不跨时区硬转换，当日不是完整一天。
5. **每次刷新**：pool 实时请求，DeepSeek 实时核价并重读本机记录；显式导入的账单标明截至导出时点。
6. **只读与凭据保全**：不调用模型、不修改会话和服务、不输出密钥/cookie/正文/原始HTTP错误体；账单原件不提交Git。

## 反模式

❌ 用户问消费却只给 token 数。→ 2026-10-21 用户已明确纠正为“花了多少钱”，默认给费用表。

❌ 没有官方流水便说 DeepSeek 费用查不了、要求用户先登录。→ 复用已有逐请求计价口径，默认给估算金额并明确标记。

❌ 按总 token 乘一个单价。→ 分模型、缓存、输入输出和峰谷时段计价。

❌ pool 历史起止日期传入后直接信任日桶或历史总量。→ 按 days 取回溯窗后筛选，再对已取得的日费用求和。

## 常见问题

| 现象 | 处理 |
|---|---|
| pool 网络失败 | 若为沙箱网络限制，按宿主流程重跑同一只读命令；不启动模型探测。 |
| pool HTTP 401/403 | 核对已有 profile 与 key 文件是否有效可读，不打印key。 |
| DeepSeek 官方价目变化或不可读 | 明确计价暂不可用；维护价卡及生效区间，不默用过期价格。 |
| DeepSeek 缺日志或分项 | 保留已计算小计，标明缺口；不要填零或要求先登录官网。 |
| CSV 重复日期、混币种或时区不符 | 回官方原件核对后整理成一致的逐日记录，不在代码中猜测合并。 |
| 用户另要 token | 显式使用 `--metric tokens`，保留本机覆盖限制。 |

离线回归命令：

```bash
python3 -m unittest discover -s ~/.codex/skills/weekly-token-usage/scripts -p 'test_*.py' -v
```
