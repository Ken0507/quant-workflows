---
name: hft-onboard
description: 一键把 HFT 角色包接到当前 Codex 工作目录——定位角色包源→校验研究环境(HFT SDK release 树 / py311+mcp 包 / bond_sz 数据根)→把角色包 skills 软链到你选定的 .agents/skills→把 .codex/config.toml 按环境实际可 import 过滤后语义合并到你选定目录(ob-investigator)→(可选)在 ~/.bashrc 写 HFT_SDK_ROOT 导出块→冒烟自检(ob_mcp stdio 握手 + 数据根抽查)。全程幂等。首次上机/换工作目录/环境重建后跑一次;深度研究前发现 ob-investigator 工具不可见也跑这个。
---

# hft-onboard —— HFT 研究栈一键上手 + 就地安装

面向**使用方**：把角色包的 skill 与 OB 调查 MCP **安装到你选定的工作目录**，之后在该目录起
Codex 即加载全套 `aef-hft-*` skill 与 `ob-investigator` 工具。

> SDK release 树 / 行情数据的部署是维护者的活（hft_build vendor 通道），本 skill **不装 SDK**——
> 它把「已部署好的研究环境」接到你当前的工作目录，并把**角色包 skill + MCP 注册就地安装**。
> 唯一会补装的依赖是 python 的 `mcp`（FastMCP SDK）包（缺失时提示，`--fix-deps` 自动 pip 安装）。

## 前提

- 研究环境已就绪：SDK release 树（工作站现役 `/data/share/dev/hft`，含 `sdk_tools/ob_mcp/`）+
  bond_sz 行情 parquet + py311 python。
- 本 skill 随角色包交付，脚本**自动定位角色包源**（自身所在 `.../.agents/skills/hft-onboard/`
  向上找角色包根；从仓库源码目录直接跑时回落 `~/.aef/hft`），从那里取要安装的 skill 与 `.codex/config.toml`。
- **当前为维护者工作站单机模式**；服务器角色路径 / SSH 双模式待 HFT 线服务器交付段建成后对齐
  quantamental 的 `aef-alpha-onboard`（见 ae-fin-platform#11 依赖断点）。

## 用法（agent：先问路径，再带参调用）

在 Codex 里 `$hft-onboard`。先问两个安装路径：

1. **skills 安装目录**（默认 `<当前目录>/.agents/skills`）；
2. **MCP 目录**（默认 `<当前目录>`，`.codex/config.toml` 写这里）——在该目录起 Codex 会同时加载 skill 和 MCP。

拿到后执行（agent 一律带参、非交互）：

```bash
bash onboard.sh --skills-dir <你选的>/.agents/skills --mcp-dir <你选的目录>
```

其他形态：

```bash
bash onboard.sh --check        # 只体检（环境/依赖/数据根/握手），不改任何文件
bash onboard.sh --fix-deps     # 允许自动 pip install mcp（缺 FastMCP SDK 时）
bash onboard.sh --no-shell     # 不写 ~/.bashrc 的 HFT_SDK_ROOT 导出块
bash onboard.sh --copy         # skills 用复制而非软链（跨机/脱离源目录场景）
```

## 它做了什么（5 步，全部幂等，可重复跑）

1. **定位角色包源**：脚本自身路径向上找含 `.agents/skills` 的角色包根；不在角色包内时回落
   `~/.aef/hft`（本地 dogfood）。
2. **校验研究环境**（以角色包 `.codex/config.toml` 为准逐 server 校验）：python 可执行、server
   脚本存在、`HFT_SDK_ROOT` 存在、`HFT_DATA_ROOT` 非空、python 可 `import mcp` 与 server 模块
   （缺 `mcp` 包时给出 `pip install mcp` 指引，或 `--fix-deps` 自动装）。
3. **安装 skills**：角色包 `.agents/skills/*` **软链**（默认；`--copy` 改复制）到 `<skills-dir>`。
   幂等：已正确指向的软链跳过、非软链实体不覆盖只告警。
4. **安装 MCP**：把角色包 `.codex/config.toml` 按第 2 步校验结果过滤后**合并**写入 `<mcp-dir>/.codex/config.toml`
   （保留该文件里已有的其他 server，同名条目以角色包为准），校验不过的 server 剔除并告警。
5. **冒烟自检**：对每个已注册 server 发 JSON-RPC `initialize` 做 stdio 握手（收到 `serverInfo`
   即通），并抽查 `HFT_DATA_ROOT` 下行情数据可读。修改过 `.codex/config.toml` 后需**重开会话**才会加载，
   脚本结束时会提示。

## 完成后

- 在安装目录起 Codex：`aef-hft-*` skill 可用 `$skill-name` 或自然语言触发，`ob-investigator` 工具可用。
- OB 工具全集与用法以 `$HFT_SDK_ROOT/ai_playground_prompt.md` 为准（深度研究 skill 会强制读取）。
- 出问题回流：修好 `$ae-report-fix`，修不好 `$ae-submit-bug`。
