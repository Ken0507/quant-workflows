#!/usr/bin/env bash
# 把本机 SignalAnalyzer 部署到新疆投研机 k8s-worker-01（rsync 方案，服务器不碰 GitHub）。
# 沿用 findata / SignalMaker 部署模式（见 findata#12），共用落点 / wheelhouse / 公共环境。
#
#   bash scripts/deploy_signalanalyzer_to_xinjiang.sh                 # 开发同步：rsync 源码 + 服务器跑源码测试
#   bash scripts/deploy_signalanalyzer_to_xinjiang.sh --no-test       # 只同步源码，不跑测试
#   bash scripts/deploy_signalanalyzer_to_xinjiang.sh --release       # 发版部署：rsync → 测试 → build wheel →
#                                                                     #   发包 wheelhouse → 安装公共 py311 → smoke
#   bash scripts/deploy_signalanalyzer_to_xinjiang.sh --release --no-test
#
# 两种模式：
#   开发同步 —— 源=本机当前工作区（含未提交改动），只更新服务器源码副本
#               /data/hftprop/infra/SignalAnalyzer，供 cken 调试；不碰公共环境。
#   发版部署 —— 要求 HEAD 落在 release tag 上（先跑 scripts/release.sh X.Y.Z），
#               服务器从源码构建 wheel（含 signalanalyzer + sa_mcp），归档 wheelhouse，
#               装进公共 py311 环境 /data/hftprop/envs/py311（hftprop 组=cken+lgj）。
#
# 前置依赖：公共环境里必须已装 findata + cube + signalmaker（SA 的 load_factor 委托
# signalmaker.load_factors）。缺位即中止——先跑 findata 侧、再跑 signalmaker 侧 --release。
# 服务器无任何 GitHub 凭证（SAML 约束，见 findata#11），更新代码只经本机 rsync。
# ⚠️ cube 在 PyPI 有无关同名包：signalanalyzer/signalmaker/findata/cube 永远从本地 wheel 安装
#    （--no-index），只有三方依赖（numpy/pandas/mcp/matplotlib/reportlab）走公网 PyPI。
set -euo pipefail

SRC="/home/cken/alpha_projects"
HOST="cken@222.81.173.58"
DST="/data/hftprop/infra"                  # 服务器源码落点（仅 cken）
PUBENV="/data/hftprop/envs/py311"          # 公共运行环境（hftprop 组）
WHEELHOUSE="$DST/wheelhouse"               # wheel 归档（仅 cken）
SOCK="/tmp/xj_deploy_cm.sock"
REPO="SignalAnalyzer"
# signalanalyzer + sa_mcp 的三方依赖（与 pyproject 的 dependencies + optional[mcp,report] 同步）。
# mcp：sa_mcp（MCP server）运行需 mcp SDK；matplotlib/reportlab：generate_report 出 PDF。
# findata/cube/signalmaker 的三方依赖由各自部署链负责，不在此重复。
PYPI_DEPS="numpy pandas mcp matplotlib reportlab"

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
    || { echo "✗ SignalAnalyzer 工作区有未提交改动；发版部署要求与仓库一致（先 commit/stash）" >&2; exit 1; }
  TAG="$(git describe --exact-match --tags HEAD 2>/dev/null)" \
    || { echo "✗ SignalAnalyzer HEAD 不在 tag 上；先跑 scripts/release.sh X.Y.Z 再 --release" >&2; exit 1; }
  ver_file="$(cat signalanalyzer/VERSION.txt)"
  [[ "v$ver_file" == "$TAG" ]] \
    || { echo "✗ tag ($TAG) 与 VERSION.txt ($ver_file) 不一致" >&2; exit 1; }
  echo "  ok: signalanalyzer $TAG"
fi

# 复用/建立 SSH ControlMaster
ssh -S "$SOCK" -O check "$HOST" 2>/dev/null \
  || ssh -M -S "$SOCK" -o ControlPersist=600 -o ConnectTimeout=15 -fN "$HOST"
SSH=(ssh -S "$SOCK")

EXCLUDES=(--exclude '.git' --exclude '__pycache__' --exclude '.pytest_cache'
          --exclude 'docs/_build' --exclude 'docs/_build_local' --exclude '*.pyc'
          --exclude '.ipynb_checkpoints' --exclude '*.egg-info' --exclude 'build'
          --exclude 'dist')

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
  echo "==> 服务器 py311 跑源码测试"
  "${SSH[@]}" "$HOST" "[[ -d '$DST/findata' && -d '$DST/cube' && -d '$DST/SignalMaker' ]] \
      || { echo '✗ 缺源码副本 $DST/{findata,cube,SignalMaker}：先跑 findata / signalmaker 侧 dev 同步' >&2; exit 1; } && \
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate py311 && \
    cd '$DST/$REPO' && python -m pytest tests/ -q 2>&1 | tail -3"
fi

# ---- 发版：build wheel → wheelhouse → 安装公共环境 → smoke ----
if [[ "$RELEASE" == "1" ]]; then
  echo "==> 发版 $TAG：构建 wheel 并更新公共环境 $PUBENV"
  "${SSH[@]}" "$HOST" "DST='$DST' PUBENV='$PUBENV' WHEELHOUSE='$WHEELHOUSE' TAG='$TAG' \
      STAMP='$STAMP' REPO='$REPO' PYPI_DEPS='$PYPI_DEPS' bash -s" <<'REMOTE'
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py311                       # 构建用 cken 个人 py311

# 0) 前置：公共环境必须已装 findata + cube + signalmaker
[[ -x "$PUBENV/bin/python" ]] \
  || { echo "✗ 公共环境 $PUBENV 不存在：先跑 findata 侧 deploy --release" >&2; exit 1; }
"$PUBENV/bin/python" -c "import findata, cube, signalmaker" 2>/dev/null \
  || { echo "✗ 公共环境缺 findata/cube/signalmaker：先跑 findata 侧、再跑 signalmaker 侧 --release" >&2; exit 1; }
fver="$("$PUBENV/bin/python" -c "import findata; print(findata.__version__)")"
sver="$("$PUBENV/bin/python" -c "import signalmaker; print(signalmaker.__version__)")"

# 1) 构建 wheel（纯 python，py3-none-any；含 signalanalyzer + sa_mcp 两包）
python -m pip install -qU setuptools wheel
TMP="$(mktemp -d)"
python -m pip wheel --no-deps --no-build-isolation -w "$TMP" "$DST/$REPO"
rm -rf "$DST/$REPO"/build "$DST/$REPO"/*.egg-info
ls -l "$TMP"/*.whl

# 2) 归档到 wheelhouse
mkdir -p "$WHEELHOUSE"
cp -f "$TMP"/*.whl "$WHEELHOUSE/"

# 3) 三方依赖走 PyPI；signalanalyzer 只从本地 wheel 装（--no-index --no-deps）
"$PUBENV/bin/python" -m pip install -U $PYPI_DEPS
"$PUBENV/bin/python" -m pip install --no-index --no-deps --force-reinstall "$TMP"/*.whl
"$PUBENV/bin/python" -m pip check

# 4) 锁定环境快照 + 发布台账
"$PUBENV/bin/python" -m pip freeze > "$WHEELHOUSE/constraints-signalanalyzer-$TAG.txt"
echo "$STAMP  signalanalyzer $TAG  findata==$fver signalmaker==$sver" >> "$WHEELHOUSE/RELEASES.log"

# 5) 权限：环境对 hftprop 组开放，组外不可见；wheelhouse 维持仅 cken
chmod -R g+rX,o-rwx /data/hftprop/envs
chmod -R go-rwx "$WHEELHOUSE"

# 6) smoke：用已安装的包跑（中性 cwd）——导入两包 + 核心数据接口在位 + sa_mcp server 可加载
cd /tmp
env -u FINDATA_CUBE_PATH -u PYTHONPATH FINDATA_DATA_ROOT=/data/findata "$PUBENV/bin/python" - <<'PY'
import signalanalyzer, signalmaker, findata
print(f"smoke: signalanalyzer {signalanalyzer.__version__} / signalmaker {signalmaker.__version__} / findata {findata.__version__}")
from signalanalyzer import data as sadata
for fn in ("load_factor", "load_labels", "close_to_close_labels", "load_universe", "load_tradable_mask"):
    assert hasattr(sadata, fn), f"signalanalyzer.data 缺 {fn}"
print("smoke: signalanalyzer.data 核心接口在位")
import sa_mcp            # MCP server 包可导入（mcp SDK 已装）
print(f"smoke: sa_mcp 导入 OK -> {sa_mcp.__name__}")
PY
echo "--- 发版完成：$TAG 已装入 $PUBENV ---"
REMOTE
fi

echo "==> 全部完成。源码在 $DST/$REPO$([[ "$RELEASE" == "1" ]] && echo "；$TAG 已发布到 $PUBENV" || true)"
