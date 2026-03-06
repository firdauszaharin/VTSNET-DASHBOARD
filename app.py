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

# 2. DARK MODE MODERN CSS
st.markdown("""
    <style>
    .stApp { 
        background-color: #0E1117;
        background-image: radial-gradient(circle at top right, #1a2a6c, #0E1117, #0E1117);
        color: #E0E0E0;
        font-family: 'Inter', sans-serif; 
    }
    [data-testid="stSidebar"] { 
        background-color: rgba(20, 26, 35, 0.95) !important; 
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    [data-testid="stMetric"] { 
        background: #1D232D !important; 
        padding: 20px !important; 
        border-radius: 20px !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(255,255,255,0.05);
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    [data-testid="stMetricLabel"] { color: #A0A0A0 !important; }
    
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
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
        return data
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- HELPER FUNCTION ---
def color_status_report(val):
    if val == 'APPROVED': return 'background-color: #1b5e20; color: white;'
    if val == 'REJECTED': return 'background-color: #b71c1c; color: white;'
    return ''

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.title("📌 MENU")
    # Ditambah key unik untuk elak DuplicateElementId
    menu_selection = st.radio("Pilih Paparan:", ["📝 Maintenance Reports", "⚙️ Equipment Status"], key="main_nav")
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    search_report = st.text_input("🔎 Search Site/Type:", key="search_side_1")
    search_staff = st.text_input("👤 Search Staff Name:", key="search_side_2")

# --- HEADER BANNER ---
st.title("VTSNET Management Dashboard")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    if not df_raw.empty:
        df = df_raw.copy()
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df, names='STATUS', hole=0.4, title="Status Distribution", 
                          template="plotly_dark", color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.histogram(df, x='REPORT CHECKLIST', color='STATUS', title="Reports by Type",
                               template="plotly_dark", color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📋 Record Table")
        styled_df = df.style.map(color_status_report, subset=['STATUS']) if 'STATUS' in df.columns else df
        st.dataframe(styled_df, use_container_width=True, hide_index=True,
                    column_config={PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")})
    else:
        st.info("Waiting for data...")

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if c.lower() == 'site'), None)
        
        if month_cols:
            c1, c2 = st.columns(2)
            with c1:
                selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=len(month_cols)-1)
            
            df_working = df_equip.copy()
            if site_col:
                unique_sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().unique().tolist())
                with c2:
                    selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
                if selected_site != "ALL SITES":
                    df_working = df_working[df_working[site_col] == selected_site]

            status_series = df_working[selected_month].astype(str).str.strip().str.upper()
            if 'filter_status' not in st.session_state: st.session_state.filter_status = "ALL"

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1: 
                if st.button(f"🟢 OK: {len(df_working[status_series == 'OK'])}", use_container_width=True): st.session_state.filter_status = "OK"
            with col_m2:
                if st.button(f"🟡 FAULTY: {len(df_working[status_series == 'FAULTY'])}", use_container_width=True): st.session_state.filter_status = "FAULTY"
            with col_m3:
                if st.button(f"🔴 MISSING: {len(df_working[status_series == 'MISSING'])}", use_container_width=True): st.session_state.filter_status = "MISSING"
            with col_m4:
                if st.button("🔵 SHOW ALL", use_container_width=True): st.session_state.filter_status = "ALL"

            df_filtered = df_working.copy()
            df_filtered[selected_month] = df_filtered[selected_month].astype(str).str.strip().str.upper()
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered[selected_month] == st.session_state.filter_status]

            col_chart1, col_chart2 = st.columns([0.3, 0.7])
            with col_chart1:
                fig_donut = px.pie(df_working, names=selected_month, hole=0.6, title='Overall Condition',
                                  template="plotly_dark", color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_chart2:
                type_col = next((c for c in df_filtered.columns if c.lower() == 'type'), None)
                if type_col and not df_filtered.empty:
                    df_type_status = df_filtered.groupby([type_col, selected_month]).size().reset_index(name='count')
                    fig_type = px.bar(df_type_status, x=type_col, y='count', color=selected_month,
                                     template="plotly_dark", barmode='group',
                                     color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'})
                    st.plotly_chart(fig_type, use_container_width=True)

            st.divider()
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
