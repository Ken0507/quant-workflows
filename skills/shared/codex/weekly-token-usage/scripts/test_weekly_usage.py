import argparse
from datetime import date, datetime
import unittest
from zoneinfo import ZoneInfo

from weekly_usage import UsageError, normalize_pool, window


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


if __name__ == "__main__":
    unittest.main()
