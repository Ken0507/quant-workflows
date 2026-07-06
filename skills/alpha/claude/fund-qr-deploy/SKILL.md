---
name: fund-qr-deploy
description: "fund-qr（基本面案例显微镜 MCP server）部署到新疆投研机 k8s-worker-01：dev 模式同步源码副本调试；release 模式 build wheel → wheelhouse 发包 → 安装公共 py311 环境 → 功能 smoke（装配 server + 真实取数）。挂在 findata 部署链后（公共环境须已有 findata≥0.13）。"
---

# fund-qr-deploy — fund-qr 部署到新疆投研机

通过 `~/alpha_projects/.claude/skills/fund-qr-deploy/deploy_fund_qr_to_xinjiang.sh` 把 fund-qr
（`fund_qr` 包，纯 agent MCP 工具面）部署到 k8s-worker-01（`222.81.173.58`）。服务器零 GitHub
凭证，代码只经本机 rsync（SAML 约束，见 findata#11）。沿用 SignalAnalyzer 轻量部署模式。

## 使用方式

```
/fund-qr-deploy                  # dev 模式：同步源码 + 服务器跑源码测试（信息性）
/fund-qr-deploy --no-test        # dev 模式：只同步
/fund-qr-deploy release          # 发版部署：build wheel → 装公共 py311 环境 → 功能 smoke
/fund-qr-deploy release --no-test
```

## 两种模式

| 模式 | 命令 | 影响范围 |
|---|---|---|
| **dev**（默认） | `bash …/deploy_fund_qr_to_xinjiang.sh [--no-test]` | 只更新服务器源码副本 `/data/hftprop/infra/fund-qr`（仅 cken 可见），供调试；公共环境无感知 |
| **release** | `bash …/deploy_fund_qr_to_xinjiang.sh --release [--no-test]` | rsync → build wheel（`fund_qr`）→ 归档 `wheelhouse/` → 装公共环境 `/data/hftprop/envs/py311`（hftprop 组=cken+lgj）→ **功能 smoke** |

## 前置依赖（release 模式强校验，缺位即中止）

- 公共环境 `/data/hftprop/envs/py311` 已装 **findata ≥ 0.13**（avail_ts 语义，#54）——fund_qr 全部数据经 findata。
  不满足先跑 findata 侧 `--release`。
- 三方依赖（`numpy pandas mcp matplotlib`）通常已由 findata / SignalAnalyzer 部署链装齐，fund-qr **零新增**（幂等再确认）。
- **发版预检**：fund-qr HEAD 落在 release tag 上（先跑 `/fund-qr-release`），tag 与 `src/fund_qr/VERSION.txt` 一致。

> fund-qr 消费 findata、不产出需对账的数据 → **无 findata 那种门②零差对账**；**功能 smoke 即闸门**。

## release 模式验收清单

1. **findata 前置通过**：`ok: 公共环境 findata X.Y.Z 满足 >= 0.13`
2. wheel 构建成功（`fund_qr-X.Y.Z-py3-none-any.whl`）
3. `pip check` 无报错
4. **功能 smoke 三步全出**（真实数据经 findata）：
   - `smoke: fund_qr X.Y.Z`
   - `smoke: FastMCP server 装配 OK`（证明 mcp SDK + 全部工具注册）
   - `smoke: catalog rows=N / 000001.SZ 事件=M —— 真实取数链路 OK`
5. `wheelhouse/` 留痕齐全：wheel、`constraints-fund-qr-vX.Y.Z.txt`、`RELEASES.log` 新行

## 部署后：研究员如何拿到

fund_qr 装进公共环境后即可 `import fund_qr` → **下次 ae-fin-platform `publish.sh quantamental --server`
+ 研究员 `/alpha-onboard` 会自动纳入 fund-qr MCP**（onboard 逐 server 探测 import，之前因 `fund_qr`
未装而剔除，现自动保留），**无需改 onboard/manifest**（声明与实装解耦）。

## 故障排查

- **ssh 连不上 / 卡住**：ControlMaster sock 残留 → `rm /tmp/xj_deploy_cm.sock` 重试。
- **findata 前置不过**：公共环境 findata 缺失/过低 → 先跑 findata 侧 `--release`。
- **smoke 真实取数失败**：多为 findata DSN / 数据根问题——findata 侧 DSN 走包内 `_secrets.py`
  （findata#50），确认公共环境 findata 版本带集中 DSN；`FINDATA_DATA_ROOT=/data/findata` 存在。
- **import 到旧版本**：`pip show fund-qr` 看公共环境实际版本；`fund_qr` 永远 `--no-index --no-deps` 从本地 wheel 装。
