import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="NSE Sector Rotation & Advanced Screener",
    page_icon="📈",
    layout="wide",
)

st.title("NSE Sector Rotation & Nifty 500 Advanced Momentum Screener")
st.markdown(
    "Track overall NSE sector rotation, constituent directories, and"
    " multi-factor VCP + 9/20 EMA setups."
)

# Sidebar UI Controls
st.sidebar.header("Configuration")
timeframe = st.sidebar.selectbox("Select Timeframe View", ["Daily", "Weekly"])
tail_length = st.sidebar.slider("Tail Length (History)", 3, 15, 5)

# ==========================================
# PART 1: ALL SECTORS ROTATION CHART & SUMMARY
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
# PART 2: SECTOR CONSTITUENT STOCKS DIRECTORY
# ==========================================
st.markdown("---")
st.header("📋 Sector Constituent Stocks Directory")

sector_stocks_db = {
    "IT": [
        "TCS (TCS.NS)",
        "Infosys (INFY.NS)",
        "Wipro (WIPRO.NS)",
        "HCL Technologies (HCLTECH.NS)",
        "Tech Mahindra (TECHM.NS)",
        "LTIMindtree (LTIM.NS)",
        "Persistent Systems (PERSISTENT.NS)",
        "Coforge (COFORGE.NS)",
        "Mphasis (MPHASIS.NS)",
    ],
    "AUTO": [
        "Tata Motors (TATAMOTORS.NS)",
        "Maruti Suzuki (MARUTI.NS)",
        "Mahindra & Mahindra (M&M.NS)",
        "Bajaj Auto (BAJAJ-AUTO.NS)",
        "Hero MotoCorp (HEROMOTOCO.NS)",
        "Eicher Motors (EICHERMOT.NS)",
        "TVS Motor (TVSMOTOR.NS)",
        "Ashok Leyland (ASHOKLEY.NS)",
    ],
    "PHARMA": [
        "Sun Pharmaceutical (SUNPHARMA.NS)",
        "Dr. Reddy's Laboratories (DRREDDY.NS)",
        "Cipla (CIPLA.NS)",
        "Divi's Laboratories (DIVISLAB.NS)",
        "Apollo Hospitals (APOLLOHOSP.NS)",
        "Lupin (LUPIN.NS)",
        "Torrent Pharma (TORNTPHARM.NS)",
        "Mankind Pharma (MANKIND.NS)",
    ],
    "FMCG": [
        "Hindustan Unilever (HINDUNILVR.NS)",
        "ITC (ITC.NS)",
        "Nestle India (NESTLEIND.NS)",
        "Britannia Industries (BRITANNIA.NS)",
        "Tata Consumer Products (TATACONSUM.NS)",
        "Dabur India (DABUR.NS)",
        "Marico (MARICO.NS)",
        "Godrej Consumer (GODREJCP.NS)",
    ],
    "METAL": [
        "Tata Steel (TATASTEEL.NS)",
        "Hindalco Industries (HINDALCO.NS)",
        "JSW Steel (JSWSTEEL.NS)",
        "Vedanta (VEDL.NS)",
        "Coal India (COALINDIA.NS)",
        "NMDC (NMDC.NS)",
        "Jindal Steel & Power (JSL.NS)",
        "SAIL (SAIL.NS)",
    ],
    "BANK": [
        "HDFC Bank (HDFCBANK.NS)",
        "ICICI Bank (ICICIBANK.NS)",
        "State Bank of India (SBIN.NS)",
        "Kotak Mahindra Bank (KOTAKBANK.NS)",
        "Axis Bank (AXISBANK.NS)",
        "IndusInd Bank (INDUSINDBK.NS)",
        "Bank of Baroda (BANKBARODA.NS)",
        "Punjab National Bank (PNB.NS)",
    ],
}

selected_directory_sector = st.selectbox(
    "Select a Sector to View Constituent Stocks", list(sector_stocks_db.keys())
)

st.markdown(f"### Stocks in {selected_directory_sector} Sector:")
stocks_list = sector_stocks_db[selected_directory_sector]

col_a, col_b = st.columns(2)
half_len = (len(stocks_list) + 1) // 2

with col_a:
  for stock in stocks_list[:half_len]:
    st.markdown(f"✅ {stock}")

with col_b:
  for stock in stocks_list[half_len:]:
    st.markdown(f"✅ {stock}")


# ==========================================
# PART 3: ADVANCED VCP + 9/20 EMA + SUPER SCREENER (6 STOCKS)
# ==========================================
st.markdown("---")
st.header(
    "🚀 Advanced VCP + 9/20 EMA Momentum & Super Breakout Screener"
)
st.markdown(
    "Screening Nifty 500 stocks for volatility contraction (VCP), 9/20 EMA"
    " bullish crossover alignment, and volume explosion."
)


@st.cache_data(ttl=600)
def scan_advanced_setups():
  screening_pool = {
      "Apar Industries": "APARINDS.NS",
      "BEML": "BEML.NS",
      "Aegis Vopak": "AEGISVOPAK.NS",
      "Deepak Fertilisers": "DEEPAKFERT.NS",
      "Jubilant Food": "JUBLFOOD.NS",
      "HDFC Life": "HDFCLIFE.NS",
      "Tata Motors": "TATAMOTORS.NS",
      "Sun Pharma": "SUNPHARMA.NS",
      "Tata Steel": "TATASTEEL.NS",
      "Hindalco": "HINDALCO.NS",
      "Divi's Lab": "DIVISLAB.NS",
      "BHEL": "BHEL.NS",
      "Cochin Shipyard": "COCHINSHIP.NS",
      "Mazagon Dock": "MAZDOCK.NS",
      "Kaynes Technology": "KAYNES.NS",
      "KPIT Tech": "KPITTECH.NS",
      "Persistent Systems": "PERSISTENT.NS",
      "Trent": "TRENT.NS",
      "Bharat Electronics": "BEL.NS",
  }

  results = []
  for name, ticker in screening_pool.items():
    try:
      df = yf.download(ticker, period="3mo", interval="1d", progress=False)
      if not df.empty and len(df) >= 50:
        if isinstance(df.columns, pd.MultiIndex):
          close_s = df[("Close", ticker)]
          vol_s = df[("Volume", ticker)]
        else:
          close_s = df["Close"]
          vol_s = df["Volume"]

        curr_price = close_s.iloc[-1]

        # 1. Calculate 9 and 20 EMAs
        ema_9 = close_s.ewm(span=9, adjust=False).mean().iloc[-1]
        ema_20 = close_s.ewm(span=20, adjust=False).mean().iloc[-1]

        # 2. VCP Volatility Contraction Check
        recent_range = (
            close_s.tail(10).max() - close_s.tail(10).min()
        ) / curr_price
        prev_range = (
            close_s.iloc[-30:-10].max() - close_s.iloc[-30:-10].min()
        ) / curr_price

        # 3. Super Feature: Volume Explosion / Pocket Pivot Check
        avg_vol = vol_s.tail(20).mean()
        latest_vol = vol_s.iloc[-1]
        vol_multiple = latest_vol / avg_vol if avg_vol > 0 else 1.0

        # Scoring logic: Must have 9 EMA > 20 EMA, price tightening up (VCP), and volume support
        if ema_9 > ema_20 and curr_price > ema_9:
          tightening_score = (
              prev_range - recent_range
          ) * 100  # Positive means contracting volatility
          super_score = tightening_score + (vol_multiple * 5)

          results.append({
              "name": name,
              "ticker": ticker.split(".")[0],
              "price": curr_price,
              "ema_status": "9 EMA > 20 EMA 🟢",
              "vol_spike": f"{vol_multiple:.1f}x",
              "score": super_score,
          })
    except Exception:
      pass

  # Sort by highest composite score and return top 6
  results = sorted(results, key=lambda x: x["score"], reverse=True)
  return results[:6]


advanced_stocks = scan_advanced_setups()

if not advanced_stocks:
  st.info("Scanning database for high-conviction VCP + EMA setups...")
else:
  cols = st.columns(3)
  for idx, stock in enumerate(advanced_stocks):
    col_target = cols[idx % 3]
    with col_target:
      st.markdown(
          f"### ⚡ {stock['name']} (`{stock['ticker']}`)\n"
          f"**Price:** ₹{stock['price']:,.2f}  \n"
          f"**EMA Trend:** {stock['ema_status']}  \n"
          f"**Volume Power:** {stock['vol_spike']} average"
      )
      st.markdown("---")
