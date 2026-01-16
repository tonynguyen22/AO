import streamlit as st
import pandas as pd
from utils import fetch_and_cache, format_item_id
from datetime import datetime, timezone

# CUSTOM CSS TO REMOVE STREAMLIT PADDING AND TIGHTEN UI
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        div.stButton > button {margin-bottom: -1rem;}
        #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)

def get_item_icon(item_id):
    return f"https://render.albiononline.com/v1/item/{item_id}.png?size=32"

def get_time_diff(date_str):
    if not date_str or date_str == "0001-01-01T00:00:00":
        return "N/A"
    try:
        data_time = pd.to_datetime(date_str).tz_localize('UTC')
        now = datetime.now(timezone.utc)
        diff = now - data_time
        minutes = int(diff.total_seconds() // 60)
        if minutes < 0: return "0m"
        return f"{minutes}m" if minutes < 60 else f"{minutes // 60}h"
    except:
        return "Err"

st.set_page_config(layout="wide")
st.title("🧥 High-Tier Leather Selling Strategy")

# Updated URL with your specific high-tier requirements
# T4.3, T5.2, T5.3, T6.0, T6.1, T6.2, T7.0, T7.1, T8.0
LEATHER_URL = "https://west.albion-online-data.com/api/v2/stats/prices/T4_LEATHER_LEVEL3@3,T5_LEATHER_LEVEL2@2,T5_LEATHER_LEVEL3@3,T6_LEATHER,T6_LEATHER_LEVEL1@1,T6_LEATHER_LEVEL2@2,T7_LEATHER,T7_LEATHER_LEVEL1@1,T8_LEATHER?locations=Martlock,Thetford,Bridgewatch&qualities=1"

if st.button('Refresh Leather Market'):
    fetch_and_cache(LEATHER_URL, "leather_high")

data = st.session_state.get("data_cache", {}).get("leather_high")

if data:
    df = pd.DataFrame(data)
    SELL_HURDLE = 1.03 

    pv = df.pivot(index='item_id', columns='city', values=['sell_price_min', 'sell_price_min_date'])
    city_map = {'Martlock': 'ML', 'Thetford': 'TF', 'Bridgewatch': 'BW'}
    pv.columns = [f"{city_map.get(c[1], c[1])}_{'Price' if c[0]=='sell_price_min' else 'Date'}" for c in pv.columns]
    pv = pv.reset_index()

    for c in ['ML_Price', 'TF_Price', 'BW_Price']:
        if c not in pv.columns: pv[c] = 0
    for d in ['ML_Date', 'TF_Date', 'BW_Date']:
        if d not in pv.columns: pv[d] = "0001-01-01T00:00:00"

    st.subheader("📋 Unified Selling Guide")

    # Tightened List Layout using Flexbox for maximum density
    for _, row in pv.iterrows():
        name = format_item_id(row['item_id'], "Leather")
        icon = get_item_icon(row['item_id'])
        ml_p, tf_p, bw_p = row['ML_Price'], row['TF_Price'], row['BW_Price']
        
        # Determine best export destination
        if tf_p >= bw_p:
            best_ex_p, best_ex_city, best_ex_key, ex_color = tf_p, "THETFORD", "TF", "#A020F0" # Purple
        else:
            best_ex_p, best_ex_city, best_ex_key, ex_color = bw_p, "BRIDGEWATCH", "BW", "#FFA500" # Orange

        # Final Decision: Export vs Local
        if best_ex_p > (ml_p * SELL_HURDLE) and best_ex_p > 0:
            dest_city, dest_p, dest_key, dest_color = best_ex_city, best_ex_p, best_ex_key, ex_color
        else:
            dest_city, dest_p, dest_key, dest_color = "MARTLOCK", ml_p, "ML", "#ADD8E6" # Lightblue

        time_ago = get_time_diff(row[f'{dest_key}_Date'])

        st.markdown(f"""
            <div style="display: flex; align-items: center; width: 700px; line-height: 1.1; margin-bottom: 1px; border-bottom: 1px solid #333;">
                <div style="width: 35px;"><img src="{icon}" width="24"></div>
                <div style="width: 120px; font-weight: bold; font-size: 0.85em;">{name}</div>
                <div style="width: 200px; color: {dest_color}; font-weight: bold; font-size: 0.8em;">[SELL {dest_city}]</div>
                <div style="width: 110px; color: #bbb; font-size: 0.85em;">Price: <b>{int(dest_p):,}</b></div>
                <div style="width: 80px; color: #666; font-style: italic; font-size: 0.75em;">({time_ago} ago)</div>
            </div>
        """, unsafe_allow_html=True)

    # --- RAW MARKET DATA (COMPACT) ---
    st.write("---")
    st.subheader("📊 Raw Market Data")
    
    raw_table = pv.copy()
    raw_table['Item Name'] = raw_table['item_id'].apply(lambda x: format_item_id(x, "Leather"))
    
    st.dataframe(
        raw_table[['Item Name', 'BW_Price', 'TF_Price', 'ML_Price']], 
        column_config={
            "Item Name": st.column_config.TextColumn("Item Name", width="medium"),
            "BW_Price": st.column_config.NumberColumn("BW Insta", format="%d", width="small"),
            "TF_Price": st.column_config.NumberColumn("TF Insta", format="%d", width="small"),
            "ML_Price": st.column_config.NumberColumn("ML Insta", format="%d", width="small")
        },
        use_container_width=False,
        hide_index=True
    )
else:
    st.info("Click Refresh to load High-Tier leather data.")