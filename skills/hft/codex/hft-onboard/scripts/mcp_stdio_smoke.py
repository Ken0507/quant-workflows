#!/usr/bin/env python3
"""Run a bounded MCP stdio initialize probe and clean up its process group."""

from __future__ import annotations

import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
import tomllib


TIMEOUT_SECONDS = 25.0
MAX_STDERR_BYTES = 8192


def process_group_alive(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
        return True
    except ProcessLookupError:
        return False


def stop_process_group(proc: subprocess.Popen[bytes]) -> None:
    if process_group_alive(proc.pid):
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        pass
    if process_group_alive(proc.pid):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=1.0)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("MCP process cleanup timed out") from exc
    if process_group_alive(proc.pid):
        raise RuntimeError("MCP process group remains alive after cleanup")


def probe(config_path: Path, server_name: str) -> str:
    with config_path.open("rb") as fh:
        config = tomllib.load(fh)
    server = config["mcp_servers"][server_name]
    env = dict(os.environ)
    env.update({str(key): str(value) for key, value in server.get("env", {}).items()})
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "aef-codex-migration-probe", "version": "2.0.0"},
        },
    }
    proc = subprocess.Popen(
        [server["command"], *(str(arg) for arg in server.get("args", []))],
        cwd=str(config_path.parent.parent),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        bufsize=0,
        start_new_session=True,
    )
    selector = selectors.DefaultSelector()
    response: dict[str, object] | None = None
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    try:
        assert proc.stdin is not None
        assert proc.stdout is not None
        assert proc.stderr is not None
        proc.stdin.write((json.dumps(request, separators=(",", ":")) + "\n").encode("utf-8"))
        proc.stdin.flush()
        selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
        selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
        deadline = time.monotonic() + TIMEOUT_SECONDS
        while time.monotonic() < deadline and response is None:
            events = selector.select(max(0.0, deadline - time.monotonic()))
            if not events:
                break
            for key, _ in events:
                chunk = os.read(key.fileobj.fileno(), 4096)
                if not chunk:
                    try:
                        selector.unregister(key.fileobj)
                    except KeyError:
                        pass
                    continue
                if key.data == "stderr":
                    remaining = MAX_STDERR_BYTES - len(stderr_buffer)
                    if remaining > 0:
                        stderr_buffer.extend(chunk[:remaining])
                    continue
                stdout_buffer.extend(chunk)
                while b"\n" in stdout_buffer:
                    line, _, remainder = stdout_buffer.partition(b"\n")
                    stdout_buffer = bytearray(remainder)
                    try:
                        candidate = json.loads(line.decode("utf-8", errors="replace"))
                    except json.JSONDecodeError:
                        continue
                    if isinstance(candidate, dict) and candidate.get("id") == 1:
                        response = candidate
                        break
                if response is not None:
                    break
        if response is not None and "result" in response:
            notification = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
            try:
                proc.stdin.write((json.dumps(notification, separators=(",", ":")) + "\n").encode("utf-8"))
                proc.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
    finally:
        selector.close()
        stop_process_group(proc)

    if response is None:
        tail = stderr_buffer.decode("utf-8", errors="replace").splitlines()[-1:]
        detail = f"; last stderr: {tail[0]}" if tail else ""
        raise RuntimeError(f"no initialize response within {TIMEOUT_SECONDS:g}s{detail}")
    if "result" not in response:
        raise RuntimeError(f"initialize error: {response.get('error', 'unknown error')}")
    result = response["result"]
    if not isinstance(result, dict):
        raise RuntimeError("initialize result is not an object")
    info = result.get("serverInfo")
    info = info if isinstance(info, dict) else {}
    label = f"{info.get('name')} v{info.get('version', '?')}" if info.get("name") else "serverInfo not provided"
    return f"protocol {result.get('protocolVersion', '?')}; {label}"


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} CONFIG_TOML SERVER_NAME", file=sys.stderr)
        return 2
    try:
        print(probe(Path(sys.argv[1]).resolve(), sys.argv[2]))
    except Exception as exc:
        print(f"MCP stdio probe failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
