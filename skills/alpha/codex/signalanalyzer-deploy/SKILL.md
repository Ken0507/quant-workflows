---
name: signalanalyzer-deploy
description: "SignalAnalyzer(含 sa_mcp) 部署到新疆投研机 k8s-worker-01：dev 模式同步源码副本调试；release 模式 build wheel → wheelhouse 发包 → 安装公共 py311 环境 → smoke 验证。挂在 findata + signalmaker 部署链上(公共环境须已有 findata+cube+signalmaker)。"
---

# signalanalyzer-deploy — SignalAnalyzer 部署到新疆投研机

通过 `~/alpha_projects/.agents/skills/signalanalyzer-deploy/deploy_signalanalyzer_to_xinjiang.sh`
把 SignalAnalyzer(评价核心库 `signalanalyzer` + MCP server `sa_mcp`)部署到 k8s-worker-01
(`222.81.173.58`)。服务器零 GitHub 凭证,代码只经本机 rsync(SAML 约束,见 findata#11)。
挂在 findata + signalmaker 部署链上:wheelhouse / 公共环境 / 保密边界全部复用前两者。

## 使用方式

```
$signalanalyzer-deploy                  # dev 模式：同步源码 + 服务器跑测试
$signalanalyzer-deploy --no-test        # dev 模式：只同步
$signalanalyzer-deploy release          # 发版部署：build wheel → 装公共 py311 环境
$signalanalyzer-deploy release --no-test
```

## 两种模式

| 模式 | 命令 | 影响范围 |
|---|---|---|
| **dev**（默认） | `bash ~/alpha_projects/.agents/skills/signalanalyzer-deploy/deploy_signalanalyzer_to_xinjiang.sh [--no-test]` | 只更新服务器源码副本 `/data/hftprop/infra/SignalAnalyzer`（仅 cken 可见），供自己调试；公共环境与使用方无感知 |
| **release** | `bash ~/alpha_projects/.agents/skills/signalanalyzer-deploy/deploy_signalanalyzer_to_xinjiang.sh --release [--no-test]` | build wheel（含 signalanalyzer + sa_mcp）→ 归档 `wheelhouse/` → 安装公共环境 `/data/hftprop/envs/py311`（hftprop 组 = cken+lgj）→ 装包 smoke |

release 模式预检（脚本强校验，失败即中止）：SignalAnalyzer 工作区干净 + HEAD 在
release tag 上 + tag 与 `signalanalyzer/VERSION.txt` 一致。**不满足说明还没定版，先跑
`$signalanalyzer-release`**。

**前置依赖**：公共环境里必须已装 findata + cube + **signalmaker**（SA 的 `load_factor`
委托 `signalmaker.load_factors`）。缺位脚本会中止——先跑 `$findata-deploy release`、
再跑 `$signalmaker-deploy release`。

## 执行后验收清单

dev 模式看测试尾巴：SignalAnalyzer `tests/` 全过。源码测试依赖同级源码副本
`/data/hftprop/infra/{findata,cube,SignalMaker}`（conftest 自动接 sys.path），缺位先跑
findata / signalmaker 侧 dev 同步。

release 模式额外确认四件事：
1. wheel 构建成功（`signalanalyzer-X.Y.Z-py3-none-any`，含 signalanalyzer + sa_mcp）
2. `pip check` 无报错
3. smoke 三行全出：`signalanalyzer X.Y.Z / signalmaker a.b.c / findata d.e.f` 版本号正确 /
   `signalanalyzer.data 核心接口在位`（load_factor/load_labels/close_to_close_labels/…）/
   `sa_mcp 导入 OK`
4. `wheelhouse/` 留痕齐全：wheel、`constraints-signalanalyzer-vX.Y.Z.txt`、`RELEASES.log` 新行

## 故障排查

- **ssh 连不上 / 卡住**：ControlMaster sock 残留 → `rm /tmp/xj_deploy_cm.sock` 重试。
- **公共环境缺 findata/cube/signalmaker**：先跑 findata 侧、再 signalmaker 侧 `--release`。
- **pip 装出莫名其妙的 cube**：PyPI 有无关同名包 `cube`——signalanalyzer/signalmaker/findata/cube
  永远 `--no-index` 从本地 wheel 装,脚本已内置;手工操作时切勿公网索引解析这几个包。
- **sa_mcp 导入失败 / smoke 缺 mcp**：`mcp` SDK 在 deploy 脚本 `PYPI_DEPS` 里装；确认
  `pip show mcp` 有值。matplotlib/reportlab 缺失只影响 `generate_report` 出 PDF。
- **import 到旧版本**：检查服务器 shell 有无残留 `PYTHONPATH` 指向源码目录；
  `pip show signalanalyzer` 看公共环境实际版本。
- **三方依赖缺失（pip check 报错）**：signalanalyzer 的三方依赖两处需同步——deploy 脚本
  `PYPI_DEPS`(numpy pandas mcp matplotlib reportlab) 与 `pyproject.toml`；findata/cube/signalmaker
  的三方依赖归各自部署链管。

## 回滚

```bash
ssh cken@222.81.173.58
/data/hftprop/envs/py311/bin/pip install --no-index --no-deps \
    --find-links=/data/hftprop/infra/wheelhouse 'signalanalyzer==<旧版本>'
# 或按 wheelhouse/constraints-signalanalyzer-v<旧版本>.txt 重建环境
```

## 收尾

- release 部署完成后，可用 issue-update 把部署记录（版本、测试结果、smoke）
  追加到 SignalAnalyzer #8（部署记录）。
- 使用方说明（不需要 pip）：`conda activate /data/hftprop/envs/py311` 直接
  `import signalanalyzer` / `python -m sa_mcp.install` 注册评价 MCP；环境变量与 findata 一致
  （`FINDATA_DATA_ROOT` / `FINDATA_UNIVERSE_ROOT` 由 activate.d 提供，DSN 由 findata 集中提供）。
