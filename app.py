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

# Benchmark and Sector Tickers
benchmark = "^NSEI"
sectors = {
    "IT": "^CNXIT",
    "AUTO": "^CNXAUTO",
    "PHARMA": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "METAL": "^CNXMETAL",
    "REALTY": "^CNXREALTY",
    "ENERGY": "^CNXENERGY",
    "PSU BANK": "^CNXPSUBANK",
    "PVT BANK": "^CNXPVTBNK",
    "MEDIA": "^CNXMEDIA",
    "INFRA": "^CNXINFRA",
}


@st.cache_data(ttl=3600)
def fetch_data(tf):
  period = "1y" if tf == "Daily" else "2y"
  interval = "1d" if tf == "Daily" else "1wk"

  all_tickers = list(sectors.values()) + [benchmark]
  df_dict = {}

  for ticker in all_tickers:
    try:
      df = yf.download(
          ticker, period=period, interval=interval, progress=False
      )
      if not df.empty:
        # Extract Close column safely regardless of multi-index structure
        if isinstance(df.columns, pd.MultiIndex):
          close_series = df[("Close", ticker)]
        else:
          close_series = df["Close"]
        df_dict[ticker] = close_series.squeeze()
    except Exception as e:
      print(f"Error fetching {ticker}: {e}")

  combined_df = pd.DataFrame(df_dict)
  combined_df.dropna(how="all", inplace=True)
  return combined_df


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
      rs = sec_series / bench_series
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
              marker=dict(size=[6] * (len(x_vals) - 1) + [12]),
          )
      )

  fig.update_layout(
      title=f"Sector Rotation Graph — {timeframe} View",
      xaxis_title="RS-Ratio (Trend Strength)",
      yaxis_title="RS-Momentum",
      xaxis=dict(range=[90, 110]),
      yaxis=dict(range=[90, 110]),
      height=700,
      template="plotly_white",
  )

  st.plotly_chart(fig, use_container_width=True)
