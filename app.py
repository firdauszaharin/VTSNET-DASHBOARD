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

# --- SIDEBAR THEME TOGGLE ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.title("🌓 SETTINGS")
    # Switch untuk Dual Mode
    dark_mode = st.toggle("Dark Mode View", value=False)
    st.divider()

# --- DYNAMIC CSS LOGIC ---
if dark_mode:
    # Warna untuk MOD GELAP
    primary_bg = "radial-gradient(circle at top right, #1e272e, #0f172a)"
    sidebar_bg = "rgba(30, 39, 46, 0.95)"
    card_bg = "#1e293b"
    text_main = "#f8fafc"
    shadow = "0 10px 25px rgba(0,0,0,0.5)"
    plotly_template = "plotly_dark"
else:
    # Warna untuk MOD ASAL (LIGHT)
    primary_bg = "radial-gradient(circle at top right, #f8faff, #eef2f7,#f8faff)"
    sidebar_bg = "rgba(255, 255, 255, 0.8)"
    card_bg = "white"
    text_main = "#1e293b"
    shadow = "0 10px 25px rgba(0,0,0,0.03)"
    plotly_template = "plotly_white"

st.markdown(f"""
    <style>
    .stApp {{ 
        background: {primary_bg}; 
        font-family: 'Inter', sans-serif; 
        color: {text_main};
    }}

    [data-testid="stSidebar"] {{ 
        background-color: {sidebar_bg} !important; 
        backdrop-filter: blur(10px); 
    }}

    [data-testid="stMetric"] {{ 
        background: {card_bg} !important; 
        padding: 20px !important; 
        border-radius: 20px !important; 
        box-shadow: {shadow} !important; 
    }}
    
    /* Warna text untuk Metric */
    [data-testid="stMetricValue"] {{ color: {text_main} !important; }}
    [data-testid="stMetricLabel"] {{ color: {text_main} !important; opacity: 0.8; }}

    header[data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0) !important;
        color: #0984E3 !important;
    }}
    
    .st-emotion-cache-hp888a {{ color: #0984E3 !important; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- SET MALAYSIA TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

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
            data['Year'] = data[time_col].dt.year
        return data
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

def color_status(val):
    if val == 'APPROVED': return 'background-color: #d4edda; color: #155724;'
    if val == 'REJECTED': return 'background-color: #f8d7da; color: #721c24;'
    return ''

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("📌 MENU")
    menu_selection = st.radio("Pilih Paparan:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    search_report = st.text_input("🔎 Search Site/Type:")
    search_staff = st.text_input("👤 Search Staff Name:")

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
            st.plotly_chart(px.pie(df, names='STATUS', hole=0.4, title="Status Distribution", template=plotly_template,
                                   color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        with c2:
            st.plotly_chart(px.histogram(df, x='REPORT CHECKLIST', color='STATUS', title="Reports by Type", template=plotly_template,
                                         color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)

        st.subheader("📋 Record Table")
        styled_df = df.style.map(color_status, subset=['STATUS']) if 'STATUS' in df.columns else df
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
                selected_month = st.selectbox("📅 Select Month:", month_cols, index=len(month_cols)-1)
            
            df_working = df_equip.copy()
            if site_col:
                unique_sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().unique().tolist())
                with c2:
                    selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
                if selected_site != "ALL SITES":
                    df_working = df_working[df_working[site_col] == selected_site]

            st.divider()
            status_series = df_working[selected_month].astype(str).str.strip().str.upper()
            
            if 'filter_status' not in st.session_state:
                st.session_state.filter_status = "ALL"

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

            st.markdown(f"### 🎯 Performance Overview: {selected_site}")
            col_chart1, col_chart2 = st.columns([0.3, 0.7])
            
            with col_chart1:
                fig_donut = px.pie(df_working, names=selected_month, hole=0.6, template=plotly_template,
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_chart2:
                type_col = next((c for c in df_filtered.columns if c.lower() == 'type'), None)
                if type_col and not df_filtered.empty:
                    df_type_status = df_filtered.groupby([type_col, selected_month]).size().reset_index(name='count')
                    fig_type = px.bar(df_type_status, x=type_col, y='count', color=selected_month, template=plotly_template,
                                     color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}, barmode='group')
                    st.plotly_chart(fig_type, use_container_width=True)

            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
