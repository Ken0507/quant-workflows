#!/usr/bin/env python3
"""Read pool daily accounting and local DeepSeek settlements; never run inference."""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "total_tokens")


class UsageError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise UsageError("用量接口发生重定向；停止以避免将凭据发给其他地址。")


def day_range(start, end):
    return [start + timedelta(days=n) for n in range((end - start).days + 1)]


def window(args, now):
    today = now.date()
    if args.last_week:
        if args.end or args.days != 7:
            raise UsageError("--last-week 不能与 --end 或非默认 --days 合用。")
        end = today - timedelta(days=today.weekday() + 1)
        return end - timedelta(days=6), end
    end = args.end or today
    if not 1 <= args.days <= 90 or end > today:
        raise UsageError("--days 必须为 1–90，结束日期不能在未来。")
    return end - timedelta(days=args.days - 1), end


def count(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise UsageError("接口 token/请求计数不符合非负整数契约。")
    return value


def normalize_pool(payload, start, end):
    if not isinstance(payload, dict):
        raise UsageError("pool 返回格式变化：应为 JSON 对象。")
    payload = payload.get("data", payload)
    if not isinstance(payload, dict) or not isinstance(payload.get("daily_usage"), list):
        raise UsageError("pool 返回缺少 daily_usage。")
    days = {d.isoformat(): None for d in day_range(start, end)}
    for row in payload["daily_usage"]:
        if not isinstance(row, dict):
            raise UsageError("pool 日记录格式错误。")
        try:
            key = date.fromisoformat(row["date"]).isoformat()
        except (KeyError, TypeError, ValueError):
            raise UsageError("pool 日记录日期格式错误。") from None
        if key not in days:
            continue
        if days[key] is not None:
            raise UsageError("pool 返回重复日期，不能直接累加。")
        try:
            values = {k: count(row[k]) for k in TOKEN_FIELDS}
            values["requests"] = count(row["requests"])
        except KeyError:
            raise UsageError("pool 日记录缺少 token 分项，停止以免静默算错。") from None
        if sum(values[k] for k in TOKEN_FIELDS[:-1]) != values["total_tokens"]:
            raise UsageError("pool 输入、输出、缓存之和与 total_tokens 不一致。")
        amount = row.get("actual_cost")
        if amount is not None:
            try:
                cost = Decimal(str(amount))
                if not cost.is_finite() or cost < 0:
                    raise InvalidOperation
                values["actual_cost"] = str(cost)
            except InvalidOperation:
                raise UsageError("pool actual_cost 格式错误。") from None
        days[key] = values
    totals = {k: sum(r[k] for r in days.values() if r is not None) for k in (*TOKEN_FIELDS, "requests")}
    observed = [r for r in days.values() if r is not None]
    if observed and all("actual_cost" in r for r in observed):
        totals["actual_cost"] = str(sum((Decimal(r["actual_cost"]) for r in observed), Decimal(0)))
    return {
        "status": "ok", "scope": "configured_pool_api_key", "days": days,
        "totals": totals, "currency": payload.get("unit"),
        "warnings": ["无记录日期不等于已确认零消费。"] if any(v is None for v in days.values()) else [],
    }


def pool_usage(profile_path, start, end, now, timezone):
    try:
        profile = tomllib.loads(profile_path.read_text())
        provider = profile["model_providers"][profile["model_provider"]]
        auth = provider["auth"]
        if auth.get("command") != "/bin/cat" or len(auth.get("args", [])) != 1:
            raise UsageError("pool profile 需要单文件 /bin/cat 认证；不执行任意认证命令。")
        key = Path(auth["args"][0]).expanduser().read_text().strip()
        base = provider["base_url"].rstrip("/")
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError):
        raise UsageError("无法读取 pool profile 或其中指定的 key 文件；核对路径和权限。") from None
    parts = urllib.parse.urlsplit(base)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise UsageError("pool base_url 格式不受支持。")
    if not key or "\n" in key or "\r" in key:
        raise UsageError("pool key 文件为空或格式异常。")
    # Live probe: start_date/end_date are ignored; days counts backwards from today.
    lookback = (now.date() - start).days + 1
    if lookback > 90:
        raise UsageError("目标起始日期距今天超过90天，当前 pool 查询范围不支持。")
    query = urllib.parse.urlencode({"days": lookback, "timezone": timezone})
    endpoint = base + ("/usage" if parts.path.rstrip("/").endswith("/v1") else "/v1/usage")
    request = urllib.request.Request(endpoint + "?" + query, headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise UsageError(f"pool 用量查询 HTTP {exc.code}；检查已有 key 的有效性和权限。") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise UsageError("pool 网络连接失败；检查网络/代理，若为沙箱限制按宿主流程申请联网。") from None
    except (ValueError, UnicodeError):
        raise UsageError("pool 返回无法解析的 JSON。") from None
    result = normalize_pool(payload, start, end)
    result["source"] = endpoint
    result["requested_lookback_days"] = lookback
    return result


def read_deepseek_bill(path, start, end, timezone):
    """Import normalized daily amounts from an authorized official bill export."""
    if not path.is_file():
        return {"status": "unavailable", "days": {},
                "error": "账单未接入：需要 DeepSeek 官方逐日费用导出；本机 token 和当前余额不能证明每天实际扣费。"}
    days = {d.isoformat(): None for d in day_range(start, end)}
    currencies = set()
    seen = set()
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not {"date", "actual_cost", "currency", "timezone"}.issubset(reader.fieldnames or []):
                raise UsageError("DeepSeek 账单列必须包含 date,actual_cost,currency,timezone。")
            for row in reader:
                key = date.fromisoformat(row["date"]).isoformat()
                cost = Decimal(row["actual_cost"])
                if not cost.is_finite() or cost < 0:
                    raise UsageError("DeepSeek 账单金额必须是有限非负数。")
                if row["timezone"] != timezone:
                    raise UsageError("DeepSeek 账单日桶时区与查询不同；无法从日汇总重新分桶。")
                if row["currency"] not in {"CNY", "USD"}:
                    raise UsageError("DeepSeek 账单需明确 CNY 或 USD，不自动换汇。")
                if key in seen:
                    raise UsageError("DeepSeek 账单存在重复日期；先从官方明细按日期和币种核对汇总。")
                seen.add(key)
                if key in days:
                    days[key] = {"actual_cost": str(cost)}
                    currencies.add(row["currency"])
    except (OSError, UnicodeError, csv.Error, ValueError, InvalidOperation, TypeError):
        raise UsageError("DeepSeek 账单不可读或格式错误；未输出原始内容。") from None
    if len(currencies) > 1:
        raise UsageError("DeepSeek 账单区间含多币种，不能直接相加。")
    observed = [r for r in days.values() if r is not None]
    result = {"status": "ok" if observed else "unavailable", "days": days,
              "currency": next(iter(currencies), None), "source": str(path),
              "basis": "imported_official_bill", "refreshed_at": None,
              "warnings": ["DeepSeek 来自已导入账单，不是实时查询；当日金额截至导出时点，重新导出后再刷新。"]}
    if observed:
        result["totals"] = {"actual_cost": str(sum((Decimal(r["actual_cost"]) for r in observed), Decimal(0)))}
    return result


def cost_markdown(report):
    pool, deepseek = report["codex_pool"], report["deepseek_cost"]
    def money(provider, row):
        if provider.get("status") == "error":
            return "查询失败"
        if provider.get("status") == "unavailable" and not provider.get("days"):
            return "账单未接入"
        if row is None:
            return "无记录"
        estimated = provider.get("basis") == "local_usage_official_rate_estimate"
        amount = row.get("estimated_cost" if estimated else "actual_cost")
        if amount is None:
            return "费用缺失"
        currency = provider.get("currency")
        if currency not in {"USD", "CNY"}:
            return "币种未确认"
        symbol = "$" if currency == "USD" else "¥"
        return f"{'≈' if estimated else ''}{symbol}{Decimal(amount):,.2f}"
    lines = [f"费用区间：{report['start']} 至 {report['end']}（{report['timezone']}）；查询时间：{report['queried_at']}。",
             "", "| 日期 | codex-pool 费用 | DeepSeek 费用 |", "|---|---:|---:|"]
    for day in day_range(date.fromisoformat(report["start"]), date.fromisoformat(report["end"])):
        key = day.isoformat()
        label = key + ("（今日未结束）" if key == report["today"] else "")
        lines.append(f"| {label} | {money(pool, pool.get('days', {}).get(key))} | {money(deepseek, deepseek.get('days', {}).get(key))} |")
    lines += [f"| 已取得费用合计 | {money(pool, pool.get('totals'))} | {money(deepseek, deepseek.get('totals'))} |", "",
              "codex-pool 为当前 key 的平台 actual_cost 费用；$ 为美元，¥ 为人民币，不跨币种合计。"]
    for name, provider in (("codex-pool", pool), ("DeepSeek", deepseek)):
        if provider.get("error"):
            lines.append(f"{name}：{provider['error']}")
        for warning in provider.get("warnings", []):
            lines.append(f"{name}：{warning}")
    return "\n".join(lines)


def markdown(report):
    if report.get("metric", "cost") == "cost":
        return cost_markdown(report)
    pool, deepseek = report["codex_pool"], report["deepseek"]
    lines = [
        f"统计区间：{report['start']} 至 {report['end']}（{report['timezone']}）；查询时间：{report['queried_at']}。",
        "", "| 日期 | codex-pool token | DeepSeek 本机 token |", "|---|---:|---:|",
    ]
    def cell(provider, day):
        if provider.get("status") == "error":
            return "查询失败"
        row = provider.get("days", {}).get(day)
        if row is None or row.get("requests", 0) == 0:
            return "无记录"
        return f"{row['total_tokens']:,}"
    for d in day_range(date.fromisoformat(report["start"]), date.fromisoformat(report["end"])):
        label = d.isoformat() + ("（截至查询时刻）" if d.isoformat() == report["today"] else "")
        lines.append(f"| {label} | {cell(pool, d.isoformat())} | {cell(deepseek, d.isoformat())} |")
    def total(provider):
        if provider.get("status") == "error":
            return "查询失败"
        rows = [r for r in provider.get("days", {}).values() if r is not None]
        return f"{sum(r['total_tokens'] for r in rows):,}" if any(r.get('requests', 0) for r in rows) else "无记录"
    lines += [f"| 已记录合计 | {total(pool)} | {total(deepseek)} |", "",
              "Token 总数包含未缓存输入、缓存读取/写入和输出；缓存只计一次。",
              "codex-pool 覆盖当前配置 key 的服务端记录；DeepSeek 仅覆盖本机已发现的会话日志，不代表账户全部消费。"]
    if pool.get("totals", {}).get("actual_cost") is not None:
        lines.append(f"pool 已记录费用：{pool['totals']['actual_cost']} {pool.get('currency') or '（币种未知）'}（平台 actual_cost 记账，非现金支出）。")
    for name, provider in (("codex-pool", pool), ("DeepSeek", deepseek)):
        if provider.get("error"):
            lines.append(f"{name}：{provider['error']}")
        for warning in provider.get("warnings", []):
            lines.append(f"{name}：{warning}")
    lines.append("输入/输出/缓存分项及覆盖详情见同命令 --format json。")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="查询最近一周每天 codex-pool 和 DeepSeek 花了多少钱。")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--end", type=date.fromisoformat)
    parser.add_argument("--last-week", action="store_true", help="上一个完整周一至周日")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--pool-profile", type=Path, default=Path.home()/".codex/lgj.config.toml")
    parser.add_argument("--dsh-root", type=Path, action="append", help="会话根目录，可多次；指定后替换默认根")
    parser.add_argument("--metric", choices=("cost", "tokens"), default="cost", help="默认显示费用；tokens 为辅助用量视图")
    parser.add_argument("--deepseek-bill", type=Path, help="可选：用官方逐日费用 CSV 替代默认的本机计价估算")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)
    try:
        tz = ZoneInfo(args.timezone)
        now = datetime.now(tz)
        start, end = window(args, now)
    except (UsageError, ZoneInfoNotFoundError) as exc:
        parser.error(str(exc))
    report = {"start": start.isoformat(), "end": end.isoformat(), "today": now.date().isoformat(),
              "timezone": args.timezone, "queried_at": now.isoformat(timespec="seconds"), "metric": args.metric}
    try:
        report["codex_pool"] = pool_usage(args.pool_profile.expanduser(), start, end, now, args.timezone)
    except UsageError as exc:
        report["codex_pool"] = {"status": "error", "error": str(exc)}
    roots = args.dsh_root or [Path.home()/".ae/workbench/home/sessions", Path.home()/".ae/workbench/home/sessions-archive", Path.home()/".dsh/sessions"]
    if args.metric == "cost":
        try:
            if args.deepseek_bill is not None:
                report["deepseek_cost"] = read_deepseek_bill(args.deepseek_bill.expanduser(), start, end, args.timezone)
            else:
                from deepseek_cost import PriceError, estimate_cost
                try:
                    report["deepseek_cost"] = estimate_cost([p.expanduser() for p in roots], start, end, tz)
                except PriceError as exc:
                    raise UsageError(str(exc)) from None
        except UsageError as exc:
            report["deepseek_cost"] = {"status": "error", "error": str(exc)}
        except Exception as exc:
            report["deepseek_cost"] = {"status": "error", "error": f"DeepSeek 计价失败（{type(exc).__name__}），未输出原始记录。"}
    if args.metric == "tokens":
        try:
            from deepseek_local import collect
            report["deepseek"] = collect([p.expanduser() for p in roots], start, end, tz)
        except Exception as exc:
            # Exception text may contain raw session data; emit only the class.
            report["deepseek"] = {"status": "error", "error": f"本机会话统计失败（{type(exc).__name__}）；检查日志格式与 zstandard 依赖。"}
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown(report))
    sources = ("codex_pool", "deepseek_cost" if args.metric == "cost" else "deepseek")
    return 2 if any(report[k].get("status") in {"error", "unavailable"} for k in sources) else 0


if __name__ == "__main__":
    sys.exit(main())
