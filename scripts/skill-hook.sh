#!/usr/bin/env bash
# Hook: detect changes in quant-workflows/skills/ and prompt for sync.
#
# Behavior:
#   - Reads hook JSON from stdin (PostToolUse).
#   - For Write tool: checks tool_input.file_path.
#   - For Bash tool: checks tool_input.command for the marker string.
#   - If the change touches quant-workflows/skills/, prints a prompt to stdout
#     so Claude is nudged to run /sync-skills.
#   - Any error is swallowed to avoid disrupting the main flow.

set +e

INPUT=$(cat 2>/dev/null)
if [[ -z "$INPUT" ]]; then
    exit 0
fi

# Use python for JSON parsing (jq not always available).
# Pass the JSON via env var to avoid stdin conflicts with the heredoc.
RESULT=$(HOOK_JSON="$INPUT" python3 - <<'PY' 2>/dev/null
import json, os, sys

raw = os.environ.get("HOOK_JSON", "")
try:
    data = json.loads(raw or "{}")
except Exception:
    sys.exit(0)

tool_name = data.get("tool_name") or ""
tool_input = data.get("tool_input") or {}

marker = "quant-workflows/skills/"
should_prompt = False

if tool_name == "Write":
    file_path = tool_input.get("file_path") or ""
    if marker in file_path:
        should_prompt = True
elif tool_name == "Bash":
    command = tool_input.get("command") or ""
    if marker in command:
        should_prompt = True

if should_prompt:
    print("MATCH")
PY
)

if [[ "$RESULT" == "MATCH" ]]; then
    echo "[skill-hook] 检测到 quant-workflows/skills/ 下的变更。请调用 /sync-skills 同步软链接。"
fi

exit 0
