---
name: findata-deploy
description: "findata+cube 部署到新疆投研机 k8s-worker-01：dev 模式同步源码副本调试；release 模式 build wheel → wheelhouse 发包 → 安装公共 py311 环境 → smoke 验证。含验收清单与回滚方法。"
---

# findata-deploy — findata+cube 部署到新疆投研机

通过 `~/alpha_projects/deploy_to_xinjiang.sh` 把 findata + cube 部署到
k8s-worker-01（`222.81.173.58`）。服务器零 GitHub 凭证，代码只经本机 rsync
（SAML 约束，见 findata#11）。完整手册：`findata/docs/deploy_xinjiang.md`。

## 使用方式

```
/findata-deploy                  # dev 模式：同步源码 + 服务器跑测试
/findata-deploy --no-test        # dev 模式：只同步
/findata-deploy release          # 发版部署：build wheel → 装公共 py311 环境
/findata-deploy release --no-test
```

## 两种模式

| 模式 | 命令 | 影响范围 |
|---|---|---|
| **dev**（默认） | `bash ~/alpha_projects/deploy_to_xinjiang.sh [--no-test]` | 只更新服务器源码副本 `/data/hftprop/infra/{findata,cube}`（仅 cken 可见），供自己调试；公共环境与使用方无感知 |
| **release** | `bash ~/alpha_projects/deploy_to_xinjiang.sh --release [--no-test]` | build wheel → 归档 `wheelhouse/` → 安装公共环境 `/data/hftprop/envs/py311`（hftprop 组 = cken+lgj）→ 装包 smoke |

release 模式预检（脚本强校验，失败即中止）：findata 工作区干净 + HEAD 在
release tag 上 + tag 与 `VERSION.txt` 一致。**不满足说明还没定版，先跑
`/findata-release`**。cube 工作区有未提交改动只警告不阻断（cube 版本号不治理）。

## 执行后验收清单

dev 模式看两行测试尾巴：
- `--- findata ---` 全过（当前基线 ~287 passed）
- `--- cube ---` 111 passed / 4 failed 为已知基线（backfill 写死 `/home/lgj`，
  cube#4 跟踪中，与部署无关）

release 模式额外确认四件事：
1. wheel 构建成功（`cube-0.1.0` + `findata-X.Y.Z` 两个 `py3-none-any`）
2. `pip check` 无报错
3. smoke 三行全出：`findata X.Y.Z` 版本号正确 / `catalog (N, 7)` / `stock_quote(mock)` 形状正常
4. `wheelhouse/` 留痕齐全：wheel、`constraints-vX.Y.Z.txt`、`RELEASES.log` 新行

## 故障排查

- **ssh 连不上 / 卡住**：ControlMaster sock 残留 → `rm /tmp/xj_deploy_cm.sock` 重试。
- **pip 装出莫名其妙的 cube**：PyPI 有无关同名包 `cube`——cube/findata 永远
  `--no-index` 从本地 wheel 装，脚本已内置；手工操作时切勿公网索引解析这两个包。
- **import 到旧版本**：检查服务器 shell 有无残留 `FINDATA_CUBE_PATH`/`PYTHONPATH`
  指向源码目录；`pip show findata` 看公共环境实际版本。
- **三方依赖缺失（pip check 报错）**：依赖清单三处需同步——deploy 脚本 `PYPI_DEPS`、
  `findata/pyproject.toml`、`cube/pyproject.toml`。
- **公共环境损坏**：删 `/data/hftprop/envs/py311` 重跑 release 模式即可完整重建
  （wheel + constraints 都在 wheelhouse）。

## 回滚

```bash
ssh cken@222.81.173.58
/data/hftprop/envs/py311/bin/pip install --no-index \
    --find-links=/data/hftprop/infra/wheelhouse 'findata==<旧版本>'
# cube 同理；或按 wheelhouse/constraints-v<旧版本>.txt 重建环境
```

## 收尾

- release 部署完成后，可用 issue-update 把部署记录（版本、测试结果、smoke）
  追加到 findata#11 或相关 issue。
- 使用方说明（不需要 pip）：`conda activate /data/hftprop/envs/py311` 直接
  `import findata`；环境变量样例见 `findata/docs/deploy_xinjiang.md`。
