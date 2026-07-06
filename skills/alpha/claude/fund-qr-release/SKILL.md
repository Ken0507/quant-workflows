---
name: fund-qr-release
description: "fund-qr（基本面案例显微镜 MCP server）定版发布：预检 CHANGELOG/工作区 → scripts/release.sh 打 tag → push。发布后衔接 /fund-qr-deploy release 部署到新疆投研机公共环境。与 signalanalyzer-release 同模式（vendor 轻量）。"
---

# fund-qr-release — fund-qr 定版发布

对 `hft-prop/fund-qr` 做一次正式发版：写 `src/fund_qr/VERSION.txt`、切 CHANGELOG、
打 `vX.Y.Z` tag、push。流程与 signalanalyzer-release / findata-release 同模式。

> 仓库位置 `~/alpha_projects/fund-qr`。发版只定版不部署；部署到新疆投研机
> 用 `/fund-qr-deploy release`（完整发版 = 本 skill → fund-qr-deploy）。
> 打包一个包 `fund_qr`（纯 agent MCP 工具面），版本单一事实源 = `src/fund_qr/VERSION.txt`。

## 使用方式

```
/fund-qr-release            # 自动建议版本号，确认后发布
/fund-qr-release 0.1.0      # 指定版本号
/fund-qr-release 0.1.0 --dry-run   # 只预演（release.sh 原生支持），不落地
```

## 执行流程

### 1. 预检（不满足先修，不要硬闯）

```bash
cd ~/alpha_projects/fund-qr
git status                      # 必须干净、在 main（release.sh 也会强校验）
```

- CHANGELOG.md 的「## [Unreleased]」段**必须有实际内容**（release.sh 强校验，空段中止）；
  没写就先按 Keep a Changelog 格式补（`### Added`/`Changed`/`Verified`/…）——段落即 tag 说明。
- **push 鉴权**：fund-qr 走 HTTPS，release.sh 自动用 `gh auth token --user ken-chen_scale` 注入
  x-access-token（hft-prop SAML 下 SSH 会过期，本机走 HTTPS+token）。取不到 token 会中止，
  先 `gh auth login`（企业账号 ken-chen_scale）。

### 2. 确定版本号

读 `cat src/fund_qr/VERSION.txt`，按语义化版本建议：
- 不兼容的 MCP 工具签名 / 输出契约变更 → major（v1 前可放宽 minor）
- 新增工具 / 能力 / 参数 → minor
- 纯修复 / 文档 → patch

**首发 = v0.1.0**（VERSION.txt 已 0.1.0、CHANGELOG 仍 `[Unreleased]`）。用户未指定时给建议并**确认后**执行。

### 3. 发布

```bash
scripts/release.sh X.Y.Z          # 可先 scripts/release.sh X.Y.Z --dry-run 预演
```

脚本自带全部预检（main / 干净 / 与远端同步 / tag 不存在 / CHANGELOG 非空），
任一失败即中止；成功 = release commit + annotated tag 已 push。

> fund-qr 仓**无 CI**（同 SignalAnalyzer）：发版只 push tag，不挂 GitHub Release 资产；
> 部署 wheel 由 deploy 脚本在服务器本地构建。

## 收尾

- 发布完成后衔接 `/fund-qr-deploy release` 装进新疆投研机公共环境（服务器零 GitHub 凭证）。
- 装进公共环境后，`fund_qr` 即可 import → 下次 ae-fin-platform `publish.sh quantamental --server`
  + 研究员 `/alpha-onboard` 会**自动纳入 fund-qr MCP**（onboard 逐 server 探测 import，无需改配置）。
- 可用 issue-update 把发版记录追加到相关 issue（如 ae-fin-platform#2 接入台账）。
