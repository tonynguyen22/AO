import streamlit as st
import pandas as pd
from utils import fetch_and_cache, format_item_id, get_avg_indicators

def get_smart_sell(row, threshold=0.03):
    ml = row["Martlock"]
    bw, th = row["Bridgewatch"], row["Thetford"]
    best_alt_price = max(bw, th)
    if best_alt_price > ml * (1 + threshold):
        return "Bridgewatch" if bw > th else "Thetford"
    return "Martlock"

def highlight_recommendation(row):
    return ['background-color: #1e3d24' if col == row['Recommended City'] else '' for col in row.index]

st.title("🛡️ Leather Smart Selling (5% Hurdle)")

LEATHER_URL = "https://west.albion-online-data.com/api/v2/stats/prices/T4_LEATHER,T4_LEATHER_LEVEL1@1,T4_LEATHER_LEVEL2@2,T5_LEATHER,T5_LEATHER_LEVEL1@1,T5_LEATHER_LEVEL2@2,T6_LEATHER,T6_LEATHER_LEVEL1@1,T6_LEATHER_LEVEL2@2?locations=Bridgewatch,Martlock,Thetford&qualities=1"

if st.button('Update Prices'):
    fetch_and_cache(LEATHER_URL, "leather")

data = st.session_state.get("data_cache", {}).get("leather")
if data:
    df = pd.DataFrame(data)
    df['Display Name'] = df['item_id'].apply(lambda x: format_item_id(x, "Leather"))
    pivot = df.pivot(index='Display Name', columns='city', values='sell_price_min')
    id_map = df.set_index('Display Name')['item_id'].to_dict()
    pivot['Recommended City'] = pivot.apply(get_smart_sell, axis=1)
    
    st.dataframe(pivot.style.apply(highlight_recommendation, axis=1), use_container_width=True)

    st.subheader("💰 Best Cities to Sell")
    cities = ["Bridgewatch", "Martlock", "Thetford"]
    cols = st.columns(3)
    for i, city in enumerate(cities):
        with cols[i]:
            st.success(f"**Sell in {city}**")
            items = pivot[pivot['Recommended City'] == city]
            for name, row in items.iterrows():
                indicator = get_avg_indicators(id_map[name], city, row[city])
                st.write(f"- {name}: **{int(round(row[city]))}**{indicator}")