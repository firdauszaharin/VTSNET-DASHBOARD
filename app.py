import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz
import requests
import io

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="GreenFinder VTMS Admin & Inventory",
    layout="wide",
    page_icon="📊"
)

# --- CSS MODEN (GLASSMORPHISM) ---
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #1a1a2e, #16213e, #0f3460);
        color: white;
        font-family: 'Inter', sans-serif;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    h1, h2, h3 { color: white !important; }
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. DATA LOADING
@st.cache_data(ttl=600)
def load_data(url):
    try:
        response = requests.get(url).content
        return pd.read_csv(io.StringIO(response.decode('utf-8')))
    except:
        return pd.DataFrame()

# URLs
MAINTENANCE_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv"
EQUIPMENT_URL = "https://docs.google.com/spreadsheets/d/1HQUV7NXuhAKtKW-weSwAmhIMOde8CZM8XiTiaF1P7K4/export?format=csv&gid=0"

df_maint = load_data(MAINTENANCE_URL)
df_equip = load_data(EQUIPMENT_URL)

# 3. HEADER
col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991108.png", width=80)
with col2:
    st.title("GreenFinder VTMS Admin & Inventory")
    st.caption("Electronic Data Management System - Going Forward")

# 4. TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Inventory"])

with tab1:
    st.subheader("Maintenance Reports")
    if not df_maint.empty:
        # Metrik ringkas
        cols = st.columns(4)
        cols[0].metric("Total Reports", len(df_maint))
        cols[1].metric("Approved", len(df_maint[df_maint.get('STATUS', '') == 'APPROVED']))
        cols[2].metric("Rejected", len(df_maint[df_maint.get('STATUS', '') == 'REJECTED']))
        cols[3].metric("Pending", len(df_maint[~df_maint.get('STATUS', '').isin(['APPROVED', 'REJECTED'])]))
        
        st.dataframe(df_maint, use_container_width=True)
    else:
        st.warning("Data Maintenance tidak dijumpai.")

with tab2:
    st.subheader("AIS VTS & AIS VDES Monitoring")
    if not df_equip.empty:
        # Filter status
        status_filter = st.multiselect("Filter Status:", options=df_equip.iloc[:, -1].unique())
        df_show = df_equip
        if status_filter:
            df_show = df_equip[df_equip.iloc[:, -1].isin(status_filter)]
            
        st.dataframe(df_show, use_container_width=True)
        
        # Ringkasan Carta
        if not df_show.empty:
            fig = px.pie(df_show, names=df_show.columns[-1], title="Status Distribution")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Data Equipment tidak dijumpai.")

# 5. FOOTER
st.divider()
st.markdown("© 2025 GreenFinder VTMS Admin & Inventory Dashboard. All rights reserved.")
