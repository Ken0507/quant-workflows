#!/usr/bin/env bash
# 把本机 findata + cube 部署到新疆投研机 k8s-worker-01（rsync 方案，服务器不碰 GitHub）。
#
#   bash deploy_to_xinjiang.sh                  # 开发同步：rsync 源码 + 服务器跑源码测试
#   bash deploy_to_xinjiang.sh --no-test        # 只同步源码，不跑测试
#   bash deploy_to_xinjiang.sh --release        # 发版部署：rsync(staging) → 源码测试 →
#                                               #   门②真实数据闸门 → build wheel → 发包 wheelhouse →
#                                               #   安装公共 py311 → smoke（staging→gate→promote）
#   bash deploy_to_xinjiang.sh --release --no-test            # 跳过源码 mock 测试（门②与 wheel smoke 仍跑）
#   bash deploy_to_xinjiang.sh --release --skip-realdata-gate # 应急：跳过门②真实数据闸门（风险自负）
#
# 两种模式的分工：
#   开发同步 —— 源 = 本机当前工作区（含未提交改动），只更新服务器源码副本
#               /data/hftprop/infra/{findata,cube}，供 cken 自己在服务器上调试；
#               不碰公共环境，研究使用方无感知。
#   发版部署 —— 要求 findata HEAD 落在 release tag 上（先跑 scripts/release.sh X.Y.Z），
#               在服务器上从源码构建 wheel，归档到 wheelhouse，并安装进公共 py311 环境
#               /data/hftprop/envs/py311（hftprop 组=cken+lgj 可用）。
#
# 服务器无任何 GitHub 凭证（SAML 约束，见 findata#11），更新代码只经本机 rsync。
# ⚠️ cube 在 PyPI 有无关同名包：cube/findata 永远从本地 wheel 文件安装（--no-index），
#    只有三方依赖（numpy/pandas/...）走公网 PyPI。
set -euo pipefail

SRC="/home/cken/alpha_projects"
HOST="cken@222.81.173.58"
DST="/data/hftprop/infra"                  # 服务器源码落点（仅 cken）
PUBENV="/data/hftprop/envs/py311"          # 公共运行环境（hftprop 组）
WHEELHOUSE="$DST/wheelhouse"               # wheel 归档（仅 cken；安装由 cken 执行）
SOCK="/tmp/xj_deploy_cm.sock"
REPOS=(findata cube)
# 公共环境的三方依赖（与 findata/pyproject.toml + cube/pyproject.toml 保持同步）
PYPI_DEPS="numpy pandas pyarrow sqlalchemy pymysql clickhouse-connect h5py tqdm pytz"

RUN_TEST=1 RELEASE=0 SKIP_GATE=0
for arg in "$@"; do
  case "$arg" in
    --no-test) RUN_TEST=0 ;;
    --release) RELEASE=1 ;;
    --skip-realdata-gate) SKIP_GATE=1 ;;
    *) echo "未知参数: $arg" >&2; exit 1 ;;
  esac
done

# ---- 发版预检（本机）----
TAG=""
if [[ "$RELEASE" == "1" ]]; then
  echo "==> 发版预检"
  cd "$SRC/findata"
  [[ -z "$(git status --porcelain)" ]] \
    || { echo "✗ findata 工作区有未提交改动；发版部署要求与仓库一致（先 commit/stash）" >&2; exit 1; }
  TAG="$(git describe --exact-match --tags HEAD 2>/dev/null)" \
    || { echo "✗ findata HEAD 不在 tag 上；先跑 scripts/release.sh X.Y.Z 再 --release" >&2; exit 1; }
  ver_file="$(cat findata/VERSION.txt)"
  [[ "v$ver_file" == "$TAG" ]] \
    || { echo "✗ tag ($TAG) 与 VERSION.txt ($ver_file) 不一致" >&2; exit 1; }
  if [[ -n "$(cd "$SRC/cube" && git status --porcelain)" ]]; then
    echo "  ⚠ cube 工作区有未提交改动，将随源码进 wheel（cube 仓版本号不治理，仅提示）"
  fi
  echo "  ok: findata $TAG"
fi

# 复用/建立 SSH ControlMaster（避免反复握手）
ssh -S "$SOCK" -O check "$HOST" 2>/dev/null \
  || ssh -M -S "$SOCK" -o ControlPersist=600 -o ConnectTimeout=15 -fN "$HOST"
SSH=(ssh -S "$SOCK")

EXCLUDES=(--exclude '.git' --exclude '__pycache__' --exclude '.pytest_cache'
          --exclude 'docs/build' --exclude '*.pyc' --exclude '.ipynb_checkpoints'
          --exclude '*.egg-info' --exclude 'build' --exclude 'dist')

echo "==> 同步代码到 $HOST:$DST"
"${SSH[@]}" "$HOST" "mkdir -p '$DST' && chmod 700 '$DST'"
for repo in "${REPOS[@]}"; do
  echo "  - $repo"
  rsync -az --delete -e "ssh -S $SOCK" "${EXCLUDES[@]}" "$SRC/$repo" "$HOST:$DST/"
done

# 记录本次部署来源版本（本机 commit + 是否有未提交改动）
STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
for repo in "${REPOS[@]}"; do
  cd "$SRC/$repo"
  rev="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
  dirty="$(git status -s 2>/dev/null | wc -l | tr -d ' ')"
  "${SSH[@]}" "$HOST" "printf '%s\n' 'deployed_at: $STAMP' 'src_commit: $rev' 'uncommitted_files: $dirty' > '$DST/$repo/DEPLOYED_FROM.txt'"
done

# 收紧权限（仅 cken；目录已 700，这里确保文件无 group/other 位）
"${SSH[@]}" "$HOST" "chmod -R go-rwx '$DST/findata' '$DST/cube'"
echo "==> 同步完成"

if [[ "$RUN_TEST" == "1" ]]; then
  echo "==> 服务器 py311 跑源码测试"
  "${SSH[@]}" "$HOST" "source ~/miniconda3/etc/profile.d/conda.sh && conda activate py311 && \
    export FINDATA_CUBE_PATH='$DST/cube' && \
    echo '--- findata ---' && (cd '$DST/findata' && python -m pytest tests/ -q 2>&1 | tail -3) && \
    echo '--- cube ---'    && (cd '$DST/cube'    && python -m pytest tests/ -q --ignore=tests/regression_test.py 2>&1 | tail -3)"
fi

# ---- 门②：promote 前真实数据闸门（在 staged 源码 + 服务器真实 jydb 上零差对账）----
# staging→gate→promote：rsync 已把 staged 源码（含 scripts/release_gate_realdata.py）落到 $DST，
# 这里在服务器 py311（conda env vars 已注入 FINDATA_MYSQL_DSN、直连 jydb）跑门②；不过即中止，
# 绝不往下 build/install 去顶替别人在用的公共环境 $PUBENV（fin-infra/findata#27）。
if [[ "$RELEASE" == "1" ]]; then
  if [[ "$SKIP_GATE" == "1" ]]; then
    echo "==> 门②  ⚠ --skip-realdata-gate 跳过（仅限服务器无 jydb 连接的应急，风险自负）"
  else
    echo "==> 门②  服务器真实数据零差对账（staged 源码，promote 前）"
    "${SSH[@]}" "$HOST" "source ~/miniconda3/etc/profile.d/conda.sh && conda activate py311 && \
      export FINDATA_CUBE_PATH='$DST/cube' && cd '$DST/findata' && \
      python scripts/release_gate_realdata.py" \
      || { echo "✗ 门② 未通过 → 中止发版，公共环境 $PUBENV 未改动（staged 源码已在 $DST，可排查）" >&2; exit 1; }
  fi
fi

# ---- 发版：build wheel → wheelhouse → 安装公共环境 → smoke ----
if [[ "$RELEASE" == "1" ]]; then
  echo "==> 发版 $TAG：构建 wheel 并更新公共环境 $PUBENV"
  cube_rev="$(cd "$SRC/cube" && git rev-parse --short HEAD 2>/dev/null || echo '?')"
  "${SSH[@]}" "$HOST" "DST='$DST' PUBENV='$PUBENV' WHEELHOUSE='$WHEELHOUSE' TAG='$TAG' \
      STAMP='$STAMP' CUBE_REV='$cube_rev' PYPI_DEPS='$PYPI_DEPS' bash -s" <<'REMOTE'
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py311                       # 构建用 cken 个人 py311

# 1) 构建 wheel（纯 python，py3-none-any；--no-build-isolation 免公网拉 setuptools）
python -m pip install -qU setuptools wheel
TMP="$(mktemp -d)"
python -m pip wheel --no-deps --no-build-isolation -w "$TMP" "$DST/cube" "$DST/findata"
rm -rf "$DST"/cube/build "$DST"/cube/*.egg-info "$DST"/findata/build "$DST"/findata/*.egg-info
ls -l "$TMP"/*.whl

# 2) 归档到 wheelhouse
mkdir -p "$WHEELHOUSE"
cp -f "$TMP"/*.whl "$WHEELHOUSE/"

# 3) 公共环境：不存在则创建
if [[ ! -x "$PUBENV/bin/python" ]]; then
  echo "--- 公共环境不存在，创建 $PUBENV ---"
  # conda-forge --override-channels：绕开 repo.anaconda.com 默认渠道的 ToS/商业授权门槛（findata#17 部署）。
  # 显式带 pip：conda-forge 的裸 python 不自带 pip（默认渠道 python 才捆绑）。
  conda create -y -p "$PUBENV" -c conda-forge --override-channels python=3.11 pip
fi

# 4) 三方依赖走 PyPI；cube/findata 只从本地 wheel 装（--no-index，防 PyPI 同名包 cube）
"$PUBENV/bin/python" -m pip install -qU pip
"$PUBENV/bin/python" -m pip install -U $PYPI_DEPS
"$PUBENV/bin/python" -m pip install --no-index --no-deps --force-reinstall "$TMP"/*.whl
"$PUBENV/bin/python" -m pip check

# 5) 锁定本次发布的完整环境快照 + 发布台账
"$PUBENV/bin/python" -m pip freeze > "$WHEELHOUSE/constraints-$TAG.txt"
echo "$STAMP  findata $TAG  cube@$CUBE_REV" >> "$WHEELHOUSE/RELEASES.log"

# 6) 权限：环境对 hftprop 组开放（组内可用），组外不可见；wheelhouse 维持仅 cken
chmod -R g+rX,o-rwx /data/hftprop/envs
chmod -R go-rwx "$WHEELHOUSE"

# 7) smoke：用「已安装的包」跑（中性 cwd、不依赖源码目录与 FINDATA_CUBE_PATH）
cd /tmp
env -u FINDATA_CUBE_PATH FINDATA_DATA_ROOT=/data/findata "$PUBENV/bin/python" - <<'PY'
import findata, cube
print(f"smoke: findata {findata.__version__} / cube wheel OK")
findata.mock.install()
print("smoke: catalog", findata.catalog().shape)
c = findata.stock_quote(20240102, 20240105, field="close", rtype="fdf")   # v0.3.0: narrow/wide→stack_df/fdf (findata#17)
print("smoke: stock_quote(mock)", c.shape)
PY
echo "--- 发版完成：$TAG 已装入 $PUBENV ---"
REMOTE
fi

echo "==> 全部完成。源码在 $DST/{findata,cube}$([[ "$RELEASE" == "1" ]] && echo "；$TAG 已发布到 $PUBENV" || true)"
