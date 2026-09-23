import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="NSE Sector Rotation RRG", page_icon="📈", layout="wide"
)

st.title("NSE Sector Rotation (RRG) Dashboard")
st.markdown(
    "Relative Rotation Graph tracking NSE sectors against the Nifty 50"
    " benchmark."
)

# Sidebar UI Controls
st.sidebar.header("Configuration")
timeframe = st.sidebar.selectbox("Select Timeframe View", ["Daily", "Weekly"])
tail_length = st.sidebar.slider("Tail Length (History)", 3, 15, 5)

# Benchmark and Sector Tickers (Using reliable standard NSE index symbols)
benchmark = "^NSEI"
sectors = {
    "IT": "^CNXIT",
    "AUTO": "^CNXAUTO",
    "PHARMA": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "METAL": "^CNXMETAL",
    "REALTY": "^CNXREALTY",
    "ENERGY": "^CNXENERGY",
    "INFRA": "^CNXINFRA",
}


@st.cache_data(ttl=3600)
def fetch_data(tf):
  period = "1y" if tf == "Daily" else "2y"
  interval = "1d" if tf == "Daily" else "1wk"

  all_tickers = list(sectors.values()) + [benchmark]

  # Download all tickers at once to avoid separate request limits
  df = yf.download(
      all_tickers, period=period, interval=interval, progress=False
  )["Close"]

  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

  df.dropna(how="all", inplace=True)
  return df


# Load Data
data = fetch_data(timeframe)

if benchmark not in data.columns:
  st.error(
      "Benchmark data could not be retrieved. Please check your network or"
      " ticker symbols."
  )
else:
  bench_series = data[benchmark]

  # Calculate RRG metrics
  ratio_df = pd.DataFrame(index=data.index)
  mom_df = pd.DataFrame(index=data.index)

  for name, ticker in sectors.items():
    if ticker in data.columns:
      sec_series = data[ticker]
      # Drop missing rows for individual sectors to prevent blank plots
      temp_df = pd.concat([sec_series, bench_series], axis=1).dropna()
      if not temp_df.empty:
        rs = temp_df.iloc[:, 0] / temp_df.iloc[:, 1]
        sma_rs = rs.rolling(window=14).mean()
        ratio = 100 + ((rs - sma_rs) / sma_rs) * 100
        momentum = 100 + ratio.diff(1)
        ratio_df[name] = ratio
        mom_df[name] = momentum

  ratio_df.dropna(inplace=True)
  mom_df.dropna(inplace=True)

  # Build Plotly RRG Chart
  fig = go.Figure()

  # Quadrant reference lines centered at 100
  fig.add_hline(y=100, line_dash="dash", line_color="gray")
  fig.add_vline(x=100, line_dash="dash", line_color="gray")

  # Plot each sector's trailing path and current position dot
  for name in sectors.keys():
    if name in ratio_df.columns and not ratio_df[name].empty:
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
              marker=dict(size=[6] * (len(x_vals) - 1) + [12], symbol="circle"),
          )
      )

  fig.update_layout(
      title=f"Sector Rotation Graph — {timeframe} View",
      xaxis_title="RS-Ratio (Trend Strength)",
      yaxis_title="RS-Momentum",
      xaxis=dict(range=[90, 110]),
      yaxis=dict(range=[90, 110]),
      height=600,
      template="plotly_white",
  )

  st.plotly_chart(fig, use_container_width=True)

  # --- QUADRANT CARDS BREAKDOWN SECTION ---
  st.markdown("---")
  st.subheader("📊 Sector Quadrant Summary")

  latest_ratios = ratio_df.iloc[-1]
  latest_moms = mom_df.iloc[-1]

  leading, weakening, lagging, improving = [], [], [], []

  for name in sectors.keys():
    if name in ratio_df.columns:
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
