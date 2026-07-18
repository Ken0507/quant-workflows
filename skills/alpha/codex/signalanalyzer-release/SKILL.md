---
name: signalanalyzer-release
description: "SignalAnalyzer 定版发布：预检 CHANGELOG/工作区 → scripts/release.sh 打 tag → push。发布后衔接 $signalanalyzer-deploy release 部署到新疆投研机公共环境。与 findata-release / signalmaker-release 同模式。"
---

# signalanalyzer-release — SignalAnalyzer 定版发布

对 `hft-prop/SignalAnalyzer` 做一次正式发版：写 `signalanalyzer/VERSION.txt`、切 CHANGELOG、
打 `vX.Y.Z` tag、push。流程与 findata-release / signalmaker-release 同模式（约定见 findata#12）。

> 仓库位置 `~/alpha_projects/SignalAnalyzer`。发版只定版不部署；部署到新疆投研机
> 用 `$signalanalyzer-deploy release`（完整发版 = 本 skill → signalanalyzer-deploy）。
> 打包两包 `signalanalyzer` + `sa_mcp`,版本单一事实源 = `signalanalyzer/VERSION.txt`。

## 使用方式

```
$signalanalyzer-release            # 自动建议版本号，确认后发布
$signalanalyzer-release 0.1.1      # 指定版本号
$signalanalyzer-release --dry-run  # 只预演（release.sh 原生支持），不落地
```

## 执行流程

### 1. 预检（不满足先修，不要硬闯）

```bash
cd ~/alpha_projects/SignalAnalyzer
git status                      # 必须干净、在 main
git log origin/main..HEAD       # 必须与 origin 同步（release.sh 也会强校验）
```

⚠️ **push 鉴权**：SignalAnalyzer 走 `git@github-hft` SSH,hft-prop SAML 会过期。若
`git fetch/push` 报权限失败,先跑 `$gh-saml-refresh` 刷新授权再发版。

检查 `CHANGELOG.md` 的「## [未发布]」段：
- **必须有实际内容**（release.sh 强校验，空段中止）；
- 若本次变更没写进去，先按 Keep a Changelog 格式补好（`新增`/`变更`/`修复`/…），
  再走发布——CHANGELOG 段落就是 tag 说明,质量直接面向读者。

### 2. 确定版本号

读当前版本 `cat signalanalyzer/VERSION.txt`，按语义化版本建议：
- 有不兼容接口变更（Analyzer / sa_mcp 工具签名 / data 接口语义）→ major（v1 前可放宽为 minor）
- 新增接口 / 能力 / 参数 → minor
- 纯修复 / 文档 → patch

用户未指定版本号时，给出建议并**与用户确认后**再执行。

### 3. 发布

```bash
scripts/release.sh X.Y.Z          # 可先 scripts/release.sh X.Y.Z --dry-run 预演
```

脚本自带全部预检（main / 干净 / 同步 / tag 不存在 / 版本递增 / CHANGELOG 非空），
任一失败即中止；成功 = release commit + annotated tag 已 push。

> 注：SignalAnalyzer 仓目前**无 release CI workflow**（不同于 findata/SM），发版只 push
> tag、不自动挂 GitHub Release 资产；部署用的 wheel 由 deploy 脚本在服务器本地构建。

## 收尾

- 发布完成后衔接 `$signalanalyzer-deploy release` 部署到新疆投研机公共环境
  （服务器零 GitHub 凭证，见 findata#11/#12）。
- 可用 issue-update 把发版记录追加到 SignalAnalyzer 相关 issue（如 #8 部署记录）。
