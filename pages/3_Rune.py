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
        return f"{minutes}m" if minutes < 60 else f"{minutes // 60}h"
    except:
        return "Err"

st.set_page_config(layout="wide")
st.title("💎 Artifact Procurement: BW vs Caerleon")

# Define item groups for strict ordering
TIERS = ["T5", "T6", "T7"]
TYPES = ["RUNE", "SOUL", "RELIC"]

# Flatten list for the API call
ITEMS_LIST = [f"{t}_{typ}" for t in TIERS for typ in TYPES]
ITEMS_QUERY = ",".join(ITEMS_LIST)
RUNE_URL = f"https://west.albion-online-data.com/api/v2/stats/prices/{ITEMS_QUERY}?locations=Bridgewatch,Caerleon&qualities=1"

if st.button('Refresh Artifact Market'):
    fetch_and_cache(RUNE_URL, "artifacts")

data = st.session_state.get("data_cache", {}).get("artifacts")

if data:
    df = pd.DataFrame(data)
    HURDLE = 1.08  # 8% Risk/Transport Premium

    # Pivot and Clean
    pv = df.pivot(index='item_id', columns='city', values=['sell_price_min', 'sell_price_min_date'])
    city_map = {'Bridgewatch': 'BW', 'Caerleon': 'CL'}
    pv.columns = [f"{city_map.get(c[1], c[1])}_{'Price' if c[0]=='sell_price_min' else 'Date'}" for c in pv.columns]
    pv = pv.reset_index()

    # Safety: Ensure columns exist
    for c in ['BW_Price', 'CL_Price']:
        if c not in pv.columns: pv[c] = 0
    for d in ['BW_Date', 'CL_Date']:
        if d not in pv.columns: pv[d] = "0001-01-01T00:00:00"

    st.subheader("📋 Unified Procurement Guide")

    # Loop through Tiers then Types for strict ordering
    for tier in TIERS:
        st.markdown(f"### {tier} Artifacts")
        for typ in TYPES:
            item_id = f"{tier}_{typ}"
            row = pv[pv['item_id'] == item_id]
            
            if not row.empty:
                row = row.iloc[0]
                name = item_id.replace("T", "Tier ").replace("_", " ")
                icon = get_item_icon(item_id)
                
                bw_p = row['BW_Price']
                cl_p = row['CL_Price']
                
                # Logic: Buy BW if it's cheaper than CL even with 8% premium
                if (bw_p * HURDLE < cl_p) and bw_p > 0:
                    dest_city, dest_p, dest_color, dest_key = "BRIDGEWATCH", bw_p, "#FFA500", "BW"
                    action_text = "BUY AT BW (TRANSPORT)"
                else:
                    dest_city, dest_p, dest_color, dest_key = "CAERLEON", cl_p, "#FF4B4B", "CL"
                    action_text = "BUY LOCAL (CAERLEON)"

                time_ago = get_time_diff(row[f'{dest_key}_Date'])

                st.markdown(f"""
                    <table style="width:750px; border:none; border-collapse:collapse; background-color:transparent; line-height:1; margin-bottom:2px;">
                        <tr style="border:none;">
                            <td style="width:35px; border:none; padding:2px;"><img src="{icon}" width="28"></td>
                            <td style="width:150px; border:none; padding:2px; font-weight:bold; font-size:0.95em;">{name}</td>
                            <td style="width:220px; border:none; padding:2px;">
                                <span style="color: {dest_color}; font-weight: bold; font-size:0.9em;">[{action_text}]</span>
                            </td>
                            <td style="width:120px; border:none; padding:2px; color:#bbb; font-size:0.9em;">Price: <b>{int(dest_p):,}</b></td>
                            <td style="width:80px; border:none; padding:2px; color:#888; font-style:italic; font-size:0.8em;">({time_ago} ago)</td>
                        </tr>
                    </table>
                """, unsafe_allow_html=True)
        
        # Add a visual divider between Tier groups
        st.markdown("---")

    # --- RAW DATA TABLE ---
    st.subheader("📊 Raw Market Data (Instant Buy Only)")
    
    # Re-order the dataframe to match the requested Rune -> Soul -> Relic flow
    raw_table = pv.copy()
    raw_table['temp_tier'] = raw_table['item_id'].apply(lambda x: x.split('_')[0])
    raw_table['temp_type'] = raw_table['item_id'].apply(lambda x: x.split('_')[1])
    
    # Custom sorting logic
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
    st.info("Click Refresh to pull market data.")