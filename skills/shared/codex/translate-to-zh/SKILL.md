---
name: translate-to-zh
description: "将英文 Markdown 文档翻译为中文。参数可为单个 .md 文件路径（翻译后写入 doc_zh.md）或目录路径（在同级生成 <dir>_zh 目录，保留原目录结构，翻译其中所有 .md 文件）。对 ob-research 项目目录（hft 或 crypto）做特殊处理：在项目目录下新建 report_zh/ 子目录，翻译其中的顶层 .md 文件。学术名词、专有名词、代码、公式、命令保持英文原文不变，其余内容翻译为中文。翻译工作通过 Codex subagent 执行。"
---
# Translate to Chinese — 英译中翻译

将英文 Markdown 文档翻译为中文，学术名词保留原文。

## 使用方式

```
/translate-to-zh <path>
```

`<path>` 为 `.md` 文件或目录（绝对或相对路径均可）。

## 输出规则

- **文件**：`/a/b/doc.md` → `/a/b/doc_zh.md`（同目录下新增 `_zh` 后缀文件）。
- **ob-research 项目目录**（特殊情形）：若目录路径匹配 `.../ob_research/<project>/` 或 `.../crypto_ob_research/<project>/`，则目标目录为该项目目录下的 `report_zh/`（**而非同级的 `<project>_zh`**），并且**只翻译项目顶层的 `.md` 文件**（不递归进入 `code/` 等子目录）。例：
  - `/home/cken/hft_projects/HFTPool/ob_research/86-price_neutral_churn_rate/` → 顶层 md 译文写入 `/home/cken/hft_projects/HFTPool/ob_research/86-price_neutral_churn_rate/report_zh/`。
  - `/home/cken/crypto_world/crypto_ob_research/1-depth_fair_price/` → 顶层 md 译文写入 `/home/cken/crypto_world/crypto_ob_research/1-depth_fair_price/report_zh/`。
- **普通目录**：`/a/b/translate` → `/a/b/translate_zh`（新建同级目录，保留子目录结构，逐个翻译其中所有 `.md` 文件；非 md 文件不复制、不翻译）。
- **原文件/原目录保持不变**。
- 若目标文件已存在，直接覆盖。

## 翻译规则

- 学术名词、技术术语、专有名词（如 `Transformer`、`order book`、`VWAP`、`Sharpe ratio`、`backtest`、产品/库/框架名）保持英文原文不变，不加括号注释。
- 代码块（```...```）、行内代码（`...`）、数学公式、链接 URL、文件路径、命令行保持原样不翻译。
- Markdown 结构（标题层级、列表、表格、引用、图片语法、脚注）完整保留。
- 其余自然语言文本翻译为自然、通顺的中文。
- 不要添加译者注、不要改动原文语义、不要增删段落。

## 执行流程

**全部翻译工作通过一个 Codex subagent 完成**，主 agent 只负责解析参数、枚举文件列表、启动 subagent、汇报结果。

### Step 1 — 解析参数

1. 判断 `<path>` 是文件还是目录（用 `Bash` 的 `test -f` / `test -d`，或 `Glob`）。
2. 规范化为绝对路径。
3. 若是目录：
   - **先判断是否为 ob-research 项目目录**：路径匹配正则 `.*/(crypto_)?ob_research/[^/]+/?$`（即 `ob_research/` 或 `crypto_ob_research/` 下的单个项目目录）。
     - **是**：目标目录设为 `<path>/report_zh/`；用 `Glob` 列出 `<path>/*.md`（**仅顶层**，不递归），建立 `(src, dst)` 映射（dst 保持原文件名，写入 `report_zh/` 内）。若顶层已有 `report_zh/` 目录中的 md 文件被 glob 命中，需显式过滤掉以免自指。`mkdir -p <path>/report_zh`。
     - **否**：普通目录模式。目标目录 `<path>_zh`；用 `Glob` 列出 `<path>/**/*.md`，建立 `(src, dst)` 映射列表，保留子目录结构；`mkdir -p` 预创建所有子目录。
4. 若是文件：
   - 校验后缀为 `.md`，否则报错退出。
   - 目标为同目录下的 `<stem>_zh.md`。

### Step 2 — 启动 Codex subagent

使用 Codex subagent 启动独立执行者，默认使用 `model: gpt-5.4`、`reasoning_effort: xhigh`。prompt 中给出完整任务清单（每一对 src→dst）与翻译规则，让 subagent 自己逐个读取源文件、翻译、写入目标文件。

subagent prompt 模板：

```
你的任务是将下列英文 Markdown 文件翻译为中文。逐个处理，每个文件都必须：
1. 用 Read 读取源文件全部内容。
2. 按下述规则翻译。
3. 用 Write 将译文写入目标路径（目录已由主 agent 预创建，直接写即可）。

## 翻译规则（严格遵守）

- 学术名词、技术术语、专有名词保持英文原文不变，不加括号注释。例：
  Transformer / attention / order book / VWAP / Sharpe ratio / backtest /
  L2 / tick / latency / alpha / PnL / 以及所有库名、产品名、论文名。
- 代码块 ```...```、行内代码 `...`、数学公式、链接 URL、文件路径、shell
  命令、API 签名原样保留，不翻译、不改格式。
- Markdown 结构（标题层级 # ## ###、列表、表格、引用 >、图片 ![]()、
  脚注 [^1]）完整保留。
- 英文标点在中文句子里改为中文标点；中英混排时英文与中文之间按惯例留空格。
- 翻译要自然通顺，不要逐字直译，不要添加译者注，不要增删段落。
- 输出必须是**完整的整篇译文**，不允许使用 "（以下省略）" 之类的占位。

## 待翻译文件列表

<这里由主 agent 填入 (src -> dst) 列表，每行一对>

## 完成标准

所有文件都成功 Write 后，回报：每个 dst 的行数、总字符数、任何失败项。
不要输出翻译内容本身，只回报进度与结果。
```

Codex subagent 调用示例参数：

```json
{
  "description": "Translate md to Chinese",
  "model": "gpt-5.4",
  "reasoning_effort": "xhigh",
  "prompt": "<上面的 prompt，已填入文件列表>"
}
```

### Step 3 — 汇报结果

subagent 返回后，主 agent 向用户汇报：
- 翻译了多少个文件；
- 输出路径（文件情形给出 `_zh.md` 路径；ob-research 项目目录情形给出 `<path>/report_zh/`；普通目录情形给出 `<path>_zh/`）；
- 任何失败项。

不要让主 agent 自己翻译文件内容，避免占用主上下文。

## 注意事项

- **不要修改原文件**。只新建 `_zh` 文件或 `_zh` 目录。
- 大文件（>50KB）也由 subagent 一次性读取并整篇翻译；若单个文件过大超出 subagent 上下文，可在 prompt 中指示 subagent 分段 Read/Write 同一目标文件（追加模式），但默认先尝试一次性翻译。
- 若 `<path>_zh` 目录已存在，直接写入（可能覆盖已有译文），不要删除原有内容。
- 非 `.md` 文件一律忽略，不复制到 `_zh` 目录。
- **ob-research 情形**：仅翻译项目顶层 md 文件（`research_report.md`、`research_log.md`、`factor_definition.md`、`quality_review.md` 等），不进入 `code/` 子目录；译文按原文件名写入 `<path>/report_zh/` 内。若 `report_zh/` 已存在旧译文，直接覆盖。
