import streamlit as st
import pandas as pd
from utils import fetch_and_cache, format_item_id
from datetime import datetime, timezone

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
        if minutes < 60: return f"{minutes}m"
        return f"{minutes // 60}h"
    except:
        return "Err"

st.set_page_config(layout="wide")
st.title("🧥 Leather Selling Strategy: Optimized Export")

LEATHER_URL = "https://west.albion-online-data.com/api/v2/stats/prices/T4_LEATHER,T4_LEATHER_LEVEL1@1,T4_LEATHER_LEVEL2@2,T5_LEATHER,T5_LEATHER_LEVEL1@1,T5_LEATHER_LEVEL2@2,T6_LEATHER,T6_LEATHER_LEVEL1@1,T6_LEATHER_LEVEL2@2?locations=Martlock,Thetford,Bridgewatch&qualities=1"

if st.button('Refresh Leather Market'):
    fetch_and_cache(LEATHER_URL, "leather")

data = st.session_state.get("data_cache", {}).get("leather")

if data:
    df = pd.DataFrame(data)
    SELL_HURDLE = 1.03 

    pv = df.pivot(index='item_id', columns='city', values=['sell_price_min', 'sell_price_min_date'])
    city_map = {'Martlock': 'ML', 'Thetford': 'TF', 'Bridgewatch': 'BW'}
    pv.columns = [f"{city_map.get(c[1], c[1])}_{'Price' if c[0]=='sell_price_min' else 'Date'}" for c in pv.columns]
    pv = pv.reset_index()

    # Ensure columns exist
    for c in ['ML_Price', 'TF_Price', 'BW_Price']:
        if c not in pv.columns: pv[c] = 0
    for d in ['ML_Date', 'TF_Date', 'BW_Date']:
        if d not in pv.columns: pv[d] = "0001-01-01T00:00:00"

    st.subheader("📋 Unified Selling Guide")

    # Tighter List Layout
    for _, row in pv.iterrows():
        name = format_item_id(row['item_id'], "Leather")
        icon = get_item_icon(row['item_id'])
        ml_p, tf_p, bw_p = row['ML_Price'], row['TF_Price'], row['BW_Price']
        
        # Logic to find best destination
        if tf_p >= bw_p:
            best_ex_p, best_ex_city, best_ex_key, ex_color = tf_p, "THETFORD", "TF", "#A020F0" # Purple
        else:
            best_ex_p, best_ex_city, best_ex_key, ex_color = bw_p, "BRIDGEWATCH", "BW", "#FFA500" # Orange

        if best_ex_p > (ml_p * SELL_HURDLE) and best_ex_p > 0:
            dest_city, dest_p, dest_key, dest_color = best_ex_city, best_ex_p, best_ex_key, ex_color
        else:
            dest_city, dest_p, dest_key, dest_color = "MARTLOCK", ml_p, "ML", "#ADD8E6" # Lightblue

        time_ago = get_time_diff(row[f'{dest_key}_Date'])

        # Removed table padding and reduced widths to bring elements closer
        st.markdown(f"""
            <table style="width:700px; border:none; border-collapse:collapse; background-color:transparent; line-height:1;">
                <tr style="border:none;">
                    <td style="width:35px; border:none; padding:2px;"><img src="{icon}" width="28"></td>
                    <td style="width:120px; border:none; padding:2px; font-weight:bold; font-size:0.95em;">{name}</td>
                    <td style="width:180px; border:none; padding:2px;">
                        <span style="color: {dest_color}; font-weight: bold; font-size:0.9em;">[SELL {dest_city}]</span>
                    </td>
                    <td style="width:110px; border:none; padding:2px; color:#bbb; font-size:0.9em;">Price: <b>{int(dest_p):,}</b></td>
                    <td style="width:80px; border:none; padding:2px; color:#888; font-style:italic; font-size:0.8em;">({time_ago} ago)</td>
                </tr>
            </table>
        """, unsafe_allow_html=True)

    # --- RAW MARKET DATA (COMPACT) ---
    st.write("---")
    st.subheader("📊 Raw Market Data")
    
    raw_table = pv.copy()
    raw_table['Item Name'] = raw_table['item_id'].apply(lambda x: format_item_id(x, "Leather"))
    
    # Matching the compact styling of your Hide screenshot
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
    st.info("Click Refresh to load data.")