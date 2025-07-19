# Stock Veda – Streamlit web‑app (Advanced Edition)
# ---------------------------------------------------
# Quick‑start:
#   $ pip install -r requirements.txt
#   $ streamlit run stock_veda_app.py
#
# requirements.txt should contain:
# streamlit
import yfinance as yf
pandas
ta
mplfinance
numpy
matplotlib

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import mplfinance as mpf
import ta
import matplotlib.pyplot as plt
from io import BytesIO

# ---------------------------------------------------
# Helper functions
# ---------------------------------------------------

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)
    df["EMA20"] = ta.trend.ema_indicator(close, window=20)
    df["EMA50"] = ta.trend.ema_indicator(close, window=50)
    df["RSI14"] = ta.momentum.rsi(close, window=14)
    df["OBV"] = ta.volume.on_balance_volume(close, volume)
    df["AD"] = ta.volume.acc_dist_index(high=df["High"], low=df["Low"], close=close, volume=volume)
    # Custom Smart Money Detection – CVD based
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    money_flow = typical_price * df["Volume"]
    df["CVD"] = money_flow.cumsum()
    df["CVD_SLOPE"] = df["CVD"].diff()
    df["SMART_CANDLE"] = df["CVD_SLOPE"] > df["CVD_SLOPE"].rolling(10).mean() * 2
    return df


def detect_vcp(df: pd.DataFrame) -> str:
    highs = df["High"].tail(60).astype(float)
    lows = df["Low"].tail(60).astype(float)
    swings = ((highs - lows) / lows).rolling(5).max()
    last_swings = swings.dropna().tail(4).values
    if len(last_swings) < 4:
        return "Insufficient data"
    contractions = np.all(last_swings[1:] < last_swings[:-1] * 0.9)
    return "Strong VCP pattern" if contractions else "No clear VCP"


def breakout_zone(df: pd.DataFrame) -> tuple:
    recent_high = df["High"].tail(60).max()
    latest_close = df["Close"].iloc[-1]
    vol_ratio = df["Volume"].iloc[-1] / df["Volume"].tail(20).mean()
    is_breakout = latest_close > recent_high * 0.995 and vol_ratio > 1.5
    return is_breakout, recent_high


def smart_money_signal(df: pd.DataFrame) -> str:
    ad = df["AD"].tail(20)
    slope = np.polyfit(range(len(ad)), ad, 1)[0]
    return "Accumulation" if slope > 0 else "Distribution"


def final_verdict(vcp: str, breakout: bool, smart: str, rsi: float) -> str:
    if breakout and vcp.startswith("Strong") and smart == "Accumulation" and 40 < rsi < 70:
        return "BUY 📈 – breakout from VCP with smart‑money support"
    if smart == "Distribution" or rsi > 80:
        return "SELL/AVOID 🚫 – distribution or overbought"
    return "WATCHLIST 👀 – setup forming but not ready"

# ---------------------------------------------------
# Streamlit UI
# ---------------------------------------------------

st.set_page_config(page_title="Stock Veda", layout="wide")
st.title("📈 Stock Veda – Auto Chart Insight Bot (Advanced Edition)")

st.sidebar.header("🔍 Stock Selector")
symbol = st.sidebar.text_input("Enter stock symbol (e.g. RELIANCE.NS)", value="RELIANCE.NS")
period = st.sidebar.selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=1)
interval = st.sidebar.selectbox("Interval", ["1d", "1h"], index=0)

if not symbol:
    st.stop()

TAB_TITLES = ["Auto Analysis", "Colab Tab 1", "Colab Tab 2", "Colab Tab 3", "Colab Tab 4", "Colab Tab 5"]
tabs = st.tabs(TAB_TITLES)
auto_tab = tabs[0]

with auto_tab:
    st.subheader(f"🧪 Automated Technical Snapshot : {symbol.upper()}")
    try:
        data = yf.download(symbol, period=period, interval=interval, progress=False)
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        st.stop()

    if data.empty:
        st.warning("No price data returned – check symbol or increase period.")
        st.stop()

    data = compute_indicators(data)
    vcp_status = detect_vcp(data)
    is_breakout, resistance_level = breakout_zone(data)
    smart_status = smart_money_signal(data)
    latest_rsi = data["RSI14"].iloc[-1]
    verdict = final_verdict(vcp_status, is_breakout, smart_status, latest_rsi)

    # Custom colors for smart money candles
    candle_colors = ["#FFD700" if smart else "#26a69a" if o < c else "#ef5350" for o, c, smart in zip(data.Open, data.Close, data.SMART_CANDLE)]

    fig, ax = mpf.plot(
        data,
        type="candle",
        mav=(20, 50),
        volume=True,
        style="yahoo",
        returnfig=True,
        fill_between=dict(y1=data["EMA20"], y2=data["EMA50"], alpha=0.1, color="purple"),
        update_width_config=dict(candle_linewidth=0.8),
        alines=dict(alines=[]),
        candle_colors=candle_colors
    )
    ax[0].axhline(y=resistance_level, color='orange', linestyle='--', label='Resistance')
    if is_breakout:
        ax[0].annotate(
            'BO 💥',
            xy=(data.index[-1], data["Close"].iloc[-1]),
            xytext=(data.index[-10], data["Close"].iloc[-1] + 0.05 * data["Close"].iloc[-1]),
            arrowprops=dict(facecolor='green', shrink=0.05),
            fontsize=10, color='green'
        )
    fig_buf = BytesIO()
    fig.savefig(fig_buf, format="png", bbox_inches="tight")
    st.image(fig_buf, caption="Smart Money Candle Highlight + EMA + S/R", use_column_width=True)

    st.markdown("#### RSI (14)")
    st.line_chart(data["RSI14"].astype(float), height=150)

    st.markdown("### Signal Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VCP", vcp_status)
    col2.metric("Breakout Zone", "Yes" if is_breakout else "No")
    col3.metric("Smart Money", smart_status)
    col4.metric("RSI", f"{latest_rsi:.1f}")
    st.markdown(f"## Verdict: **{verdict}**")

placeholder_md = """### Embed your Google Colab notebook here\nPaste the **public shareable link** below and press Enter."""
for i in range(1, 6):
    with tabs[i]:
        st.write(placeholder_md)
        colab_url = st.text_input(f"Colab {i} URL", key=f"colab{i}")
        if colab_url:
            st.components.v1.iframe(colab_url, height=800, scrolling=True)

