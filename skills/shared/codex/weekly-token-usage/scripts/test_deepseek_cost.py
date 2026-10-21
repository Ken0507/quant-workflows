from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch
import unittest

import deepseek_cost as subject
from weekly_usage import cost_markdown


def attempt(day="2026-10-20", hour=10, model="deepseek-flash"):
    stamp = datetime.fromisoformat(day).replace(hour=hour, tzinfo=subject.CHINA)
    return {"time": int(stamp.timestamp()*1000), "route": ("deepseek-official", model),
            "usage": {"input_tokens": 1_000_000, "cache_read_tokens": 1_000_000,
                      "cache_write_tokens": 0, "output_tokens": 1_000_000}}


class CostTests(unittest.TestCase):
    def test_input_cache_output_have_distinct_rates(self):
        self.assertEqual(subject.price_attempt(attempt()), (Decimal("10.04"), "peak"))
        self.assertEqual(subject.price_attempt(attempt(hour=20)), (Decimal("5.02"), "off_peak"))

    def test_peak_boundaries(self):
        for hour, peak in [(8,False),(9,True),(11,True),(12,False),(13,False),(14,True),(17,True),(18,False)]:
            self.assertEqual(subject.price_attempt(attempt(hour=hour))[1], "peak" if peak else "off_peak")

    def test_weekends_holidays_and_makeup_weekend(self):
        for day in ["2026-09-25", "2026-10-01", "2026-10-07", "2026-10-10", "2026-10-17"]:
            self.assertEqual(subject.price_attempt(attempt(day=day))[1], "off_peak")

    def test_models_unknown_prices_and_missing_cache(self):
        self.assertEqual(subject.price_attempt(attempt(model="deepseek-v4-pro"))[0], Decimal("36.30"))
        for value in [attempt(model="unknown"), attempt(day="2026-09-09"), attempt(day="2027-01-01")]:
            self.assertIsNone(subject.price_attempt(value)[0])
        value=attempt(); value["usage"]["cache_read_tokens"]=None
        self.assertIsNone(subject.price_attempt(value)[0])

    def test_estimator_keeps_missing_days_and_marks_estimate(self):
        def collect(roots,start,end,tz,on_attempt):
            on_attempt(attempt())
            return {"status":"partial","warnings":["local"],"coverage":{"account_complete":False}}
        with patch.object(subject,"verify_current_prices",return_value="now"), patch.object(subject,"collect",side_effect=collect):
            result=subject.estimate_cost([],date(2026,10,20),date(2026,10,21),subject.CHINA)
        self.assertIsNone(result["days"]["2026-10-21"])
        self.assertEqual(result["totals"]["estimated_cost"],"10.04")
        self.assertNotIn("actual_cost",result["totals"])
        report={"start":"2026-10-20","end":"2026-10-21","today":"2026-10-21",
                "timezone":"Asia/Shanghai","queried_at":"now", "deepseek_cost":result,
                "codex_pool":{"status":"error"}}
        self.assertIn("≈¥10.04",cost_markdown(report))


if __name__ == "__main__":
    unittest.main()
