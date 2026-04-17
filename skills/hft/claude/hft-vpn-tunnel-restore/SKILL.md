---
name: hft-vpn-tunnel-restore
description: "恢复工作站到交易机的 SSH 隧道（localhost:2223 → 192.168.10.215）。检查 EasyConnect Docker VPN 状态，通过容器内 xdotool 自动化登录 EasyConnect GUI（短信验证码与改密需用户配合），然后让 lgj 的常驻 ssh 转发自动恢复（或手动建立本地端口转发）。"
argument-hint: ""
---

# 交易机 SSH 隧道恢复

## 架构概览

```
Workstation(CK, 39.173.176.131)
  └─ localhost:2223  (SSH local forward, 由 lgj 的常驻 ssh -fN 维护)
       └─ Docker easyconnect (172.17.0.2:2223)
            └─ 容器内 socat: TCP-LISTEN:2223 → 192.168.10.215:22
                 └─ VPN tun0 ──> 192.168.10.215:22 (交易机 .215)
```

| 组件 | 说明 |
|------|------|
| Docker 容器 | `easyconnect` (`hagb/docker-easyconnect:7.6.7`) |
| VPN 服务器 | `183.234.94.162:4433` (华鑫 EasyConnect) |
| VPN 账号 | `chjp007_hx`（密码已缓存在容器内 `/root/conf/setting_root.json`） |
| 交易机内网 IP | `192.168.10.215`（.190 已废弃） |
| Docker 容器 IP | `172.17.0.2`（bridge 网络） |
| VNC 端口 | `5902`（映射容器内 5901） |
| VNC 密码 | `easyconnect` |
| SOCKS 代理 | `localhost:1080` |
| 凭据文件 | `~/.hft/credentials.env`（`HFT_TRADING_PASS`） |
| lgj 的常驻转发 | `ssh -N -f -L 2223:192.168.10.215:22 ... trading-server`（VPN 恢复后自动重连） |

## 执行流程

按顺序检查，哪一步通过就跳到最后的验证步骤。

### Step 1: 检查隧道是否已通

```bash
source ~/.hft/credentials.env
timeout 5 sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -p 2223 userlgj@localhost "echo TUNNEL_OK" 2>&1
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
docker exec easyconnect ip -br addr 2>/dev/null | grep -E 'tun|ppp' || echo "VPN_DOWN"
```

- 如果有 `tun0` 且有 IP（如 `2.0.1.37/24`） → VPN 已连，跳到 Step 5。
- 如果 `VPN_DOWN` → 继续 Step 4 做 EasyConnect 自动化登录。

### Step 4: 自动化 EasyConnect 登录

容器里装了 `xdotool` + `scrot`，EasyConnect GUI 跑在 `DISPLAY=:1` 上，账号密码已保存（`savePwd:1`）。主流程可以不走 VNC，直接用 xdotool 驱动 GUI。只有**短信验证码**和**密码过期时的新密码**需要问用户。

#### 4.1 截图确认登录界面状态

```bash
docker exec easyconnect bash -c 'export DISPLAY=:1; scrot -o /tmp/ec_screen.png' \
  && docker cp easyconnect:/tmp/ec_screen.png /tmp/ec_screen.png
```

然后用 Read 工具查看 `/tmp/ec_screen.png`，根据当前状态分三种情况：

- **状态 A：Use Account 登录页**（填好了用户名 `chjp007_hx` + 8 位密码占位） → 做 4.2
- **状态 B：已经在主界面**（显示 `192.168.10.215` / `192.168.10.190` 资源列表） → VPN 其实已连，回到 Step 3 重新检查 tun0（可能 ip 命令时机问题）
- **状态 C：其他弹窗**（错误提示、换机登录提示等） → 告知用户，让其 VNC 处理

#### 4.2 点击 Log In 触发登录

显示分辨率 **1112x620**，Log In 按钮坐标约 `(715, 383)`。如果 UI 改版导致坐标漂移，先看 4.1 的截图微调：

```bash
docker exec easyconnect bash -c 'export DISPLAY=:1; xdotool mousemove 715 383 click 1'
sleep 3
```

再截图看结果。通常会弹出 **SMS Authentication** 对话框。

#### 4.3 处理 SMS 验证码（必须用户配合）

提示用户查看绑定的手机短信，把 6 位验证码给你。然后：

```bash
# 坐标是改密/验证码弹窗版面：输入框 (535, 305)、Log In 按钮 (535, 373)
docker exec easyconnect bash -c "export DISPLAY=:1; xdotool mousemove 535 305 click 1; sleep 0.3; xdotool type --delay 50 '<SMS_CODE>'; sleep 0.3; xdotool mousemove 535 373 click 1"
sleep 5
```

再截图。可能结果：

- **成功** → 出现资源列表（含 `192.168.10.215`） → 进入 Step 5
- **密码过期** → 弹 `Change Password` 对话框 → 进入 4.4
- **验证码错误** → 再问一次用户

#### 4.4 处理密码过期（必须用户配合 + 授权）

**这是 shared-state 操作**：VPN 账号 `chjp007_hx` 可能被 lgj 或他人共用，改密前必须：

1. 明确告知用户"VPN 服务器要求改密，新密码是 shared state，改后得通知 lgj"。
2. **等用户明确授权并给出新密码**。严禁自己编密码。
3. 密码写入对话后再删除记录（或让用户写到 `~/.hft/credentials.env`）。

坐标：New PWD 输入框 `(535, 280)`，Retype `(535, 349)`，OK 按钮 `(535, 420)`。

```bash
NEW_PWD='<用户提供>'
docker exec easyconnect bash -c "export DISPLAY=:1; \
  xdotool mousemove 535 280 click 1; sleep 0.3; xdotool type --delay 50 '$NEW_PWD'; sleep 0.3; \
  xdotool mousemove 535 349 click 1; sleep 0.3; xdotool type --delay 50 '$NEW_PWD'; sleep 0.3; \
  xdotool mousemove 535 420 click 1"
sleep 5
```

改完 EasyConnect 会自动更新 `setting_root.json` 里的加密密码（`savePwd:1`），后续 xdotool 流程仍可用。**务必提醒用户同步 lgj**。

#### 4.5 确认 tun0 起来

```bash
for i in $(seq 1 12); do
    docker exec easyconnect ip -br addr 2>/dev/null | grep -q '^tun0.*UP' \
      && echo "VPN_UP" && break
    sleep 2
done
```

- 起来后进入 Step 5。
- 60 秒仍 DOWN → 截图看 GUI 错误信息，告知用户。

#### 4.6 手动 VNC 兜底

xdotool 任一步出错（坐标不对、窗口丢失、截图全黑等），退回手工 VNC：

1. Mac 终端：`ssh -L 5902:localhost:5902 cken@39.173.176.131`
2. VNC 客户端连 `vnc://localhost:5902`，密码 `easyconnect`
3. 手动在 EasyConnect GUI 点登录

### Step 5: 检查 2223 隧道是否自动恢复

lgj 在宿主机上维护了一个常驻 ssh 转发（`ssh -N -f -L 2223:192.168.10.215:22 ... trading-server`），VPN 恢复后通常会自动重连。优先检查它是否已经起来：

```bash
ss -tlnp 2>/dev/null | grep ':2223' || netstat -tlnp 2>/dev/null | grep ':2223'
pgrep -af 'ssh.*-L.*2223' | grep -v grep
```

- 如果有监听 + 有 ssh 进程 → 跳到 Step 7 验证。
- 如果没有 → 继续 Step 6 手动建。

### Step 6: 手动建立隧道（Step 5 失败时的兜底）

先保证容器内 socat 转发在位：

```bash
docker exec easyconnect bash -c 'exec 3<>/dev/tcp/127.0.0.1/2223; timeout 3 head -1 <&3; exec 3>&-' 2>&1
```

- 返回 `SSH-2.0-OpenSSH_7.4` → OK。
- 失败 → 建 socat：
  ```bash
  docker exec -d easyconnect socat TCP-LISTEN:2223,fork,reuseaddr TCP:192.168.10.215:22
  sleep 2
  ```

然后宿主机 ssh -L：

```bash
pkill -f 'ssh.*-L.*2223.*172.17.0.2' 2>/dev/null
sleep 1
source ~/.hft/credentials.env
sshpass -p "$HFT_TRADING_PASS" ssh -fN -L 2223:localhost:22 \
  -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes userlgj@172.17.0.2 -p 2223
```

如果报 `Address already in use` → Step 5 的进程还在，不用自己建；回 Step 7 直接验证。

### Step 7: 端到端验证

```bash
source ~/.hft/credentials.env
sshpass -p "$HFT_TRADING_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p 2223 userlgj@localhost "hostname && echo TUNNEL_VERIFIED"
```

- 返回 `TUNNEL_VERIFIED` → 成功。
- 失败 → 按各步日志定位。

## 故障排查

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| Docker 容器不存在 | 被删除或未创建 | 联系 lgj |
| xdotool click 后没反应 | 坐标漂移 / 显示分辨率变了 | 重新 scrot 截图对坐标 |
| 截图全黑或 `Can't open display` | DISPLAY 不对 / VNC server 挂了 | 改用 VNC 兜底（Step 4.6） |
| SMS 发不出（`Send Again (xx)` 一直倒计时） | VPN 账号被锁 / 运营商问题 | 联系 lgj |
| 密码过期弹窗反复出现 | 新密码不满足策略 | 至少 6 位、含数字、不含用户名 |
| 宿主机 2223 `Address already in use` | lgj 的常驻转发已在跑 | 别新建，直接 Step 7 |
| 直连 192.168.10.215:22 `Connection closed` | 必须走容器内转发 | 确保走 `172.17.0.2:2223` |

## 注意事项

1. **VPN 账号是共享资源** — `chjp007_hx` 是华鑫发给团队的账号，改密后**必须同步 lgj**，否则他的自动化会断。
2. **不要自作主张改密码** — 只有在用户明确授权并提供新密码时才操作。
3. **xdotool 坐标基于 1112x620 显示** — 改过分辨率要重新校准。
4. **不要直接 SSH 到 192.168.10.215** — VPN 路由只到 container，host 直连会被拒。
5. **不要修改 Docker 容器配置** — 容器由 lgj 创建，数据挂载在 `/home/lgj/.ecdata`。
6. **lgj 的常驻转发会自动恢复 2223** — VPN 起来后大多数情况 Step 5 就通了，不用手动建。
