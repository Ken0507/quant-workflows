"""Estimate local DeepSeek model charges with verified official peak/off-peak rates."""
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal
from html.parser import HTMLParser
import re
import urllib.request
from zoneinfo import ZoneInfo

from deepseek_local import collect

PRICE_URL = "https://api-docs.deepseek.com/zh-cn/quick_start/pricing"
UPDATES_URL = "https://api-docs.deepseek.com/zh-cn/updates"
EFFECTIVE_FROM = date(2026, 9, 10)
CHINA = ZoneInfo("Asia/Shanghai")
# Remaining 2026 official holiday periods after this price card's start date.
HOLIDAYS = ((date(2026, 9, 25), date(2026, 9, 27)), (date(2026, 10, 1), date(2026, 10, 7)))
RATES = {
    "deepseek-flash": {"off_peak": ("1", "0.02", "4"), "peak": ("2", "0.04", "8")},
    "deepseek-v4-pro": {"off_peak": ("4.5", "0.15", "13.5"), "peak": ("9", "0.30", "27")},
}
ALIASES = {"deepseek-flash": "deepseek-flash", "deepseek-v4-flash": "deepseek-flash",
           "deepseek-v4-flash-vision-exp": "deepseek-flash", "deepseek-v4-pro": "deepseek-v4-pro"}


class PriceError(Exception):
    pass


class PriceTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth, self.cell, self.row = 0, None, []
        self.rows, self.text = [], []

    def handle_starttag(self, tag, attrs):
        if tag == "table": self.depth += 1
        if self.depth and tag == "tr": self.row = []
        if self.depth and tag in {"td", "th"}: self.cell = ""

    def handle_data(self, text):
        self.text.append(text)
        if self.cell is not None: self.cell += text

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(re.sub(r"\s+", "", self.cell)); self.cell = None
        if self.depth and tag == "tr": self.rows.append(self.row)
        if tag == "table": self.depth -= 1


def validate_price_page(html):
    """Require the supported table and schedule; a changed tariff is never silently reused."""
    page = PriceTable(); page.feed(html)
    text = re.sub(r"\s+", "", "".join(page.text))
    if not all(s in text for s in ("北京时间周一至周五", "不含中国法定节假日", "9:00-12:00", "14:00-18:00")):
        raise PriceError("官方峰谷时间规则变化，需更新价卡后重算。")
    if not any(len(r) == 3 and r[0] == "模型" and r[1].startswith("deepseek-flash") and r[2] == "deepseek-v4-pro" for r in page.rows):
        raise PriceError("官方模型价格列变化，需核对模型映射。")
    expected = [(("0.02", "0.15"), "空闲时段"), (("0.04", "0.30"), "高峰时段"),
                (("1", "4.5"), "空闲时段"), (("2", "9.0"), "高峰时段"),
                (("4", "13.5"), "空闲时段"), (("8", "27.0"), "高峰时段")]
    found = [r for r in page.rows if len(r) >= 3 and r[-3] in {"空闲时段", "高峰时段"}]
    if len(found) != 6:
        raise PriceError("官方价格表结构变化，未自动计价。")
    for row, (numbers, period) in zip(found, expected):
        if row[-3] != period or any(not v.endswith("元") for v in row[-2:]):
            raise PriceError("官方计价币种或峰谷规则变化，未自动计价。")
        try:
            same = tuple(Decimal(v[:-1]) for v in row[-2:]) == tuple(map(Decimal, numbers))
        except Exception:
            same = False
        if not same:
            raise PriceError("官方单价已变化，需新增生效日期价卡，不能用旧价。")


def verify_current_prices():
    try:
        with urllib.request.urlopen(PRICE_URL, timeout=25) as response:
            html = response.read(2_000_000).decode("utf-8")
    except Exception:
        raise PriceError("官方价目页暂时不可读，未使用未经核对的价格估算。") from None
    validate_price_page(html)
    return datetime.now(CHINA).isoformat(timespec="seconds")


def price_attempt(attempt):
    """Return CNY and band, using the locally recorded settlement time as a proxy."""
    provider, model = attempt["route"]
    stamp = datetime.fromtimestamp(attempt["time"] / 1000, CHINA)
    day = stamp.date()
    if provider != "deepseek-official" or model not in ALIASES:
        return None, "模型或通道不在已验证价卡中"
    if day < EFFECTIVE_FROM or day.year != 2026:
        return None, "日期超出已核对的历史价卡或节假日日历"
    usage = attempt["usage"]
    if any(usage.get(k) is None for k in ("input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens")):
        return None, "缓存或输出分项缺失"
    if usage["cache_write_tokens"] != 0:
        return None, "缓存写入计价尚未核实"
    holiday = any(start <= day <= end for start, end in HOLIDAYS)
    peak = day.weekday() < 5 and not holiday and (9 <= stamp.hour < 12 or 14 <= stamp.hour < 18)
    band = "peak" if peak else "off_peak"
    rates = tuple(map(Decimal, RATES[ALIASES[model]][band]))
    tokens = (usage["input_tokens"], usage["cache_read_tokens"], usage["output_tokens"])
    return sum((n * r for n, r in zip(tokens, rates)), Decimal(0)) / Decimal(1_000_000), band


def estimate_cost(roots, start, end, tz):
    checked_at = verify_current_prices()
    days = { (start + timedelta(days=i)).isoformat(): None for i in range((end-start).days+1) }
    rejected = Counter()
    def on_attempt(attempt):
        key = datetime.fromtimestamp(attempt["time"] / 1000, tz).date().isoformat()
        row = days[key]
        if row is None:
            row = days[key] = {"estimated_cost": Decimal(0), "priced_requests": 0,
                               "unpriced_requests": 0, "peak_requests": 0, "off_peak_requests": 0}
        amount, band = price_attempt(attempt)
        if amount is None:
            row["unpriced_requests"] += 1; rejected[band] += 1
        else:
            row["estimated_cost"] += amount; row["priced_requests"] += 1
            row[band + "_requests"] += 1
    local = collect(roots, start, end, tz, on_attempt=on_attempt)
    if local["status"] == "error":
        return {"status": "error", "error": local["error"], "warnings": local["warnings"]}
    total = sum((r["estimated_cost"] for r in days.values() if r), Decimal(0))
    priced = sum(r["priced_requests"] for r in days.values() if r)
    for row in days.values():
        if row is not None:
            row["estimated_cost"] = str(row["estimated_cost"]) if row["priced_requests"] else None
    warnings = ["DeepSeek 为本机已记录请求按官方模型价估算（≈），不含缺失用量或其他机器，不是账户扣费流水。",
                "按北京时间结算记录时刻划分峰谷；跨计费边界、折扣和赠送额度可能与账单不同。",
                "只估算模型 token 费用；Search/Fetch 等独立工具费用未纳入。"]
    warnings += local["warnings"][1:]
    warnings += [f"{n} 次请求未计价：{reason}。" for reason, n in sorted(rejected.items())]
    return {"status": "partial", "basis": "local_usage_official_rate_estimate", "currency": "CNY",
            "days": days, "totals": {"estimated_cost": str(total) if priced else None},
            "coverage": local["coverage"], "warnings": warnings,
            "pricing": {"source": PRICE_URL, "history_source": UPDATES_URL,
                        "verified_at": checked_at, "effective_from": EFFECTIVE_FROM.isoformat(),
                        "calendar_year": 2026, "timestamp_basis": "local_settlement_time", "rates_cny_per_million": RATES}}
