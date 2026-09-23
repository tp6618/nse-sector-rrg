import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="NSE Sector & Stock Rotation RRG", page_icon="📈", layout="wide"
)

st.title("NSE Sector & Stock Rotation (RRG) Dashboard")
st.markdown("Relative Rotation Graph tracking sectors and constituent stocks.")

# Sidebar UI Controls
st.sidebar.header("Configuration")
timeframe = st.sidebar.selectbox("Select Timeframe View", ["Daily", "Weekly"])

view_mode = st.sidebar.selectbox(
    "Select View Mode",
    [
        "All Sectors",
        "IT Stocks",
        "Auto Stocks",
        "Pharma Stocks",
        "FMCG Stocks",
        "Metal Stocks",
        "Bank Stocks",
    ],
)

tail_length = st.sidebar.slider("Tail Length (History)", 3, 15, 5)

# Define Benchmarks and Ticker Dictionaries
if view_mode == "All Sectors":
  benchmark = "^NSEI"
  tickers_dict = {
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
elif view_mode == "IT Stocks":
  benchmark = "^CNXIT"
  tickers_dict = {
      "TCS": "TCS.NS",
      "INFY": "INFY.NS",
      "WIPRO": "WIPRO.NS",
      "HCLTECH": "HCLTECH.NS",
      "TECHM": "TECHM.NS",
      "LTIM": "LTIM.NS",
      "PERSISTENT": "PERSISTENT.NS",
  }
elif view_mode == "Auto Stocks":
  benchmark = "^CNXAUTO"
  tickers_dict = {
      "TATAMOTORS": "TATAMOTORS.NS",
      "MARUTI": "MARUTI.NS",
      "M&M": "M&M.NS",
      "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
      "HEROMOTOCO": "HEROMOTOCO.NS",
      "EICHERMOT": "EICHERMOT.NS",
      "TVSMOTOR": "TVSMOTOR.NS",
  }
elif view_mode == "Pharma Stocks":
  benchmark = "^CNXPHARMA"
  tickers_dict = {
      "SUNPHARMA": "SUNPHARMA.NS",
      "DRREDDY": "DRREDDY.NS",
      "CIPLA": "CIPLA.NS",
      "DIVISLAB": "DIVISLAB.NS",
      "APOLLOHOSP": "APOLLOHOSP.NS",
      "LUPIN": "LUPIN.NS",
      "TORNTPHARM": "TORNTPHARM.NS",
  }
elif view_mode == "FMCG Stocks":
  benchmark = "^CNXFMCG"
  tickers_dict = {
      "HINDUNILVR": "HINDUNILVR.NS",
      "ITC": "ITC.NS",
      "NESTLEIND": "NESTLEIND.NS",
      "BRITANNIA": "BRITANNIA.NS",
      "TATACONSUM": "TATACONSUM.NS",
      "DABUR": "DABUR.NS",
      "MARICO": "MARICO.NS",
  }
elif view_mode == "Metal Stocks":
  benchmark = "^CNXMETAL"
  tickers_dict = {
      "TATASTEEL": "TATASTEEL.NS",
      "HINDALCO": "HINDALCO.NS",
      "JSWSTEEL": "JSWSTEEL.NS",
      "VEDL": "VEDL.NS",
      "COALINDIA": "COALINDIA.NS",
      "NMDC": "NMDC.NS",
      "JSL": "JSL.NS",
  }
elif view_mode == "Bank Stocks":
  benchmark = "^NSEBANK"
  tickers_dict = {
      "HDFCBANK": "HDFCBANK.NS",
      "ICICIBANK": "ICICIBANK.NS",
      "SBIN": "SBIN.NS",
      "KOTAKBANK": "KOTAKBANK.NS",
      "AXISBANK": "AXISBANK.NS",
      "INDUSINDBK": "INDUSINDBK.NS",
      "BANKBARODA": "BANKBARODA.NS",
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


# Load Data
data = fetch_data(timeframe, benchmark, tickers_dict)

if benchmark not in data.columns:
  st.error(
      "Benchmark data could not be retrieved. Please check network or symbols."
  )
else:
  bench_series = data[benchmark]

  ratio_df = pd.DataFrame(index=data.index)
  mom_df = pd.DataFrame(index=data.index)

  for name in tickers_dict.keys():
    if name in data.columns:
      sec_series = data[name]
      rs = sec_series / bench_series
      sma_rs = rs.rolling(window=14).mean()
      ratio = 100 + ((rs - sma_rs) / sma_rs) * 100
      momentum = 100 + ratio.diff(1)
      ratio_df[name] = ratio
      mom_df[name] = momentum

  ratio_df.dropna(inplace=True)
  mom_df.dropna(inplace=True)

  if ratio_df.empty or mom_df.empty:
    st.warning("Not enough overlapping data found. Try toggling timeframe.")
  else:
    # Build Plotly RRG Chart
    fig = go.Figure()

    fig.add_hline(y=100, line_dash="dash", line_color="gray")
    fig.add_vline(x=100, line_dash="dash", line_color="gray")

    # Watermarks
    fig.add_annotation(
        x=107,
        y=108,
        text="<b>LEADING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(40, 167, 69, 0.25)"),
    )
    fig.add_annotation(
        x=93,
        y=108,
        text="<b>IMPROVING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(0, 123, 255, 0.25)"),
    )
    fig.add_annotation(
        x=93,
        y=92,
        text="<b>LAGGING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(220, 53, 69, 0.25)"),
    )
    fig.add_annotation(
        x=107,
        y=92,
        text="<b>WEAKENING</b>",
        showarrow=False,
        font=dict(size=20, color="rgba(255, 193, 7, 0.35)"),
    )

    for name in ratio_df.columns:
      x_vals = ratio_df[name].tail(tail_length)
      y_vals = mom_df[name].tail(tail_length)

      fig.add_trace(
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

    fig.update_layout(
        title=f"{view_mode} Rotation Graph — {timeframe} View",
        xaxis_title="RS-Ratio (Trend Strength)",
        yaxis_title="RS-Momentum",
        xaxis=dict(range=[90, 110]),
        yaxis=dict(range=[90, 110]),
        height=700,
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- QUADRANT CARDS BREAKDOWN SECTION ---
    st.markdown("---")
    st.subheader(f"📊 {view_mode} Quadrant Summary")

    latest_ratios = ratio_df.iloc[-1]
    latest_moms = mom_df.iloc[-1]

    leading, weakening, lagging, improving = [], [], [], []

    for name in ratio_df.columns:
      r = latest_ratios[name]
      m = latest_moms[name]
      if r >= 100 and m >= 100:
        leading.append(name)
      elif r >= 100 and m < 100:
        weakening.append(name)
      elif r < 100 and m < 100:
        lagging.append(name)
      else:
        improving.append(name)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
      st.markdown("#### 🟢 Leading")
      for s in leading:
        st.markdown(f"- **{s}**")

    with col2:
      st.markdown("#### 🔵 Improving")
      for s in improving:
        st.markdown(f"- **{s}**")

    with col3:
      st.markdown("#### 🟡 Weakening")
      for s in weakening:
        st.markdown(f"- **{s}**")

    with col4:
      st.markdown("#### 🔴 Lagging")
      for s in lagging:
        st.markdown(f"- **{s}**")

    # --- SEPARATE PARTITION: DETAILED STOCKS / ITEMS TABLE ---
    st.markdown("---")
    st.subheader(f"📋 Detailed Breakdown Table ({view_mode})")

    summary_data = []
    for name in ratio_df.columns:
      r = latest_ratios[name]
      m = latest_moms[name]
      if r >= 100 and m >= 100:
        quad = "Leading"
      elif r >= 100 and m < 100:
        quad = "Weakening"
      elif r < 100 and m < 100:
        quad = "Lagging"
      else:
        quad = "Improving"

      summary_data.append(
          {"Name": name, "RS-Ratio (X)": round(r, 2), "RS-Momentum (Y)": round(m, 2), "Quadrant": quad}
      )

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
