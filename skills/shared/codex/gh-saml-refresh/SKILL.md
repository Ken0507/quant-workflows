---
name: gh-saml-refresh
description: "git push / gh 操作被 SAML 过期或 token 缺 scope 拒绝时，在 headless 机器上跑 GitHub device flow 刷新授权：pty 控制器自动过确认提示 → 提取一次性 code 给用户浏览器输入 → 验证 scope → HTTPS+token 补推。含完整坑清单。"
---
# gh-saml-refresh — headless 机器刷新 GitHub SAML / token scope

公司 org（fin-infra / hft-prop）强制 SAML SSO，授权会过期；gh token 也可能缺
scope（如改 `.github/workflows/` 需要 `workflow`）。本 skill 在无浏览器的机器上
走 device flow 刷新：**Codex 给用户一个一次性 code，用户在自己浏览器输入授权**。

## 症状 → 诊断

| 报错 | 原因 |
|---|---|
| SSH push 报 `ERROR: ... and the repository exists` | SSH key 的 SAML 授权过期 |
| HTTPS push 报 `refusing to allow an OAuth App to ... workflow ... without 'workflow' scope` | token 缺 scope（本例 `workflow`） |
| gh api 403 + `Resource protected by organization SAML enforcement` | token 的 SAML session 过期 |

先看现状（本机有双账号：公司 ken-chen_scale + 个人 Ken0507，**refresh 作用于
active account**，确认是 ken-chen_scale）：

```bash
gh auth status     # 看 active account 与 Token scopes
```

## 执行流程

### 1. 后台启动 device flow（必须用 skill 目录里的 pty 控制器）

```bash
python3 -u <本skill目录>/gh_pty_refresh.py -h github.com -s workflow > /tmp/gh_refresh.log 2>&1
```

用长运行 shell 会话启动上述命令，记录 session id / PID，并保持该 gh device-flow 进程存活直到用户完成浏览器授权。

缺什么 scope 就 `-s` 什么（可多个）；纯 SAML 过期不缺 scope 也走同一流程
（refresh 会顺带重建 SAML session）。

### 2. 提取一次性 code，发给用户

```bash
timeout 15 bash -c 'until grep -q "auto-Enter sent" /tmp/gh_refresh.log 2>/dev/null; do sleep 1; done'
grep -o "one-time code: [A-Z0-9-]*" /tmp/gh_refresh.log
```

用 SendUserMessage 把 code 醒目地发给用户：**https://github.com/login/device**
输入 code，用公司身份（ken-chen_scale）授权。日志里
`Failed opening a web browser` 是 headless 预期输出，不是错误——此时 gh 已在轮询。

### 3. 等授权完成（后台任务退出即领取成功），验证并重试原操作

```bash
gh auth status   # 确认新 scope 已出现
```

push 用 HTTPS + token（credential helper 方式，token 不进 argv/进程列表）：

```bash
cd <repo>
GH_TOKEN=$(gh auth token --user ken-chen_scale) git \
  -c credential.helper='!f() { echo username=x-access-token; echo "password=$GH_TOKEN"; }; f' \
  push https://github.com/<org>/<repo>.git main
```

> fin-infra 仓长期约定：SSH SAML 总会过期，push 一律走上面的 HTTPS+token；
> SSH 只给 hft-prop（alias `github-hft`）用且也可能过期。

## 坑清单（实战验证，2026-06-12）

1. **不要 `printf '\n' | script -qec "gh auth refresh ..."`**：回车在提示出现前
   被吃掉，gh 永远停在 "Press Enter"、不进入轮询——**用户授权了也无人领取**，
   code 作废只能重来。延迟喂（`sleep 5; printf '\n'`）同样不可靠（`script`
   对管道 stdin 的转发不稳定）。pty 控制器是唯一稳的方案。
2. **TIOCSTI 注入救不了卡住的进程**（`Operation not permitted`，需要
   CAP_SYS_ADMIN）。卡住只能杀掉重跑、换新 code。
3. **必须保持打印 code 的那个 gh 进程活着**：code 与该进程的 device session
   绑定，进程死了授权就成孤儿。
4. **杀残留进程别用 `pkill -f "gh auth refresh"`**：模式会匹配到自己 shell 的
   命令行把自己杀掉（exit 144）。用 `pkill -xf` 精确匹配或先 `pgrep` 确认 PID。
5. **每次重跑 code 都会变**，重跑后必须把新 code 发给用户，旧的作废。
6. 多账号环境 refresh 只动 active account——动手前 `gh auth status` 确认。
