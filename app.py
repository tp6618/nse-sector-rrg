import io
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Dual-Partition Live Nifty 500 Multi-Screener",
    page_icon="📈",
    layout="wide",
)

st.title("NSE Sector Rotation & Dual-Partition Live Nifty 500 Screener")
st.markdown(
    "Automatically fetches live Nifty 500 components from NSE India and scans"
    " across 5 custom screeners for both near-highs (0-10%) and pullback (5-7%)"
    " setups."
)

# Sidebar UI Controls
st.sidebar.header("Configuration")
timeframe = st.sidebar.selectbox("Select Timeframe View", ["Daily", "Weekly"])
tail_length = st.sidebar.slider("Tail Length (History)", 3, 15, 5)

if st.sidebar.button("🔄 Refresh Live Market Data"):
  st.cache_data.clear()
  st.success("Cache cleared! Fetching fresh live market data...")
  time.sleep(1)
  st.rerun()

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


@st.cache_data(ttl=300)
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
              marker=dict(size=[6] * (len(x_vals) - 1) + [12], symbol="circle"),
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
# PART 3: DUAL-PARTITION LIVE NIFTY 500 SCREENER
# ==========================================
st.markdown("---")
st.header("🔍 Auto-Updating Multi-Screener Engine (Dual Partitions)")


@st.cache_data(ttl=3600)
def get_nifty500_tickers():
  url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
      df_csv = pd.read_csv(io.StringIO(response.text))
      if "Symbol" in df_csv.columns:
        return [str(sym).strip() + ".NS" for sym in df_csv["Symbol"].tolist()]
  except Exception:
    pass

  return [
      "RELIANCE.NS",
      "TCS.NS",
      "HDFCBANK.NS",
      "ICICIBANK.NS",
      "INFY.NS",
      "SBIN.NS",
      "AXISBANK.NS",
      "ITC.NS",
      "BHARTIARTL.NS",
      "TATAMOTORS.NS",
      "SUNPHARMA.NS",
      "MARUTI.NS",
      "TITAN.NS",
      "BAJFINANCE.NS",
      "ASIANPAINT.NS",
      "HCLTECH.NS",
      "ADANIENT.NS",
      "NTPC.NS",
      "ONGC.NS",
  ]


@st.cache_data(ttl=300)
def run_dual_screeners():
  tickers = get_nifty500_tickers()
  near_highs_results = []
  pullback_results = []

  nifty_df = yf.download(
      "^NSEI", period="1y", interval="1d", progress=False
  )
  nifty_close = (
      nifty_df[("Close", "^NSEI")]
      if isinstance(nifty_df.columns, pd.MultiIndex)
      else nifty_df["Close"]
  )
  nifty_return_60d = (
      (nifty_close.iloc[-1] - nifty_close.iloc[-60]) / nifty_close.iloc[-60]
      if len(nifty_close) >= 60
      else 0
  )

  progress_bar = st.progress(0)
  total_stocks = len(tickers)

  for i, ticker in enumerate(tickers):
    progress_bar.progress((i + 1) / total_stocks)
    try:
      df = yf.download(ticker, period="1y", interval="1d", progress=False)
      if not df.empty and len(df) >= 200:
        if isinstance(df.columns, pd.MultiIndex):
          close = df[("Close", ticker)]
          vol = df[("Volume", ticker)]
          high = df[("High", ticker)]
        else:
          close = df["Close"]
          vol = df["Volume"]
          high = df["High"]

        curr_close = close.iloc[-1]
        prev_close = close.iloc[-2]
        curr_vol = vol.iloc[-1]
        prev_vol = vol.iloc[-2]

        high_ref = high.max()
        pct_below_high = (high_ref - curr_close) / high_ref

        # Check which partition zone this stock falls into
        is_near_highs = pct_below_high <= 0.10
        is_pullback_zone = 0.05 <= pct_below_high <= 0.07

        if not (is_near_highs or is_pullback_zone):
          continue

        # ADTV Liquidity Filter (>= 1 Crore INR)
        adtv = (close * vol).tail(20).mean()
        if adtv < 10000000:
          continue

        # Relative Strength Filter
        stock_return_60d = (
            (curr_close - close.iloc[-60]) / close.iloc[-60]
            if len(close) >= 60
            else 0
        )
        if stock_return_60d < nifty_return_60d:
          continue

        # Volume Dry-up Check
        vol_sma_20 = vol.rolling(20).mean()
        volume_dry_up = (
            vol.iloc[-2] < vol_sma_20.iloc[-2]
            or vol.iloc[-3] < vol_sma_20.iloc[-3]
        )
        if not volume_dry_up:
          continue

        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        curr_rsi = rsi.iloc[-1]

        # EMAs and SMAs
        ema_5 = close.ewm(span=5).mean().iloc[-1]
        ema_13 = close.ewm(span=13).mean().iloc[-1]
        ema_20 = close.ewm(span=20).mean().iloc[-1]
        ema_21 = close.ewm(span=21).mean().iloc[-1]
        ema_26 = close.ewm(span=26).mean().iloc[-1]
        sma_vol_30 = vol.tail(30).mean()

        # 5 Custom Screeners
        s1 = (
            curr_vol > prev_vol
            and curr_close > close.iloc[-14]
            and curr_vol > 100000
            and curr_close > prev_close
        )
        s2 = (
            curr_close >= high_ref * 0.95
            and curr_close <= high_ref * 1.02
            and 55 <= curr_rsi <= 80
        )
        ema_bunched = (
            abs((curr_close - ema_5) / ema_5) * 100 <= 1
            and abs((curr_close - ema_13) / ema_13) * 100 <= 1
            and abs((curr_close - ema_21) / ema_21) * 100 <= 1
            and abs((curr_close - ema_26) / ema_26) * 100 <= 1
        )
        s3 = curr_vol > 100000 and curr_vol > sma_vol_30 and ema_bunched
        pole_move = (
            (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]
            if len(close) >= 20
            else 0
        )
        s4 = curr_vol > 500000 and curr_close > 100 and pole_move > 0.04
        s5 = (
            curr_close > ema_20
            and curr_rsi >= 58
            and curr_vol >= (vol_sma_20.iloc[-1] * 1.2)
            and (curr_close * curr_vol) >= 5000000
        )

        passed_count = sum([s1, s2, s3, s4, s5])

        if passed_count >= 2:
          vol_multiple = (
              curr_vol / vol_sma_20.iloc[-1]
              if vol_sma_20.iloc[-1] > 0
              else 1.0
          )
          composite_score = (
              passed_count * 20
              + (stock_return_60d * 10)
              + (vol_multiple * 5)
              + ((1 - pct_below_high) * 15)
          )

          entry = {
              "ticker": ticker.split(".")[0],
              "price": curr_close,
              "high_ref": high_ref,
              "pullback_pct": f"{pct_below_high * 100:.2f}%",
              "matches": passed_count,
              "details": f"Passed {passed_count}/5 Screeners",
              "score": composite_score,
          }

          if is_near_highs:
            near_highs_results.append(entry)
          elif is_pullback_zone:
            pullback_results.append(entry)
    except Exception:
      pass

  progress_bar.empty()
  near_highs_results = sorted(
      near_highs_results, key=lambda x: x["score"], reverse=True
  )
  pullback_results = sorted(
      pullback_results, key=lambda x: x["score"], reverse=True
  )
  return near_highs_results, pullback_results


near_highs, pullbacks = run_dual_screeners()

# --- Partition 1: Near 52W Highs (0-10%) ---
st.subheader(
    "📈 Partition 1: Auto-Updating Screener (Near 52W Highs: 0-10% below peak)"
)
if not near_highs:
  st.info("No stocks currently match the Near Highs intersection criteria.")
else:
  st.success(f"Found {len(near_highs)} stocks testing near 52W highs!")
  cols1 = st.columns(3)
  for idx, stock in enumerate(near_highs[:9]):
    with cols1[idx % 3]:
      st.markdown(
          f"### ⭐ `{stock['ticker']}`\n"
          f"**Price:** ₹{stock['price']:,.2f}  \n"
          f"**52W High:** ₹{stock['high_ref']:,.2f}  \n"
          f"**Status:** {stock['details']}"
      )
      st.markdown("---")

st.markdown("\n")

# --- Partition 2: Pullback Zone (5-7%) ---
st.subheader("📉 Partition 2: Auto Update Screener (5-7% Pullback Zone)")
if not pullbacks:
  st.info("No stocks currently match the 5-7% pullback zone criteria.")
else:
  st.success(f"Found {len(pullbacks)} stocks in the 5-7% pullback zone!")
  cols2 = st.columns(3)
  for idx, stock in enumerate(pullbacks[:9]):
    with cols2[idx % 3]:
      st.markdown(
          f"### ⭐ `{stock['ticker']}`\n"
          f"**Price:** ₹{stock['price']:,.2f}  \n"
          f"**High Ref:** ₹{stock['high_ref']:,.2f}  \n"
          f"**Pullback Depth:** {stock['pullback_pct']} below High  \n"
          f"**Status:** {stock['details']}"
      )
      st.markdown("---")
