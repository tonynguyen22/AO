import streamlit as st
import requests
import time

def fetch_and_cache(url, category):
    now = time.time()
    if 'last_fetch' not in st.session_state:
        st.session_state.last_fetch = {"hide": 0, "leather": 0, "gold": 0}
    if 'data_cache' not in st.session_state:
        st.session_state.data_cache = {"hide": None, "leather": None, "gold": None}

    if now - st.session_state.last_fetch.get(category, 0) > 300:
        try:
            response = requests.get(url)
            st.session_state.data_cache[category] = response.json()
            st.session_state.last_fetch[category] = now
            st.toast(f"{category.capitalize()} data updated!")
        except Exception as e:
            st.error(f"Error: {e}")

def format_item_id(item_id, category_name):
    parts = item_id.split('_')
    tier = parts[0].replace('T', '')
    suffix = next((s for s in [".1", ".2", ".3", ".4"] if f"LEVEL{s[-1]}" in item_id), ".0")
    return f"{tier}{suffix} {category_name}"

def get_avg_indicators(item_id, location, current_price):
    if 'history_cache' not in st.session_state:
        st.session_state.history_cache = {}
    
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