---
name: ob-mode
description: 当用户要求进入 OB 模式、提到 `/ob_mode`、使用 ob-investigator MCP、或在执行 hft-deep-factor-research 前需要激活 Playground 的 OB 调查工具链时使用；目标是在 Codex 中提供与 Claude `/ob_mode` 等价的最小兼容入口。
---

# OB 模式

## 目标

在进入任何 OB 调查前，激活 Codex 侧的 `ob-investigator` 工具链，并以 Playground 文档为唯一口径。

## 执行步骤

1. 先读取：
   - `/data/share/dev/hft/ai_playground_prompt.md`
2. 检查 `~/.codex/config.toml` 是否存在 `mcp_servers.ob-investigator`。若缺失或配置错误，按 `/data/share/dev/hft/sdk_tools/cli/commands/mcp.py` 的 canonical config 修正为：
   - `command=/home/cken/anaconda3/envs/py311/bin/python`
   - `args=[/data/share/dev/hft/sdk_tools/ob_mcp/server.py, --stdio]`
   - `env.HFT_SDK_ROOT=/data/share/dev/hft`
   - `env.HFT_DATA_ROOT=/data/share/dev/hft/data/market_data_parquet`
   - `env.PYTHONPATH=/data/share/dev/hft/sdk_tools`
3. 验证 `py311` 环境可 `import mcp`，并确认 `/data/share/dev/hft/sdk_tools/ob_mcp/server.py --stdio` 能正常启动。
4. 如果当前会话已经暴露 `ob-investigator` 工具，后续 OB 调查直接使用这些工具。
5. 如果配置已正确但当前会话仍看不到 `ob-investigator` 工具，明确告知用户需要重开一个 Codex 会话以重新加载 MCP 配置。
6. 完成后再进入 `hft-deep-factor-research` 或其他依赖 OB 工具链的流程。

## 约束

- 不要凭记忆描述 OB 工具，始终以 `ai_playground_prompt.md` 为准。
- 不要改动 HFT SDK 代码或数据，只修正 Codex 侧配置。
- 这是 Codex 对 Claude `/ob_mode` 的兼容入口，不应额外改变研究流程本身。
