import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="NSE Sector & Stock Rotation RRG", page_icon="📈", layout="wide"
)

st.title("NSE Sector & Stock Rotation (RRG) Dashboard")
st.markdown(
    "Relative Rotation Graph tracking NSE sector rotation and stock-level"
    " drill-downs."
)

# Sidebar UI Controls
st.sidebar.header("Configuration")
timeframe = st.sidebar.selectbox("Select Timeframe View", ["Daily", "Weekly"])
tail_length = st.sidebar.slider("Tail Length (History)", 3, 15, 5)

# ==========================================
# PART 1: ALL SECTORS ROTATION
# ==========================================
st.header("🌐 All Sectors Rotation View")

all_sectors_benchmark = "^NSEI"
sectors_dict = {
    "AUTO": "^CNXAUTO",
    "BANK": "^NSEBANK",
    "FIN SERVICE": "^CNXFIN",
    "FMCG": "^CNXFMCG",
    "IT": "^CNXIT",
    "MEDIA": "^CNXMEDIA",
    "METAL": "^CNXMETAL",
    "PHARMA": "^CNXPHARMA",
    "PSU BANK": "^CNXPSUBANK",
    "REALTY": "^CNXREALTY",
    "PVT BANK": "^CNXPVTBNK",
    "HEALTHCARE": "^CNXHEALTH",
    "CONSR DURBL": "^CNXCONSUM",
    "OIL & GAS": "^CNXENERGY",
    "INFRA": "^CNXINFRA",
    "COMMODITIES": "^CNXCMDT",
}


@st.cache_data(ttl=3600)
def fetch_data(tf, bench, items):
  period = "1y" if tf == "Daily" else "2y"
  interval = "1d" if tf == "Daily" else "1wk"

  data_dict = {}
  try:
    b_df = yf.download(bench, period=period, interval=interval, progress=False)
    if not b_df.empty:
      if isinstance(b_df.columns, pd.MultiIndex):
        data_dict[bench] = b_df[("Close", bench)].squeeze()
      else:
        data_dict[bench] = b_df["Close"].squeeze()
  except Exception:
    pass

  for name, ticker in items.items():
    try:
      df = yf.download(
          ticker, period=period, interval=interval, progress=False
      )
      if not df.empty:
        if isinstance(df.columns, pd.MultiIndex):
          close_series = df[("Close", ticker)]
        else:
          close_series = df["Close"]
        data_dict[name] = close_series.squeeze()
    except Exception:
      pass

  combined_df = pd.DataFrame(data_dict)
  combined_df.dropna(inplace=True)
  return combined_df


# Load All Sectors Data
data_sectors = fetch_data(timeframe, all_sectors_benchmark, sectors_dict)

if all_sectors_benchmark not in data_sectors.columns:
  st.error("Benchmark data could not be retrieved.")
else:
  bench_series = data_sectors[all_sectors_benchmark]
  ratio_df = pd.DataFrame(index=data_sectors.index)
  mom_df = pd.DataFrame(index=data_sectors.index)

  for name in sectors_dict.keys():
    if name in data_sectors.columns:
      sec_series = data_sectors[name]
      rs = sec_series / bench_series
      sma_rs = rs.rolling(window=14).mean()
      ratio = 100 + ((rs - sma_rs) / sma_rs) * 100
      momentum = 100 + ratio.diff(1)
      ratio_df[name] = ratio
      mom_df[name] = momentum

  ratio_df.dropna(inplace=True)
  mom_df.dropna(inplace=True)

  if not ratio_df.empty:
    fig_sec = go.Figure()
    fig_sec.add_hline(y=100, line_dash="dash", line_color="gray")
    fig_sec.add_vline(x=100, line_dash="dash", line_color="gray")

    # Watermarks
    fig_sec.add_annotation(
        x=107,
        y=108,
        text="<b>LEADING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(40, 167, 69, 0.25)"),
    )
    fig_sec.add_annotation(
        x=93,
        y=108,
        text="<b>IMPROVING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(0, 123, 255, 0.25)"),
    )
    fig_sec.add_annotation(
        x=93,
        y=92,
        text="<b>LAGGING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(220, 53, 69, 0.25)"),
    )
    fig_sec.add_annotation(
        x=107,
        y=92,
        text="<b>WEAKENING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(255, 193, 7, 0.35)"),
    )

    for name in ratio_df.columns:
      x_vals = ratio_df[name].tail(tail_length)
      y_vals = mom_df[name].tail(tail_length)
      fig_sec.add_trace(
          go.Scatter(
              x=x_vals,
              y=y_vals,
              mode="lines+markers+text",
              name=name,
              text=[""] * (len(x_vals) - 1) + [name],
              textposition="top center",
              line=dict(width=2),
              marker=dict(size=[6] * (len(x_vals) - 1) + [12]),
          )
      )

    fig_sec.update_layout(
        title=f"All Sectors Rotation Graph — {timeframe} View",
        xaxis_title="RS-Ratio",
        yaxis_title="RS-Momentum",
        xaxis=dict(range=[90, 110]),
        yaxis=dict(range=[90, 110]),
        height=650,
        template="plotly_white",
    )
    st.plotly_chart(fig_sec, use_container_width=True)

    # Quadrant Summary Cards for All Sectors
    st.subheader("📊 All Sectors Quadrant Summary")
    latest_r = ratio_df.iloc[-1]
    latest_m = mom_df.iloc[-1]
    lead, weak, lag, imp = [], [], [], []

    for name in ratio_df.columns:
      r, m = latest_r[name], latest_m[name]
      if r >= 100 and m >= 100:
        lead.append(name)
      elif r >= 100 and m < 100:
        weak.append(name)
      elif r < 100 and m < 100:
        lag.append(name)
      else:
        imp.append(name)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
      st.markdown("#### 🟢 Leading")
      for s in lead:
        st.markdown(f"- **{s}**")
    with c2:
      st.markdown("#### 🔵 Improving")
      for s in imp:
        st.markdown(f"- **{s}**")
    with c3:
      st.markdown("#### 🟡 Weakening")
      for s in weak:
        st.markdown(f"- **{s}**")
    with c4:
      st.markdown("#### 🔴 Lagging")
      for s in lag:
        st.markdown(f"- **{s}**")


# ==========================================
# PART 2: STOCK-LEVEL DRILL-DOWN (NEW PARTITION)
# ==========================================
st.markdown("---")
st.header("🔍 Stock-Level Rotation (Drill-Down)")

# Sector mapping database with stock tickers and their respective index benchmark
stock_sector_db = {
    "IT": {
        "benchmark": "^CNXIT",
        "stocks": {
            "TCS": "TCS.NS",
            "INFY": "INFY.NS",
            "WIPRO": "WIPRO.NS",
            "HCLTECH": "HCLTECH.NS",
            "TECHM": "TECHM.NS",
            "LTIM": "LTIM.NS",
        },
    },
    "AUTO": {
        "benchmark": "^CNXAUTO",
        "stocks": {
            "TATAMOTORS": "TATAMOTORS.NS",
            "MARUTI": "MARUTI.NS",
            "M&M": "M&M.NS",
            "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
            "HEROMOTOCO": "HEROMOTOCO.NS",
        },
    },
    "PHARMA": {
        "benchmark": "^CNXPHARMA",
        "stocks": {
            "SUNPHARMA": "SUNPHARMA.NS",
            "DRREDDY": "DRREDDY.NS",
            "CIPLA": "CIPLA.NS",
            "DIVISLAB": "DIVISLAB.NS",
            "APOLLOHOSP": "APOLLOHOSP.NS",
        },
    },
    "FMCG": {
        "benchmark": "^CNXFMCG",
        "stocks": {
            "HINDUNILVR": "HINDUNILVR.NS",
            "ITC": "ITC.NS",
            "NESTLEIND": "NESTLEIND.NS",
            "BRITANNIA": "BRITANNIA.NS",
            "TATACONSUM": "TATACONSUM.NS",
        },
    },
    "METAL": {
        "benchmark": "^CNXMETAL",
        "stocks": {
            "TATASTEEL": "TATASTEEL.NS",
            "HINDALCO": "HINDALCO.NS",
            "JSWSTEEL": "JSWSTEEL.NS",
            "VEDL": "VEDL.NS",
            "COALINDIA": "COALINDIA.NS",
        },
    },
    "BANK": {
        "benchmark": "^NSEBANK",
        "stocks": {
            "HDFCBANK": "HDFCBANK.NS",
            "ICICIBANK": "ICICIBANK.NS",
            "SBIN": "SBIN.NS",
            "KOTAKBANK": "KOTAKBANK.NS",
            "AXISBANK": "AXISBANK.NS",
        },
    },
}

selected_sector = st.selectbox(
    "Select Sector to View Constituent Stocks", list(stock_sector_db.keys())
)

sec_info = stock_sector_db[selected_sector]
stock_bench = sec_info["benchmark"]
stocks_dict = sec_info["stocks"]

# Fetch stock data against sector index
data_stocks = fetch_data(timeframe, stock_bench, stocks_dict)

if stock_bench not in data_stocks.columns:
  st.warning(
      f"Could not load benchmark index for {selected_sector}. Try another"
      " sector."
  )
else:
  s_bench_series = data_stocks[stock_bench]
  s_ratio_df = pd.DataFrame(index=data_stocks.index)
  s_mom_df = pd.DataFrame(index=data_stocks.index)

  for s_name in stocks_dict.keys():
    if s_name in data_stocks.columns:
      st_series = data_stocks[s_name]
      rs = st_series / s_bench_series
      sma_rs = rs.rolling(window=14).mean()
      ratio = 100 + ((rs - sma_rs) / sma_rs) * 100
      momentum = 100 + ratio.diff(1)
      s_ratio_df[s_name] = ratio
      s_mom_df[s_name] = momentum

  s_ratio_df.dropna(inplace=True)
  s_mom_df.dropna(inplace=True)

  if not s_ratio_df.empty:
    fig_stk = go.Figure()
    fig_stk.add_hline(y=100, line_dash="dash", line_color="gray")
    fig_stk.add_vline(x=100, line_dash="dash", line_color="gray")

    # Watermarks for stocks partition
    fig_stk.add_annotation(
        x=107,
        y=108,
        text="<b>LEADING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(40, 167, 69, 0.25)"),
    )
    fig_stk.add_annotation(
        x=93,
        y=108,
        text="<b>IMPROVING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(0, 123, 255, 0.25)"),
    )
    fig_stk.add_annotation(
        x=93,
        y=92,
        text="<b>LAGGING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(220, 53, 69, 0.25)"),
    )
    fig_stk.add_annotation(
        x=107,
        y=92,
        text="<b>WEAKENING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(255, 193, 7, 0.35)"),
    )

    for s_name in s_ratio_df.columns:
      x_vals = s_ratio_df[s_name].tail(tail_length)
      y_vals = s_mom_df[s_name].tail(tail_length)
      fig_stk.add_trace(
          go.Scatter(
              x=x_vals,
              y=y_vals,
              mode="lines+markers+text",
              name=s_name,
              text=[""] * (len(x_vals) - 1) + [s_name],
              textposition="top center",
              line=dict(width=2),
              marker=dict(size=[6] * (len(x_vals) - 1) + [12]),
          )
      )

    fig_stk.update_layout(
        title=(
            f"{selected_sector} Stocks Rotation Graph — {timeframe} View"
            f" (Benchmark: {stock_bench})"
        ),
        xaxis_title="RS-Ratio",
        yaxis_title="RS-Momentum",
        xaxis=dict(range=[90, 110]),
        yaxis=dict(range=[90, 110]),
        height=650,
        template="plotly_white",
    )
    st.plotly_chart(fig_stk, use_container_width=True)

    # Quadrant Summary for Stocks of Selected Sector
    st.subheader(f"📊 {selected_sector} Stocks Quadrant Summary")
    st_latest_r = s_ratio_df.iloc[-1]
    st_latest_m = s_mom_df.iloc[-1]
    s_lead, s_weak, s_lag, s_imp = [], [], [], []

    for s_name in s_ratio_df.columns:
      r, m = st_latest_r[s_name], st_latest_m[s_name]
      if r >= 100 and m >= 100:
        s_lead.append(s_name)
      elif r >= 100 and m < 100:
        s_weak.append(s_name)
      elif r < 100 and m < 100:
        s_lag.append(s_name)
      else:
        s_imp.append(s_name)

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
      st.markdown("#### 🟢 Leading")
      for s in s_lead:
        st.markdown(f"- **{s}**")
    with sc2:
      st.markdown("#### 🔵 Improving")
      for s in s_imp:
        st.markdown(f"- **{s}**")
    with sc3:
      st.markdown("#### 🟡 Weakening")
      for s in s_weak:
        st.markdown(f"- **{s}**")
    with sc4:
      st.markdown("#### 🔴 Lagging")
      for s in s_lag:
        st.markdown(f"- **{s}**")
