---
name: findata-release
description: "findata 定版发布：预检 CHANGELOG/工作区 → scripts/release.sh 打 tag → 验证 CI（wheel + GitHub Release + Pages 文档）。发布后衔接 /findata-deploy release 部署到新疆投研机公共环境。"
---

# findata-release — findata 定版发布

对 `fin-infra/findata` 做一次正式发版：写 `VERSION.txt`、切 CHANGELOG、打 `vX.Y.Z` tag、
push 触发 CI（构建 wheel 挂 GitHub Release + 重建 Pages 文档）。

> 仓库位置 `~/alpha_projects/findata`。发版只定版不部署；部署到新疆投研机
> 用 `/findata-deploy release`（完整发版 = 本 skill → findata-deploy）。

## 使用方式

```
/findata-release            # 自动建议版本号，确认后发布
/findata-release 0.3.0      # 指定版本号
/findata-release --dry-run  # 只预演（release.sh 原生支持），不落地
```

## 执行流程

### 1. 预检（不满足先修，不要硬闯）

```bash
cd ~/alpha_projects/findata
git status                      # 必须干净、在 main
git log origin/main..HEAD       # 必须与 origin 同步（release.sh 也会强校验）
```

检查 `CHANGELOG.md` 的「## [未发布]」段：
- **必须有实际内容**（release.sh 强校验，空段中止）；
- 若本次变更没写进去，先按 Keep a Changelog 格式补好（`新增`/`变更`/`修复`/…），
  再走发布——CHANGELOG 段落就是 release notes 与 tag 说明，质量直接面向读者。

### 2. 确定版本号

读当前版本 `cat findata/VERSION.txt`，按语义化版本建议：
- 有不兼容接口变更 → major（v1 前可放宽为 minor）
- 新增接口 / 数据集 / 参数 → minor
- 纯修复 / 文档 → patch

用户未指定版本号时，给出建议并**与用户确认后**再执行。

### 3. 发布

```bash
scripts/release.sh X.Y.Z          # 可先 scripts/release.sh X.Y.Z --dry-run 预演
```

脚本自带全部预检（main / 干净 / 同步 / tag 不存在 / 版本递增 / CHANGELOG 非空），
任一失败即中止；成功 = release commit + annotated tag 已 push。

### 4. 验证 CI（fin-infra 仓 gh 操作必须带 token）

```bash
GH_TOKEN=$(gh auth token --user ken-chen_scale) gh run list --repo fin-infra/findata --limit 3
GH_TOKEN=$(gh auth token --user ken-chen_scale) gh release view vX.Y.Z --repo fin-infra/findata
```

确认三件事：`release.yml` 绿（wheel 已挂 Release 资产）、`docs.yml` 绿（Pages 文档更新）、
GitHub Release 的 notes 来自本版本 CHANGELOG 段。

### 5. 收尾

- 提示下一步：`/findata-deploy release` 把本 tag 部署到新疆投研机公共 py311 环境。
- 重要版本可用 issue-update 把发布记录追加到相关 issue（如 findata#11）。

## 已知约定

- 版本号事实源 = `findata/VERSION.txt`（wheel 版本 = `__version__` = git tag 同源）。
- 不发 PyPI（内部保密包，pyproject 带 `Private :: Do Not Upload`）；分发只走
  服务器 wheelhouse 与 GitHub Release 资产。
- CI 够不着部署服务器（服务器零 GitHub 凭证，SAML 约束，见 findata#11），
  所以发布与部署是两步：CI 只产 wheel 工件，部署永远从本机 rsync。
