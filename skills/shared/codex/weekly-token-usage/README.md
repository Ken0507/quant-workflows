# 每周模型费用

让 cken 一次查看最近一周每天 codex-pool 和 DeepSeek 花了多少钱。默认输出每日费用、币种与各自合计；北京时间今天及前六天，也支持完整上周和指定结束日期。保留 `weekly-token-usage` 原名称作为兼容入口，token 数只作可选附录。

## 供应链位置

个人工具费用核对链 · 只读统计。

```text
pool 配置 → 服务端 daily_usage ──────────┐
DSH 去重请求 + 官方峰谷价 ────────────────┼→ [weekly-token-usage] → 每日费用、币种、合计、来源说明
可选官方账单 CSV ────────────────────────┘
```

- **上游**：当前 pool key 的服务端记录、本机 DSH 请求结算元数据、官方价格；可选官方费用导出。
- **下游**：cken 直接查看每日花费，agent无需另作手工计算。不发送报告或配置定时任务。
- **相邻范围**：原生 Codex 订阅额度、其他机器使用和账户实际扣费流水不混入本机计价结果。

## 需求与已定口径

用户于2026-10-21明确：“我要的是花了多少钱”，并指出 Praxis Zone 上已经使用过 DeepSeek 费用查询。初版只给 token；随后又把官方扣费流水当成唯一可交付金额来源，导致已有本机计价能力被阻断。这两点均已纠正：默认先给费用，有估算就明确标记，不为普通费用查询额外要求登录后台。

本机当日已有 `/data/db/hft/temp/data-watch-cost-20261021/cost.py`：按请求的输入、缓存命中、输出 token，结合工作日峰谷价计算人民币金额，来源记录在同目录 `calls.json`。这些是可能被清理的本机证据；不作为运行依赖，也不修改或复制其业务原件。它是一个指定任务子集的计价脚本，不是全账户流水；本次没有从 DSH 对话历史证明它与哪次 Praxis 页面操作一一对应，因此不宣称找到了官方账单 API。

本 skill 复用这一计价方法，增加请求去重、模型映射、节假日、官方价目核对和显式覆盖诊断。原生账户插件目前查到的详情接口是账户资料/余额及用量页面链接；仅对一个猜测的 `/user/usage` 返回404，不能证明不存在其他账单接口。官方流水能力没有被否定，也不再成为默认费用查询的前置。

## 默认费用来源

| 来源 | 取数与计价 | 展示与边界 |
|---|---|---|
| codex-pool | 从实际 profile 读取现有 endpoint/key，以 `days/timezone` 查日桶，再本地截取区间；累加日记录 `actual_cost` | 平台记账费用，按返回币种展示；不是余额或历史总累计。 |
| DeepSeek | 流式读取本机 DSH 已去重请求，按模型、未缓存输入、缓存读取、输出及峰谷分别计算 | `estimated_cost`、`≈¥`；是本机记录的模型费用估算，不是账户扣费流水。 |
| 可选 DeepSeek 账单 | 显式 `--deepseek-bill PATH` 读取经官方原件核对的规范化 CSV | `actual_cost`；截至导出时点，缺日不填零，禁止混币种/时区/重复日期。 |

默认日志根为 `~/.ae/workbench/home/sessions`、`sessions-archive`、`~/.dsh/sessions`；显式 `--dsh-root` 可重复并替换默认根。Python 3.11+，解压用已有 `zstandard` 模块或 `zstd`；不落解压文件、不安装常驻服务。只保留计数及请求身份元数据，不输出正文或认证。

## 价格与日期依据

2026-10-21已核对[官方价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)及[更新日志](https://api-docs.deepseek.com/zh-cn/updates)：9月10日Flash价格调整，10月17日模型更新价格不变。当前价卡从2026-09-10开始，未知历史区间不猜测。

| 每百万 token（人民币） | Flash 高峰 / 空闲 | Pro 高峰 / 空闲 |
|---|---:|---:|
| 未缓存输入 | 2 / 1 | 9 / 4.5 |
| 缓存命中 | 0.04 / 0.02 | 0.30 / 0.15 |
| 输出 | 8 / 4 | 27 / 13.5 |

北京时间周一至周五（不含中国法定节假日）09:00–12:00、14:00–18:00为高峰，其余为空闲。官方明确周末全天空闲，因此补班周末也不改为高峰。2026年价卡范围内，中秋9月25–27日、国庆10月1–7日；依据[国务院2026年节假日通知，北京市政府转载](https://www.beijing.gov.cn/zhengce/zhengcefagui/202511/t20251104_4258873.html)，国办发明电〔2025〕7号。未知年份不静默套用普通工作日。

每次计算前实时核对官方表格和时间规则；单价或结构变化即明确失败，保留pool结果，维护者须新增对应生效区间。旧Flash别名按官方映射处理，未知provider/model、缺缓存桶或未核实缓存写入价不瞎算。

按本机结算时点近似计费时点；跨峰谷边界、折扣、赠送余额可能使估算与账单不同。本机删失记录、其他机器、缺usage、后台调用和独立Search/Fetch费用不在估算覆盖内，合计只能称为已记录请求的估算。

## 去重与回归

同一会话的归档/迁移副本只取一次，fork排除继承前缀；同turn/step的结算替换保留最终样本，显式retry另算。日期按事件时间，不以文件修改时间猜测。缺日期不填零，未知字段不推算；总token包含输入、缓存与输出，不能再将缓存重复加进费用。

已完成真实七日查询，另有合成回归覆盖日期边界、币种、账单缺失、归档/fork/retry、token分项、峰谷整点、周末/节假日和模型计价。测试通过不代表官方账户流水已验证。真实逐日金额、凭据、会话正文不提交Git。

## 维护入口与复用选择

- [hft-sdk-issues #319](https://github.com/hft-prop/hft-sdk-issues/issues/319)：pool配置来由及认证边界。
- [Sub2API gateway_handler.go](https://github.com/Wei-Shaw/sub2api/blob/main/backend/internal/handler/gateway_handler.go)：`Usage/buildAPIKeyDailyUsage`；`start_date/end_date`影响分模型统计，不截取日桶。
- 本机 DSH `0.2.1-alpha.3` 的 `dsh-token-meter/lib/types/usage-projection.js`：请求结算替换和retry投影口径。
- `scripts/deepseek_cost.py`：当前价格、模型映射、官方表格验证、峰谷及日历；`deepseek_local.py`：本机只读解码与去重。
- `scripts/weekly_usage.py`：两来源编排、费用展示和可选CSV导入。CSV列为 `date,actual_cost,currency,timezone`，它是本工具规范化输入，不冒称官网原始格式。

已调研 ccusage/better-ccusage；它们不直接覆盖本任务的pool服务端与DSH组合，因此保留Python薄封装、标准库HTTP/Decimal及已有zstd。源码归个人 quant-workflows 的 `skills/shared/codex/weekly-token-usage`，全局软链接到 `~/.codex/skills/weekly-token-usage`；不触碰AE正式包或已退役HFT入口。

## 变更记录

- 2026-10-21：首次建立token统计。
- 同日：用户纠正为金额，默认改为费用；加入可选规范化官方CSV。
- 同日第二次纠正：核对本机已有DeepSeek计价脚本，默认自动提供逐请求峰谷费用估算，取消强制账单/登录前置，保留平台记账与估算区别。
