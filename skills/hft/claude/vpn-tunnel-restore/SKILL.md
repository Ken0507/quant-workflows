---
name: hft-vpn-tunnel-restore
description: "恢复工作站到交易机的 SSH 隧道（localhost:2222）。检查 EasyConnect Docker VPN 状态，必要时引导用户通过 VNC 重新登录 VPN，然后建立本地端口转发。"
argument-hint: ""
---

# 交易机 SSH 隧道恢复

## 架构概览

```
Workstation(CK, 39.173.176.131)
  └─ localhost:2222  (SSH local forward)
       └─ Docker easyconnect (172.17.0.2:2222)
            └─ 容器内 socat/端口转发
                 └─ VPN tun0 ──> 192.168.10.190:22 (交易机)
```

| 组件 | 说明 |
|------|------|
| Docker 容器 | `easyconnect` (`hagb/docker-easyconnect:7.6.7`) |
| VPN 服务器 | `183.234.94.162:4433` (华鑫 EasyConnect) |
| VPN 账号 | `chjp007_hx`（密码已缓存在容器内） |
| 交易机内网 IP | `192.168.10.190` |
| Docker 容器 IP | `172.17.0.2`（bridge 网络） |
| VNC 端口 | `5902`（映射容器内 5901） |
| VNC 密码 | `easyconnect` |
| SOCKS 代理 | `localhost:1080` |
| 凭据文件 | `~/.hft/credentials.env`（`HFT_TRADING_PASS`） |

## 执行流程

按顺序检查，哪一步通过就跳到最后的验证步骤。

### Step 1: 检查隧道是否已通

```bash
source ~/.hft/credentials.env
timeout 5 sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -p 2222 userlgj@localhost "echo TUNNEL_OK" 2>&1
```

- 如果返回 `TUNNEL_OK` → 隧道正常，直接告知用户，流程结束。
- 否则继续 Step 2。

### Step 2: 检查 Docker 容器状态

```bash
docker ps --filter name=easyconnect --format '{{.Names}} {{.Status}}'
```

- 如果容器不存在或已停止 → 告知用户联系 lgj 重建容器（不要自行创建，容器挂载了 `/home/lgj/.ecdata`）。
- 如果容器正在运行 → 继续 Step 3。

### Step 3: 检查 VPN 连接状态

```bash
docker exec easyconnect ip addr show tun0 2>/dev/null && echo "VPN_UP" || echo "VPN_DOWN"
```

- 如果 `VPN_UP` → 跳到 Step 5。
- 如果 `VPN_DOWN` → 继续 Step 4（需要用户手动 VNC 登录）。

### Step 4: 引导用户 VNC 重连 EasyConnect

VPN 断了需要用户手动操作 EasyConnect GUI。

**告知用户执行以下步骤：**

1. 在 Mac 终端建立 VNC 的 SSH 隧道（防火墙不开放 5902）：
   ```bash
   ssh -L 5902:localhost:5902 cken@39.173.176.131
   ```
2. 保持 SSH 连接，用 Mac 自带 VNC 客户端连接 `vnc://localhost:5902`
3. VNC 密码：`easyconnect`
4. 在 EasyConnect GUI 中点击登录（VPN 地址和凭据已缓存）

**等待用户确认已操作后**，循环检查 VPN 状态（最多等待 60 秒）：

```bash
for i in $(seq 1 12); do
    if docker exec easyconnect ip addr show tun0 >/dev/null 2>&1; then
        echo "VPN_UP"
        break
    fi
    sleep 5
done
```

- 如果 60 秒后仍 `VPN_DOWN` → 告知用户检查 VNC 中的 EasyConnect 错误信息。
- 如果 `VPN_UP` → 继续 Step 5。

### Step 5: 检查容器内 2222 端口转发

```bash
docker exec easyconnect bash -c 'exec 3<>/dev/tcp/127.0.0.1/2222; timeout 3 cat <&3; exec 3>&-' 2>&1
```

- 如果返回 `SSH-2.0-OpenSSH_7.4` 之类的 banner → 容器内转发正常，继续 Step 6。
- 如果失败 → 容器内没有 2222 转发，需要手动创建：
  ```bash
  docker exec -d easyconnect socat TCP-LISTEN:2222,fork,reuseaddr TCP:192.168.10.190:22
  ```
  等待 2 秒后重新验证。如果仍然失败，告知用户联系 lgj。

### Step 6: 建立宿主机本地端口转发

先清理可能残留的旧转发进程：

```bash
# 杀掉旧的 ssh 转发进程（如果有）
pkill -f 'ssh.*-L.*2222.*172.17.0.2' 2>/dev/null
sleep 1
```

建立新的本地转发（通过 Docker 容器中转到交易机）：

```bash
source ~/.hft/credentials.env
sshpass -p "$HFT_TRADING_PASS" ssh -fN -L 2222:localhost:22 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 userlgj@172.17.0.2 -p 2222
```

说明：
- `-fN`：后台运行，不执行远程命令
- `-L 2222:localhost:22`：在交易机上 `localhost:22` 就是交易机自己的 SSH，转发到本地 2222
- `userlgj@172.17.0.2 -p 2222`：先 SSH 到 Docker 容器内的 2222 端口（由容器内的 socat 转发到交易机）
- `ServerAliveInterval=30`：每 30 秒发心跳，避免空闲断开

### Step 7: 端到端验证

```bash
source ~/.hft/credentials.env
sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p 2222 userlgj@localhost "hostname && echo TUNNEL_VERIFIED"
```

- 如果返回 `TUNNEL_VERIFIED` → 隧道恢复成功，告知用户。
- 如果失败 → 检查各环节日志，报告具体失败点。

## 故障排查

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| Docker 容器不存在 | 被删除或未创建 | 联系 lgj |
| VPN 连不上（VNC 中 EasyConnect 报错） | VPN 账号过期或服务器故障 | 联系 lgj |
| 容器内 2222 端口无响应 | socat 进程挂了 | 用 `docker exec -d easyconnect socat ...` 重建 |
| 宿主机 2222 端口建立后连接超时 | SSH 转发进程异常 | `pkill -f 'ssh.*2222.*172.17.0.2'` 后重建 |
| `kex_exchange_identification: Connection closed` | 直连交易机被拒（必须走容器内转发） | 确保走 `172.17.0.2:2222` 而非直连 `192.168.10.190` |

## 注意事项

1. **不要直接 SSH 到 192.168.10.190** — 即使 TCP 能通，SSH 握手也会被拒。必须走容器内的端口转发。
2. **转发进程不会自动重启** — 如果 VPN 断了再恢复，需要重新执行此 skill。后续可考虑安装 `autossh` 做自动重连。
3. **不要修改 Docker 容器配置** — 容器由 lgj 创建，数据挂载在 `/home/lgj/.ecdata`。
4. **VNC 只在 VPN 断开时需要** — 正常使用不需要 VNC，只有 EasyConnect 需要重新登录时才用。
