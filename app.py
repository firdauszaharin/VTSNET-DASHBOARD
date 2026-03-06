import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="VTSNET Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- SET MALAYSIA TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# 2. MODERN CSS
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #f8faff, #eef2f7,#f8faff); font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.8) !important; backdrop-filter: blur(10px); }
    [data-testid="stMetric"] { background: white !important; padding: 20px !important; border-radius: 20px !important; box-shadow: 0 10px 25px rgba(0,0,0,0.03) !important; }
    header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1HQUV7NXuhAKtKW-weSwAmhIMOde8CZM8XiTiaF1P7K4/export?format=csv"
PDF_COL = "UPLOAD REPORT" 

# 4. DATA LOAD FUNCTION
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        time_col = next((c for c in data.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        if time_col and not data.empty:
            data[time_col] = pd.to_datetime(data[time_col], errors='coerce')
            data['Year'] = data[time_col].dt.year
        return data
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- NAVIGATION SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.title("📌 NAVIGATION")
    # INI ADALAH MENU PENUKAR (REPLACING TABS)
    menu_selection = st.sidebar.radio(
        "Pilih Paparan:",
        ["📝 Maintenance Reports", "⚙️ Equipment Status"],
        index=0
    )
    
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    
    st.markdown("### 🔍 GLOBAL FILTERS")
    search_report = st.text_input("🔎 Search Report/Site:", placeholder="e.g. RSS, MET")
    search_staff = st.text_input("👤 Performed by:")
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/...link...", use_container_width=True)

# --- HEADER BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #0984E3, #6c5ce7); padding: 30px; border-radius: 20px; color: white; margin-bottom: 25px;">
        <h1 style="color: white; margin: 0;">VTSNET ASSET MONITORING CENTER</h1>
        <p style="opacity: 0.9;">Mode: {menu_selection}</p>
    </div>
""", unsafe_allow_html=True)

# --- LOGIC PEMILIHAN MENU ---

# PAGE 1: MAINTENANCE REPORTS
if menu_selection == "📝 Maintenance Reports":
    if not df_raw.empty:
        df = df_raw.copy()
        if search_report: 
            df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        st.subheader("📋 Submitted Reports Record")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Data laporan tidak dijumpai.")

# PAGE 2: EQUIPMENT STATUS
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Condition")
        
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026"])]
        if month_cols:
            selected_month = st.selectbox("📅 Pilih Bulan Laporan:", month_cols, index=len(month_cols)-1)
            
            # Status Metrics
            status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
            c1, c2, c3 = st.columns(3)
            c1.metric("Condition: OK", len(df_equip[status_series == 'OK']))
            c2.metric("Condition: FAULTY", len(df_equip[status_series == 'FAULTY']))
            c3.metric("Condition: MISSING", len(df_equip[status_series == 'MISSING']))
            
            st.divider()
            # Search for assets
            if search_report: # Reuse search bar from sidebar for asset name/site
                df_equip = df_equip[df_equip.astype(str).apply(lambda x: x.str.contains(search_report, case=False)).any(axis=1)]
                
            st.dataframe(df_equip[["Site", "Type", "Serial No", selected_month]], use_container_width=True, hide_index=True)
    else:
        st.warning("Data peralatan tidak dijumpai.")
