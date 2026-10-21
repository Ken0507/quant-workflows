"""Read-only token accounting from local DSH v2-v4 session logs.

The counts are provider-reported settlements, not account billing. JSON lines
are decoded in memory, but only accounting metadata is retained or returned.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import zstandard
except ImportError:  # The CLI fallback does not install or modify anything.
    zstandard = None


FIELDS = ("input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens", "total_tokens")
_USAGE_KEYS = ("inputTokens", "cacheReadTokens", "cacheWriteTokens", "outputTokens", "totalTokens")
_FILE = re.compile(r"session(?:\.v(\d+))?\.jsonl(?:\.zstd)?$")


@contextmanager
def _lines(path: Path):
    if path.suffix != ".zstd":
        with path.open(encoding="utf-8") as stream:
            yield stream
    elif zstandard is not None:
        with path.open("rb") as raw, zstandard.ZstdDecompressor().stream_reader(raw) as decoded:
            with io.TextIOWrapper(decoded, encoding="utf-8") as stream:
                yield stream
    else:
        binary = shutil.which("zstd")
        if not binary:
            raise RuntimeError("zstd_decoder_unavailable")
        with subprocess.Popen([binary, "-dc", "--", str(path)], stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL) as process:
            assert process.stdout is not None
            try:
                with io.TextIOWrapper(process.stdout, encoding="utf-8") as stream:
                    yield stream
            except BaseException:
                if process.poll() is None:
                    process.terminate()
                process.wait()
                raise
            status = process.wait()
            if status:
                raise ValueError("zstd_decode_failed")


def _usage(data: dict):
    value = data.get("usage")
    if value is None:
        for item in data.get("stream", []):
            if not isinstance(item, dict):
                continue
            chunk = item.get("chunk", item)
            if isinstance(chunk, dict) and chunk.get("type") == "usage":
                value = chunk.get("usage")
    return value


def _normalize(value):
    if not isinstance(value, dict):
        return None
    required = ("inputTokens", "outputTokens")
    for key in _USAGE_KEYS:
        n = value.get(key)
        if n is None and key not in required:
            continue
        if type(n) is not int or not 0 <= n <= 2**53 - 1:
            return None
    known = sum(value.get(k) or 0 for k in _USAGE_KEYS[:-1])
    total = value.get("totalTokens")
    cache_complete = value.get("cacheReadTokens") is not None and value.get("cacheWriteTokens") is not None
    if total is None:
        if not cache_complete:
            return None
        total = known
    if total < known or (cache_complete and total != known):
        return None
    # Unknown cache buckets remain unknown: never silently turn them into zero.
    return dict(zip(FIELDS, [value.get(k) for k in _USAGE_KEYS[:-1]] + [total]))


def _route(data):
    message = data.get("message")
    source = message.get("source", {}) if isinstance(message, dict) else {}
    return (source.get("provider"), source.get("model"))


def _deepseek(route):
    return any(isinstance(x, str) and "deepseek" in x.lower() for x in route)


def _read_metadata(path):
    """Return safe metadata, with no message/tool/header text retained."""
    records = []
    header = None
    max_seq = -1
    incomplete = False
    try:
        with _lines(path) as lines:
            for line in lines:
                try:
                    row = json.loads(line)
                except (ValueError, UnicodeError):
                    incomplete = True
                    break
                if not isinstance(row, dict):
                    incomplete = True
                    break
                if header is None:
                    if row.get("type") != "session":
                        raise ValueError("missing_session_header")
                    header = {k: row.get(k) for k in ("id", "version", "isSeeded", "parentSession")}
                    continue
                typ = row.get("type")
                seq, time = row.get("seq"), row.get("time")
                if type(seq) is not int or type(time) is not int or seq != max_seq + 1:
                    incomplete = True
                    break
                max_seq = seq
                data = row.get("data", {})
                if not isinstance(data, dict):
                    incomplete = True
                    break
                if typ in ("assistant/message", "assistant/attempt"):
                    records.append({"type": typ, "seq": seq, "time": time,
                                    "turn": data.get("turn"), "step": data.get("step"),
                                    "usage": _normalize(_usage(data)), "route": _route(data)})
                elif typ in ("step/start", "step/end", "llm/retry-started"):
                    records.append({"type": typ, "seq": seq, "time": time,
                                    "turn": data.get("turn"), "step": data.get("step")})
                elif typ in ("request/context", "model/selection"):
                    records.append({"type": typ, "seq": seq, "time": time,
                                    "route": (data.get("provider"), data.get("model"))})
                elif typ == "request/header":
                    req = data.get("header", {})
                    config = req.get("config", req) if isinstance(req, dict) else {}
                    records.append({"type": typ, "seq": seq, "time": time,
                                    "route": (config.get("provider"), config.get("model"))})
                elif typ == "session/end-seed" and data.get("inherited") is True:
                    records.append({"type": "inherited_cut", "seq": seq, "time": time})
                elif typ == "session/title-llm-request":
                    records.append({"type": "auxiliary_request", "seq": seq, "time": time})
    except RuntimeError:
        raise
    except (OSError, ValueError, EOFError, UnicodeError):
        incomplete = True
    except Exception as exc:
        if zstandard is not None and isinstance(exc, zstandard.ZstdError):
            incomplete = True
        else:
            raise
    if not header or not isinstance(header.get("id"), str):
        raise ValueError("invalid_session_header")
    return {"header": header, "records": records, "max_seq": max_seq, "incomplete": incomplete}


def _fold(session, start_ms, end_ms, diagnostics):
    header, records = session["header"], session["records"]
    cuts = [r["seq"] for r in records if r["type"] == "inherited_cut"]
    if header.get("isSeeded") is True:
        if not cuts:
            diagnostics["seeded_sessions_without_cut"] += 1
            return []
        cut = max(cuts)
    else:
        cut = -1
        if cuts:
            diagnostics["contradictory_inherited_markers"] += 1
            return []
    route = (None, None)
    attempts, last, open_steps = [], None, {}
    in_window = lambda time: start_ms <= time < end_ms
    for record in records:
        typ = record["type"]
        # Route inheritance is needed even when the prompt history is excluded.
        if typ in ("request/header", "request/context", "model/selection"):
            if any(record["route"]):
                route = record["route"]
        if record["seq"] <= cut:
            if typ in ("assistant/message", "assistant/attempt") and in_window(record["time"]):
                diagnostics["inherited_settlements_excluded"] += 1
            continue
        key = (record.get("turn"), record.get("step"))
        if typ == "step/start":
            open_steps[key] = record["time"]
        elif typ == "step/end":
            started = open_steps.pop(key, None)
            if started is not None and in_window(record["time"]):
                diagnostics["steps_without_settlement"] += 1
        elif typ == "llm/retry-started":
            if last is not None and attempts[last]["key"] == key:
                last = None
            open_steps[key] = record["time"]
        elif typ in ("assistant/message", "assistant/attempt"):
            open_steps.pop(key, None)
            actual_route = record["route"] if any(record["route"]) else route
            current = {"key": key, "time": record["time"], "usage": record["usage"],
                       "route": actual_route}
            if last is not None and attempts[last]["key"] == key:
                # A later settlement is the same request unless retry-started
                # explicitly opened another request. Missing usage does not erase
                # the previous valid provider sample, matching token-meter.
                if current["usage"] is not None or attempts[last]["usage"] is None:
                    attempts[last] = current
                diagnostics["settlement_replacements"] += 1
            else:
                attempts.append(current)
                last = len(attempts) - 1
        elif typ == "auxiliary_request" and in_window(record["time"]):
            diagnostics["auxiliary_requests_without_usage"] += 1
    diagnostics["open_steps"] += sum(in_window(t) for t in open_steps.values())
    accepted = []
    for attempt in attempts:
        if not in_window(attempt["time"]):
            continue
        if not any(attempt["route"]):
            diagnostics["unattributed_attempts"] += 1
            continue
        if not _deepseek(attempt["route"]):
            diagnostics["other_provider_attempts_excluded"] += 1
            continue
        if attempt["usage"] is None:
            diagnostics["attempts_without_valid_usage"] += 1
            continue
        if any(v is None for v in attempt["usage"].values()):
            diagnostics["attempts_with_unknown_cache_buckets"] += 1
        accepted.append(attempt)
    return accepted


def collect(roots: list[Path], start: date, end: date, tz: ZoneInfo, on_attempt=None) -> dict:
    """Aggregate inclusive local dates; return only counts and coverage metadata."""
    if start > end:
        raise ValueError("start must be on or before end")
    start_ms = int(datetime.combine(start, datetime.min.time(), tz).timestamp() * 1000)
    end_ms = int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tz).timestamp() * 1000)
    days = {}
    for offset in range((end - start).days + 1):
        days[(start + timedelta(days=offset)).isoformat()] = {**dict.fromkeys(FIELDS, 0), "requests": 0}
    diagnostics = Counter()
    files, seen_files, seen_roots, missing_roots = [], set(), set(), []
    for raw_root in roots:
        root = Path(raw_root).expanduser().resolve()
        if root in seen_roots:
            diagnostics["duplicate_roots_excluded"] += 1
            continue
        seen_roots.add(root)
        if not root.is_dir():
            missing_roots.append(str(root))
            continue
        for path in sorted(root.rglob("session*.jsonl*")):
            if not _FILE.fullmatch(path.name) or not path.is_file():
                continue
            try:
                stat = path.stat()
            except OSError:
                diagnostics["unreadable_files"] += 1
                continue
            identity = (stat.st_dev, stat.st_ino)
            if identity in seen_files:
                diagnostics["duplicate_files_excluded"] += 1
                continue
            seen_files.add(identity)
            files.append(path)
    # One durable session can have an archive copy or multiple migrated formats.
    # Select the highest supported format, then the longest event log. Distinct
    # sessions are never collapsed just because they have equal token counts.
    sessions = {}
    for path in files:
        try:
            candidate = _read_metadata(path)
        except RuntimeError:
            diagnostics["decoder_unavailable_files"] += 1
            continue
        except (OSError, ValueError):
            diagnostics["unreadable_files"] += 1
            continue
        header = candidate["header"]
        if header.get("version") not in (2, 3, 4):
            diagnostics["unsupported_version_files"] += 1
            continue
        if candidate["incomplete"]:
            diagnostics["incomplete_files"] += 1
        sid = header["id"]
        previous = sessions.get(sid)
        if previous is not None:
            diagnostics["duplicate_session_copies_excluded"] += 1
            if previous["header"]["version"] == header["version"]:
                limit = min(previous["max_seq"], candidate["max_seq"])
                left = [r for r in previous["records"] if r["seq"] <= limit]
                right = [r for r in candidate["records"] if r["seq"] <= limit]
                if left != right:
                    diagnostics["conflicting_session_copies"] += 1
            prev_rank = (previous["header"]["version"], previous["max_seq"], not previous["incomplete"])
            cand_rank = (header["version"], candidate["max_seq"], not candidate["incomplete"])
            if prev_rank >= cand_rank:
                continue
        sessions[sid] = candidate
    for session in sessions.values():
        header = session["header"]
        if header.get("isSeeded") and header.get("parentSession") not in sessions:
            diagnostics["seeded_parents_not_in_roots"] += 1
        for attempt in _fold(session, start_ms, end_ms, diagnostics):
            if on_attempt is not None:
                on_attempt(attempt)
            day = datetime.fromtimestamp(attempt["time"] / 1000, tz).date().isoformat()
            row = days[day]
            for key in FIELDS:
                value = attempt["usage"][key]
                row[key] = None if row[key] is None or value is None else row[key] + value
            row["requests"] += 1
    partial_keys = ("unreadable_files", "decoder_unavailable_files", "unsupported_version_files",
                    "incomplete_files", "conflicting_session_copies", "seeded_sessions_without_cut",
                    "seeded_parents_not_in_roots",
                    "contradictory_inherited_markers", "steps_without_settlement", "open_steps",
                    "auxiliary_requests_without_usage", "unattributed_attempts", "attempts_without_valid_usage",
                    "attempts_with_unknown_cache_buckets")
    warnings = ["仅覆盖所列本机 DSH 日志中的 DeepSeek 请求，不是 DeepSeek 账户完整账单；已删除日志、其他机器和未落 usage 的请求无法统计。"]
    if missing_roots:
        warnings.append("部分候选日志目录不存在；缺失目录见 coverage.missing_roots。")
    descriptions = {
        "unreadable_files": "个会话文件无法读取，未计入",
        "decoder_unavailable_files": "个压缩文件缺少 zstandard 库或 zstd 命令，未计入",
        "unsupported_version_files": "个日志使用暂不支持的格式版本，未计入",
        "incomplete_files": "个日志存在截断或损坏，仅保留已验证的有效前缀",
        "conflicting_session_copies": "组同一会话的副本存在冲突，仅选取一份，结果可能缺失",
        "seeded_sessions_without_cut": "个分叉会话缺少继承边界，整份排除以免重复计费",
        "seeded_parents_not_in_roots": "个分叉会话的父会话不在日志范围内，继承部分未计入",
        "contradictory_inherited_markers": "个会话的继承标记与头信息矛盾，整份排除",
        "steps_without_settlement": "个已结束步骤没有请求结算记录，无法确认用量",
        "open_steps": "个请求步骤尚未结算，用量待落盘",
        "auxiliary_requests_without_usage": "次后台标题生成请求没有 usage，未计入",
        "unattributed_attempts": "次请求无法确认 provider/model，未计入 DeepSeek",
        "attempts_without_valid_usage": "次请求缺少有效 usage，未计入",
        "attempts_with_unknown_cache_buckets": "次请求缺少缓存细分，相关缓存列标为未知",
    }
    for key in partial_keys:
        if diagnostics[key]:
            warnings.append(f"{diagnostics[key]} {descriptions[key]}。")
    if not files:
        warnings.append("未发现会话日志；每日零值表示本机未观察到记录，不能解释为账户零消费。")
    partial = not files or any(diagnostics[k] for k in partial_keys)
    return {"status": "error" if not sessions else "partial",
            **({"error": "没有可解析的受支持 DSH 会话日志，不能统计 DeepSeek 本机用量。"} if not sessions else {}),
            "days": days, "warnings": warnings,
            "coverage": {"scope": "local_dsh_logs_only", "account_complete": False,
                         "status": "partial" if partial else "observed_local_logs",
                         "timezone": str(tz), "date_basis": "provider_usage_settlement_event_time",
                         "roots": sorted(str(p) for p in seen_roots), "missing_roots": missing_roots,
                         "files_scanned": len(files), "unique_sessions": len(sessions),
                         "supported_session_versions": [2, 3, 4], "diagnostics": dict(diagnostics)}}
