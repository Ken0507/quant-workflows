---
name: weekly-token-usage
description: 当用户要一次查看最近一周每天的 codex-pool 和 DeepSeek token 消耗、上周用量或指定日期区间用量时使用。读取 pool 服务端日统计，并汇总本机 DeepSeek 会话记录；明确区分账户覆盖与本机覆盖。
metadata:
  short-description: 最近一周 codex-pool 与 DeepSeek 每日 token 用量
---

# 每日 token 用量

> 你是用量核对助手。一次返回逐日表和已记录合计，使用实时查询与本机实际记录，保留日期、时区和覆盖边界。

## 查询流程

默认统计 `Asia/Shanghai` 今天及前 6 天，含首尾共 7 个自然日。今天标为“截至查询时刻”。用户说“上周”时用上一个完整周一至周日；指定区间时按结束日期和天数换算。

从本 skill 的实际目录运行随附脚本；本机全局安装入口如下：

```bash
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py
```

其他已验证入口：

```bash
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --last-week
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --days 7 --end 2026-10-20
python3 ~/.codex/skills/weekly-token-usage/scripts/weekly_usage.py --format json
```

收到结果后直接给中文每日表与合计，并说明 DeepSeek 为本机记录。如果有缺失、解析问题或失败，保留结果中的具体限制；`exit 2` 表示至少一个来源失败，仍展示另一来源成功取得的数据。`partial` 是有数据但覆盖不完整，不能写成完整账单。用户只问 token 时重点给 token，费用可附一行。

需要输入、输出、缓存分项时用 `--format json`。总 token 为未缓存输入 + 缓存读取 + 缓存写入 + 输出；JSON 的 `input_tokens` 指未缓存输入。需要总输入时把两个缓存桶加回；任一桶未知则不补零、不反推。费用只使用 pool 返回的 `actual_cost` 与币种。

## 数据源与依赖

- Python 3.11+；本机 `zstandard` 模块，或已安装的 `zstd` 命令。不自动安装或升级环境。
- pool 从 `~/.codex/lgj.config.toml` 获取当前 provider/base URL 和 `/bin/cat` 指向的专用 key 文件。可用 `--pool-profile PATH` 指定另一份已有配置；不执行其他认证命令。
- pool 日桶参数是 `days` 和 `timezone`；`start_date/end_date` 只影响服务端的其他统计，不截取 `daily_usage`。脚本取从目标起始日到今天的日桶，再本地筛选，最大回溯 90 天。不能用 `usage.total` 代替目标区间合计。
- DeepSeek 默认扫描 `~/.ae/workbench/home/sessions`、`sessions-archive` 和 `~/.dsh/sessions`。支持 DSH v2–v4 已识别的结算事件。`--dsh-root PATH` 可重复，指定后替换默认目录列表；只添加用户实际需要的本机日志根。
- DeepSeek 官方 `/user/balance` 只返回余额。本机 key 对 `/user/usage` 的实测为 HTTP 404，不能从余额倒算逐日 token。若用户要求**全账户**用量，需要获授权的官方用量后台或导出记录；本 skill 当前自动结果不能替代它。不要请求用户把 key/cookie 贴到聊天。

最低依赖与真实链路检查就是运行默认查询。离线维护回归：

```bash
python3 -m unittest discover -s ~/.codex/skills/weekly-token-usage/scripts -p 'test_*.py' -v
```

## 硬性规则

1. **每次新查**：每次调用实时查询 pool 并重新读取本机记录，不把上次数字当作当前值。
2. **保留覆盖**：pool 是当前 key 的服务端用量；DeepSeek 是所列本机日志的已记录用量。不能称为两个账户的完整账单。
3. **不重复计数**：使用脚本处理重试结算替换、归档/格式迁移副本和 fork 继承前缀，不直接相加所有 usage，也不相加累计计数。
4. **未知不等于零**：缺日期、缺 usage、未支持的日志格式和查询失败必须明确显示。无记录不能说成零消费。
5. **保护原件和认证**：只读配置、日志与用量接口；不打印密钥、cookie、对话正文、HTTP 原始错误体，不发送模型请求，不修改会话或服务。
6. **金额口径**：pool `actual_cost` 是平台记账金额，不能叫现金支出；不从 token 估算 DeepSeek 费用，不将其他单位换算为美元。

## 反模式

❌ 给 pool 传入历史起止日后，直接信任返回日期。→ 实测日桶仍以今天回溯；必须先取足够天数再筛选。

❌ 相加 DSH 中每条 usage 或同一会话的多个归档版本。→ 已发现结算替换、重试、迁移副本和继承前缀，按模块的请求身份去重。

❌ 把 DeepSeek 余额或本机会话合计称为账户完整历史消费。→ 余额没有日 token；本机日志不覆盖其他机器及未落记录请求。

## 常见问题

| 现象 | 处理 |
|---|---|
| pool 网络失败 | 若是沙箱拒绝网络，按宿主授权流程重跑同一只读命令；不要换凭据或启动模型探测。 |
| pool HTTP 401/403 | 核对指定 profile 和既有 key 文件的可读性及有效性，不输出 key。保留 DeepSeek 结果。 |
| DeepSeek 缺日志或解码器 | 查看 JSON 的 `coverage.roots/missing_roots/diagnostics`；确认实际会话根与现有 Python/zstd 环境。 |
| 记录缺 usage 或格式不支持 | 保留已记录小计和遗漏数量；不能估算填平。维护细节及来源见 [README.md](README.md)。 |
| 要完整 DeepSeek 账户账单 | 明确当前覆盖不足，需官方用量后台或获授权的导出；本地结果只能作为补充。 |
