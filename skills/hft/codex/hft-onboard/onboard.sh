#!/usr/bin/env bash
set -euo pipefail

# hft-onboard —— HFT 角色包就地安装 + 研究环境体检（维护者工作站单机模式）
# 用法见同目录 SKILL.md。全程幂等。

SKILLS_DIR="" MCP_DIR="" CHECK_ONLY=0 NO_SHELL=0 COPY=0 FIX_DEPS=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skills-dir) SKILLS_DIR="$2"; shift 2 ;;
        --mcp-dir)    MCP_DIR="$2"; shift 2 ;;
        --check)      CHECK_ONLY=1; shift ;;
        --no-shell)   NO_SHELL=1; shift ;;
        --copy)       COPY=1; shift ;;
        --fix-deps)   FIX_DEPS=1; shift ;;
        -h|--help)    grep '^#' "$0" | head -5; exit 0 ;;
        *) echo "未知参数: $1" >&2; exit 1 ;;
    esac
done
SKILLS_DIR="${SKILLS_DIR:-$PWD/.agents/skills}"
MCP_DIR="${MCP_DIR:-$PWD}"

ok()   { echo "[onboard] ✓ $*"; }
warn() { echo "[onboard] ⚠ $*" >&2; }
die()  { echo "[onboard] ✗ $*" >&2; exit 1; }

# ---- 1) 定位角色包源 -------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT=""
probe="$SCRIPT_DIR"
for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    [[ -d "$probe/.agents/skills" && -f "$probe/.codex/config.toml" ]] && { PKG_ROOT="$probe"; break; }
done
if [[ -z "$PKG_ROOT" ]]; then
    [[ -d "$HOME/.aef/hft/.agents/skills" && -f "$HOME/.aef/hft/.codex/config.toml" ]] && PKG_ROOT="$HOME/.aef/hft" \
        || die "找不到角色包源（既不在角色包内运行，~/.aef/hft 也不存在；维护者先 publish.sh hft）"
fi
MANIFEST="$PKG_ROOT/.codex/config.toml"
ok "角色包源: $PKG_ROOT"

# ---- 2) 逐 server 校验研究环境（以角色包 .codex/config.toml 为准） ----------
# 输出通过校验的 server 名列表；校验含: command 可执行/server 脚本存在/HFT_SDK_ROOT 存在/
# HFT_DATA_ROOT 非空/import mcp + server 模块。
declare -A SRV_OK
mapfile -t SERVERS < <(python3 -c "import tomllib;print('\n'.join(tomllib.load(open('$MANIFEST','rb')).get('mcp_servers',{})))")
[[ ${#SERVERS[@]} -gt 0 ]] || die "config 里没有任何 mcp_servers: $MANIFEST"

for srv in "${SERVERS[@]}"; do
    cfg_py() { python3 -c "import tomllib;c=tomllib.load(open('$MANIFEST','rb'))['mcp_servers']['$srv'];$1"; }
    CMD="$(cfg_py "print(c['command'])")"
    SCRIPT="$(cfg_py "print(c['args'][0])")"
    SDK_ROOT="$(cfg_py "print(c.get('env',{}).get('HFT_SDK_ROOT',''))")"
    DATA_ROOT="$(cfg_py "print(c.get('env',{}).get('HFT_DATA_ROOT',''))")"
    PYPATH="$(cfg_py "print(c.get('env',{}).get('PYTHONPATH',''))")"
    MODULE="$(basename "$(dirname "$SCRIPT")")"   # .../sdk_tools/ob_mcp/server.py -> ob_mcp

    fail=""
    [[ -x "$CMD" ]] || fail="python 不可执行: $CMD"
    [[ -z "$fail" && -f "$SCRIPT" ]] || fail="${fail:-server 脚本不存在: $SCRIPT}"
    [[ -z "$fail" && ( -z "$SDK_ROOT" || -d "$SDK_ROOT" ) ]] || fail="${fail:-HFT_SDK_ROOT 不存在: $SDK_ROOT}"
    if [[ -z "$fail" && -n "$DATA_ROOT" ]]; then
        [[ -d "$DATA_ROOT" && -n "$(ls -A "$DATA_ROOT" 2>/dev/null | head -1)" ]] || fail="HFT_DATA_ROOT 为空或不存在: $DATA_ROOT"
    fi
    if [[ -z "$fail" ]] && ! "$CMD" -c "import mcp" >/dev/null 2>&1; then
        if [[ "$FIX_DEPS" == 1 && "$CHECK_ONLY" == 0 ]]; then
            warn "python 缺 mcp 包，--fix-deps 自动安装中..."
            "$(dirname "$CMD")/pip" install -q mcp && ok "已安装 mcp(FastMCP SDK)" || fail="pip install mcp 失败"
        else
            fail="python 缺 mcp(FastMCP SDK) 包 —— 运行: $(dirname "$CMD")/pip install mcp（或加 --fix-deps）"
        fi
    fi
    [[ -z "$fail" ]] && ! PYTHONPATH="$PYPATH" "$CMD" -c "import $MODULE" >/dev/null 2>&1 && fail="import $MODULE 失败(PYTHONPATH=$PYPATH)"

    if [[ -z "$fail" ]]; then SRV_OK[$srv]=1; ok "server '$srv' 环境校验通过"; else warn "server '$srv' 剔除: $fail"; fi
done
[[ ${#SRV_OK[@]} -gt 0 ]] || die "没有任何 MCP server 通过环境校验"

# ---- 冒烟: stdio 握手 -------------------------------------------------------
smoke() {
    local srv="$1"
    python3 "$SCRIPT_DIR/scripts/mcp_stdio_smoke.py" "$MANIFEST" "$srv"
}
for srv in "${!SRV_OK[@]}"; do
    if smoke "$srv"; then ok "server '$srv' stdio 握手通过"; else
        warn "server '$srv' stdio 握手失败，剔除"; unset "SRV_OK[$srv]"; fi
done
[[ ${#SRV_OK[@]} -gt 0 ]] || die "没有任何 MCP server 通过 stdio 冒烟"

if [[ "$CHECK_ONLY" == 1 ]]; then ok "--check 体检完成，未改任何文件"; exit 0; fi

# ---- 3) 安装 skills（软链，幂等） -------------------------------------------
mkdir -p "$SKILLS_DIR"
n_link=0 n_skip=0
for src in "$PKG_ROOT/.agents/skills"/*/; do
    name="$(basename "$src")"; dst="$SKILLS_DIR/$name"
    if [[ -L "$dst" && "$(readlink -f "$dst")" == "$(readlink -f "$src")" ]]; then n_skip=$((n_skip+1)); continue; fi
    if [[ -e "$dst" && ! -L "$dst" ]]; then warn "跳过 $name：目标已存在且不是软链"; continue; fi
    if [[ "$COPY" == 1 ]]; then rm -rf "$dst"; cp -r "$src" "$dst"; else ln -sfn "${src%/}" "$dst"; fi
    n_link=$((n_link+1))
done
ok "skills 安装到 $SKILLS_DIR（新装/更新 $n_link，已就绪 $n_skip）"

# ---- 4) 安装 MCP（过滤 + 语义合并写入） -------------------------------------
KEEP=$(printf '%s\n' "${!SRV_OK[@]}" | paste -sd, -)
mkdir -p "$MCP_DIR/.codex"
python3 - "$MANIFEST" "$MCP_DIR/.codex/config.toml" "$KEEP" <<'PY'
import json
import os
from pathlib import Path
import re
import sys
import tomllib

manifest, out, keep_csv = sys.argv[1], sys.argv[2], sys.argv[3]
keep = {name for name in keep_csv.split(",") if name}
with open(manifest, "rb") as f:
    source_doc = tomllib.load(f)
src = {k: v for k, v in source_doc.get("mcp_servers", {}).items() if k in keep}
if not src:
    raise SystemExit("没有通过校验、可写入 Codex 配置的 MCP server")

out_path = Path(out)
old_text = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
if old_text:
    try:
        tomllib.loads(old_text)
    except Exception as exc:
        raise SystemExit(f"现有 Codex 配置无法解析，拒绝覆盖: {out_path}: {exc}")

table_header = re.compile(r"^\s*\[\[?.+\]\]?\s*(?:#.*)?$")

def header_path(line: str) -> tuple[str, ...]:
    try:
        node = tomllib.loads(line + ("" if line.endswith("\n") else "\n"))
    except Exception:
        return ()
    path = []
    while isinstance(node, dict) and len(node) == 1:
        key, node = next(iter(node.items()))
        path.append(key)
    return tuple(path)

# 保留用户原文件的注释、顺序与非 MCP 配置；只移除即将由角色包更新的同名 server table。
kept_lines = []
skip = False
for line in old_text.splitlines(keepends=True):
    if table_header.match(line):
        path = header_path(line)
        skip = len(path) >= 2 and path[0] == "mcp_servers" and path[1] in src
    if not skip:
        kept_lines.append(line)

def toml_value(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(v) for v in value) + "]"
    raise TypeError(f"不支持的 TOML 值: {value!r}")

def render_table(path, table):
    header = "[" + ".".join(json.dumps(p, ensure_ascii=False) for p in path) + "]"
    lines = [header]
    children = []
    for key, value in table.items():
        if isinstance(value, dict):
            children.append((key, value))
        else:
            lines.append(f"{json.dumps(key, ensure_ascii=False)} = {toml_value(value)}")
    blocks = ["\n".join(lines)]
    for key, value in children:
        blocks.extend(render_table((*path, key), value))
    return blocks

blocks = []
for name, cfg in src.items():
    blocks.extend(render_table(("mcp_servers", name), cfg))

prefix = "".join(kept_lines).rstrip()
new_text = (prefix + "\n\n" if prefix else "") + "\n\n".join(blocks) + "\n"
try:
    merged_doc = tomllib.loads(new_text)
except Exception as exc:
    raise SystemExit(f"合并后的 Codex 配置无法解析，未写入: {exc}")

tmp = out_path.with_name(out_path.name + ".hft-onboard.tmp")
tmp.write_text(new_text, encoding="utf-8")
os.replace(tmp, out_path)
total = len(merged_doc.get("mcp_servers", {}))
print(f"[onboard] ✓ .codex/config.toml 语义合并写入 {out_path}（{', '.join(src)}；共 {total} server）")
PY

# ---- 5) shell 环境块（可选，幂等） ------------------------------------------
if [[ "$NO_SHELL" == 0 ]]; then
    SDK_ROOT_ANY="$(python3 -c "import tomllib;cs=tomllib.load(open('$MANIFEST','rb'))['mcp_servers'];print(next((c['env']['HFT_SDK_ROOT'] for c in cs.values() if c.get('env',{}).get('HFT_SDK_ROOT')),''))")"
    if [[ -n "$SDK_ROOT_ANY" ]]; then
        BLK_S="# >>> hft-onboard >>>" BLK_E="# <<< hft-onboard <<<"
        tmp="$(mktemp)"; touch "$HOME/.bashrc"
        sed "/^$BLK_S/,/^$BLK_E/d" "$HOME/.bashrc" > "$tmp"
        printf '%s\nexport HFT_SDK_ROOT="%s"\n%s\n' "$BLK_S" "$SDK_ROOT_ANY" "$BLK_E" >> "$tmp"
        mv "$tmp" "$HOME/.bashrc"
        ok "~/.bashrc 已写 HFT_SDK_ROOT 导出块（--no-shell 可跳过）"
    fi
fi

echo "[onboard] 完成。修改过 .codex/config.toml 后需在 $MCP_DIR 重开 Codex 会话才会加载 MCP。"
