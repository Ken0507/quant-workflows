# 每周模型费用

让 cken 用一次调用查看最近一周每天的 codex-pool 和 DeepSeek 费用。2026-10-21 用户纠正：“我要的是花了多少钱”。默认输出已改为每日金额、币种和费用合计；token 查询仅保留为可选附录。默认覆盖北京时间今天及前六天；也支持完整上周和指定结束日期。skill 源码属于个人通用技能仓 quant-workflows 的 shared/codex，不属于 AE 正式角色包，不触碰已退役的 HFT 项目技能入口。

## 供应链位置

个人工具费用核对链 · 只读统计。

```text
当前 pool 配置 → pool 服务端 daily_usage ──┐
官方 DeepSeek 账单 → 规范化费用 CSV ───┼→ [weekly-token-usage] → 每日费用、分币种合计、缺失说明
用户日期范围与时区 ───────────────────────┘
```

- **上游**：pool 维护的 key 费用记录、DeepSeek 官方费用导出、用户所需日期范围；可选 token 附录读取 DSH 结算元数据。
- **下游**：cken 核对个人工具用量；后续 agent 直接展示结果。不会自动发送报告或配置定时任务。
- **相邻能力**：原生 Codex/ChatGPT 账户额度、DeepSeek 官方账户账单均有独立范围，不与这里混算。

## 当前费用交付与未完成项

- pool：默认直接展示服务端每日 `actual_cost` 和区间合计。
- DeepSeek：增加规范化官方费用 CSV 读取入口，默认 `~/.config/weekly-token-usage/deepseek-bill.csv`，可用 `--deepseek-bill` 指定。字段为 `date,actual_cost,currency,timezone`。读取器已用合成账单验证，**尚未拿到用户真实官方账单或后台登录态，实际费用链路仍未接通**；默认显示“账单未接入”并退出2。
- 导入并非实时查询；当天费用截至导出时点。重复日期、混币种、跨时区日桶均拒绝直接累加。账单缺日不补零，金额原件不入Git。
- 只在明确 `--metric tokens` 时读取本机 DSH 日志；这保留初版统计能力，但不再代替费用答案。

本次核查官方[价目表](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)确认有缓存/未缓存/输出的差别和峰谷价，[更新日志](https://api-docs.deepseek.com/zh-cn/updates)确认10月17日模型更新价格不变。本机日志没有货币结算字段，不能因此推断实际账户扣费。准确费用仍须官方原件；需要 cken 提供已登录后台入口或账单导出路径，agent再核对整理并验证真实数据接入。

## 初版 token 附录的背景与设计

之前 codex-pool 查询需要现场发现接口、加载配置并手工汇总；DeepSeek 使用路径在本机工作台。用户希望一次拿到两个来源每天的数据。创建时实测 pool 用量接口可用；DeepSeek 官方 key 的余额接口可用，但 `/user/usage` 返回 404，公开 API 文档列出的余额接口不提供每日 token。

初版 token 附录保留两种不同覆盖：pool 由配置 key 的服务端日记录给出，DeepSeek 由本机 DSH 结算元数据给出。后者**不是全账户用量**，无法覆盖其他机器、已删除会话、后台标题等未落 usage 的调用、取消/失败后没有 token 记录的请求。当前缺口明确保留；未来有官方用量接口或授权导出格式后，可增加账户来源，不能静默替换成猜测。

| 设计选择 | 理由 |
|---|---|
| 默认今天及前六天；上周为完整周一至周日 | 两个常见问法含义不同，避免当天不完整数据被当作已结束自然日。 |
| pool 从实际配置读取地址和 key 路径 | 不在仓库硬编码服务地址、复制密钥或执行任意认证程序。 |
| 使用 `days` 取足够范围，再筛选日桶 | 实测 `start_date/end_date` 不约束 `daily_usage`；公开实现也确认这些日期参数用于 `model_stats`。 |
| 合计只累加选中日桶 | `usage.total` 是历史累计，不能直接当七天总量。 |
| DSH 流式解压，只保留计数和身份元数据 | 无需把对话正文存入统计输出，不生成解压中间文件。 |
| 归档与格式迁移按会话 ID 去重；fork 排除继承前缀 | 避免一次请求因复制、迁移或分叉被反复记账。 |
| 同 turn/step 结算替换；显式 retry 开新请求 | 对齐已安装 DSH token-meter 的结算投影。 |
| 无记录与未知分项显式展示 | 数据遗漏和真零消费不能混为一谈。 |

输入/缓存口径：两个适配器的 `input_tokens` 都是未缓存输入，缓存读取与写入另列，总数为 `input + cache_read + cache_write + output`。缓存缺项时保留未知；有服务端 total 但缓存分项未知时只保留可证实的 total，不倒算分项。

## 复用调研

调研了 [ccusage](https://github.com/ccusage/ccusage) 和 [better-ccusage](https://github.com/cobra91/better-ccusage)；这些本地 agent 日志工具没有本任务的 pool 服务端日桶与 DSH 结算组合入口。选择 Python 标准库薄封装 pool，复用已安装 zstandard 解码，按 DSH 的已验证元数据格式做有界统计。没有另造 API 代理或安装常驻服务。

## 初版 token 链路验证与来源

2026-10-21 在 84 本机先用裸命令验证，再包装 skill：

- pool 默认七天查询成功；把 `days=2` 与历史 `start_date/end_date` 一起传入仍返回今天及昨天，证明不能直接按起止参数信任日桶。脚本只用 `days/timezone`，随后筛选。
- DeepSeek `/user/balance` 返回 200，`/user/usage` 返回 404。认证只在内存使用，未打印或存入报告。
- 完整脚本成功返回七个日期以及本机覆盖提示；读取的 DSH 版本为 `0.2.1-alpha.3`。本机存在 v3/v4、归档及少量未支持旧格式；缺 usage 的请求和未支持格式明确列在 JSON 中。
- 合成测试覆盖北京时间跨日、跨年周窗口、完整上周、pool 历史总量误用、缓存重复计入、日期重复、缺字段、DSH 重试和结算替换、继承前缀、其他 provider 排除、缺 usage、归档/迁移去重与截断日志。具体测试名称可用 `unittest` 列出。

维护时优先查看以下精确入口：

| 来源 | 用途 |
|---|---|
| [hft-sdk-issues #319](https://github.com/hft-prop/hft-sdk-issues/issues/319) | 双入口配置的归属、现有 profile/key 文件职责与认证边界。 |
| [Sub2API gateway_handler.go](https://github.com/Wei-Shaw/sub2api/blob/main/backend/internal/handler/gateway_handler.go) | `Usage`、`parseUsageDateRange`、`buildAPIKeyDailyUsage`：区分日桶 days 与分模型日期筛选。公开源码是参考，已部署行为另以实测为准。 |
| [DeepSeek 官方余额 API](https://api-docs.deepseek.com/api/get-user-balance) | 确认余额不是历史 token 数据。 |
| 本机 `~/.ae/workbench/runtime/node_modules/.pnpm/@deepseek-ai+dsh-token-meter@*/node_modules/@deepseek-ai/dsh-token-meter/lib/types/usage-projection.js` | 已安装结算替换与 retry 的实现口径；升级后应按现有测试复验。 |
| `scripts/deepseek_local.py` | 实际支持的事件、归档选择、继承前缀、provider 过滤和诊断字段。 |

真实逐日用量、密钥、会话正文和本机认证文件不提交进 Git。没有把 token 统计或合成费用导入测试通过视为 DeepSeek 真实账户账单已接通。

## 维护与安装

源码位于 `skills/shared/codex/weekly-token-usage`，安装到 `~/.codex/skills/weekly-token-usage` 的单一软链接。只添加这个入口，不运行旧版全仓同步去恢复已退役的 HFT skill。换机器时提供已获授权的 pool 配置与本机 DSH 目录即可；默认路径不是跨机器可达性的承诺。

`--dsh-root` 可以重复；显式指定后替换默认根列表。日志全量流式读取，日期按结算事件时间筛选，不能按文件修改时间猜测事件日期。目录缺失、解析中断和未支持格式保留在 `coverage`。历史日志持续增大时可优化元数据索引，但索引必须可重建且不能把旧缓存当作当前请求结果。

## 变更记录

- 2026-10-21 用户纠偏：默认改为每日费用表；pool 展示每日金额，DeepSeek 增加官方费用CSV读取、币种/时区/重复校验，缺账单明确未接入；保留原技能名及可选token模式。

- 2026-10-21：首次创建；接通 pool 实时日桶和 DeepSeek 本机已记录用量，提供每日表、JSON 分项、上周/结束日期参数及覆盖诊断。
