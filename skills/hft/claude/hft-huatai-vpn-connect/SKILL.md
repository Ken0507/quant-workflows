---
name: hft-huatai-vpn-connect
description: "连接华泰(新券商)交易机的方法:起华泰行知零信任 VPN(奇安信 TrustAgent,docker 容器 workstation-ops/docker/huatai-vpn)并 SSH 接入交易机 cken@10.46.13.34:8888(注意端口 8888 不是 22)。工作站经容器 SOCKS5(127.0.0.1:1082)直连即可 `ssh huatai-trading`,不依赖 Mac。换券商 broker switch #166/#168 的接入链路。"
argument-hint: ""
---

# 华泰零信任 VPN + 交易机接入

华泰是新券商(换券商 broker switch #166/#168)。本 skill 是接入华泰交易机的操作手册,
与华鑫(EasyConnect,见 `hft-vpn-tunnel-restore`)是**两套独立 VPN**,互不影响。

## 接入架构

```
主路径(当前可用,无需 Mac):
  工作站 ssh huatai-trading ──ncat socks5 127.0.0.1:1082──▶ huatai-vpn 容器(华泰隧道 vnic) ──▶ 10.46.13.34:8888

备用路径(容器/会话出问题时的临时跳板):
  工作站 ssh ──127.0.0.1:12234──▶ cken Mac 反向隧道(Mac 行知) ──▶ 10.46.13.34:8888
```

- **主路径**:工作站本地 `huatai-vpn` docker 容器自带华泰隧道;`dante-autoconf` 探测到隧道后
  在容器内起 SOCKS5(宿主映射 `127.0.0.1:1082`),工作站 SSH 经它直连交易机。**不依赖任何外部机器。**
- **注意 trustAccess**:网关 sync 里 `trustAccess=false`(容器无安全沙箱,行知 GUI「业务资源」列表为 0),
  但交易机 `10.46.13.34:8888` 这个资源的**网络层 ACL 已放行、可达**。直连可用。若以后访问变不稳,
  再找 IT 处理 Linux 设备的沙箱/设备合规(让 `trustAccess=true`)。
- **备用路径**:仅当容器会话掉线/出问题、又急需接入时,用 cken Mac(可信设备)反向隧道兜底。

## 关键参数(凭据均在 `~/.hft/credentials.env`,`HUATAI_*`)

| 项 | 值 |
|---|---|
| 零信任网关 | `zero-trust.htzq.com.cn:443`(真实 IP 见 clash 坑) |
| 安全码(配置安全码) | `HUATAI_VPN_SECCODE`(首次登录"配置安全码"用) |
| 账号 / 登录方式 | `zytzxmsm07` / **默认AD登陆** |
| MFA | 手机「行知 App」动态口令(华泰动态令牌) |
| **交易机** | `cken@10.46.13.34` **端口 8888(不是 22!)**,Ubuntu24.04/56核/1007G |
| 交易机授权密钥 | 工作站 `~/.ssh/id_rsa`(指纹 KXqk32ew...) + cken Mac 的 ed25519 |
| 交易机 host key | ed25519 `SHA256:U4alKI0NZd4NfHmo+kY5ce0my8S41vrxr7YA5z9NrdA` |
| 行情 Insight | `168.81.71.15:9362` |
| 容器 / SOCKS5 / noVNC | `huatai-vpn:latest` / `127.0.0.1:1082` / `127.0.0.1:6081` |

`~/.ssh/config` 已配 `huatai-trading`(HostName 10.46.13.34 / Port 8888 / id_rsa / ProxyCommand 走 1082)。

## 日常用法(主路径)

```bash
ssh huatai-trading             # 工作站直连交易机(经容器 SOCKS)
ssh huatai-trading 'hostname'  # 单条命令
```
前提:`huatai-vpn` 容器在跑、华泰会话在线、SOCKS 已起。检查:
```bash
docker ps --filter name=huatai-vpn --format '{{.Status}}'
docker exec huatai-vpn ss -tln | grep 1082          # 容器内 danted 在监听 = SOCKS OK
docker exec huatai-vpn ip -br addr | grep vnic       # 有 vnic = 隧道在
```
连不上的排查见下。

## 起 / 重建华泰 VPN 容器

容器是 systemd-in-docker,首启在真 systemd 下装官方 deb(奇安信 TrustAgent 3.4.0.30008)。

```bash
cd ~/hft_projects/workstation-ops/docker/huatai-vpn
./docker-run.sh --build      # 首次构建+启动;之后 ./docker-run.sh
```

**noVNC 登录(行知动态码需本人配合,每次重建/会话掉线都要重登):**
1. 本地/Mac:`ssh -L 6081:127.0.0.1:6081 cken@39.173.176.131`
2. 浏览器 `http://127.0.0.1:6081/vnc.html` → Connect
3. 服务器地址 `zero-trust.htzq.com.cn` / 端口 `443`;点"配置安全码"填 `HUATAI_VPN_SECCODE` → 连接
4. 账号页(默认AD登陆):`zytzxmsm07` + `HUATAI_VPN_PASS` → 登录
5. 华泰动态令牌页:输手机行知 App 当前动态口令
(容器已装 xdotool/scrot,GUI 在 `DISPLAY=:99`,可 scrot 截图 + xdotool 驱动)

**⚠️ clash fake-ip 坑(必做)**:工作站宿主跑 mihomo,DNS 把网关解析成 fake-ip(198.18/16),
会把零信任 **SPA(UDP 单包授权)打挂**(TCP 认证能成、隧道建不起来)。容器 `/etc/hosts` 钉真实 IP:
```bash
curl -s "https://223.5.5.5/resolve?name=zero-trust.htzq.com.cn&type=1"   # 取真实 IP(TTL 会变)
docker exec huatai-vpn bash -c 'echo "<真实IP> zero-trust.htzq.com.cn" >> /etc/hosts'
docker exec huatai-vpn systemctl restart trustdservice trustagentfront trustagent-gui
```

**⚠️ dante 端口必须 8888**:`dante-autoconf` 用 `/etc/huatai-vpn.env` 里的 `HUATAI_TRADING_PORT`
做 SSH-banner 就绪探测,**必须是 8888**(端口错→探测不到 banner→danted 不起→SOCKS 没有)。
docker-run.sh 从 `~/.hft/credentials.env` 取值生成,确保那里是 8888。

## 排错

| 现象 | 原因 / 处理 |
|---|---|
| `ssh huatai-trading` 报 `malformed connect response from proxy` / 拒绝 | 容器内 danted 没起 → 多半 `dante-autoconf` 端口不是 8888,或华泰会话掉线。`docker exec huatai-vpn ss -tln\|grep 1082` 看,改 `.huatai-vpn.env` 端口=8888 后 `systemctl restart dante-autoconf` |
| `ssh huatai-trading` 超时 | 容器没跑 / 隧道(vnic)没起 / 华泰会话掉 → 起容器 + noVNC 重登 |
| 连 22 一直超时 | **端口是 8888 不是 22** |
| 容器登录成功但访问不了(RX≈0) | `trustAccess=false` + 资源未放行 → 该资源 ACL 没推下来,找 IT;或换备用 Mac 路径 |
| 容器里 SPA 发到 198.18.x | clash fake-ip → 上面 `/etc/hosts` 钉真实 IP |
| `Permission denied (publickey)` | 交易机 authorized_keys 缺 key → 登进去 `echo <pub> >> ~/.ssh/authorized_keys`(工作站用 id_rsa) |
| 6080 端口冲突 | 宿主 6080 被占,本容器 noVNC 映射在 **6081** |

## 安全护栏

- 本容器与华鑫 `easyconnect` 完全独立,`docker-run.sh` 只操作 `huatai-vpn`,绝不碰华鑫。
- 端口只绑 `127.0.0.1`(noVNC 6081 / SOCKS5 1082),外网不可直达;不用 `--network host`。
- 交易机是新券商生产机,**改 crontab / 配置 / 部署策略前先向用户报告确认**(同实盘安全红线)。
- 凭据只在 `~/.hft/credentials.env`,不入 git。
