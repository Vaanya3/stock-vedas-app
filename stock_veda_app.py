# Stock Veda – Streamlit web‑app skeleton
# ---------------------------------------
# Quick‑start:  
#   $ pip install streamlit yfinance ta mplfinance pandas
#   $ streamlit run stock_veda_app.py
#
# This skeleton gives you:
#   • Text input for stock symbol
#   • One functional analysis tab (Auto Analysis)
#   • Five additional empty tabs ready to embed Google Colab notebooks via iframe.
# Adapt/extend at will – happy hacking!

import streamlit as st
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import ta  # pip install ta
from io import BytesIO

st.set_page_config(page_title="Stock Veda", layout="wide")

st.title("📈 Stock Veda – Auto Chart Insight Bot")

# -------------------- Sidebar --------------------
st.sidebar.header("🔍 Stock Selector")
symbol = st.sidebar.text_input("Enter stock symbol (e.g. RELIANCE.NS)", value="RELIANCE.NS")
period = st.sidebar.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
interval = st.sidebar.selectbox("Interval", ["1d", "1h", "30m"], index=0)
if not symbol:
    st.stop()

# -------------------- Tabs --------------------
TAB_TITLES = [
    "Auto Analysis",  # functional tab
    "Colab Tab 1",    # empty placeholder
    "Colab Tab 2",
    "Colab Tab 3",
    "Colab Tab 4",
    "Colab Tab 5",
]

tabs = st.tabs(TAB_TITLES)

auto_tab = tabs[0]
with auto_tab:
    st.subheader(f"🔬 Automated Technical Snapshot : {symbol.upper()}")

    # Fetch data
    try:
        data = yf.download(symbol, period=period, interval=interval, progress=False)
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        st.stop()

    if data.empty:
        st.warning("No price data returned – check symbol or select a larger period.")
        st.stop()

    # Indicators – simple examples, extend as you like
    data["EMA20"] = ta.trend.ema_indicator(data["Close"], window=20)
    data["EMA50"] = ta.trend.ema_indicator(data["Close"], window=50)
    data["RSI14"] = ta.momentum.rsi(data["Close"], window=14)

    # Chart – candles + EMAs
    fig_buf = BytesIO()
    mpf.plot(
        data,
        type="candle",
        mav=(20, 50),
        volume=True,
        style="yahoo",
        returnfig=True,
    )[0].savefig(fig_buf, format="png", bbox_inches="tight")
    st.image(fig_buf, caption="Price with EMA20 / EMA50 & Volume", use_column_width=True)

    # RSI chart
    st.markdown("### RSI (14)")
    st.line_chart(data["RSI14"], height=150)

    # Simple verdict logic
    latest_close = data["Close"].iloc[-1]
    ema20 = data["EMA20"].iloc[-1]
    ema50 = data["EMA50"].iloc[-1]

    verdict = "Sideways 🚦"
    if latest_close > ema20 > ema50:
        verdict = "Bullish 📈 – price above EMA20 & EMA50"
    elif latest_close < ema20 < ema50:
        verdict = "Bearish 📉 – price below EMA20 & EMA50"

    st.markdown(f"#### Verdict: **{verdict}**")

# -------------------- Empty Colab Tabs --------------------
placeholder_text = """
### Embed your Google Colab notebook here
Paste the **public shareable link** of your Colab notebook below and press Enter.
"""
for i in range(1, 6):
    with tabs[i]:
        st.write(placeholder_text)
        colab_url = st.text_input(f"Colab {i} URL", key=f"colab{i}")
        if colab_url:
            st.components.v1.iframe(colab_url, height=800, scrolling=True)
