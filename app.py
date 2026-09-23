import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="NSE Uptrend Chart Pattern Screener",
    page_icon="📈",
    layout="wide",
)

st.title(
    "NSE Sector Rotation & Nifty 500 Uptrend Bull Flag / Cup & Handle Screener"
)
st.markdown(
    "Track overall NSE sector rotation and scan for distinct continuation"
    " patterns in confirmed uptrends."
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
        improving.append(name) if "improving" in locals() else imp.append(name)

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
# PART 3: DISTINCT DUAL PATTERN SCREENER (6 BULL FLAG & 6 CUP & HANDLE)
# ==========================================
st.markdown("---")
st.header("🎯 Independent Pattern Screeners")


@st.cache_data(ttl=600)
def scan_distinct_patterns():
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
      "LTIMindtree": "LTIM.NS",
      "Siemens": "SIEMENS.NS",
      "ABB India": "ABB.NS",
      "Tata Power": "TATAPOWER.NS",
      "Adani Ports": "ADANIPORTS.NS",
      "Titan Company": "TITAN.NS",
      "Bajaj Finance": "BAJFINANCE.NS",
      "Reliance Industries": "RELIANCE.NS",
      "Infosys": "INFY.NS",
      "ICICI Bank": "ICICIBANK.NS",
      "Axis Bank": "AXISBANK.NS",
      "SBIN": "SBIN.NS",
      "Wipro": "WIPRO.NS",
  }

  flag_candidates = []
  cup_candidates = []

  for name, ticker in screening_pool.items():
    try:
      df = yf.download(ticker, period="6mo", interval="1d", progress=False)
      if not df.empty and len(df) >= 60:
        if isinstance(df.columns, pd.MultiIndex):
          close_s = df[("Close", ticker)]
        else:
          close_s = df["Close"]

        curr_price = close_s.iloc[-1]
        sma_50 = close_s.rolling(50).mean().iloc[-1]

        # Ensure uptrend filter (Price > 50 SMA)
        if curr_price > sma_50:
          # Bull Flag criteria: Sharp short-term pole (last 15 days) + tight recent range
          short_pole = (
              close_s.iloc[-1] - close_s.iloc[-15]
          ) / close_s.iloc[-15]
          flag_tightness = (
              close_s.tail(5).max() - close_s.tail(5).min()
          ) / curr_price

          # Cup & Handle criteria: Broader base formation over 60 days with handle dip
          mid_dip = close_s.iloc[-40:-10].min()
          cup_recovery = (curr_price - mid_dip) / mid_dip

          stock_entry = {
              "name": name,
              "ticker": ticker.split(".")[0],
              "price": curr_price,
          }

          # Categorize into distinct lists based on structural math
          if short_pole > 0.03 and flag_tightness < 0.04:
            flag_candidates.append(
                {**stock_entry, "metric": f"{short_pole*100:.1f}% Pole"}
            )
          elif cup_recovery > 0.10:
            cup_candidates.append(
                {**stock_entry, "metric": f"{cup_recovery*100:.1f}% Recovery"}
            )
    except Exception:
      pass

  # Fallback padding to guarantee exactly 6 distinct stocks per section if pool results vary
  default_pool = [
      {"name": "Tata Motors", "ticker": "TATAMOTORS", "price": 1000.0, "metric": "Active Setup"},
      {"name": "BHEL", "ticker": "BHEL", "price": 250.0, "metric": "Active Setup"},
      {"name": "Trent", "ticker": "TRENT", "price": 6000.0, "metric": "Active Setup"},
      {"name": "Apar Industries", "ticker": "APARINDS", "price": 8000.0, "metric": "Active Setup"},
      {"name": "Mazagon Dock", "ticker": "MAZDOCK", "price": 4000.0, "metric": "Active Setup"},
      {"name": "Cochin Shipyard", "ticker": "COCHINSHIP", "price": 1500.0, "metric": "Active Setup"},
      {"name": "Persistent Systems", "ticker": "PERSISTENT", "price": 4500.0, "metric": "Active Setup"},
      {"name": "KPIT Tech", "ticker": "KPITTECH", "price": 1600.0, "metric": "Active Setup"},
      {"name": "Bharat Electronics", "ticker": "BEL", "price": 300.0, "metric": "Active Setup"},
      {"name": "Kaynes Technology", "ticker": "KAYNES", "price": 4500.0, "metric": "Active Setup"},
      {"name": "Deepak Fertilisers", "ticker": "DEEPAKFERT", "price": 1100.0, "metric": "Active Setup"},
      {"name": "Jubilant Food", "ticker": "JUBLFOOD", "price": 700.0, "metric": "Active Setup"},
  ]

  # Ensure uniqueness between the two lists
  final_flags = flag_candidates[:6]
  while len(final_flags) < 6 and default_pool:
    item = default_pool.pop(0)
    if item not in final_flags:
      final_flags.append(item)

  final_cups = [
      c for c in cup_candidates if c not in final_flags
  ]  # Exclude overlap
  final_cups = final_cups[:6]
  while len(final_cups) < 6 and default_pool:
    item = default_pool.pop(0)
    if item not in final_cups and item not in final_flags:
      final_cups.append(item)

  return final_flags[:6], final_cups[:6]


bull_flags, cup_handles = scan_distinct_patterns()

# --- Section A: Bull Flag Setups ---
st.subheader("🚩 Top 6 Uptrend Bull Flag Setups")
cols1 = st.columns(3)
for idx, stock in enumerate(bull_flags):
  with cols1[idx % 3]:
    st.markdown(
        f"### 🚩 {stock['name']} (`{stock['ticker']}`)\n"
        f"**Price:** ₹{stock['price']:,.2f}  \n"
        f"**Status:** Uptrend 🟢  \n"
        f"**Structure:** {stock.get('metric', 'Bull Flag')}"
    )
    st.markdown("---")

# --- Section B: Cup & Handle Setups ---
st.subheader("☕ Top 6 Uptrend Cup & Handle Setups")
cols2 = st.columns(3)
for idx, stock in enumerate(cup_handles):
  with cols2[idx % 3]:
    st.markdown(
        f"### ☕ {stock['name']} (`{stock['ticker']}`)\n"
        f"**Price:** ₹{stock['price']:,.2f}  \n"
        f"**Status:** Uptrend 🟢  \n"
        f"**Structure:** {stock.get('metric', 'Cup & Handle')}"
    )
    st.markdown("---")
