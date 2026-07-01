"""findata 真实数据验收 · ground-truth 对账骨架(复制改块名/GT 表/口径即用)。

用法(投研机,bash -lc 加载 DSN):
  scp recon_template.py cken@222.81.173.58:/tmp/
  ssh cken@222.81.173.58 'bash -lc "export FINDATA_UNIVERSE_ROOT=/data/hftprop/research_data/universe; \
    /data/hftprop/envs/py311/bin/python -u /tmp/recon_template.py"'
  # 验补丁代码时前置 PYTHONPATH=$HOME/experiments/<你的补丁源目录>

方法:jydb 厂商表独立复算 ground truth → findata 取值 → 逐字段 rel 误差分位 + top-N worst → 逐票溯源。
坑:LC_* 键列是 CompanyCode 非 InnerCode;decimal 列先 float();SecuMain 用 SecuCode REGEXP '^[0-9]{6}$' 滤 X 占位码;
    对账列选对(PE 归母 vs PETTMCut 扣非;TotalMV 单位=元非万元);多源字段溯源用 _fin_asof 非单字段 ytd_pit。
"""
import os
import numpy as np
import pandas as pd
import sqlalchemy as sa
import findata

pd.set_option("display.width", 240, "display.max_columns", 50, "display.float_format", lambda x: f"{x:,.6g}")
print("findata", findata.__version__, "|", findata.__file__)
ENG = sa.create_engine(os.environ["FINDATA_MYSQL_DSN"])

# ── 参数:改这里 ─────────────────────────────────────────────────────────────
DS = "20240105"                 # 锚定交易日(用完整全市场日;近端最新完整=20260608)
DD = f"{DS[:4]}-{DS[4:6]}-{DS[6:]}"
# 含边界类型:金融/科创/A+H/困境/普通;别只挑白马
NAMES = {"600519": "茅台·非金融", "000001": "平安银行·银行", "600999": "招商证券·A+H",
         "300750": "宁德·创业板", "600340": "华夏幸福·困境", "601318": "中国平安·综合金融"}
SECUS = list(NAMES)

def rel(a, b):
    a, b = float(a), float(b)
    return abs(a - b) / abs(b) if (np.isfinite(a) and np.isfinite(b) and abs(b) > 1e-12) else np.nan

def fdcode(s): return f"{s}.{'SH' if s[0] == '6' else 'SZ'}"

# ── SecuMain 映射(A 股,滤 X 占位码)──────────────────────────────────────────
with ENG.connect() as c:
    sm = pd.read_sql(sa.text(
        "SELECT InnerCode,CompanyCode,SecuCode FROM SecuMain "
        "WHERE SecuCode IN :s AND SecuCategory=1 AND SecuCode REGEXP '^[0-9]{6}$'"
    ), c, params={"s": tuple(SECUS)})
sm["SecuCode"] = sm.SecuCode.astype(str)
s2i = {r.SecuCode: int(r.InnerCode) for r in sm.itertuples()}   # → InnerCode(行情/估值/资金流键)
s2c = {r.SecuCode: int(r.CompanyCode) for r in sm.itertuples()}  # → CompanyCode(财务/事件键)
i2s = {v: k for k, v in s2i.items()}

# ── 1) jydb ground truth ─────────────────────────────────────────────────────
# 例:估值(单位=元!)。换块时改表/列/键。
with ENG.connect() as c:
    gt = pd.read_sql(sa.text(
        "SELECT InnerCode, PE, PB, PSTTM, TotalMV, NegotiableMV FROM LC_DIndicesForValuation "
        "WHERE InnerCode IN :ic AND DATE(TradingDay)=:d"
    ), c, params={"ic": tuple(s2i.values()), "d": DD})
gt["secu"] = gt.InnerCode.astype(int).map(i2s)
for col in ["PE", "PB", "PSTTM", "TotalMV", "NegotiableMV"]:
    gt[col] = gt[col].astype(float)   # decimal → float
gtk = gt.set_index("secu")

# ── 2) findata 取值 ──────────────────────────────────────────────────────────
codes = [fdcode(s) for s in SECUS]
def fd_last(fn, col, **kw):
    df = fn(DS, DS, code=codes, **kw).reset_index()
    df["secu"] = df.code.str.split(".").str[0]
    return df.set_index("secu")[col]
mc = fd_last(findata.market_cap, "cap")
pb = fd_last(findata.pb, "pb")
pe = fd_last(findata.pe_ttm, "pe_ttm")

# ── 3) 逐字段对账 + rel 分位 + top-N ─────────────────────────────────────────
rows = []
for s in SECUS:
    if s not in gtk.index:
        print(f"  {s} 无厂商行"); continue
    g = gtk.loc[s]
    rows.append({"secu": s, "标签": NAMES[s],
                 "mv_fd": mc.get(s, np.nan), "mv_jy": g.TotalMV, "mv_rel": rel(mc.get(s, np.nan), g.TotalMV),
                 "pb_fd": pb.get(s, np.nan), "pb_jy": g.PB, "pb_rel": rel(pb.get(s, np.nan), g.PB),
                 "pe_fd": pe.get(s, np.nan), "pe_jy": g.PE, "pe_rel": rel(pe.get(s, np.nan), g.PE)})
R = pd.DataFrame(rows)
print("\n== 对账 ==")
print(R.to_string(index=False))
print("\n== rel 分位(max/median);>1% 要逐票溯源(Step3)==")
for col in ["mv_rel", "pb_rel", "pe_rel"]:
    print(f"  {col}: max={R[col].max():.2e} median={R[col].median():.2e} | >1% 票: {R[R[col]>0.01].secu.tolist()}")

# ── 4) 全市场深度 EDA(可选,把 code 换成 'StockA';比率慢→抽样,market_cap 可全市场)──
# px = findata.stock_quote(DS, DS, code="StockA", field="close", adjust=None, rtype="fdf")
# codes_all = list(px.columns); mc_all = findata.market_cap(DS,DS,code="StockA",rtype="fdf").reindex(columns=codes_all).iloc[0]
# 覆盖率 NaN% 按板块 / 对账 rel 分位 / top-N worst / 符号边界(负值、float>total、极端)

print("\nRECON_DONE")
