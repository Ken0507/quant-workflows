"""Synthetic accounting regressions; fixtures contain no real conversations."""

import io
import json
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

import deepseek_local as subject


TZ = ZoneInfo("Asia/Shanghai")
DAY = date(2026, 10, 20)
MS = int(datetime(2026, 10, 20, 12, tzinfo=TZ).timestamp() * 1000)


def usage(input=10, cache=100, output=3):
    return {"inputTokens": input, "cacheReadTokens": cache, "cacheWriteTokens": 0,
            "outputTokens": output, "totalTokens": input + cache + output}


def event(seq, typ="assistant/message", *, turn=1, step=1, sample=None, time=MS, **data):
    data.update(turn=turn, step=step)
    if typ in ("assistant/message", "assistant/attempt"):
        data.update(message={"source": {"provider": "deepseek-official", "model": "deepseek-flash"}})
        if sample is not None:
            data["usage"] = sample
    return {"type": typ, "seq": seq, "time": time, "data": data}


def session(events, *, sid="one", seeded=False, version=4):
    header = {"type": "session", "id": sid, "version": version, "isSeeded": seeded}
    data = "\n".join(json.dumps(x) for x in [header] + events) + "\n"
    with patch.object(subject, "_lines") as opening:
        opening.return_value.__enter__.return_value = io.StringIO(data)
        return subject._read_metadata(Path("synthetic.jsonl"))


def fold(value):
    diagnostics = subject.Counter()
    records = subject._fold(value, MS - 12 * 3600 * 1000, MS + 12 * 3600 * 1000, diagnostics)
    return records, diagnostics


class AccountingTests(unittest.TestCase):
    def test_prompt_cache_is_disjoint_and_total_not_double_counted(self):
        records, _ = fold(session([event(0, sample=usage())]))
        self.assertEqual(records[0]["usage"]["total_tokens"], 113)
        self.assertEqual(records[0]["usage"]["input_tokens"], 10)

    def test_settlement_replacement_and_retry_are_separate_requests(self):
        value = session([event(0, "assistant/attempt", sample=usage(1)),
                         event(1, sample=usage(2)),
                         event(2, "llm/retry-started"),
                         event(3, sample=usage(4))])
        records, diagnostics = fold(value)
        self.assertEqual([x["usage"]["input_tokens"] for x in records], [2, 4])
        self.assertEqual(diagnostics["settlement_replacements"], 1)

    def test_nested_fork_uses_last_inherited_marker_and_subagent_keeps_usage(self):
        value = session([event(0, sample=usage(1)),
                         event(1, "session/end-seed", inherited=True),
                         event(2, sample=usage(2), step=2),
                         event(3, "session/end-seed", inherited=True),
                         event(4, sample=usage(4), step=3)], seeded=True)
        records, diagnostics = fold(value)
        self.assertEqual([x["usage"]["input_tokens"] for x in records], [4])
        self.assertEqual(diagnostics["inherited_settlements_excluded"], 2)
        value["header"].update(isSeeded=False, parentSession="parent")
        value["records"] = [value["records"][-1]]
        self.assertEqual(len(fold(value)[0]), 1)

    def test_missing_fork_cut_fails_closed(self):
        records, diagnostics = fold(session([event(0, sample=usage())], seeded=True))
        self.assertEqual(records, [])
        self.assertEqual(diagnostics["seeded_sessions_without_cut"], 1)

    def test_stream_final_sample_and_no_body_retention(self):
        stream = [{"type": "chunk", "chunk": {"type": "usage", "usage": usage(1)}},
                  {"type": "chunk", "chunk": {"type": "usage", "usage": usage(7)}}]
        value = session([event(0, stream=stream, private="DO_NOT_RETAIN")])
        records, _ = fold(value)
        self.assertEqual(records[0]["usage"]["input_tokens"], 7)
        self.assertNotIn("DO_NOT_RETAIN", json.dumps(value))

    def test_unknown_cache_bucket_and_invalid_totals(self):
        sample = usage()
        del sample["cacheReadTokens"]
        self.assertIsNone(subject._normalize(sample)["cache_read_tokens"])
        sample["totalTokens"] = 1
        self.assertIsNone(subject._normalize(sample))

    def test_null_cache_bucket_preserves_reported_total_and_other_requests(self):
        sample = usage()
        sample["cacheReadTokens"] = None
        records, diagnostics = fold(session([event(0, sample=sample),
                                              event(1, step=2, sample=usage())]))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["usage"]["total_tokens"], 113)
        self.assertIsNone(records[0]["usage"]["cache_read_tokens"])
        self.assertEqual(diagnostics["attempts_with_unknown_cache_buckets"], 1)

    def test_china_midnight_boundaries_and_provider_filter(self):
        start = MS - 12 * 3600 * 1000
        value = session([event(0, sample=usage(), time=start - 1),
                         event(1, sample=usage(), step=2, time=start),
                         event(2, sample=usage(), step=3, time=start + 86400000)])
        self.assertEqual(len(fold(value)[0]), 1)
        value["records"][1]["route"] = ("openai", "gpt")
        records, diagnostics = fold(value)
        self.assertEqual(records, [])
        self.assertEqual(diagnostics["other_provider_attempts_excluded"], 1)

    def test_missing_usage_and_auxiliary_requests_are_visible(self):
        records, diagnostics = fold(session([event(0), event(1, "session/title-llm-request")]))
        self.assertEqual(records, [])
        self.assertEqual(diagnostics["attempts_without_valid_usage"], 1)
        self.assertEqual(diagnostics["auxiliary_requests_without_usage"], 1)

    def test_empty_roots_returns_explicit_unavailable_coverage(self):
        result = subject.collect([], DAY, DAY, TZ)
        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)
        self.assertEqual(result["coverage"]["status"], "partial")
        self.assertFalse(result["coverage"]["account_complete"])
        self.assertEqual(result["days"][DAY.isoformat()]["requests"], 0)

    def test_duplicate_roots_and_archive_copies_count_once(self):
        first = Path("/synthetic/a/session.v4.jsonl")
        second = Path("/synthetic/archive/session.v4.jsonl")
        value = session([event(0, sample=usage())])
        with patch.object(Path, "resolve", lambda self: self), \
                patch.object(Path, "is_dir", return_value=True), \
                patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "rglob", return_value=[first, second]), \
                patch.object(Path, "stat", side_effect=[SimpleNamespace(st_dev=1, st_ino=1),
                                                       SimpleNamespace(st_dev=1, st_ino=2)]), \
                patch.object(subject, "_read_metadata", return_value=value):
            result = subject.collect([Path("/synthetic"), Path("/synthetic")], DAY, DAY, TZ)
        self.assertEqual(result["days"][DAY.isoformat()]["requests"], 1)
        self.assertEqual(result["coverage"]["diagnostics"]["duplicate_roots_excluded"], 1)
        self.assertEqual(result["coverage"]["diagnostics"]["duplicate_session_copies_excluded"], 1)

    def test_migrated_format_is_not_added_to_old_format(self):
        paths = [Path("/synthetic/session.v3.jsonl"), Path("/synthetic/session.v4.jsonl")]
        values = [session([event(0, sample=usage(2))], version=3),
                  session([event(0, sample=usage(2)), event(1, sample=usage(7), step=2)], version=4)]
        with patch.object(Path, "resolve", lambda self: self), \
                patch.object(Path, "is_dir", return_value=True), \
                patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "rglob", return_value=paths), \
                patch.object(Path, "stat", side_effect=[SimpleNamespace(st_dev=1, st_ino=1),
                                                       SimpleNamespace(st_dev=1, st_ino=2)]), \
                patch.object(subject, "_read_metadata", side_effect=values):
            result = subject.collect([Path("/synthetic")], DAY, DAY, TZ)
        self.assertEqual(result["days"][DAY.isoformat()]["input_tokens"], 9)
        self.assertEqual(result["days"][DAY.isoformat()]["requests"], 2)

    def test_truncated_tail_preserves_valid_prefix_without_raw_exception(self):
        rows = [{"type": "session", "id": "one", "version": 4, "isSeeded": False},
                event(0, sample=usage())]
        data = "\n".join(json.dumps(row) for row in rows) + '\n{"private":"NEVER_OUTPUT'
        with patch.object(subject, "_lines") as opening:
            opening.return_value.__enter__.return_value = io.StringIO(data)
            value = subject._read_metadata(Path("synthetic.jsonl"))
        self.assertTrue(value["incomplete"])
        self.assertEqual(len(fold(value)[0]), 1)
        self.assertNotIn("NEVER_OUTPUT", json.dumps(value))


if __name__ == "__main__":
    unittest.main()
