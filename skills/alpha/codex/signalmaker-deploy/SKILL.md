---
name: signalmaker-deploy
description: "SignalMaker 部署到新疆投研机 k8s-worker-01：dev 模式同步源码副本调试；release 模式 build wheel → wheelhouse 发包 → 安装公共 py311 环境 → smoke 验证。挂在 findata 部署链上（公共环境须已有 findata+cube）。"
---
# signalmaker-deploy — SignalMaker 部署到新疆投研机

通过 `~/alpha_projects/.codex/skills/signalmaker-deploy/deploy_signalmaker_to_xinjiang.sh` 把 SignalMaker 部署到
k8s-worker-01（`222.81.173.58`）。服务器零 GitHub 凭证，代码只经本机 rsync
（SAML 约束，见 findata#11）。挂在 findata 部署链上：wheelhouse / 公共环境 /
保密边界全部复用 findata 侧。完整手册：`SignalMaker/docs/deploy_xinjiang.md`。

## 使用方式

```
/signalmaker-deploy                  # dev 模式：同步源码 + 服务器跑测试
/signalmaker-deploy --no-test        # dev 模式：只同步
/signalmaker-deploy release          # 发版部署：build wheel → 装公共 py311 环境
/signalmaker-deploy release --no-test
```

## 两种模式

| 模式 | 命令 | 影响范围 |
|---|---|---|
| **dev**（默认） | `bash ~/alpha_projects/.codex/skills/signalmaker-deploy/deploy_signalmaker_to_xinjiang.sh [--no-test]` | 只更新服务器源码副本 `/data/hftprop/infra/SignalMaker`（仅 cken 可见），供自己调试；公共环境与使用方无感知 |
| **release** | `bash ~/alpha_projects/.codex/skills/signalmaker-deploy/deploy_signalmaker_to_xinjiang.sh --release [--no-test]` | build wheel → 归档 `wheelhouse/` → 安装公共环境 `/data/hftprop/envs/py311`（hftprop 组 = cken+lgj）→ 装包 smoke |

release 模式预检（脚本强校验，失败即中止）：SignalMaker 工作区干净 + HEAD 在
release tag 上 + tag 与 `VERSION.txt` 一致。**不满足说明还没定版，先跑
`/signalmaker-release`**。

**前置依赖**：公共环境里必须已装 findata + cube（findata 侧
`deploy_to_xinjiang.sh --release`），缺位脚本会中止——先跑 `/findata-deploy release`。

## 执行后验收清单

dev 模式看测试尾巴：SignalMaker `tests/` 全过（已知基线：
`test_pitframe_avail_ts_intraday_clamp` 受 findata#5 口径联动影响可能 fail，
与部署无关，跟踪见 SignalMaker 仓 issue）。源码测试依赖同级源码副本
`/data/hftprop/infra/{findata,cube}`，缺位先跑 `/findata-deploy`。

release 模式额外确认四件事：
1. wheel 构建成功（`signalmaker-X.Y.Z-py3-none-any`）
2. `pip check` 无报错
3. smoke 两行全出：`signalmaker X.Y.Z / findata a.b.c` 版本号正确 /
   `Executor.run(mock) -> (T, C)` 形状正常（mock 数据完整走 FactorBase → Executor）
4. `wheelhouse/` 留痕齐全：wheel、`constraints-signalmaker-vX.Y.Z.txt`、`RELEASES.log` 新行

## 故障排查

- **ssh 连不上 / 卡住**：ControlMaster sock 残留 → `rm /tmp/xj_deploy_cm.sock` 重试。
- **公共环境缺 findata/cube**：先跑 findata 侧 `deploy_to_xinjiang.sh --release`。
- **pip 装出莫名其妙的 cube**：PyPI 有无关同名包 `cube`——signalmaker/findata/cube
  永远 `--no-index` 从本地 wheel 装，脚本已内置；手工操作时切勿公网索引解析这几个包。
- **import 到旧版本**：检查服务器 shell 有无残留 `PYTHONPATH`/`FINDATA_CUBE_PATH`
  指向源码目录；`pip show signalmaker` 看公共环境实际版本。
- **三方依赖缺失（pip check 报错）**：signalmaker 的三方依赖两处需同步——deploy 脚本
  `PYPI_DEPS` 与 `SignalMaker/pyproject.toml`；findata/cube 的三方依赖归 findata 部署链管。
- **公共环境损坏**：删 `/data/hftprop/envs/py311`，先重跑 findata 侧 release 再跑本
  脚本 release（wheel + constraints 都在 wheelhouse，可完整重建）。

## 回滚

```bash
ssh cken@222.81.173.58
/data/hftprop/envs/py311/bin/pip install --no-index --no-deps \
    --find-links=/data/hftprop/infra/wheelhouse 'signalmaker==<旧版本>'
# 或按 wheelhouse/constraints-signalmaker-v<旧版本>.txt 重建环境
```

## 收尾

- release 部署完成后，可用 issue-update 把部署记录（版本、测试结果、smoke）
  追加到 SignalMaker 部署约定 issue。
- 使用方说明（不需要 pip）：`conda activate /data/hftprop/envs/py311` 直接
  `from signalmaker import FactorBase, Slot, Executor`；环境变量与 findata 一致
  （`FINDATA_DATA_ROOT` / 个人 `FINDATA_MYSQL_DSN`，`FINDATA_CUBE_PATH` 不要设）。
