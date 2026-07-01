#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intraday trading analysis for Benchmark100Trader.

Parses strategy.log and session CSV to produce a text report covering:
  1. Overview  2. PnL  3. Roundtrip detail  4. Cancel rates
  5. Signal scores  6. Latency  7. Per-code activity

Usage:
    python3 analyze_intraday.py --log strategy.log --csv session_*.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Regex patterns for strategy log
# ---------------------------------------------------------------------------
RE_ENTRY = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\].*"
    r"\[Benchmark100Trader\] ENTRY,(\w+),(\d+),ref=(\d+),vol=(\d+),"
    r"px=([0-9.]+),.*?score=([0-9.-]+),thr=([0-9.-]+),lat_us=(\d+)"
)
RE_FILL = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\].*"
    r"\[Benchmark100Trader\] FILL,(\w+),ref=(\d+),dir=(\w+),vol=(\d+),px=([0-9.]+)"
)
RE_EXIT = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\].*"
    r"\[Benchmark100Trader\] EXIT,(\w+),(\d+),ref=(\d+),vol=(\d+),"
    r"px=([0-9.]+),.*?score=([0-9.-]+),thr=([0-9.-]+),lat_us=(\d+)"
)
RE_CANCEL = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\].*"
    r"\[Benchmark100Trader\] CANCEL,(\w+),(\d+),n=(\d+),score=([0-9.-]+),bid=([0-9.]+)"
)
RE_EXIT_REPRICE = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\].*"
    r"\[Benchmark100Trader\] EXIT_REPRICE,(\d+),ref=(\d+),"
    r"old_px=([0-9.]+),.*?score=([0-9.-]+)"
)
# ENTRY order repricing (distinct from EXIT_REPRICE)
# Format: REPRICE,<code>,ref=<ref>,old=<px>,new=<px>,score=<score>
RE_ENTRY_REPRICE = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\].*"
    r"\[Benchmark100Trader\] REPRICE,(\d+),ref=(\d+),"
    r"old=([0-9.]+),new=([0-9.]+),score=([0-9.-]+)"
)
RE_INIT_BALANCE = re.compile(r"Initial Balance:\s*([0-9.]+)")
RE_PARAM = re.compile(
    r"\[Benchmark100Trader\] Init|"
    r"^\s*(open_bps|open_market_bps|hold_bps|score_hysteresis_bps|"
    r"cancel_threshold_bps|target_vol|tick_size|entry_aggressive_bps|"
    r"decision_on_update_only|cancel_reduce_scheme|exit_reprice_tolerance_bps)=(.+)"
)
RE_UNIVERSE = re.compile(r"Universe:\s*(\d+)\s*codes")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse_log(path: str) -> dict:
    """Parse strategy.log and return structured events."""
    entries: List[dict] = []
    fills: List[dict] = []
    unknown_fills: List[dict] = []
    exits: List[dict] = []
    cancels: List[dict] = []
    reprices: List[dict] = []        # EXIT_REPRICE events
    entry_reprices: List[dict] = []  # REPRICE (entry order repricing) events
    params: Dict[str, str] = {}
    init_balance: Optional[float] = None
    universe_size: Optional[int] = None

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            # ENTRY
            m = RE_ENTRY.search(line)
            if m:
                entries.append(dict(
                    ts=m.group(1), type=m.group(2), code=m.group(3),
                    ref=int(m.group(4)), vol=int(m.group(5)),
                    px=float(m.group(6)),
                    score=float(m.group(7)), thr=float(m.group(8)),
                    lat_us=int(m.group(9)),
                ))
                continue

            # FILL
            m = RE_FILL.search(line)
            if m:
                d = dict(
                    ts=m.group(1), code=m.group(2), ref=int(m.group(3)),
                    dir=m.group(4), vol=int(m.group(5)),
                    px=float(m.group(6)),
                )
                (unknown_fills if d["code"] == "UNKNOWN" else fills).append(d)
                continue

            # EXIT
            m = RE_EXIT.search(line)
            if m:
                exits.append(dict(
                    ts=m.group(1), type=m.group(2), code=m.group(3),
                    ref=int(m.group(4)), vol=int(m.group(5)),
                    px=float(m.group(6)), score=float(m.group(7)),
                    thr=float(m.group(8)), lat_us=int(m.group(9)),
                ))
                continue

            # CANCEL
            m = RE_CANCEL.search(line)
            if m:
                cancels.append(dict(
                    ts=m.group(1), type=m.group(2), code=m.group(3),
                    n=int(m.group(4)), score=float(m.group(5)),
                    bid=float(m.group(6)),
                ))
                continue

            # EXIT_REPRICE (must be checked before ENTRY_REPRICE)
            m = RE_EXIT_REPRICE.search(line)
            if m:
                reprices.append(dict(
                    ts=m.group(1), code=m.group(2), ref=int(m.group(3)),
                    old_px=float(m.group(4)), score=float(m.group(5)),
                ))
                continue

            # ENTRY_REPRICE: REPRICE,<code>,ref=...,old=...,new=...,score=...
            m = RE_ENTRY_REPRICE.search(line)
            if m:
                entry_reprices.append(dict(
                    ts=m.group(1), code=m.group(2), ref=int(m.group(3)),
                    old_px=float(m.group(4)), new_px=float(m.group(5)),
                    score=float(m.group(6)),
                ))
                continue

            # Init balance
            m = RE_INIT_BALANCE.search(line)
            if m:
                init_balance = float(m.group(1))
                continue

            # Universe
            m = RE_UNIVERSE.search(line)
            if m:
                universe_size = int(m.group(1))
                continue

            # Params (simple key=value lines after [Benchmark100Trader] Init)
            m2 = re.match(r"^\s*(open_bps|open_market_bps|hold_bps|score_hysteresis_bps|"
                          r"cancel_threshold_bps|target_vol|tick_size|entry_aggressive_bps|"
                          r"decision_on_update_only|cancel_reduce_scheme|exit_reprice_tolerance_bps)"
                          r"=(.+)", line.strip())
            if m2:
                params[m2.group(1)] = m2.group(2).strip()

    return dict(
        entries=entries, fills=fills, unknown_fills=unknown_fills,
        exits=exits, cancels=cancels, reprices=reprices,
        entry_reprices=entry_reprices,
        params=params, init_balance=init_balance,
        universe_size=universe_size,
    )


def parse_csv(path: str) -> List[dict]:
    """Parse session CSV into list of row dicts."""
    rows: List[dict] = []
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------
def _ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")


def _percentile(arr: List[float], p: float) -> float:
    s = sorted(arr)
    idx = min(int(len(s) * p), len(s) - 1)
    return s[idx]


def _pct_stats(arr: List[float], name: str, unit: str = "us") -> str:
    if not arr:
        return f"  {name}: no data\n"
    s = sorted(arr)
    n = len(s)
    lines = [f"  {name} (n={n}):"]
    for label, idx in [("Min", 0), ("P25", int(n * 0.25)), ("P50", n // 2),
                       ("P75", int(n * 0.75)), ("P90", min(int(n * 0.9), n - 1)),
                       ("P99", min(int(n * 0.99), n - 1)), ("Max", n - 1)]:
        v = s[idx]
        extra = f" ({v / 1000:.2f} ms)" if unit == "us" and v >= 100 else ""
        lines.append(f"    {label:>4}: {v:>8.0f} {unit}{extra}")
    lines.append(f"    Mean: {sum(s) / n:>8.0f} {unit}")
    return "\n".join(lines) + "\n"


def build_roundtrips(fills: List[dict], ref_to_entry: dict, ref_to_exit: dict) -> Tuple[List[dict], dict]:
    """Match BUY/SELL fills by code to form roundtrips. Returns (roundtrips, open_positions)."""
    code_buys: Dict[str, list] = defaultdict(list)
    code_sells: Dict[str, list] = defaultdict(list)
    for f in fills:
        if f["dir"] == "BUY":
            code_buys[f["code"]].append(f)
        else:
            code_sells[f["code"]].append(f)

    roundtrips: List[dict] = []
    open_positions: Dict[str, list] = {}

    all_codes = sorted(set(list(code_buys.keys()) + list(code_sells.keys())))
    for code in all_codes:
        buys = code_buys[code]
        sells = code_sells[code]
        n = min(len(buys), len(sells))
        for i in range(n):
            b, s = buys[i], sells[i]
            pnl = (s["px"] - b["px"]) * b["vol"]
            pnl_bps = (s["px"] / b["px"] - 1) * 10000 if b["px"] else 0
            bt, st = _ts(b["ts"]), _ts(s["ts"])
            hold_ms = (st - bt).total_seconds() * 1000
            entry_info = ref_to_entry.get(b["ref"], {})
            exit_info = ref_to_exit.get(s["ref"], {})
            roundtrips.append(dict(
                code=code, buy_px=b["px"], sell_px=s["px"],
                buy_ts=b["ts"], sell_ts=s["ts"],
                vol=b["vol"], pnl=pnl, pnl_bps=pnl_bps,
                hold_ms=hold_ms,
                entry_score=entry_info.get("score"),
                entry_lat_us=entry_info.get("lat_us"),
                exit_lat_us=exit_info.get("lat_us"),
                exit_score=exit_info.get("score"),
            ))
        if len(buys) > n:
            open_positions[code] = buys[n:]
    return roundtrips, open_positions


def calc_csv_latencies(csv_rows: List[dict]) -> dict:
    """Calculate order lifecycle latencies from CSV nanosecond timestamps."""
    ref_submit: Dict[str, int] = {}
    ref_ack: Dict[str, int] = {}
    ref_accepted: Dict[str, int] = {}
    ref_fill: Dict[str, int] = {}
    ref_code: Dict[str, str] = {}
    ref_dir: Dict[str, str] = {}

    for r in csv_rows:
        ref = r.get("order_ref", "0")
        if ref == "0":
            continue
        ts = int(r["local_ts"])
        evt = r["event_type"]
        if evt == "ORDER_SUBMIT":
            ref_submit[ref] = ts
            ref_code[ref] = r.get("security_id", "?")
            ref_dir[ref] = r.get("direction", "?")
        elif evt == "ORDER_ACK":
            ref_ack[ref] = ts
        elif evt == "ORDER_STATUS" and r.get("status") == "Accepted":
            if ref not in ref_accepted:
                ref_accepted[ref] = ts
        elif evt == "TRADE_REPORT":
            ref_fill[ref] = ts

    submit_to_ack_us: List[float] = []
    submit_to_accepted_us: List[float] = []
    submit_to_fill_us: List[float] = []

    for ref, sub in ref_submit.items():
        if ref in ref_ack:
            submit_to_ack_us.append((ref_ack[ref] - sub) / 1e3)
        if ref in ref_accepted:
            submit_to_accepted_us.append((ref_accepted[ref] - sub) / 1e3)
        if ref in ref_fill:
            submit_to_fill_us.append((ref_fill[ref] - sub) / 1e3)

    # Per-fill detail
    fill_details: List[dict] = []
    for ref in sorted(ref_fill.keys(), key=lambda x: int(x)):
        sub = ref_submit.get(ref)
        if not sub:
            continue
        ack = ref_ack.get(ref)
        acc = ref_accepted.get(ref)
        fil = ref_fill[ref]
        fill_details.append(dict(
            ref=ref, code=ref_code.get(ref, "?"),
            direction=ref_dir.get(ref, "?"),
            submit_to_ack_ms=(ack - sub) / 1e6 if ack else None,
            submit_to_accepted_ms=(acc - sub) / 1e6 if acc else None,
            submit_to_fill_ms=(fil - sub) / 1e6,
        ))

    return dict(
        submit_to_ack_us=submit_to_ack_us,
        submit_to_accepted_us=submit_to_accepted_us,
        submit_to_fill_us=submit_to_fill_us,
        fill_details=fill_details,
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(log_data: dict, csv_rows: List[dict]) -> str:
    """Generate full text report."""
    out: List[str] = []

    entries = log_data["entries"]
    fills = log_data["fills"]
    unknown_fills = log_data["unknown_fills"]
    exits = log_data["exits"]
    cancels = log_data["cancels"]
    reprices = log_data["reprices"]              # EXIT_REPRICE
    entry_reprices = log_data["entry_reprices"]  # REPRICE (entry order repricing)
    params = log_data["params"]
    init_balance = log_data["init_balance"]
    universe_size = log_data["universe_size"]

    ref_to_entry = {e["ref"]: e for e in entries}
    ref_to_exit = {e["ref"]: e for e in exits}
    filled_entry_refs = {f["ref"] for f in fills if f["dir"] == "BUY"}
    filled_exit_refs = {f["ref"] for f in fills if f["dir"] == "SELL"}

    # ── Section 1: Overview ──
    out.append("=" * 70)
    out.append("1. 基本概况")
    out.append("=" * 70)
    out.append(f"  策略: Benchmark100Trader")
    if universe_size:
        out.append(f"  Universe: {universe_size} codes")
    if init_balance:
        out.append(f"  初始余额: {init_balance:,.2f} 元")
    if params:
        p_str = ", ".join(f"{k}={v}" for k, v in params.items())
        out.append(f"  参数: {p_str}")

    all_ts = [e["ts"] for e in entries] + [f["ts"] for f in fills] + [e["ts"] for e in exits]
    if all_ts:
        t0 = _ts(min(all_ts))
        t1 = _ts(max(all_ts))
        dur = (t1 - t0).total_seconds()
        out.append(f"  交易窗口: {min(all_ts)} ~ {max(all_ts)}")
        out.append(f"  活跃时长: {dur:.1f}s ({dur / 60:.1f}min)")

    out.append(f"\n  ENTRY 下单: {len(entries)} 次")
    out.append(f"  ENTRY_REPRICE: {len(entry_reprices)} 次")
    out.append(f"  EXIT  下单: {len(exits)} 次")
    out.append(f"  EXIT_REPRICE: {len(reprices)} 次")
    out.append(f"  FILL (已知): {len(fills)} 次")
    out.append(f"  FILL (UNKNOWN/其他策略): {len(unknown_fills)} 次")
    out.append(f"  CANCEL: {len(cancels)} 次")

    # ── Section 2: PnL ──
    roundtrips, open_positions = build_roundtrips(fills, ref_to_entry, ref_to_exit)

    out.append(f"\n{'=' * 70}")
    out.append("2. PnL 汇总")
    out.append("=" * 70)

    if not roundtrips:
        out.append("  暂无完成的 Roundtrip。")
    else:
        total_pnl = sum(r["pnl"] for r in roundtrips)
        total_turnover = sum(r["buy_px"] * r["vol"] + r["sell_px"] * r["vol"] for r in roundtrips)
        wins = [r for r in roundtrips if r["pnl"] > 0]
        pnls = [r["pnl"] for r in roundtrips]
        bps_list = [r["pnl_bps"] for r in roundtrips]

        out.append(f"  完成 Roundtrip: {len(roundtrips)} 笔")
        out.append(f"  总 PnL: {total_pnl:+.2f} 元")
        out.append(f"  总成交金额: {total_turnover:,.0f} 元")
        if total_turnover > 0:
            out.append(f"  收益率: {total_pnl / total_turnover * 10000:.2f} bps (相对成交额)")
        out.append(f"  胜率: {len(wins)}/{len(roundtrips)} = {len(wins) / len(roundtrips) * 100:.1f}%")
        out.append(f"  最大盈利: {max(pnls):+.2f} 元, 最大亏损: {min(pnls):+.2f} 元")
        out.append(f"  均值: {sum(pnls) / len(pnls):+.2f} 元/笔, {sum(bps_list) / len(bps_list):+.1f} bps/笔")

        code_pnl: Dict[str, float] = defaultdict(float)
        code_cnt: Dict[str, int] = defaultdict(int)
        for r in roundtrips:
            code_pnl[r["code"]] += r["pnl"]
            code_cnt[r["code"]] += 1
        out.append(f"\n  各代码 PnL:")
        for code in sorted(code_pnl.keys()):
            out.append(f"    {code}: {code_pnl[code]:+.2f} 元 ({code_cnt[code]} 笔)")

    if open_positions:
        out.append(f"\n  未平仓头寸:")
        for code, buys in open_positions.items():
            for b in buys:
                out.append(f"    {code}: 持有 {b['vol']} 张 BUY @{b['px']:.3f} ({b['ts'][-12:]})")

    # ── Section 3: Roundtrip detail ──
    out.append(f"\n{'=' * 70}")
    out.append("3. Roundtrip 逐笔明细")
    out.append("=" * 70)

    if not roundtrips:
        out.append("  暂无。")
    else:
        cur_code = None
        rt_idx = defaultdict(int)
        for r in roundtrips:
            if r["code"] != cur_code:
                cur_code = r["code"]
            rt_idx[cur_code] += 1
            idx = rt_idx[cur_code]
            e_score = f"{r['entry_score']:.2f}" if r["entry_score"] is not None else "?"
            e_lat = f"{r['entry_lat_us']}" if r["entry_lat_us"] is not None else "?"
            x_lat = f"{r['exit_lat_us']}" if r["exit_lat_us"] is not None else "?"
            result = "WIN" if r["pnl"] > 0 else "LOSS"
            out.append(
                f"  {cur_code} RT#{idx}: "
                f"BUY@{r['buy_px']:.3f}({r['buy_ts'][-12:]}) "
                f"-> SELL@{r['sell_px']:.3f}({r['sell_ts'][-12:]})  "
                f"PnL={r['pnl']:+.2f}元 ({r['pnl_bps']:+.1f}bps)  "
                f"hold={r['hold_ms']:.0f}ms  "
                f"score={e_score}  "
                f"entry_lat={e_lat}us exit_lat={x_lat}us  "
                f"[{result}]"
            )

    # ── Section 4: Cancel rates ──
    out.append(f"\n{'=' * 70}")
    out.append("4. 撤单率分析")
    out.append("=" * 70)

    # ENTRY
    entry_total = len(entries)
    entry_filled = len(filled_entry_refs)
    entry_cancelled = entry_total - entry_filled
    entry_rate = entry_cancelled / entry_total * 100 if entry_total else 0
    out.append(f"\n  ─── ENTRY 撤单率 ───")
    out.append(f"    下单: {entry_total}, 成交: {entry_filled}, 撤单: {entry_cancelled}, 撤单率: {entry_rate:.1f}%")

    code_entry_total: Dict[str, int] = defaultdict(int)
    code_entry_filled: Dict[str, int] = defaultdict(int)
    code_entry_reprice_cnt: Dict[str, int] = defaultdict(int)
    for e in entries:
        code_entry_total[e["code"]] += 1
    for f in fills:
        if f["dir"] == "BUY":
            code_entry_filled[f["code"]] += 1
    for r in entry_reprices:
        code_entry_reprice_cnt[r["code"]] += 1

    out.append(f"    {'代码':>8}  {'下单':>5}  {'成交':>5}  {'撤单':>5}  {'撤单率':>8}  {'REPRICE':>8}")
    for code in sorted(code_entry_total.keys()):
        t = code_entry_total[code]
        fi = code_entry_filled.get(code, 0)
        c = t - fi
        rp = code_entry_reprice_cnt.get(code, 0)
        out.append(f"    {code:>8}  {t:>5}  {fi:>5}  {c:>5}  {c / t * 100 if t else 0:>7.1f}%  {rp:>8}")

    # EXIT
    exit_total = len(exits)
    exit_filled = len(filled_exit_refs)
    exit_cancelled = exit_total - exit_filled
    exit_rate = exit_cancelled / exit_total * 100 if exit_total else 0
    out.append(f"\n  ─── EXIT 撤单率 ───")
    out.append(f"    下单: {exit_total}, 成交: {exit_filled}, 撤单: {exit_cancelled}, 撤单率: {exit_rate:.1f}%")

    code_exit_total: Dict[str, int] = defaultdict(int)
    code_exit_filled: Dict[str, int] = defaultdict(int)
    for e in exits:
        code_exit_total[e["code"]] += 1
    for f in fills:
        if f["dir"] == "SELL":
            code_exit_filled[f["code"]] += 1

    reprice_cnt: Dict[str, int] = defaultdict(int)
    for r in reprices:
        reprice_cnt[r["code"]] += 1

    out.append(f"    {'代码':>8}  {'下单':>5}  {'成交':>5}  {'撤单':>5}  {'撤单率':>8}  {'REPRICE':>8}")
    for code in sorted(code_exit_total.keys()):
        t = code_exit_total[code]
        fi = code_exit_filled.get(code, 0)
        c = t - fi
        rp = reprice_cnt.get(code, 0)
        out.append(f"    {code:>8}  {t:>5}  {fi:>5}  {c:>5}  {c / t * 100 if t else 0:>7.1f}%  {rp:>8}")

    # Overall
    total_orders = entry_total + exit_total
    total_filled_all = entry_filled + exit_filled
    total_cancelled_all = total_orders - total_filled_all
    overall_rate = total_cancelled_all / total_orders * 100 if total_orders else 0
    out.append(f"\n  ─── 综合 ───")
    out.append(f"    总下单: {total_orders}, 总成交: {total_filled_all}, 综合撤单率: {overall_rate:.1f}%")
    if total_filled_all:
        out.append(f"    撤成比: {total_cancelled_all / total_filled_all:.1f}:1")

    # Cancel reasons
    cancel_reason: Dict[str, int] = defaultdict(int)
    cancel_reason_codes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in cancels:
        cancel_reason[c["type"]] += 1
        cancel_reason_codes[c["type"]][c["code"]] += 1

    out.append(f"\n  ─── 撤单原因 ───")
    for reason in sorted(cancel_reason.keys(), key=lambda x: -cancel_reason[x]):
        cnt = cancel_reason[reason]
        pct = cnt / len(cancels) * 100 if cancels else 0
        codes_str = ", ".join(
            f"{c}:{n}" for c, n in sorted(cancel_reason_codes[reason].items(), key=lambda x: -x[1])
        )
        out.append(f"    {reason:>20}: {cnt:>3} ({pct:.1f}%)  [{codes_str}]")

    out.append(f"\n  EXIT_REPRICE 总计: {len(reprices)} 次")
    for code, cnt in sorted(reprice_cnt.items(), key=lambda x: -x[1]):
        out.append(f"    {code}: {cnt} 次")

    # ── Section 5: Signal scores ──
    out.append(f"\n{'=' * 70}")
    out.append("5. 信号 Score 分析")
    out.append("=" * 70)

    all_entry_scores = [e["score"] for e in entries]
    filled_entry_scores = [e["score"] for e in entries if e["ref"] in filled_entry_refs]
    cancelled_entry_scores = [e["score"] for e in entries if e["ref"] not in filled_entry_refs]

    out.append(_pct_stats(all_entry_scores, "全部 ENTRY score", "bps"))
    out.append(_pct_stats(filled_entry_scores, "成交 ENTRY score", "bps"))
    out.append(_pct_stats(cancelled_entry_scores, "撤单 ENTRY score", "bps"))

    # Score vs PnL
    if roundtrips:
        out.append("  ─── score vs PnL ───")
        out.append(f"    {'代码':>8}  {'score':>8}  {'entry_px':>10}  {'exit_px':>10}  {'PnL_bps':>10}  {'结果':>6}")
        for r in roundtrips:
            s = f"{r['entry_score']:.2f}" if r["entry_score"] is not None else "?"
            result = "WIN" if r["pnl"] > 0 else "LOSS"
            out.append(
                f"    {r['code']:>8}  {s:>8}  {r['buy_px']:>10.3f}  "
                f"{r['sell_px']:>10.3f}  {r['pnl_bps']:>+10.1f}  {result:>6}"
            )

    exit_scores = [e["score"] for e in exits]
    filled_exit_scores = [e["score"] for e in exits if e["ref"] in filled_exit_refs]
    out.append("")
    out.append(_pct_stats(exit_scores, "全部 EXIT score", "bps"))
    out.append(_pct_stats(filled_exit_scores, "成交 EXIT score", "bps"))

    # ── Section 6: Latency ──
    out.append(f"{'=' * 70}")
    out.append("6. 延迟分析")
    out.append("=" * 70)

    entry_lats = [e["lat_us"] for e in entries]
    exit_lats = [e["lat_us"] for e in exits]
    out.append(_pct_stats(entry_lats, "ENTRY 决策延迟 (signal -> order submit)"))
    out.append(_pct_stats(exit_lats, "EXIT  决策延迟 (signal -> order submit)"))

    # Per-code entry latency
    code_entry_lats: Dict[str, list] = defaultdict(list)
    for e in entries:
        code_entry_lats[e["code"]].append(e["lat_us"])
    out.append("  ─── 各代码 ENTRY 延迟 ───")
    out.append(f"    {'代码':>8}  {'次数':>5}  {'Min':>8}  {'P50':>8}  {'Mean':>8}  {'Max':>8} (us)")
    for code in sorted(code_entry_lats.keys()):
        lats = sorted(code_entry_lats[code])
        n = len(lats)
        out.append(
            f"    {code:>8}  {n:>5}  {lats[0]:>8}  {lats[n // 2]:>8}  "
            f"{sum(lats) // n:>8}  {lats[-1]:>8}"
        )

    code_exit_lats: Dict[str, list] = defaultdict(list)
    for e in exits:
        code_exit_lats[e["code"]].append(e["lat_us"])
    out.append(f"\n  ─── 各代码 EXIT 延迟 ───")
    out.append(f"    {'代码':>8}  {'次数':>5}  {'Min':>8}  {'P50':>8}  {'Mean':>8}  {'Max':>8} (us)")
    for code in sorted(code_exit_lats.keys()):
        lats = sorted(code_exit_lats[code])
        n = len(lats)
        out.append(
            f"    {code:>8}  {n:>5}  {lats[0]:>8}  {lats[n // 2]:>8}  "
            f"{sum(lats) // n:>8}  {lats[-1]:>8}"
        )

    # CSV latencies
    if csv_rows:
        csv_lat = calc_csv_latencies(csv_rows)
        out.append(f"\n  ─── 下单链路延迟 (from CSV nanosecond timestamps) ───")
        out.append(_pct_stats(csv_lat["submit_to_ack_us"], "ORDER_SUBMIT -> ORDER_ACK (柜台确认)"))
        out.append(_pct_stats(csv_lat["submit_to_accepted_us"], "ORDER_SUBMIT -> Accepted (交易所确认)"))
        out.append(_pct_stats(csv_lat["submit_to_fill_us"], "ORDER_SUBMIT -> TRADE_REPORT (下单到成交)"))

        if csv_lat["fill_details"]:
            out.append("  ─── 成交订单完整链路 ───")
            out.append(
                f"    {'ref':>10}  {'代码':>8}  {'方向':>5}  "
                f"{'submit->ack':>14}  {'submit->accept':>16}  {'submit->fill':>14}"
            )
            for d in csv_lat["fill_details"]:
                s2a = f"{d['submit_to_ack_ms']:.2f}ms" if d["submit_to_ack_ms"] is not None else "?"
                s2acc = f"{d['submit_to_accepted_ms']:.2f}ms" if d["submit_to_accepted_ms"] is not None else "?"
                s2f = f"{d['submit_to_fill_ms']:.2f}ms"
                out.append(
                    f"    {d['ref']:>10}  {d['code']:>8}  {d['direction']:>5}  "
                    f"{s2a:>14}  {s2acc:>16}  {s2f:>14}"
                )

    # ── Section 7: Per-code activity ──
    out.append(f"\n{'=' * 70}")
    out.append("7. 各代码活跃度")
    out.append("=" * 70)

    code_entries_cnt: Dict[str, int] = defaultdict(int)
    code_fills_cnt: Dict[str, int] = defaultdict(int)
    code_cancels_cnt: Dict[str, int] = defaultdict(int)
    for e in entries:
        code_entries_cnt[e["code"]] += 1
    for f in fills:
        code_fills_cnt[f["code"]] += 1
    for c in cancels:
        code_cancels_cnt[c["code"]] += 1

    all_codes = sorted(set(
        list(code_entries_cnt.keys()) + list(code_fills_cnt.keys()) + list(code_cancels_cnt.keys())
    ))
    out.append(f"  {'代码':>8}  {'ENTRY':>6}  {'FILL':>5}  {'CANCEL':>7}  {'成交率':>8}")
    for code in all_codes:
        ne = code_entries_cnt[code]
        nf = code_fills_cnt[code]
        nc = code_cancels_cnt[code]
        fill_rate = nf / ne * 100 if ne > 0 else 0
        out.append(f"  {code:>8}  {ne:>6}  {nf:>5}  {nc:>7}  {fill_rate:>7.1f}%")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Intraday trading analysis for Benchmark100Trader")
    ap.add_argument("--log", required=True, help="Path to strategy.log")
    ap.add_argument("--csv", required=False, default=None, help="Path to session CSV")
    ap.add_argument("--date", required=False, default=None, help="Date label (YYYYMMDD)")
    args = ap.parse_args()

    log_path = args.log
    csv_path = args.csv

    if not Path(log_path).exists():
        print(f"ERROR: Log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing log: {log_path}")
    log_data = parse_log(log_path)

    csv_rows: List[dict] = []
    if csv_path and Path(csv_path).exists():
        print(f"Parsing CSV: {csv_path}")
        csv_rows = parse_csv(csv_path)
    else:
        print("No session CSV provided or file not found; skipping CSV latency analysis.")

    date_label = args.date or "today"
    header = f"Benchmark100Trader 盘中交易分析 — {date_label}"
    print()
    print("=" * 70)
    print(header)
    print("=" * 70)
    print()

    report = generate_report(log_data, csv_rows)
    print(report)


if __name__ == "__main__":
    main()
