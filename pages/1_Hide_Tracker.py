import streamlit as st
import pandas as pd
from utils import fetch_and_cache, format_item_id
from datetime import datetime, timezone

def get_item_icon(item_id):
    # Standard Albion Render URL
    return f"https://render.albiononline.com/v1/item/{item_id}.png?size=32"

def get_time_diff(date_str):
    if not date_str or date_str == "0001-01-01T00:00:00":
        return "N/A"
    try:
        # Parse the API date (UTC)
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
st.title("🏹 Hide Procurement & Transport Strategy")

HIDE_URL = "https://west.albion-online-data.com/api/v2/stats/prices/T4_HIDE,T4_HIDE_LEVEL1@1,T4_HIDE_LEVEL2@2,T5_HIDE,T5_HIDE_LEVEL1@1,T5_HIDE_LEVEL2@2,T6_HIDE,T6_HIDE_LEVEL1@1,T6_HIDE_LEVEL2@2?locations=Bridgewatch,Martlock&qualities=1"

if st.button('Refresh Market Data'):
    fetch_and_cache(HIDE_URL, "hide")

data = st.session_state.get("data_cache", {}).get("hide")

if data:
    df = pd.DataFrame(data)
    
    # Financial constants
    FEE = 1.025 # 2.5% setup fee
    HURDLE = 1.03 # 3% Transport/Risk premium

    # Data Prep
    pv = df.pivot(index='item_id', columns='city', values=['sell_price_min', 'buy_price_max', 'sell_price_min_date'])
    pv.columns = [f"{'BW' if c[1]=='Bridgewatch' else 'ML'}_{'Insta' if c[0]=='sell_price_min' else ('Order' if c[0]=='buy_price_max' else 'Date')}" for c in pv.columns]
    pv = pv.reset_index()
    
    col_bw, col_ml = st.columns(2)

    def render_aligned_rows(row, city_prefix):
        name = format_item_id(row['item_id'], "Hide")
        icon = get_item_icon(row['item_id'])
        insta_p = int(row[f'{city_prefix}_Insta'])
        buy_limit = int(row[f'{city_prefix}_Order'] * FEE)
        time_ago = get_time_diff(row[f'{city_prefix}_Date'])
        
        # Action Logic: Orange for Order, Green for Instant
        if buy_limit < insta_p and row[f'{city_prefix}_Order'] > 0:
            action = '<span style="color: #FFA500; font-weight: bold;">[BUY ORDER]</span>'
            limit_label = "Max Buy Limit"
        else:
            action = '<span style="color: #00FF00; font-weight: bold;">[BUY INSTANT]</span>'
            limit_label = "Limit"

        # Using an HTML table for fixed-width vertical alignment
        st.markdown(f"""
            <table style="width:100%; border:none; border-collapse:collapse; background-color:transparent;">
                <tr style="border:none;">
                    <td style="width:40px; border:none;"><img src="{icon}" width="28"></td>
                    <td style="width:100px; border:none; font-weight:bold;">{name}</td>
                    <td style="width:130px; border:none;">{action}</td>
                    <td style="width:100px; border:none; color:#bbb;">Price: <b>{insta_p}</b></td>
                    <td style="width:160px; border:none; color:#bbb;">{limit_label}: <b>{buy_limit}</b></td>
                    <td style="width:80px; border:none; color:#888; font-style:italic; font-size:0.9em;">({time_ago})</td>
                </tr>
            </table>
        """, unsafe_allow_html=True)

    with col_bw:
        st.subheader("🏜️ Bridgewatch Supply")
        for _, row in pv.iterrows():
            best_bw = min(row['BW_Insta'], row['BW_Order'] * FEE)
            best_ml = min(row['ML_Insta'], row['ML_Order'] * FEE)
            if best_bw * HURDLE < best_ml:
                render_aligned_rows(row, 'BW')

    with col_ml:
        st.subheader("⚓ Martlock Local")
        for _, row in pv.iterrows():
            best_bw = min(row['BW_Insta'], row['BW_Order'] * FEE)
            best_ml = min(row['ML_Insta'], row['ML_Order'] * FEE)
            if not (best_bw * HURDLE < best_ml):
                render_aligned_rows(row, 'ML')

    # --- SIMPLIFIED RAW DATA SECTION ---
    st.write("---")
    st.subheader("📊 Raw Market Data (Instant Buy Prices Only)")
    
    raw_table = pv.copy()
    raw_table['Item'] = raw_table['item_id'].apply(lambda x: format_item_id(x, "Hide"))
    
    # Display narrowed table: Removed "Silver" unit and set fixed small widths
    st.dataframe(
        raw_table[['Item', 'BW_Insta', 'ML_Insta']], 
        column_config={
            "Item": st.column_config.TextColumn("Item Name", width="medium"),
            "BW_Insta": st.column_config.NumberColumn("BW Insta", format="%d", width="small"),
            "ML_Insta": st.column_config.NumberColumn("ML Insta", format="%d", width="small")
        },
        use_container_width=False, # Makes the table compact rather than stretching to screen
        hide_index=True
    )