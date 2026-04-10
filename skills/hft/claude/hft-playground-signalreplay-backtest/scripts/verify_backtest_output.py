#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


REQUIRED_FILES = [
    "report.md",
    "metrics.csv",
    "dashboard.png",
    "rss_guard_profile.json",
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify SignalReplay batch-backtest output directory.")
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()

    out = args.output_dir
    if not out.exists() or not out.is_dir():
        raise SystemExit(f"Not a directory: {out}")

    missing = [f for f in REQUIRED_FILES if not (out / f).exists()]
    if missing:
        raise SystemExit(f"Missing files under {out}: {missing}")

    metrics_path = out / "metrics.csv"
    df = pd.read_csv(metrics_path)

    rt = df.get("RT Count")
    no_trade_days = int((rt == 0).sum()) if rt is not None else None

    gross = float(df["Daily PnL"].sum())
    fee = float(df["Daily Fee"].sum())
    net = gross - fee

    rss_profile_path = out / "rss_guard_profile.json"
    rss_profile = json.loads(rss_profile_path.read_text(encoding="utf-8"))

    print(f"output_dir: {out}")
    print(f"rows(days): {len(df)}")
    if no_trade_days is not None:
        print(f"no_trade_days: {no_trade_days}")
    print(f"gross_pnl(sum Daily PnL): {gross:,.2f}")
    print(f"fee(sum Daily Fee):       {fee:,.2f}")
    print(f"net(gross-fee):          {net:,.2f}")
    if "peak_rss_gb" in rss_profile:
        print(f"peak_rss_gb: {rss_profile['peak_rss_gb']}")
    if "elapsed_s" in rss_profile:
        print(f"elapsed_s:   {rss_profile['elapsed_s']}")


if __name__ == "__main__":
    main()

