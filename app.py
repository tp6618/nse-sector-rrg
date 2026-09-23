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
    "Relative Rotation Graph tracking all NSE sectors & top stocks against the"
    " Nifty 50 benchmark."
)

# Sidebar UI Controls
st.sidebar.header("Configuration")
timeframe = st.sidebar.selectbox("Select Timeframe View", ["Daily", "Weekly"])
tail_length = st.sidebar.slider("Tail Length (History)", 3, 15, 5)

# Benchmark and Comprehensive NSE Sector Tickers dictionary
benchmark = "^NSEI"
sectors = {
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

# Top representative stocks for each sector (Yahoo Finance NSE format)
sector_stocks = {
    "AUTO": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "BAJAJ-AUTO.NS"],
    "BANK": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS"],
    "FIN SERVICE": ["BAJFINANCE.NS", "SBILIFE.NS", "HDFCLIFE.NS", "CHOLAFIN.NS"],
    "FMCG": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS"],
    "MEDIA": ["SUNTV.NS", "ZEEL.NS", "PVRINOX.NS"],
    "METAL": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS"],
    "PHARMA": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "PSU BANK": ["SBIN.NS", "PNB.NS", "BANKBARODA.NS", "CANBK.NS"],
    "REALTY": ["DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS"],
    "PVT BANK": [
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "AXISBANK.NS",
        "INDUSINDBK.NS",
    ],
    "HEALTHCARE": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "APOLLOHOSP.NS"],
    "CONSR DURBL": ["TITAN.NS", "HAVELLS.NS", "VOLTAS.NS", "ASIANPAINT.NS"],
    "OIL & GAS": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS"],
    "INFRA": ["LT.NS", "ADANIPORTS.NS", "NTPC.NS", "POWERGRID.NS"],
    "COMMODITIES": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "UPL.NS"],
}


@st.cache_data(ttl=3600)
def fetch_data(tf):
  period = "1y" if tf == "Daily" else "2y"
  interval = "1d" if tf == "Daily" else "1wk"

  data_dict = {}

  try:
    b_df = yf.download(
        benchmark, period=period, interval=interval, progress=False
    )
    if not b_df.empty:
      if isinstance(b_df.columns, pd.MultiIndex):
        data_dict[benchmark] = b_df[("Close", benchmark)].squeeze()
      else:
        data_dict[benchmark] = b_df["Close"].squeeze()
  except Exception:
    pass

  for name, ticker in sectors.items():
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

  for name in sectors.keys():
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

    # Add Quadrant Background Watermarks
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
        title=f"Sector Rotation Graph — {timeframe} View",
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
    st.subheader("📊 Sector Quadrant Summary")

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

    # --- TOP STOCKS PER SECTOR SECTION ---
    st.markdown("---")
    st.subheader("🚀 Top Stocks by Sector")

    # Let users pick a sector to view its top stocks
    selected_sec_stocks = st.selectbox(
        "Select a Sector to View Top Stocks:", list(sector_stocks.keys())
    )

    if selected_sec_stocks in sector_stocks:
      tickers_list = sector_stocks[selected_sec_stocks]
      st.write(
          f"Showing top constituent stocks for **{selected_sec_stocks}**:"
      )

      stock_data = []
      for t in tickers_list:
        try:
          stk = yf.Ticker(t)
          hist = stk.history(period="5d")
          if not hist.empty:
            curr_price = hist["Close"].iloc[-1]
            prev_price = hist["Close"].iloc[-2]
            change_pct = ((curr_price - prev_price) / prev_price) * 100
            stock_data.append({
                "Stock": t.replace(".NS", ""),
                "Price (₹)": round(curr_price, 2),
                "Change (%)": round(change_pct, 2),
            })
        except Exception:
          stock_data.append({"Stock": t.replace(".NS", ""), "Price (₹)": "N/A", "Change (%)": "N/A"})

      if stock_data:
        df_stocks = pd.DataFrame(stock_data)
        st.dataframe(df_stocks, use_container_width=True, hide_index=True)
