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

# 2. MODERN CSS (UI MODEN 2026)
st.markdown("""
    <style>
    /* Latar Belakang & Font */
    .stApp {
        background: radial-gradient(circle at top right, #f8faff, #eef2f7, #f8faff);
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,0,0,0.05);
    }

    /* Floating Metric Cards */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03) !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
        transition: transform 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(9, 132, 227, 0.1) !important;
    }

    /* Style for PDF Preview */
    .pdf-view-container {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #ddd;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS (Telah dibetulkan format /export?format=csv)
# Menggunakan ID unik dari link yang anda berikan sebelum ini
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1HQUV7NXuhAKtKW-weSwAmhIMOde8CZM8XiTiaF1P7K4/export?format=csv"
PDF_COL = "UPLOAD REPORT" 

# 4. DATA LOAD FUNCTION
@st.cache_data(ttl=60)
def load_data(url):
    try:
        # Load CSV data from Google Sheets export link
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip() # Buang space pada nama kolum
        
        # Cari kolum tarikh secara automatik
        time_col = next((c for c in data.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        if time_col:
            data[time_col] = pd.to_datetime(data[time_col], errors='coerce')
            data['Year'] = data[time_col].dt.year
        else:
            data['Year'] = None
        return data
    except Exception as e:
        return pd.DataFrame() # Pulangkan df kosong jika gagal

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- ICON MAPPING ---
icon_map = {
    "MET REPORT": "https://cdn-icons-png.flaticon.com/512/1146/1146869.png",
    "OPERATOR WORKSTATION": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "WALL DISPLAY REPORT": "https://cdn-icons-png.flaticon.com/512/1035/1035688.png",
    "VHF PTP FLOOR 8": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "SERVER ROOM REPORT (PTP/LPJ)": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png"
}

if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None

# 5. SIDEBAR
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.markdown(f"### 🕒 Last Sync: {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    
    st.markdown("### 🔍 GLOBAL FILTERS")
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_list = sorted([int(y) for y in df_raw['Year'].dropna().unique()], reverse=True)
        sel_year = st.selectbox("📅 Select Year:", ["All Years"] + year_list)
    else:
        sel_year = st.selectbox("📅 Select Year:", ["All Years"])
        
    search_report = st.text_input("🔎 Report Type:", placeholder="e.g. MET, SERVER")
    search_staff = st.text_input("👤 Performed by (Staff Name):")
    
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4jUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy", use_container_width=True)

# 6. EXECUTIVE SUMMARY HEADER
st.title("VTSNET Management Dashboard")

# Clock & Dashboard Banner
st.markdown("""
    <div style="background: linear-gradient(90deg, #0984E3, #6c5ce7); padding: 30px; border-radius: 20px; color: white; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0;">EDM VTMS LPJ/PTP</h1>
        <p style="opacity: 0.9;">Real-time Monitoring & Maintenance Asset System</p>
    </div>
""", unsafe_allow_html=True)

# 7. MAIN CONTENT TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

# --- TAB 1: MAINTENANCE REPORTS ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        
        # Apply Filters
        if sel_year != "All Years": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Rejected ❌", len(df[df['STATUS'] == 'REJECTED']) if 'STATUS' in df.columns else 0)
        m4.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        # Charts
        st.markdown("### 🎯 Performance Overview")
        col_pie, col_bar = st.columns(2)
        with col_pie:
            if 'STATUS' in df.columns:
                fig_pie = px.pie(df, names='STATUS', title='Approval Status', hole=0.4, color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
                st.plotly_chart(fig_pie, use_container_width=True)
        with col_bar:
            if 'REPORT CHECKLIST' in df.columns:
                fig_bar = px.histogram(df, x='REPORT CHECKLIST', color='STATUS', title='Reports by Type', color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
                st.plotly_chart(fig_bar, use_container_width=True)

        # Data Table
        st.divider()
        st.subheader("📋 Submitted Reports Record")
        
        if 'REPORT CHECKLIST' in df.columns:
            # Masukkan ikon berdasarkan jenis report
            if 'ICON' not in df.columns:
                df.insert(0, 'ICON', df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        event = st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Type"), 
                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
            },
            on_select="rerun", 
            selection_mode="single-row"
        )

        # PDF Previewer Logic
        if len(event.selection.rows) > 0:
            st.session_state.selected_row_idx = event.selection.rows[0]

        if st.session_state.selected_row_idx is not None:
            idx = st.session_state.selected_row_idx
            row = df.iloc[idx]
            link = row.get(PDF_COL, "")
            if isinstance(link, str) and "drive.google.com" in link:
                try:
                    file_id = re.search(r'[-\w]{25,}', link).group()
                    st.markdown(f'### 📄 Preview: {row.get("REPORT CHECKLIST", "Report")}')
                    st.markdown(f'<div class="pdf-view-container"><iframe src="https://drive.google.com/file/d/{file_id}/preview" width="100%" height="600px"></iframe></div>', unsafe_allow_html=True)
                except:
                    st.error("Gagal menjana preview PDF. Sila klik link 'OPEN PDF' di atas.")

# --- TAB 2: EQUIPMENT STATUS ---
with tab2:
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        # Kenal pasti kolum bulan (Contoh: JAN 2026, FEB 2026)
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026"])]
        
        if month_cols:
            selected_month = st.selectbox("📅 Select Month:", month_cols, index=len(month_cols)-1)
            
            status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
            
            e1, e2, e3 = st.columns(3)
            e1.metric("Equipment OK", len(df_equip[status_series == 'OK']))
            e2.metric("Faulty ⚠️", len(df_equip[status_series == 'FAULTY']))
            e3.metric("Missing ❌", len(df_equip[status_series == 'MISSING']))
            
            st.divider()
            st.dataframe(
                df_equip[["Site", "Type", "Serial No", selected_month]], 
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Sila pastikan data inventori dimuat naik ke Google Sheets.")
