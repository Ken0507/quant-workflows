"""gh auth refresh 的 pty 控制器 —— headless 机器上跑 GitHub device flow。

为什么需要它：`gh auth refresh` 是交互式命令（打印一次性 code 后停在
"Press Enter to open ... browser" 提示上），headless/管道环境下回车送不进去，
gh 永远不开始轮询，用户在浏览器的授权无人领取。本脚本用 pty.fork 自己当
终端主控：看到提示自动喂回车，gh 随即进入轮询；浏览器打开失败（headless
预期）不影响，用户在任意浏览器输 code 授权后 gh 领取 token 退出。

用法（参数原样透传给 gh auth refresh）：
    python3 -u gh_pty_refresh.py -s workflow
    python3 -u gh_pty_refresh.py -h github.com -s workflow -s admin:org
"""
import os
import pty
import select
import sys

args = sys.argv[1:] or ['-h', 'github.com']

pid, master = pty.fork()
if pid == 0:
    os.execvp('gh', ['gh', 'auth', 'refresh'] + args)

buf = b''
sent = False
while True:
    try:
        r, _, _ = select.select([master], [], [], 1)
        if r:
            d = os.read(master, 1024)
            if not d:
                break
            buf += d
            sys.stdout.write(d.decode(errors='replace'))
            sys.stdout.flush()
            if not sent and b'Press Enter' in buf:
                os.write(master, b'\n')
                sent = True
                sys.stdout.write('\n[auto-Enter sent]\n')
                sys.stdout.flush()
    except OSError:
        break
    p, st = os.waitpid(pid, os.WNOHANG)
    if p:
        sys.stdout.write('\n[gh exited, code=%d]\n' % os.waitstatus_to_exitcode(st))
        break
