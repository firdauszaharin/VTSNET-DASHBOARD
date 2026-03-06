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
    /* 1. Latar Belakang Gradient & Font */
    .stApp {
        background: radial-gradient(circle at top right, #f8faff, #eef2f7,#f8faff);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 2. Glassmorphism untuk Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,0,0,0.05);
    }

    /* 3. Kotak Metric yang 'Floating' */
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

    /* 4. Tajuk dan Tab yang Kemas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: white;
        border-radius: 10px;
        padding: 0px 20px;
        border: 1px solid rgba(0,0,0,0.05);
    }

    .stTabs [aria-selected="true"] {
        background: #0984E3 !important;
        color: white !important;
    }

    /* 5. Custom Alert Box (Modern Flat Design) */
    .alert-box {
        background: #FFFFFF;
        border-left: 6px solid #FF4B4B;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.1);
        margin-bottom: 25px;
    }

    /* 6. Kemaskan Ruang (Tanpa Hilangkan Butang Sidebar) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Ini akan menyembunyikan background putih header tapi kekalkan butang sidebar */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1HQUV7NXuhAKtKW-weSwAmhIMOde8CZM8XiTiaF1P7K4/edit?usp=sharing"
PDF_COL = "UPLOAD REPORT" 

# 4. DATA LOAD FUNCTION
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        time_col = next((c for c in data.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        if time_col:
            data[time_col] = pd.to_datetime(data[time_col], errors='coerce')
            data['Year'] = data[time_col].dt.year
        else:
            data['Year'] = None
        return data
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- REPORT ICON MAPPING ---
icon_map = {
    "MARDEP MONITORING": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "VTS KLANG": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "WALL DISPLAY REPORT": "https://cdn-icons-png.flaticon.com/512/1035/1035688.png",
    "RSS JLM": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "RSS APMM": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "RSS LPJ": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "APPLICATION SERVER": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png",
    "DATABASE SERVER": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png"
}

if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None

# 5. SIDEBAR
with st.sidebar:
    
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    
    st.markdown("### 🔍 GLOBAL FILTERS")
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_list = sorted(df_raw['Year'].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Select Year:", ["All Years"] + [int(t) for t in year_list])
    else:
        sel_year = st.selectbox("📅 Select Year:", ["All Years"])
        
    search_report = st.text_input("🔎 Report Type:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Staff Name:")
    
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4jUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy", use_container_width=True)

# 6. EXECUTIVE SUMMARY
st.title("VTSNET Management Dashboard")

if not df_equip.empty:
    month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
    latest_month = month_cols[-1] if month_cols else None
    
    if latest_month:
        status_check = df_equip[latest_month].astype(str).str.strip().str.upper()
        faulty_data = df_equip[status_check.isin(['FAULTY', 'MISSING'])]
        
        if len(faulty_data) > 0:
            st.markdown("""
    <div style="
        background: linear-gradient(90deg, #0984E3, #6c5ce7);
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div style="display: flex; flex-direction: column; align-items: flex-start;">
            <div style="margin-bottom: 15px;">
                <img src="https://lh3.googleusercontent.com/d/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A" 
                     style="height: 60px; filter: brightness(0) invert(1);"> 
                </div>
            
            <h1 style="
                color: white;
                font-size: 30px;
                font-weight: 800;
                margin: 0;
                letter-spacing: -1px;
                line-height: 1.1;
            ">
                EDM VTMS LPJ/PTP<br>
                <span style="font-weight: 300; opacity: 0.8; font-size: 20px;">Management Dashboard</span>
            </h1>
        </div>

        <div style="text-align: right; border-left: 2px solid rgba(255,255,255,0.2); padding-left: 30px;">
            <h2 id="clock" style="
                color: white; 
                margin: 0; 
                font-family: 'Courier New', monospace; 
                font-size: 45px; 
                font-weight: 900;
            ">00:00:00</h2>
            <p id="date" style="
                color: rgba(255,255,255,0.8); 
                margin: 5px 0 0 0; 
                font-size: 14px; 
                text-transform: uppercase;
                letter-spacing: 1px;
            "></p>
        </div>
    </div>

    <script>
    function updateClock() {
        const now = new Date();
        const tOpt = { timeZone: "Asia/Kuala_Lumpur", hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
        const dOpt = { timeZone: "Asia/Kuala_Lumpur", weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' };
        
        document.getElementById('clock').textContent = new Intl.DateTimeFormat('en-GB', tOpt).format(now);
        document.getElementById('date').textContent = new Intl.DateTimeFormat('ms-MY', dOpt).format(now);
    }
    setInterval(updateClock, 1000);
    updateClock();
    </script>
""", unsafe_allow_html=True)
            
            st.download_button(
                label="📥 Download Faulty Assets List (CSV)",
                data=faulty_data.to_csv(index=False).encode('utf-8'),
                file_name=f'Faulty_Assets_{latest_month}.csv',
                mime='text/csv',
            )

# 7. MAIN CONTENT TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

# --- TAB 1: MAINTENANCE REPORTS ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if sel_year != "All Years": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        time_col = next((c for c in df.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        display_df = df.sort_values(by=time_col, ascending=False).reset_index(drop=True) if time_col else df.reset_index(drop=True)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Reports", len(display_df))
        m2.metric("Approved ✅", len(display_df[display_df['STATUS'] == 'APPROVED']) if 'STATUS' in display_df.columns else 0)
        m3.metric("Rejected ❌", len(display_df[display_df['STATUS'] == 'REJECTED']) if 'STATUS' in display_df.columns else 0)
        m4.metric("Pending ⏳", len(display_df[~display_df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in display_df.columns else 0)

        st.markdown("### 🎯 Maintenance Performance Overview")
        col_p, col_b = st.columns(2)
        with col_p:
            st.plotly_chart(px.pie(display_df, names='STATUS', title='Approval Status Distribution', hole=0.4, 
                                  color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        with col_b:
            st.plotly_chart(px.histogram(display_df, x='REPORT CHECKLIST', color='STATUS', title='Report Frequency by Type',
                                         color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)

        st.divider()
        st.subheader("📋 Submitted Reports Record")
        
        def highlight_status(val):
            if val == 'REJECTED': return 'background-color: #F8D7DA; color: #721C24;'
            if val == 'APPROVED': return 'background-color: #D4EDDA; color: #155724;'
            return ''

        if 'REPORT CHECKLIST' in display_df.columns:
            display_df.insert(0, 'ICON', display_df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        styled_df = display_df.style.map(highlight_status, subset=['STATUS']) if 'STATUS' in display_df.columns else display_df

        event = st.dataframe(styled_df, use_container_width=True, hide_index=True,
                            column_config={
                                "ICON": st.column_config.ImageColumn("Type"), 
                                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
                            },
                            on_select="rerun", selection_mode="single-row")

        if len(event.selection.rows) > 0:
            st.session_state.selected_row_idx = event.selection.rows[0]

        if st.session_state.selected_row_idx is not None:
            idx = st.session_state.selected_row_idx
            row = display_df.iloc[idx]
            link = row.get(PDF_COL, "")
            if isinstance(link, str) and "drive.google.com" in link:
                file_id = re.search(r'[-\w]{25,}', link).group()
                st.markdown(f'<div class="pdf-view-container"><iframe src="https://drive.google.com/file/d/{file_id}/preview" width="100%" height="600px"></iframe></div>', unsafe_allow_html=True)

# --- TAB 2: EQUIPMENT STATUS ---
with tab2:
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
        
        c_sel, _ = st.columns([0.4, 0.6])
        with c_sel:
            selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=len(month_cols)-1)
        
        st.divider()

        if selected_month in df_equip.columns:
            status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
            df_pie = df_equip.copy()
            df_pie[selected_month] = status_series
            
            me1, me2, me3 = st.columns(3)
            me1.metric(f"Equipment OK", len(df_equip[status_series == 'OK']))
            me2.metric(f"Faulty ⚠️", len(df_equip[status_series == 'FAULTY']))
            me3.metric(f"Missing ❌", len(df_equip[status_series == 'MISSING']))

            st.markdown(f"### 🎯 Equipment Performance Overview ({selected_month})")
            
            # SUSUNAN DONUT DAN HISTOGRAM
            col_left, col_right = st.columns(2)
            
            with col_left:
                fig_donut = px.pie(
                    df_pie, 
                    names=selected_month, 
                    title='Condition Overview',
                    hole=0.55, 
                    color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}
                )
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_right:
                if 'Site' in df_pie.columns:
                    st.plotly_chart(px.histogram(df_pie, x='Site', color=selected_month, barmode='group', title='Status by Location',
                                                color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)
            
            if 'Type' in df_pie.columns:
                st.plotly_chart(px.histogram(df_pie, x='Type', color=selected_month, barmode='group', title='Status by Equipment Category',
                                            color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)
            
            st.divider()
            st.subheader("📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Search Asset (SN, Name, Site):", key="search_eq_tab")
            essential_cols = ["Site", "Type", "Serial No", "IP Address", selected_month]
            df_eq_show = df_equip[[c for c in essential_cols if c in df_equip.columns]].copy()
            
            if search_eq:
                df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            st.dataframe(df_eq_show.style.map(lambda x: 'background-color: #D4EDDA' if x=='OK' else ('background-color: #F8D7DA' if x=='MISSING' else ('background-color: #FFF3CD' if x=='FAULTY' else '')), subset=[selected_month]), use_container_width=True, hide_index=True)






















