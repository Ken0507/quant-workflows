#!/usr/bin/env bash
# 把本机 fund-qr（基本面案例显微镜 MCP server）部署到新疆投研机 k8s-worker-01（rsync 方案，
# 服务器不碰 GitHub）。沿用 findata / SignalAnalyzer 轻量部署模式，共用落点 / wheelhouse / 公共环境。
#
#   bash deploy_fund_qr_to_xinjiang.sh                 # 开发同步：rsync 源码 + 服务器跑源码测试
#   bash deploy_fund_qr_to_xinjiang.sh --no-test       # 只同步源码，不跑测试
#   bash deploy_fund_qr_to_xinjiang.sh --release       # 发版部署：rsync → build wheel → 发包 wheelhouse →
#                                                      #   安装公共 py311 → 功能 smoke（装配 server + 真实取数）
#   bash deploy_fund_qr_to_xinjiang.sh --release --no-test
#
# 两种模式：
#   开发同步 —— 源=本机当前工作区（含未提交改动），只更新服务器源码副本
#               /data/hftprop/infra/fund-qr，供 cken 调试；不碰公共环境。
#   发版部署 —— 要求 HEAD 落在 release tag 上（先跑 scripts/release.sh X.Y.Z），
#               服务器从源码构建 wheel（fund_qr 一个包），归档 wheelhouse，
#               装进公共 py311 环境 /data/hftprop/envs/py311（hftprop 组=cken+lgj）。
#
# 前置依赖：公共环境里必须已装 findata（>=0.13，avail_ts 语义）——fund_qr 全部数据经 findata。
#   缺位/版本过低即中止：先跑 findata 侧 --release。三方依赖（numpy/pandas/mcp/matplotlib）
#   已由 findata / SignalAnalyzer 部署链装齐，fund-qr 通常零新增。
# fund-qr 消费 findata、不产出需对账的数据 → 无 findata 那种门②零差对账，功能 smoke 即闸门。
# 服务器无任何 GitHub 凭证（SAML 约束，见 findata#11），更新代码只经本机 rsync。
# ⚠️ fund_qr 永远从本地 wheel 装（--no-index --no-deps），只有三方依赖走公网 PyPI。
set -euo pipefail

SRC="/home/cken/alpha_projects"
HOST="cken@222.81.173.58"
DST="/data/hftprop/infra"                  # 服务器源码落点（仅 cken）
PUBENV="/data/hftprop/envs/py311"          # 公共运行环境（hftprop 组）
WHEELHOUSE="$DST/wheelhouse"               # wheel 归档（仅 cken）
SOCK="/tmp/xj_deploy_cm.sock"
REPO="fund-qr"                             # 仓目录名（含连字符）；包名 fund_qr
# fund-qr 的三方依赖（与 pyproject dependencies + optional[mcp,plot] 同步）：
#   mcp：FastMCP server 运行需 mcp SDK；matplotlib：[plot] 可选出图。findata/cube 由其部署链负责。
PYPI_DEPS="numpy pandas mcp matplotlib"
FINDATA_MIN="0.13"                         # 前置 findata 最低版本（avail_ts 语义，#54）

RUN_TEST=1 RELEASE=0
for arg in "$@"; do
  case "$arg" in
    --no-test) RUN_TEST=0 ;;
    --release) RELEASE=1 ;;
    *) echo "未知参数: $arg" >&2; exit 1 ;;
  esac
done

# ---- 发版预检（本机）----
TAG=""
if [[ "$RELEASE" == "1" ]]; then
  echo "==> 发版预检"
  cd "$SRC/$REPO"
  [[ -z "$(git status --porcelain)" ]] \
    || { echo "✗ fund-qr 工作区有未提交改动；发版部署要求与仓库一致（先 commit/stash）" >&2; exit 1; }
  TAG="$(git describe --exact-match --tags HEAD 2>/dev/null)" \
    || { echo "✗ fund-qr HEAD 不在 tag 上；先跑 scripts/release.sh X.Y.Z 再 --release" >&2; exit 1; }
  ver_file="$(cat src/fund_qr/VERSION.txt)"
  [[ "v$ver_file" == "$TAG" ]] \
    || { echo "✗ tag ($TAG) 与 VERSION.txt ($ver_file) 不一致" >&2; exit 1; }
  echo "  ok: fund_qr $TAG"
fi

# 复用/建立 SSH ControlMaster
ssh -S "$SOCK" -O check "$HOST" 2>/dev/null \
  || ssh -M -S "$SOCK" -o ControlPersist=600 -o ConnectTimeout=15 -fN "$HOST"
SSH=(ssh -S "$SOCK")

EXCLUDES=(--exclude '.git' --exclude '__pycache__' --exclude '.pytest_cache'
          --exclude '.venv' --exclude '*.pyc' --exclude '.ipynb_checkpoints'
          --exclude '*.egg-info' --exclude 'build' --exclude 'dist')

echo "==> 同步代码到 $HOST:$DST"
"${SSH[@]}" "$HOST" "mkdir -p '$DST' && chmod 700 '$DST'"
rsync -az --delete -e "ssh -S $SOCK" "${EXCLUDES[@]}" "$SRC/$REPO" "$HOST:$DST/"

STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
cd "$SRC/$REPO"
rev="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
dirty="$(git status -s 2>/dev/null | wc -l | tr -d ' ')"
"${SSH[@]}" "$HOST" "printf '%s\n' 'deployed_at: $STAMP' 'src_commit: $rev' 'uncommitted_files: $dirty' > '$DST/$REPO/DEPLOYED_FROM.txt'"
"${SSH[@]}" "$HOST" "chmod -R go-rwx '$DST/$REPO'"
echo "==> 同步完成"

if [[ "$RUN_TEST" == "1" ]]; then
  echo "==> 服务器 py311 跑源码测试（fund-qr 单测=纯层 + findata mock，信息性）"
  "${SSH[@]}" "$HOST" "source ~/miniconda3/etc/profile.d/conda.sh && conda activate py311 && \
    cd '$DST/$REPO' && python -m pytest tests/ -q 2>&1 | tail -3" || true
fi

# ---- 发版：build wheel → wheelhouse → 安装公共环境 → 功能 smoke ----
if [[ "$RELEASE" == "1" ]]; then
  echo "==> 发版 $TAG：构建 wheel 并更新公共环境 $PUBENV"
  "${SSH[@]}" "$HOST" "DST='$DST' PUBENV='$PUBENV' WHEELHOUSE='$WHEELHOUSE' TAG='$TAG' \
      STAMP='$STAMP' REPO='$REPO' PYPI_DEPS='$PYPI_DEPS' FINDATA_MIN='$FINDATA_MIN' bash -s" <<'REMOTE'
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py311                       # 构建用 cken 个人 py311

# 0) 前置：公共环境必须已装 findata（>=FINDATA_MIN）
[[ -x "$PUBENV/bin/python" ]] \
  || { echo "✗ 公共环境 $PUBENV 不存在：先跑 findata 侧 deploy --release" >&2; exit 1; }
"$PUBENV/bin/python" - "$FINDATA_MIN" <<'PYCHK'
import sys
mn = tuple(int(x) for x in sys.argv[1].split("."))
try:
    import findata
except Exception as e:
    print(f"✗ 公共环境缺 findata：{e}（先跑 findata 侧 --release）", file=sys.stderr); sys.exit(1)
cur = tuple(int(x) for x in findata.__version__.split(".")[:2])
if cur < mn:
    print(f"✗ 公共环境 findata {findata.__version__} < 要求 {'.'.join(map(str,mn))}；先升级 findata", file=sys.stderr); sys.exit(1)
print(f"  ok: 公共环境 findata {findata.__version__} 满足 >= {'.'.join(map(str,mn))}")
PYCHK
fver="$("$PUBENV/bin/python" -c "import findata; print(findata.__version__)")"

# 1) 构建 wheel（纯 python，py3-none-any；fund_qr 一个包）
python -m pip install -qU setuptools wheel
TMP="$(mktemp -d)"
python -m pip wheel --no-deps --no-build-isolation -w "$TMP" "$DST/$REPO"
rm -rf "$DST/$REPO"/build "$DST/$REPO"/*.egg-info
ls -l "$TMP"/*.whl

# 2) 归档到 wheelhouse
mkdir -p "$WHEELHOUSE"
cp -f "$TMP"/*.whl "$WHEELHOUSE/"

# 3) 三方依赖走 PyPI（通常已齐，幂等）；fund_qr 只从本地 wheel 装（--no-index --no-deps）
"$PUBENV/bin/python" -m pip install -U $PYPI_DEPS
"$PUBENV/bin/python" -m pip install --no-index --no-deps --force-reinstall "$TMP"/*.whl
"$PUBENV/bin/python" -m pip check

# 4) 锁定环境快照 + 发布台账
"$PUBENV/bin/python" -m pip freeze > "$WHEELHOUSE/constraints-fund-qr-$TAG.txt"
echo "$STAMP  fund-qr $TAG  findata==$fver" >> "$WHEELHOUSE/RELEASES.log"

# 5) 权限：环境对 hftprop 组开放，组外不可见；wheelhouse 维持仅 cken
chmod -R g+rX,o-rwx /data/hftprop/envs
chmod -R go-rwx "$WHEELHOUSE"

# 6) 功能 smoke（中性 cwd，真实数据经 findata）：
#    ① 装配 FastMCP server（证明 mcp SDK + 全部工具注册）
#    ② 真实 catalog（findata 数据路径通）
#    ③ 平安 000001.SZ 事件装配（fund_qr 核心 PIT→事件链路端到端）
cd /tmp
env -u FINDATA_CUBE_PATH -u PYTHONPATH \
    FINDATA_DATA_ROOT=/data/findata \
    FINDATA_UNIVERSE_ROOT=/data/hftprop/research_data/universe \
    FUND_QR_BACKEND=real FUND_QR_WORK_DIR=/tmp/fundqr_smoke_$$ \
    "$PUBENV/bin/python" - <<'PY'
import fund_qr
print(f"smoke: fund_qr {fund_qr.__version__}")
from fund_qr.server import build_server
srv = build_server()                       # 装配 FastMCP + 注册全部工具（需 mcp SDK）
print("smoke: FastMCP server 装配 OK")
from fund_qr.config import Config
from fund_qr import loaders
from fund_qr.core import events as events_core
cfg = Config.from_env()
loaders.ensure_backend(cfg)
cat = loaders.fetch_catalog()              # 真实 findata catalog
n_cat = len(cat) if cat is not None else 0
assert n_cat > 0, "catalog 为空"
pit = loaders.fetch_pit_multiversion("000001.SZ", None, "BOD")
fam = loaders.fetch_family_frames("000001.SZ", None, "BOD")
evts = events_core.assemble(pit, fam)      # 平安事件端到端
assert len(evts) > 0, "000001.SZ 事件为空"
print(f"smoke: catalog rows={n_cat} / 000001.SZ 事件={len(evts)} —— 真实取数链路 OK")
PY
echo "--- 发版完成：$TAG 已装入 $PUBENV ---"
REMOTE
fi

echo "==> 全部完成。源码在 $DST/$REPO$([[ "$RELEASE" == "1" ]] && echo "；$TAG 已发布到 $PUBENV" || true)"
