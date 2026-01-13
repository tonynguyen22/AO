import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import altair as alt

# Set page config
st.set_page_config(page_title="Albion Smart Trader", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'last_fetch' not in st.session_state:
    st.session_state.last_fetch = {"hide": 0, "leather": 0, "gold": 0}
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = {"hide": None, "leather": None, "gold": None}
if 'history_cache' not in st.session_state:
    st.session_state.history_cache = {}

# --- LOGIC FUNCTIONS ---
def get_smart_buy(row, threshold=0.03):
    bw, ml = row["Bridgewatch"], row["Martlock"]
    if bw < ml * (1 - threshold): return "Bridgewatch"
    return "Martlock"

def get_smart_sell(row, threshold=0.03):
    ml = row["Martlock"]
    bw, th = row["Bridgewatch"], row["Thetford"]
    best_alt_price = max(bw, th)
    if best_alt_price > ml * (1 + threshold):
        return "Bridgewatch" if bw > th else "Thetford"
    return "Martlock"

def highlight_recommendation(row):
    return ['background-color: darkgrey' if col == row['Recommended City'] else '' for col in row.index]

# --- HISTORY AVERAGES WITH WHOLE NUMBERS ---
def get_avg_indicators(item_id, location, current_price):
    cache_key = f"{item_id}_{location}"
    now = time.time()
    
    if cache_key not in st.session_state.history_cache or (now - st.session_state.history_cache[cache_key]['time'] > 3600):
        url = f"https://west.albion-online-data.com/api/v2/stats/history/{item_id}?locations={location}&time-scale=24"
        try:
            resp = requests.get(url).json()
            if resp and len(resp[0]['data']) > 0:
                data = resp[0]['data']
                daily_avg = data[-1]['avg_price']
                seven_day_avg = sum(d['avg_price'] for d in data[-7:]) / min(len(data), 7)
                st.session_state.history_cache[cache_key] = {
                    'daily': int(round(daily_avg)), 
                    '7d': int(round(seven_day_avg)), 
                    'time': now
                }
            else: return ""
        except: return ""

    hist = st.session_state.history_cache[cache_key]
    d_icon = "🔺" if current_price > hist['daily'] else "🔻"
    w_icon = "🔺" if current_price > hist['7d'] else "🔻"
    
    return f" [D:{d_icon}{hist['daily']} 7d:{w_icon}{hist['7d']}]"

# --- HELPER FUNCTIONS ---
def format_item_id(item_id, category_name):
    parts = item_id.split('_')
    tier = parts[0].replace('T', '')
    suffix = next((s for s in [".1", ".2", ".3", ".4"] if f"LEVEL{s[-1]}" in item_id), ".0")
    return f"{tier}{suffix} {category_name}"

def fetch_and_cache(url, category):
    now = time.time()
    if now - st.session_state.last_fetch[category] > 300:
        try:
            response = requests.get(url)
            st.session_state.data_cache[category] = response.json()
            st.session_state.last_fetch[category] = now
            st.toast(f"{category.capitalize()} data updated!")
        except Exception as e:
            st.error(f"Error: {e}")

# --- SIDEBAR ---
st.sidebar.title("🎮 Navigation")
page = st.sidebar.radio("Category:", ["Hide Tracker (Buy)", "Leather Tracker (Sell)", "Gold Chart"])

# --- HIDE TRACKER ---
if page == "Hide Tracker (Buy)":
    st.title("🏹 Hide Smart Buying (5% Hurdle)")
    HIDE_URL = "https://west.albion-online-data.com/api/v2/stats/prices/T4_HIDE,T4_HIDE_LEVEL1@1,T4_HIDE_LEVEL2@2,T5_HIDE,T5_HIDE_LEVEL1@1,T5_HIDE_LEVEL2@2,T6_HIDE,T6_HIDE_LEVEL1@1,T6_HIDE_LEVEL2@2?locations=Bridgewatch,Martlock&qualities=1"
    
    if st.button('Update Prices'): fetch_and_cache(HIDE_URL, "hide")
    
    data = st.session_state.data_cache["hide"]
    if data:
        df = pd.DataFrame(data)
        df['Display Name'] = df['item_id'].apply(lambda x: format_item_id(x, "Hide"))
        pivot = df.pivot(index='Display Name', columns='city', values='sell_price_min')
        id_map = df.set_index('Display Name')['item_id'].to_dict()
        pivot['Recommended City'] = pivot.apply(get_smart_buy, axis=1)
        
        st.dataframe(pivot.style.apply(highlight_recommendation, axis=1))

        st.subheader("🛒 Best Cities to Buy")
        cols = st.columns(2)
        cities = ["Martlock", "Bridgewatch"]
        for i, city in enumerate(cities):
            with cols[i]:
                st.info(f"**Buy in {city}**")
                items = pivot[pivot['Recommended City'] == city]
                for name, row in items.iterrows():
                    indicator = get_avg_indicators(id_map[name], city, row[city])
                    st.write(f"- {name}: **{int(round(row[city]))}**{indicator}")

# --- LEATHER TRACKER ---
elif page == "Leather Tracker (Sell)":
    st.title("🛡️ Leather Smart Selling (5% Hurdle)")
    LEATHER_URL = "https://west.albion-online-data.com/api/v2/stats/prices/T4_LEATHER,T4_LEATHER_LEVEL1@1,T4_LEATHER_LEVEL2@2,T5_LEATHER,T5_LEATHER_LEVEL1@1,T5_LEATHER_LEVEL2@2,T6_LEATHER,T6_LEATHER_LEVEL1@1,T6_LEATHER_LEVEL2@2?locations=Bridgewatch,Martlock,Thetford&qualities=1"
    
    if st.button('Update Prices'): fetch_and_cache(LEATHER_URL, "leather")

    data = st.session_state.data_cache["leather"]
    if data:
        df = pd.DataFrame(data)
        df['Display Name'] = df['item_id'].apply(lambda x: format_item_id(x, "Leather"))
        pivot = df.pivot(index='Display Name', columns='city', values='sell_price_min')
        id_map = df.set_index('Display Name')['item_id'].to_dict()
        pivot['Recommended City'] = pivot.apply(get_smart_sell, axis=1)
        
        cities = ["Bridgewatch", "Martlock", "Thetford"]
        st.dataframe(pivot.style.apply(highlight_recommendation, axis=1))

        st.subheader("💰 Best Cities to Sell")
        cols = st.columns(3)
        for i, city in enumerate(cities):
            with cols[i]:
                st.success(f"**Sell in {city}**")
                items = pivot[pivot['Recommended City'] == city]
                for name, row in items.iterrows():
                    indicator = get_avg_indicators(id_map[name], city, row[city])
                    st.write(f"- {name}: **{int(round(row[city]))}**{indicator}")

# --- GOLD PRICE PAGE ---
elif page == "Gold Chart":
    st.title("💰 Gold OHLC Candlestick (30 Intervals)")
    URL = "https://west.albion-online-data.com/api/v2/stats/gold?count=720"
    
    if st.session_state.data_cache["gold"] is None:
        fetch_and_cache(URL, "gold")

    data = st.session_state.data_cache["gold"]
    if data:
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 1. Clean outliers (as we discussed before)
        df = df[(df['price'] > 1000) & (df['price'] < 20000)].sort_values('timestamp')

        # 2. Resample data into 30 equal buckets
        # We calculate the time delta and divide by 30 to get the frequency
        total_time = df['timestamp'].max() - df['timestamp'].min()
        freq = total_time / 30
        
        ohlc = df.resample(freq, on='timestamp').agg({
            'price': ['first', 'max', 'min', 'last']
        }).dropna()
        
        ohlc.columns = ['open', 'high', 'low', 'close']
        ohlc = ohlc.reset_index()

        # 3. Create the Altair Candlestick
        # Color: Green if close >= open, Red if close < open
        color_condition = alt.condition("datum.open <= datum.close", 
                                        alt.value("#06982d"), alt.value("#ae1325"))

        base = alt.Chart(ohlc).encode(
            x=alt.X('timestamp:T', title="Time"),
            color=color_condition
        )

        # The "Whiskers" (High/Low)
        whiskers = base.mark_rule().encode(
            y=alt.Y('low:Q', title="Silver Price", scale=alt.Scale(zero=False)),
            y2='high:Q'
        )

        # The "Body" (Open/Close)
        body = base.mark_bar().encode(
            y='open:Q',
            y2='close:Q'
        )

        chart = (whiskers + body).properties(height=500).interactive()
        st.altair_chart(chart, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("Cache protection: 5 min cooldown active.")