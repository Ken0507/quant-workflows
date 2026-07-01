---
name: signalmaker-release
description: "SignalMaker 定版发布：预检 CHANGELOG/工作区 → scripts/release.sh 打 tag → 验证 CI（wheel + GitHub Release + Pages 文档）。发布后衔接 /signalmaker-deploy release 部署到新疆投研机公共环境。"
---
# signalmaker-release — SignalMaker 定版发布

对 `hft-prop/SignalMaker` 做一次正式发版：写 `VERSION.txt`、切 CHANGELOG、打 `vX.Y.Z` tag、
push 触发 CI（构建 wheel 挂 GitHub Release + 重建 Pages 文档）。流程与 findata-release
同模式（约定见 findata#12）。

> 仓库位置 `~/alpha_projects/SignalMaker`。发版只定版不部署；部署到新疆投研机
> 用 `/signalmaker-deploy release`（完整发版 = 本 skill → signalmaker-deploy）。

## 使用方式

```
/signalmaker-release            # 自动建议版本号，确认后发布
/signalmaker-release 0.1.0      # 指定版本号
/signalmaker-release --dry-run  # 只预演（release.sh 原生支持），不落地
```

## 执行流程

### 1. 预检（不满足先修，不要硬闯）

```bash
cd ~/alpha_projects/SignalMaker
git status                      # 必须干净、在 main
git log origin/main..HEAD       # 必须与 origin 同步（release.sh 也会强校验）
```

检查 `CHANGELOG.md` 的「## [未发布]」段：
- **必须有实际内容**（release.sh 强校验，空段中止）；
- 若本次变更没写进去，先按 Keep a Changelog 格式补好（`新增`/`变更`/`修复`/…），
  再走发布——CHANGELOG 段落就是 release notes 与 tag 说明，质量直接面向读者。

### 2. 确定版本号

读当前版本 `cat signalmaker/VERSION.txt`，按语义化版本建议：
- 有不兼容接口变更（FactorBase/Executor/Slot 语义）→ major（v1 前可放宽为 minor）
- 新增接口 / 能力 / 参数 → minor
- 纯修复 / 文档 → patch

用户未指定版本号时，给出建议并**与用户确认后**再执行。

### 3. 发布

```bash
scripts/release.sh X.Y.Z          # 可先 scripts/release.sh X.Y.Z --dry-run 预演
```

脚本自带全部预检（main / 干净 / 同步 / tag 不存在 / 版本递增 / CHANGELOG 非空），
任一失败即中止；成功 = release commit + annotated tag 已 push。

### 4. 验证 CI（hft-prop 仓 gh 操作必须带 token）

```bash
GH_TOKEN=$(gh auth token --user ken-chen_scale) gh run list --repo hft-prop/SignalMaker --limit 3
GH_TOKEN=$(gh auth token --user ken-chen_scale) gh release view vX.Y.Z --repo hft-prop/SignalMaker
```

确认 release workflow 全绿、Release 资产里有 `signalmaker-X.Y.Z-py3-none-any.whl`。

## 收尾

- 发布完成后衔接 `/signalmaker-deploy release` 部署到新疆投研机公共环境
  （服务器零 GitHub 凭证，CI 不部署，见 findata#11/#12）。
- 可用 issue-update 把发版记录追加到 SignalMaker 相关 issue。
