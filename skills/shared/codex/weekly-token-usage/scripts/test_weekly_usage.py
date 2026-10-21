import argparse
import io
from datetime import date, datetime
import unittest
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from weekly_usage import UsageError, markdown, normalize_pool, read_deepseek_bill, window


def row(day):
    return dict(date=day, input_tokens=10, output_tokens=5, cache_read_tokens=100,
                cache_write_tokens=2, total_tokens=117, requests=1, actual_cost="0.13")


class AccountingTests(unittest.TestCase):
    def test_inclusive_week_crosses_month_and_year(self):
        now = datetime(2027, 1, 3, 1, tzinfo=ZoneInfo("Asia/Shanghai"))
        args = argparse.Namespace(days=7, end=None, last_week=False)
        self.assertEqual(window(args, now), (date(2026, 12, 28), date(2027, 1, 3)))

    def test_previous_calendar_week_on_sunday(self):
        args = argparse.Namespace(days=7, end=None, last_week=True)
        self.assertEqual(window(args, datetime(2027, 1, 3)), (date(2026, 12, 21), date(2026, 12, 27)))

    def test_filter_server_window_and_ignore_lifetime_total(self):
        result = normalize_pool(dict(daily_usage=[row("2026-10-20"), row("2026-10-21")],
                                     usage={"total": {"total_tokens": 9999}}), date(2026, 10, 19), date(2026, 10, 20))
        self.assertIsNone(result["days"]["2026-10-19"])
        self.assertEqual(result["totals"]["total_tokens"], 117)
        self.assertEqual(result["totals"]["actual_cost"], "0.13")

    def test_cache_double_count_fails(self):
        r = row("2026-10-20"); r["input_tokens"] += 100
        with self.assertRaises(UsageError):
            normalize_pool({"daily_usage": [r]}, date(2026, 10, 20), date(2026, 10, 20))

    def test_duplicate_day_fails(self):
        with self.assertRaises(UsageError):
            normalize_pool({"daily_usage": [row("2026-10-20")]*2}, date(2026, 10, 20), date(2026, 10, 20))

    def test_missing_required_metric_fails(self):
        r = row("2026-10-20"); del r["output_tokens"]
        with self.assertRaises(UsageError):
            normalize_pool({"daily_usage": [r]}, date(2026, 10, 20), date(2026, 10, 20))

    def test_default_report_shows_money_and_preserves_currency(self):
        report = dict(start="2026-10-20", end="2026-10-20", today="2026-10-21",
                      timezone="Asia/Shanghai", queried_at="2026-10-21T12:00:00+08:00",
                      codex_pool={"status": "ok", "currency": "USD", "days": {"2026-10-20": {"actual_cost": "12.3456"}},
                                  "totals": {"actual_cost": "12.3456"}},
                      deepseek_cost={"status": "ok", "currency": "CNY", "days": {"2026-10-20": {"actual_cost": "6.78"}},
                                     "totals": {"actual_cost": "6.78"}})
        text = markdown(report)
        self.assertIn("| 2026-10-20 | $12.35 | ¥6.78 |", text)
        self.assertNotIn("token", text)
        self.assertNotIn("$19.13", text)

    def bill(self, rows):
        raw = "date,actual_cost,currency,timezone\n" + rows
        with patch.object(Path, "is_file", return_value=True), patch.object(Path, "open", return_value=io.StringIO(raw)):
            return read_deepseek_bill(Path("synthetic.csv"), date(2026,10,19), date(2026,10,21), "Asia/Shanghai")

    def test_imported_bill_decimal_sum_missing_date_and_staleness(self):
        result = self.bill("2026-10-19,0.1,CNY,Asia/Shanghai\n2026-10-20,0.2,CNY,Asia/Shanghai\n")
        self.assertEqual(result["totals"]["actual_cost"], "0.3")
        self.assertIsNone(result["days"]["2026-10-21"])
        self.assertIsNone(result["refreshed_at"])
        self.assertTrue(result["warnings"])

    def test_bill_rejects_mixed_currencies_duplicates_and_timezone(self):
        for rows in ["2026-10-19,1,CNY,Asia/Shanghai\n2026-10-20,1,USD,Asia/Shanghai\n",
                     "2026-10-19,1,CNY,Asia/Shanghai\n2026-10-19,1,CNY,Asia/Shanghai\n",
                     "2026-10-19,1,CNY,UTC\n"]:
            with self.subTest(rows=rows), self.assertRaises(UsageError):
                self.bill(rows)

    def test_missing_bill_is_not_zero(self):
        with patch.object(Path, "is_file", return_value=False):
            result = read_deepseek_bill(Path("missing.csv"), date(2026,10,19), date(2026,10,21), "Asia/Shanghai")
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("totals", result)


if __name__ == "__main__":
    unittest.main()
