import streamlit as st
import pandas as pd
import altair as alt
from utils import fetch_and_cache

st.title("💰 Gold OHLC Candlestick")

GOLD_URL = "https://west.albion-online-data.com/api/v2/stats/gold?count=720"

# Initial fetch if cache is empty
if st.session_state.get("data_cache", {}).get("gold") is None:
    fetch_and_cache(GOLD_URL, "gold")

data = st.session_state.get("data_cache", {}).get("gold")
if data:
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[(df['price'] > 1000) & (df['price'] < 20000)].sort_values('timestamp')

    total_time = df['timestamp'].max() - df['timestamp'].min()
    freq = total_time / 30
    
    ohlc = df.resample(freq, on='timestamp').agg({
        'price': ['first', 'max', 'min', 'last']
    }).dropna()
    
    ohlc.columns = ['open', 'high', 'low', 'close']
    ohlc = ohlc.reset_index()

    color_condition = alt.condition("datum.open <= datum.close", 
                                    alt.value("#06982d"), alt.value("#ae1325"))

    base = alt.Chart(ohlc).encode(
        x=alt.X('timestamp:T', title="Time"),
        color=color_condition
    )

    whiskers = base.mark_rule().encode(
        y=alt.Y('low:Q', title="Silver Price", scale=alt.Scale(zero=False)),
        y2='high:Q'
    )

    body = base.mark_bar().encode(
        y='open:Q',
        y2='close:Q'
    )

    st.altair_chart((whiskers + body).properties(height=500).interactive(), use_container_width=True)