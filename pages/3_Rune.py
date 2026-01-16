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
        hr {margin: 0.5rem 0px;} /* Tighten the horizontal divider */
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
st.title("💎 Artifact Procurement: BW vs Caerleon")

TIERS = ["T5", "T6", "T7"]
TYPES = ["RUNE", "SOUL", "RELIC"]

ITEMS_LIST = [f"{t}_{typ}" for t in TIERS for typ in TYPES]
ITEMS_QUERY = ",".join(ITEMS_LIST)
RUNE_URL = f"https://west.albion-online-data.com/api/v2/stats/prices/{ITEMS_QUERY}?locations=Bridgewatch,Caerleon&qualities=1"

if st.button('Refresh Artifact Market'):
    fetch_and_cache(RUNE_URL, "artifacts")

data = st.session_state.get("data_cache", {}).get("artifacts")

if data:
    df = pd.DataFrame(data)
    HURDLE = 1.08 

    pv = df.pivot(index='item_id', columns='city', values=['sell_price_min', 'sell_price_min_date'])
    city_map = {'Bridgewatch': 'BW', 'Caerleon': 'CL'}
    pv.columns = [f"{city_map.get(c[1], c[1])}_{'Price' if c[0]=='sell_price_min' else 'Date'}" for c in pv.columns]
    pv = pv.reset_index()

    for c in ['BW_Price', 'CL_Price']:
        if c not in pv.columns: pv[c] = 0
    for d in ['BW_Date', 'CL_Date']:
        if d not in pv.columns: pv[d] = "0001-01-01T00:00:00"

    st.subheader("📋 Unified Procurement Guide")

    # Loop through Tiers then Types for strict ordering with dividers
    for tier in TIERS:
        # Mini-header for the tier group
        st.markdown(f"**{tier} Group**")
        
        for typ in TYPES:
            item_id = f"{tier}_{typ}"
            row = pv[pv['item_id'] == item_id]
            
            if not row.empty:
                row = row.iloc[0]
                name = item_id.replace("T", "Tier ").replace("_", " ")
                icon = get_item_icon(item_id)
                bw_p, cl_p = row['BW_Price'], row['CL_Price']
                
                # Logic: BW + Hurdle vs CL
                if (bw_p * HURDLE < cl_p) and bw_p > 0:
                    dest_p, dest_color, dest_key, action_text = bw_p, "#FFA500", "BW", "BUY AT BW (TRANSPORT)"
                else:
                    dest_p, dest_color, dest_key, action_text = cl_p, "#FF4B4B", "CL", "BUY LOCAL (CAERLEON)"

                time_ago = get_time_diff(row[f'{dest_key}_Date'])

                st.markdown(f"""
                    <div style="display: flex; align-items: center; width: 700px; line-height: 1.1; margin-bottom: 1px; border-bottom: 1px solid #333;">
                        <div style="width: 35px;"><img src="{icon}" width="24"></div>
                        <div style="width: 120px; font-weight: bold; font-size: 0.85em;">{name}</div>
                        <div style="width: 200px; color: {dest_color}; font-weight: bold; font-size: 0.8em;">[{action_text}]</div>
                        <div style="width: 100px; color: #bbb; font-size: 0.85em;">Price: <b>{int(dest_p):,}</b></div>
                        <div style="width: 80px; color: #666; font-style: italic; font-size: 0.75em;">({time_ago} ago)</div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Keep the divider between tier groups
        st.markdown("---")
        
    st.subheader("📊 Raw Market Data")
    
    # Sorting raw table to match the UI order
    raw_table = pv.copy()
    raw_table['temp_tier'] = raw_table['item_id'].apply(lambda x: x.split('_')[0])
    raw_table['temp_type'] = raw_table['item_id'].apply(lambda x: x.split('_')[1])
    type_order = {"RUNE": 0, "SOUL": 1, "RELIC": 2}
    raw_table['type_sort'] = raw_table['temp_type'].map(type_order)
    raw_table = raw_table.sort_values(['temp_tier', 'type_sort'])
    raw_table['Item Name'] = raw_table['item_id'].apply(lambda x: x.replace("T", "Tier ").replace("_", " "))
    
    st.dataframe(
        raw_table[['Item Name', 'BW_Price', 'CL_Price']], 
        column_config={
            "Item Name": st.column_config.TextColumn("Item Name", width="medium"),
            "BW_Price": st.column_config.NumberColumn("BW Price", format="%d", width="small"),
            "CL_Price": st.column_config.NumberColumn("CL Price", format="%d", width="small")
        },
        use_container_width=False,
        hide_index=True
    )
else:
    st.info("Click Refresh to load artifact prices.")