#!/usr/bin/env bash
# 把本机 SignalMaker 部署到新疆投研机 k8s-worker-01（rsync 方案，服务器不碰 GitHub）。
# 沿用 findata 部署模式（deploy_to_xinjiang.sh，约定见 findata#12），共用落点 / wheelhouse / 公共环境。
#
#   bash deploy_signalmaker_to_xinjiang.sh                  # 开发同步：rsync 源码 + 服务器跑源码测试
#   bash deploy_signalmaker_to_xinjiang.sh --no-test        # 只同步源码，不跑测试
#   bash deploy_signalmaker_to_xinjiang.sh --release        # 发版部署：rsync → 测试 → build wheel →
#                                                           #   发包 wheelhouse → 安装公共 py311 → smoke
#   bash deploy_signalmaker_to_xinjiang.sh --release --no-test   # 发版但跳过源码测试（wheel smoke 仍跑）
#
# 两种模式的分工：
#   开发同步 —— 源 = 本机当前工作区（含未提交改动），只更新服务器源码副本
#               /data/hftprop/infra/SignalMaker，供 cken 自己在服务器上调试；
#               不碰公共环境，研究使用方无感知。
#   发版部署 —— 要求 SignalMaker HEAD 落在 release tag 上（先跑 scripts/release.sh X.Y.Z），
#               在服务器上从源码构建 wheel，归档到 wheelhouse，并安装进公共 py311 环境
#               /data/hftprop/envs/py311（hftprop 组=cken+lgj 可用）。
#
# 前置依赖：公共环境里必须已装 findata + cube（findata 侧 deploy_to_xinjiang.sh --release），
# 本脚本只构建/安装 signalmaker 自己的 wheel，发现 findata 缺位即中止。
# 服务器无任何 GitHub 凭证（SAML 约束，见 findata#11），更新代码只经本机 rsync。
# ⚠️ cube 在 PyPI 有无关同名包：signalmaker/findata/cube 永远从本地 wheel 文件安装（--no-index），
#    只有三方依赖（numpy/pandas/...）走公网 PyPI。
set -euo pipefail

SRC="/home/cken/alpha_projects"
HOST="cken@222.81.173.58"
DST="/data/hftprop/infra"                  # 服务器源码落点（仅 cken）
PUBENV="/data/hftprop/envs/py311"          # 公共运行环境（hftprop 组）
WHEELHOUSE="$DST/wheelhouse"               # wheel 归档（仅 cken；安装由 cken 执行）
SOCK="/tmp/xj_deploy_cm.sock"
REPO="SignalMaker"
# 非机密默认：因子产出落盘根（findata#31 配置默认化模式）。--release 时写进公共环境
# activate.d/signalmaker_env.sh（由本脚本维护，env 重建即重写），任何人 conda activate 后即就绪。
# 落盘布局 {root}/{stage}/{slot}/{author}/{name}/{yyyymmdd}.h5。机密绝不进 activate.d。
# 落点 /data/hftprop/factor_pool：hftprop 组目录(2770 setgid)可写、与 envs/infra 同级持久盘
#（/data/findata 是 don:research 755、组外只读，不可用）。落点经 cken 确认（2026-06-18）。
SM_OUTPUT_ROOT="/data/hftprop/factor_pool"
# signalmaker 自身的三方依赖（与 SignalMaker/pyproject.toml 保持同步；findata/cube 的
# 三方依赖由 findata 部署链的 PYPI_DEPS 负责，不在此重复）
# joblib：n_jobs>1 并行刷因子的 loky 进程池引擎（v0.1.0 新增；公网 PyPI 包）
PYPI_DEPS="numpy pandas joblib"

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
    || { echo "✗ SignalMaker 工作区有未提交改动；发版部署要求与仓库一致（先 commit/stash）" >&2; exit 1; }
  TAG="$(git describe --exact-match --tags HEAD 2>/dev/null)" \
    || { echo "✗ SignalMaker HEAD 不在 tag 上；先跑 scripts/release.sh X.Y.Z 再 --release" >&2; exit 1; }
  ver_file="$(cat signalmaker/VERSION.txt)"
  [[ "v$ver_file" == "$TAG" ]] \
    || { echo "✗ tag ($TAG) 与 VERSION.txt ($ver_file) 不一致" >&2; exit 1; }
  echo "  ok: signalmaker $TAG"
fi

# 复用/建立 SSH ControlMaster（避免反复握手）
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

# 记录本次部署来源版本（本机 commit + 是否有未提交改动）
STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
cd "$SRC/$REPO"
rev="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
dirty="$(git status -s 2>/dev/null | wc -l | tr -d ' ')"
"${SSH[@]}" "$HOST" "printf '%s\n' 'deployed_at: $STAMP' 'src_commit: $rev' 'uncommitted_files: $dirty' > '$DST/$REPO/DEPLOYED_FROM.txt'"

# 收紧权限（仅 cken；目录已 700，这里确保文件无 group/other 位）
"${SSH[@]}" "$HOST" "chmod -R go-rwx '$DST/$REPO'"
echo "==> 同步完成"

if [[ "$RUN_TEST" == "1" ]]; then
  # 测试依赖同级源码副本 findata/cube（conftest 自动接 sys.path），缺位先跑 findata 侧 dev 同步
  echo "==> 服务器 py311 跑源码测试"
  "${SSH[@]}" "$HOST" "[[ -d '$DST/findata' && -d '$DST/cube' ]] \
      || { echo '✗ 缺源码副本 $DST/{findata,cube}：先跑 deploy_to_xinjiang.sh（findata 侧 dev 同步）' >&2; exit 1; } && \
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate py311 && \
    cd '$DST/$REPO' && python -m pytest tests/ -q 2>&1 | tail -3"
fi

# ---- 发版：build wheel → wheelhouse → 安装公共环境 → smoke ----
if [[ "$RELEASE" == "1" ]]; then
  echo "==> 发版 $TAG：构建 wheel 并更新公共环境 $PUBENV"
  "${SSH[@]}" "$HOST" "DST='$DST' PUBENV='$PUBENV' WHEELHOUSE='$WHEELHOUSE' TAG='$TAG' \
      STAMP='$STAMP' REPO='$REPO' PYPI_DEPS='$PYPI_DEPS' SM_OUTPUT_ROOT='$SM_OUTPUT_ROOT' bash -s" <<'REMOTE'
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py311                       # 构建用 cken 个人 py311

# 0) 前置：公共环境必须已由 findata 侧 --release 建好并装入 findata+cube
[[ -x "$PUBENV/bin/python" ]] \
  || { echo "✗ 公共环境 $PUBENV 不存在：先跑 deploy_to_xinjiang.sh --release（findata 侧）" >&2; exit 1; }
"$PUBENV/bin/python" -c "import findata, cube" 2>/dev/null \
  || { echo "✗ 公共环境缺 findata/cube：先跑 deploy_to_xinjiang.sh --release（findata 侧）" >&2; exit 1; }
fver="$("$PUBENV/bin/python" -c "import findata; print(findata.__version__)")"

# 1) 构建 wheel（纯 python，py3-none-any；--no-build-isolation 免公网拉 setuptools）
python -m pip install -qU setuptools wheel
TMP="$(mktemp -d)"
python -m pip wheel --no-deps --no-build-isolation -w "$TMP" "$DST/$REPO"
rm -rf "$DST/$REPO"/build "$DST/$REPO"/*.egg-info
ls -l "$TMP"/*.whl

# 2) 归档到 wheelhouse
mkdir -p "$WHEELHOUSE"
cp -f "$TMP"/*.whl "$WHEELHOUSE/"

# 3) 三方依赖走 PyPI；signalmaker 只从本地 wheel 装（--no-index --no-deps，
#    防 pip 从公网解析内部依赖 findata/cube——PyPI 有无关同名包 cube）
"$PUBENV/bin/python" -m pip install -U $PYPI_DEPS
"$PUBENV/bin/python" -m pip install --no-index --no-deps --force-reinstall "$TMP"/*.whl
"$PUBENV/bin/python" -m pip check

# 4) 锁定本次发布的完整环境快照 + 发布台账（快照带包名前缀，与 findata 的区分）
"$PUBENV/bin/python" -m pip freeze > "$WHEELHOUSE/constraints-signalmaker-$TAG.txt"
echo "$STAMP  signalmaker $TAG  findata==$fver" >> "$WHEELHOUSE/RELEASES.log"

# 4.5) 非机密默认化（findata#31 模式）：把 SIGNALMAKER_OUTPUT_ROOT 写进公共环境 activate.d。
#      由本脚本维护——env 重建（重跑 --release）即重写，绝不丢；机密 DSN 不在此设。
ACT_D="$PUBENV/etc/conda/activate.d"
mkdir -p "$ACT_D"
cat > "$ACT_D/signalmaker_env.sh" <<EOF
#!/bin/sh
# SignalMaker 公共环境默认（非机密）——因子产出落盘根。
# 落盘布局 {root}/{stage}/{slot}/{author}/{name}/{yyyymmdd}.h5。
# 沿 findata#31 配置默认化：非机密走 activate.d，本文件由 deploy_signalmaker_to_xinjiang.sh --release
# 维护（env 重建即重写，勿手改）。机密(如 FINDATA_MYSQL_DSN)不在此设——见 findata_env.sh 同款约定。
export SIGNALMAKER_OUTPUT_ROOT=$SM_OUTPUT_ROOT
EOF
chmod 644 "$ACT_D/signalmaker_env.sh"
# 落盘根目录：hftprop 组共享、setgid → 组内成员产出自动归 hftprop 组（lgj 等可读写）
mkdir -p "$SM_OUTPUT_ROOT"
chmod 2775 "$SM_OUTPUT_ROOT" 2>/dev/null || true
echo "  activate.d/signalmaker_env.sh -> SIGNALMAKER_OUTPUT_ROOT=$SM_OUTPUT_ROOT"
echo "  落盘根: $(ls -ld "$SM_OUTPUT_ROOT" | awk '{print $1, $3":"$4, $NF}')"

# 5) 权限：环境对 hftprop 组开放（组内可用），组外不可见；wheelhouse 维持仅 cken
chmod -R g+rX,o-rwx /data/hftprop/envs
chmod -R go-rwx "$WHEELHOUSE"

# 6) smoke：用「已安装的包」跑（中性 cwd、不依赖源码目录与 FINDATA_CUBE_PATH）——
#    mock 数据上完整走一遍 FactorBase 声明 → Executor 逐 (交易日,slot) 执行
cd /tmp
env -u FINDATA_CUBE_PATH -u PYTHONPATH FINDATA_DATA_ROOT=/data/findata "$PUBENV/bin/python" - <<'PY'
import signalmaker, findata
print(f"smoke: signalmaker {signalmaker.__version__} / findata {findata.__version__}")
findata.mock.install()
from signalmaker import FactorBase, Slot, Executor

class DeploySmoke(FactorBase):
    name = "deploy_smoke"; author = "deploy"; schedule = [Slot.EOD]; outputs = ["deploy_smoke"]

    def load(self, start_ds, end_ds, code_list):
        # 量价-only → EOD：当日 bar 真实存在，end_ds 直接取当日
        load_start = findata.get_prev_date(start_ds, n=5)
        # findata#17 起 stock_quote 默认 stack_df，喂 SignalMaker（cube_history）须显式 rtype="cube"
        return {"quote": findata.stock_quote(load_start, end_ds, code=code_list, adjust="hfq", rtype="cube")}

    def calculate(self, ctx):
        close = ctx.cube_history("quote", field="close", day_window=5, rtype="array")
        return {"deploy_smoke": -(close[-1] / close[0] - 1.0)}

out = Executor().run(DeploySmoke, "20240115", "20240119", universe=["000001.SZ", "600000.SH"])
arr = out.fnp("deploy_smoke")
print(f"smoke: Executor.run(mock) -> {arr.shape} (t={len(out.t_list)}, c={len(out.c_list)})")
PY

# 7) 验证 activate.d 经 conda activate 真生效（使用方 conda activate 后即就绪，非机密默认到位）
conda deactivate 2>/dev/null || true
conda activate "$PUBENV"
echo "  verify(conda activate $PUBENV): SIGNALMAKER_OUTPUT_ROOT=[${SIGNALMAKER_OUTPUT_ROOT:-}]  FINDATA_DATA_ROOT=[${FINDATA_DATA_ROOT:-}]"
[ -n "${SIGNALMAKER_OUTPUT_ROOT:-}" ] \
  || { echo "✗ activate.d 未生效：conda activate 后 SIGNALMAKER_OUTPUT_ROOT 仍为空" >&2; exit 1; }
echo "--- 发版完成：$TAG 已装入 $PUBENV ---"
REMOTE
fi

echo "==> 全部完成。源码在 $DST/$REPO$([[ "$RELEASE" == "1" ]] && echo "；$TAG 已发布到 $PUBENV" || true)"
