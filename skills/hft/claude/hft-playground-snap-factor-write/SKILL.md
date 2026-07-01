---
name: hft-playground-snap-factor-write
description: 当用户要用 Playground 编写/新增/修改【snap 族因子】——纯基于交易所 L2 快照(SnapBook / Context::GetSnap)的因子(如 snap-to-snap 变化量、当前帧 imbalance/spread/microprice)时使用；按 snap 自身时间每帧采样、同时记录 exchange_ts 与 local_ts。开始写代码前必须先阅读 /home/cken/hft_projects/HftKnowledge/research_docs/data.md(SnapBook / GetSnap / 双 book 章节)，并以文档口径为准。**若写的是基于 order/trade 重构 OrderBook 的因子，请改用 `hft-playground-factor-write`。**
---

# HFT Playground 写 snap 因子（snap 族：L2 快照 / SnapBook）

## 何时用本 skill（先判断因子归属）

团队因子分**两族、天生不合并**（issue #173，双 book 架构）：

| | **snap 族（本 skill）** | **recon 族（`hft-playground-factor-write`）** |
|---|---|---|
| 数据源 | 交易所 L2 快照 `SnapBook`（`Context::GetSnap(code)`） | order/trade 重构的 `OrderBook`（`GetOrderBook`） |
| 深度 | **仅 top-10**，无队列/订单流 | 全深度 + 队列/订单流 |
| 采样轴 | **每帧快照一行**，键 `(code, snap_ts)`，**无 biz_index** | `bar_aggtrans_time_1`，`md_id=biz_index` |
| 典型因子 | snap-to-snap 变化量、当前帧 imbalance/spread/microprice/depth-shape | 深度金额累计、排队位置、撤单强度 |

**两族分开训练、不 merge**；选用哪族做预测在模型/业务侧决定。
**判断规则**：因子只需要 top-10 价量、且按 3s 快照节奏取值 → snap 族（本 skill）；需要 >10 档深度 / 队列 / 逐笔 → recon 族。

## 强制前置阅读（Hard Gate）

1) 通读 `/home/cken/hft_projects/HftKnowledge/research_docs/data.md`，重点：
   - `SnapBook` / `Context::GetSnap(code)` 接口；`SnapData` 字段（10 档 ap/av/bp/bv + last）。
   - 双 book 架构（snap 与 recon 并行、不合并）。
2) 通读样例工程 `/home/cken/hft_projects/HFTPool/snap_pool/example/`（factor_list + src），它是 snap 族的开发模板与口径基准。
3) 文档/样例与本 skill 冲突时，以文档/样例为准。

## 硬规则（snap 族专用，与 recon 族不同）

- **采样：每帧快照输出一行**。在 `OnMarketEvent` 里只处理 `event.type == MarketEventType::SNAPSHOT`，读 `Context::GetSnap(event.code)`；**不要**按 aggtrans bar 采样（那是 recon 族口径）。
- **同时记录两个时间戳**（供后续对齐，二者都落盘为列）：
  - `snap_exchange_ts = sb->GetExchangeTs()`：交易所 `DataTimeStamp`（**严格 3s 网格**；注意其内容实际反映标称时戳**之后 ~500ms** 的盘口——见 data.md「内容偏移」）。
  - `snap_local_ts = sb->GetLocalTs()`：本机收到时刻（**因果对齐用，推荐作为 DataStore 的 `time` 主键**）。
- **join 轴 = `(code, snap_ts)`，没有 `biz_index`**：snap 事件不带 biz_index/seq，**不要**套用 recon 的 `md_id=biz_index`；snap 因子走自己的 snap basic_table（snap 网格 + snap 网格前向收益标签），不与 recon basic_table join。
- **能力边界**：`SnapBook` 只有 top-10 价量、OHLC/last，**没有**队列前方量/订单流/>10 档深度。需要这些的因子是 recon 族，不在本 skill。
- **有效性 gating**：`if (!sb || !sb->IsValid()) return;`（IsValid = 两侧 top-of-book 都 >0）。只在连续交易段（`IsContinuousTime`）取值；竞价/盘前/午休按需跳过。
- 价格整型缩放价 `PRICE_SCALE=1000`；`GetMidPrice()/GetMicroPrice()` 返回 double 但单位仍是缩放价。
- schema 稳定：每行同名同类型列；缺失填默认值；禁止 NaN/Inf。

## SnapBook 读接口速查（镜像 OrderBook 只读 API → 可与 recon 因子模板化共用）

```cpp
hft::SnapBook* sb = GetContext()->GetSnap(event.code);
if (!sb || !sb->IsValid()) return;
int64_t bid = sb->GetBestBid();            // 缩放价
int64_t ask = sb->GetBestAsk();
double  mid   = sb->GetMidPrice();         // 缩放价(double)
double  micro = sb->GetMicroPrice();
int64_t tb = sb->GetTotalBidVol();         // top-10 求和(非全深度)
int64_t ta = sb->GetTotalAskVol();
int64_t bp_i = sb->GetBidPriceAt(i);       // i=0..9, 0=最优; 越界返回 0
int64_t bv_i = sb->GetBidVolAt(i);
int64_t rv = sb->GetRangeVol(lo, hi, hft::Side::BUY, true, false);  // top-10 内
sb->GetHandicapWithin(vol, amt, px, hft::Side::SELL);              // top-10 VWAP 走档
auto fb = sb->GetFullBidBook();            // top-10 的 price->vol(非全深度)
int64_t ets = sb->GetExchangeTs(), lts = sb->GetLocalTs();
```

## 最小范式

```cpp
void OnInit() override { GetContext()->RegisterDataStore("<snap_table>", &store_); }

void OnMarketEvent(const hft::MarketEvent& event) override {
  if (event.type != hft::MarketEventType::SNAPSHOT) return;     // 只在快照帧采样
  auto* ctx = GetContext(); if (!ctx) return;
  hft::SnapBook* sb = ctx->GetSnap(event.code);
  if (!sb || !sb->IsValid()) return;

  std::map<std::string,int64_t> i64;
  std::map<std::string,double>  f64;
  i64["snap_exchange_ts"] = sb->GetExchangeTs();   // 两个时戳都落盘
  i64["snap_local_ts"]    = sb->GetLocalTs();
  f64["snap_imbalance"]   = imbalance(*sb);        // 当前帧因子
  // ... snap-to-snap 类因子在 CodeState 里存上一帧值后做差
  store_.AddRow(event.code, sb->GetLocalTs(), {}, {}, {}, i64, {}, {}, f64, {});
}

void OnFinish() override { store_.Flush("<snap_table>"); }
```

## Step 0：从样例工程拷贝（强制）

新 snap 因子集从 `HFTPool/snap_pool/example/` 拷贝起步（它实现了 snap-grid 采样 + 双时戳 + ~20 个样例因子 + 标签口径）：

```bash
NEW=/home/cken/hft_projects/HFTPool/snap_pool/<snap_factor_set>/code
mkdir -p "$NEW" && cp -r /home/cken/hft_projects/HFTPool/snap_pool/example/src "$NEW/src"
```

## 标签 / 评估（snap basic_table）

snap 因子在**自己的 snap 网格**上评估：标签 = 未来 K 帧的 mid（或 micro）前向收益（`fwd_ret_k`），与 recon 的 bar 网格独立。参考 `HFTPool/snap_pool/example` 的标签实现。

## 编译 / 数据 / 运行

- 数据：snap 分区现已纳入同步（`sync_market_data.sh` 的 `SYNC_SNAP`，bond 市场默认开）；离线回放默认会投递 SNAPSHOT 事件。
- 编译：`source /opt/rh/gcc-toolset-12/enable && source /data/share/dev/hft/setup_sdk.sh`。⚠️ 链接 parquet 的 exe 需 glibc≥2.30（开发机 2.28 链不动 → 走 release/Docker build）。
- 批量刷取/验收：同 recon 流程（参考 `hft-playground-factor-batch-run`），但轴对齐用 snap 网格 `(code, snap_ts)` 而非 `(code,time,md_id)`。
