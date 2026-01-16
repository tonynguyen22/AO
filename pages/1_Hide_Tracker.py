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
        data_time = datetime.fromisoformat(date_str.replace("Z", "")).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - data_time
        minutes = int(diff.total_seconds() // 60)
        if minutes < 60:
            return f"{minutes}m ago"
        else:
            return f"{minutes // 60}h {minutes % 60}m ago"
    except:
        return "Error"

st.set_page_config(layout="wide")
st.title("🏹 High-Tier Hide Procurement & Transport")

# Updated URL with your specific high-tier requirements
# Removed: T4.0, T4.1, T4.2, T5.0, T5.1
# Added: T4.3, T5.2, T5.3, T6.0, T6.1, T6.2, T7.0, T7.1, T8.0
HIDE_URL = "https://west.albion-online-data.com/api/v2/stats/prices/T4_HIDE_LEVEL3@3,T5_HIDE_LEVEL2@2,T5_HIDE_LEVEL3@3,T6_HIDE,T6_HIDE_LEVEL1@1,T6_HIDE_LEVEL2@2,T7_HIDE,T7_HIDE_LEVEL1@1,T8_HIDE?locations=Bridgewatch,Martlock&qualities=1"

if st.button('Refresh Market Data'):
    fetch_and_cache(HIDE_URL, "hide_high")

data = st.session_state.get("data_cache", {}).get("hide_high")

if data:
    df = pd.DataFrame(data)
    FEE = 1.025 
    HURDLE = 1.03 

    pv = df.pivot(index='item_id', columns='city', values=['sell_price_min', 'buy_price_max', 'sell_price_min_date'])
    pv.columns = [f"{'BW' if c[1]=='Bridgewatch' else 'ML'}_{'Insta' if c[0]=='sell_price_min' else ('Order' if c[0]=='buy_price_max' else 'Date')}" for c in pv.columns]
    pv = pv.reset_index()
    
    def render_aligned_rows(row, city_prefix):
        name = format_item_id(row['item_id'], "Hide")
        icon = get_item_icon(row['item_id'])
        insta_p = int(row[f'{city_prefix}_Insta'])
        buy_limit = int(row[f'{city_prefix}_Order'] * FEE)
        time_ago = get_time_diff(row[f'{city_prefix}_Date'])
        
        if buy_limit < insta_p and row[f'{city_prefix}_Order'] > 0:
            action_tag = '[BUY ORDER]'
            action_color = "#FFA500" # Orange
            limit_label = "Max Buy Limit"
        else:
            action_tag = '[BUY INSTANT]'
            action_color = "#00FF00" # Green
            limit_label = "Limit"

        city_label_color = "#FFA500" if city_prefix == "BW" else "#ADD8E6"
        city_name = "BRIDGEWATCH" if city_prefix == "BW" else "MARTLOCK"

        st.markdown(f"""
            <table style="width:750px; border:none; border-collapse:collapse; background-color:transparent; line-height:1; margin-bottom:2px;">
                <tr style="border:none;">
                    <td style="width:35px; border:none; padding:2px;"><img src="{icon}" width="28"></td>
                    <td style="width:110px; border:none; padding:2px; font-weight:bold; font-size:0.9em;">{name}</td>
                    <td style="width:140px; border:none; padding:2px;">
                        <span style="color: {city_label_color}; font-weight: bold; font-size:0.85em;">{city_name}</span>
                    </td>
                    <td style="width:130px; border:none; padding:2px;">
                        <span style="color: {action_color}; font-weight: bold; font-size:0.85em;">{action_tag}</span>
                    </td>
                    <td style="width:100px; border:none; padding:2px; color:#bbb; font-size:0.85em;">Price: <b>{insta_p}</b></td>
                    <td style="width:150px; border:none; padding:2px; color:#bbb; font-size:0.85em;">{limit_label}: <b>{buy_limit}</b></td>
                    <td style="width:80px; border:none; padding:2px; color:#888; font-style:italic; font-size:0.75em;">({time_ago})</td>
                </tr>
            </table>
        """, unsafe_allow_html=True)

    # --- SECTIONS STACKED VERTICALLY ---
    
    st.subheader("🏜️ Bridgewatch Supply (Transport Target)")
    for _, row in pv.iterrows():
        # Compare INSTANT to INSTANT for the city decision
        bw_insta = row['BW_Insta']
        ml_insta = row['ML_Insta']
        
        # Decision: Is BW Instant (with hurdle) cheaper than ML Instant?
        if (bw_insta * HURDLE < ml_insta) and bw_insta > 0:
            render_aligned_rows(row, 'BW')

    st.write("") 

    st.subheader("⚓ Martlock Local (Stay Local)")
    for _, row in pv.iterrows():
        bw_insta = row['BW_Insta']
        ml_insta = row['ML_Insta']
        
        # Decision: If transport doesn't beat the hurdle, buy in Martlock
        if not (bw_insta * HURDLE < ml_insta):
            render_aligned_rows(row, 'ML')

    # --- COMPACT RAW DATA SECTION ---
    st.write("---")
    st.subheader("📊 Raw Market Data")
    
    raw_table = pv.copy()
    raw_table['Item'] = raw_table['item_id'].apply(lambda x: format_item_id(x, "Hide"))
    
    st.dataframe(
        raw_table[['Item', 'BW_Insta', 'ML_Insta']], 
        column_config={
            "Item": st.column_config.TextColumn("Item Name", width="medium"),
            "BW_Insta": st.column_config.NumberColumn("BW Insta", format="%d", width="small"),
            "ML_Insta": st.column_config.NumberColumn("ML Insta", format="%d", width="small")
        },
        use_container_width=False, 
        hide_index=True
    )

else:
    st.info("Click Refresh to load market data for T4.3 - T8.0.")