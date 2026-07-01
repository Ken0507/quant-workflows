---
name: findata-data-audit
description: "对 findata 某数据块做真实数据逐接口验收:主控独立从 jydb 厂商表复算 ground truth 逐字段对账 + 全市场深度 EDA 找尾部 bug + notebook 交付 + 跟踪到 #35。用于校对 fin-infra/findata#35 里没验的块(风险模型/事件族/维表/universe)或新发版验收。要有样例、基于真实数据深挖、区分 bug/已知限制/口径。"
---
# findata-data-audit — findata 真实数据逐接口验收

对 `fin-infra/findata` 某个**数据块**(一组相关接口)做真实数据校对,跟踪 issue = **fin-infra/findata#35**。
核心不是"跑通",而是**主控独立复算对账 + 全市场深度 EDA 主动找尾部 bug**。

> 用法:`/findata-data-audit <块名>`(如 `风险模型` / `forecast` / `list_status` / `universe`)。
> 无参数则先问要验哪个块。**全部真实数据操作在新疆投研机;严格照下方连接约定,别另起炉灶。**

## 何时用

- 校对 #35 里**还没验**的块:**风险模型 `risk_model_*`** / 事件族 `forecast`·`dividend` / 维表 `list_status`·`industry` / `universe`。
- 任何 findata 数据块的真实数据验收、或新发版后的回归校对。

## 三条验收要求(每接口、每参数都要回答)

1. **是否真实数据**(非 mock、非空)——用已知真实数值锚定(如茅台千元价、平安市值)。
2. **数据是否合理**:字段缺失?是否符合金融逻辑?
3. **每个参数**是否真的 work(日期三格式 / `code` 单码·列表·StockA·传 None / `field` / `rtype` / `trunc_time` / 块特有参数)。

## 核心方法:主控独立复算对账(不信 findata 自己的输出)

**别"看起来对就 PASS"。** 从 jydb **厂商表独立重算**同一口径,逐字段 diff,报**相对误差分布(p50/p90/p99/max)+ rel>阈值 的 top-N 票**——不是"大致吻合"。headline 项主控亲自复跑,不外包给 subagent 的结论。

## 环境 / 连接(照抄)

投研机 = 跳板机 `cken@222.81.173.58`(免密、BatchMode 可用),findata 装在公共 env `/data/hftprop/envs/py311`。

- **跑 findata 必须 `bash -lc`**,否则 `FINDATA_MYSQL_DSN`(直连 jydb)不加载:
  `ssh cken@222.81.173.58 'bash -lc "/data/hftprop/envs/py311/bin/python /tmp/x.py"'`
- **直连 jydb 建 ground truth**:脚本里 `sa.create_engine(os.environ["FINDATA_MYSQL_DSN"])`(pymysql 已装)。
- **验补丁代码**(未发版的修复):本地 `tar czf` 源码 → scp 远端 → `PYTHONPATH=$HOME/experiments/<dir> /data/hftprop/envs/py311/bin/python`(不动已装版本)。
- **裸 python / cron / 补丁跑** 必须显式 `export FINDATA_UNIVERSE_ROOT=/data/hftprop/research_data/universe`,否则 `code='StockA'` 抛 `FileNotFoundError`(#31:该变量只在 conda activate.d)。
- **跳板禁 scp 下载**(只能上传)→ 取回文件用 `ssh cat`。
- 本地写脚本 → `scp` 到远端 `/tmp` → `bash -lc` 跑;别在 `/tmp` 写大数据。
- 本地测试资产根:`~/alpha_projects/researches/findata_api_test/`(`CONNECT.md` 连接约定 + `scripts/` 工具 + `results/` notebook)。

## Ground-truth 表映射(findata 接口 → jydb 对账表)

| findata 块 | jydb 厂商/原始表 | 键 / 复算口径 |
|---|---|---|
| 市值/估值 `market_cap`/`pe`/`pb`/`ps` | `LC_DIndicesForValuation`(**TotalMV/NegotiableMV 单位=元**、PE=归母、PSTTM、**PETTMCut=扣非**) | `InnerCode,TradingDay`;total_mv=股本×未复权close |
| 股本 `stock_total/float_share` | `LC_ShareStru`(科创板 `LC_STIBShareStru`,无 RestrictedShares 用 RestrictedAShares) | `CompanyCode,EndDate`;TotalShares/AFloats/RestrictedShares |
| 资金流 `stock_moneyflow` | `QT_TradingCapitalFlow`(科创板 `LC_STIBCapFlowType`) | `InnerCode,TradingDate`;ValueRange **1小2中3大4超大**,net=Buy−Sell,main=VR4+VR3,pct=main/Σ(Buy+Sell) |
| 财务三表 `{ytd,mrq,ttm,ave}_pit` | `LC_BalanceSheetAll`/`IncomeStatementAll`/`CashFlowStatementAll`(科创板 `LC_STIB*`) | `CompanyCode,EndDate,IfMerged,IfAdjusted`;mrq=YTD差分、ttm=YTD+上年报−上年同期 |
| 事件族 forecast/express/dividend | `LC_PerformanceForecast`/`LC_PerformanceLetters`+`DZ_FSPerformedLetters`/`DZ_DividendProgress` | `CompanyCode`/`InnerCode`;avail_ts=InsertTime |
| 维表 secu_main/list_status/industry | `SecuMain`/`LC_ListStatus`(∪`LC_STIBListStatus`)/`LC_ExgIndustry`(∪`LC_STIBExgIndustry`) | 走 `SecuCode REGEXP '^[0-9]{6}$'` 滤占位码 |
| 风险模型 `risk_model_*` | **待核实**(v0.11.0 #44 已区间化对齐;先探 provider 实际读哪张表/文件,再定 GT) | — |

> 不确定某块的 GT 表/口径,先 `findata.describe(...)` + 读 findata 源码 `source/db_*.py` 的 `upstream`/SQL,再定对账基准。

## 流程(7 步)

### Step 0 — 摸接口面 + 确认部署版本
- 本地读 findata 源码:该块有哪些公开接口、参数、docstring 口径、上游表(`source/db_*.py`)。
- ssh 确认投研机 `findata.__version__` 是否含要验的改动;不够新则先 `/findata-deploy release`,或用 PYTHONPATH 补丁跑。

### Step 1 — 建 ground-truth 对账(headline,主控独立复算)
- 挑锚样本:含**边界类型**(金融股/科创板/A+H/困境股/ST),不止白马股。
- jydb 直连取厂商值 → findata 取值 → 逐字段 rel 误差(用 `recon_template.py` 骨架)。
- 报 **p50/p90/p99/max + rel>阈值 top-N**。rel~1e-8=精确、~1e-5=可接受、>1% 要查。

### Step 2 — 全市场深度 EDA(真 bug 藏在尾部,别只挑白马股)
- **覆盖率**:各接口 NaN% 按板块(主板/创业板/科创板)拆——找整块缺失。
- **误差分布**:全市场对账 rel 分位 + top-N worst 票 + 其特征(板块/金融/困境)。
- **符号/边界**:负值该不该负(负 PB/PE)、`float_mv>total_mv`、`|pct|>1`、极端值、全 0 行。
- **事件连续性**(状态量):除权日/股本变更日/财报日 as-of 跳变是否连续/正确。
- 全市场比率(pe/pb/ps over StockA)慢(见坑清单)→ 用抽样(600 票),market_cap 可全市场。

### Step 3 — tail bug 定位(逐票溯源)
偏离的票:**findata 内部实际取值 → jydb 原始行(含全部时间戳/IfAdjusted)→ 公告原文**三方对。
判 InsertTime 是否可信:**同 EndDate 跨表 InsertTime 对比**(独立早入库 vs 灌年报时 backfill)+ 找**公告原文**核对数字与日期。

### Step 4 — bug vs 已知限制 vs 口径(别臆断)
- **bug**:findata 代码错(漏 union、口径实现错、参数失效)→ 修。
- **已知限制**:jydb 源头缺/停更(#30 STIB、#2 维表源)→ 确认表现符合"已知"、不当新 bug 报。
- **口径分歧**:findata 与厂商口径不同但 findata 更对(重述按 as-of、PIT 正确)→ 文档说明、非 bug。
- 找根因,别拿"早于公告=补录"之类的表象下结论;必要时查 jydb 原始 + 公告。

### Step 5 — notebook 交付(可复现、cken 经 JupyterLab 重跑)
- `scripts/nbbuild.py` 的 `build_nb(cells, out, title=)` 组装(kernel=`findata-py311`)→
  `bash scripts/run_remote_nb.sh <local.ipynb> [timeout]`(上传 `~/experiments/`→nbconvert 烘真实输出→`ssh cat` 回写本地镜像)。
- 每个发现一个可跑 cell(真实取数 + 对账 + 结论)。**注:该 kernel 不经 conda activate,cell 里 `os.environ.setdefault("FINDATA_UNIVERSE_ROOT",...)` 才能用 StockA。**

### Step 6 — 闭环产出
- **comment 到 #35**:PASS/CONCERN/FAIL 小结 + headline 对账零差证据 + 发现(区分新 bug/已知/口径)+ 复用资产。
- **bug → 开 issue + PR**(修 → 单测 → 对 jydb 验 → CHANGELOG);**缺口 → 开 issue**;**口径/文档 → 改 docstring**。
- 破坏性口径变更:先开 issue(open 只描述问题、调研/结论放 comment)、cken 拍板再改。
- 更新记忆 `findata-realdata-audit`(哪块验了、结论、坑)。

## 坑清单(血泪,直接用)

- **别只挑白马股**——白马股永远精确,bug 在尾部(困境股/次新/金融/转股期)。全市场深度 EDA 才抓得到。
- **对账列要选对**:PE 对厂商 `PE`(归母)**不是 `PETTMCut`(扣非)**;`TotalMV`/`NegotiableMV` 单位=**元**(别乘 1e4)。
- **多源 NaN**:单字段 `ytd_pit("Balance","OtherEquityinstruments")` 可能返 NaN(多源纵向 concat,#41);派生内部用 `_fin_asof` 才拿到值——溯源用 `_fin_asof` 别用单字段。
- **可得口径(#54,已改)**:判"何时可得"用 `avail_ts`(=InsertTime)**不是 InfoPubDate**(公告日不可靠、股本年末快照贴年报日);可信条件 `day_diff<=1`;`trunc_time` 默认已是 `'BOD'`(不传=盘前 09:15 可得)。
- **StockA 需 `FINDATA_UNIVERSE_ROOT`**(裸 python/cron/补丁/kernel 都要显式设,#31)。
- **jydb 坑**:财务 `LC_*` 键列是 `CompanyCode` **非 InnerCode**;`decimal` 列除法/比较**先 `float()`**;`SecuMain` 有 `X` 前缀未上市/退市占位码,取 A 股用 `SecuCode REGEXP '^[0-9]{6}$'` 滤。
- **近端数据**:量价最新完整全市场日 = **20260608**(20260609 沪市整体缺、空行不报错静默错截面);验近端先确认完整日。
- **科创板(688/689)**:走 `LC_STIB*` 平行表;近端自 2026-01-07 停更(#30),验科创板用历史日(如 20240102)。
- **全市场比率慢**:pe/pb/ps over StockA >25min(db_pit 无 SQL 窗口取全历史 + TTM 计算,见 #58)→ 抽样;`market_cap`(无财务)全市场 ~2min OK。
- **停牌判定**用 `stock_suspend`(盘前公告)**不用** `volume==0`(未来函数)或 `trade_status`(已删)。
- **判停/口径别臆断**:两版作者、重述来源、InsertTime 含义都别猜——查 jydb 原始 + 公告原文坐实。

## 样例(真实,取自第三轮 + #54 会话)

**A. ground-truth 对账骨架**(见 bundle 的 `recon_template.py`,核心):
```python
# 1) SecuMain 建 code↔InnerCode/CompanyCode 映射
# 2) jydb 直连取厂商值(GT) ; 3) findata 取值 ; 4) rel=|fd-jy|/|jy| 分位 + top-N
def rel(a,b): return abs(float(a)-float(b))/abs(float(b)) if abs(float(b))>1e-12 else np.nan
# 市值 rel p90=6.5e-8 = 精确; rel>1% 的 top 票 → 逐票 Step3 溯源
```

**B. 一个真实发现的完整链条**(#54,示范深挖):
1. 全市场 EDA:11 票总市值偏>1%(max 8.6%),方向一致 findata<厂商。
2. 锁定 603007:findata 隐含股本 349.9M vs 厂商 382.97M。
3. 溯源 jydb `LC_ShareStru`:新股本行 `InfoPubDate=2024-04-30`(年报) 但 `InsertTime=2024-01-02`。
4. 验 InsertTime 可信:公告原文(编号 2024-001、2024-01-03 发布「累计转股 49,596,241 股」数字分毫不差)+ 同 EndDate 跨表 InsertTime(股本 1 月 vs 财报三表 4 月 = 独立早入库、非 backfill)。
5. 判别:findata 按公告日截断 → 滞后近一报告周期 = **真 bug**(非厂商假数据)→ 修(四层)、开 #54、PR #55。

**C. 非 bug 的判别示范**(中国平安 PE/PS 偏 20%):查 jydb 发现 2022 年报营收 IFRS17 重述(1.11万亿→8803亿)、重述值 2024-03 才公布 → as-of 取 TTM 只能旧准则拼新准则 → findata **PIT 正确、非 bug**(纯保险中国人寿无重述故精确)→ 文档说明。

## 复用资产

- `~/alpha_projects/researches/findata_api_test/`:`CONNECT.md`(连接约定)、`scripts/nbbuild.py`+`run_remote_nb.sh`+`setup_kernel.sh`(notebook 管线)、`scripts/recon_*.py`(各块对账实例)、`results/accept_*.ipynb`(已烘输出的验收 notebook)。
- 本 skill bundle:`recon_template.py`(ground-truth 对账骨架,复制改块名/GT 表/口径即用)。
- 相关 skill:`/findata-deploy`(部署新版到投研机)、`/findata-release`(发版)、`/write-research-log`(长任务记日志)、`/memory-guard`(大任务内存兜底)。
