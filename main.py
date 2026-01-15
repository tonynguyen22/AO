import streamlit as st

st.set_page_config(page_title="Albion Smart Trader", layout="wide")

st.title("🎮 Albion Online Smart Trader")
st.markdown("""
Welcome to your personal trading dashboard. Use the sidebar to navigate between:
* **Hide Tracker:** Optimize your buy orders.
* **Leather Tracker:** Find the best markets to sell.
* **Gold Chart:** Technical analysis for Silver/Gold exchange.
""")

st.sidebar.info("Select a tool above to begin.")