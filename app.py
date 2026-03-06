import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os
from streamlit_autorefresh import st_autorefresh

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="VTSNET Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- AUTO REFRESH (5 MINIT) ---
st_autorefresh(interval=300000, key="vts_refresh")

# --- 2. LOGIN SECURITY ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<style>header {visibility: hidden;} [data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔒 VTSNET Project Access")
        pwd = st.text_input("Project Access Code:", type="password")
        correct_password = st.secrets.get("PROJECT_PASSWORD", "vtsnet2026")
        if st.button("Unlock Dashboard", use_container_width=True):
            if pwd == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong Password!")
    st.stop()

# --- 3. THEME TOGGLE & LOGOUT ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    dark_mode = st.toggle("Dark Mode View", value=False)
    st.divider()
    if st.button("🔒 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# --- 4. DYNAMIC CSS LOGIC ---
if dark_mode:
    bg_style = "linear-gradient(135deg, #1a0a2e 0%, #2c3e50 100%)" 
    sidebar_bg = "rgba(15, 10, 25, 0.98)"
    text_color = "#FFFFFF"
    plotly_theme = "plotly_dark"
    
    custom_dark_css = """
        <style>
        /* 1. Paksa SEMUA teks dashboard & sidebar jadi putih */
        .stApp, [data-testid="stSidebar"] *, .stMarkdown p, h1, h2, h3, label {
            color: #FFFFFF !important;
        }

        /* 2. FIX SEMUA BUTTON DALAM MAIN AREA (OK, FAULTY, MISSING, SHOW ALL) */
        /* Kita guna 'div[data-testid="stVerticalBlock"]' untuk target area content sahaja */
        div[data-testid="stVerticalBlock"] .stButton > button {
            color: #000000 !important; 
            background-color: #FFFFFF !important;
            font-weight: 900 !important;
            border: 2px solid #FFFFFF !important;
            opacity: 1 !important;
        }

        /* Effect bila mouse lalu (Hover) */
        div[data-testid="stVerticalBlock"] .stButton > button:hover {
            background-color: #f0f2f6 !important;
            color: #000000 !important;
            border: 2px solid #6c5ce7 !important;
        }
        /* 2. FIX BUTTON STATUS (OK/FAULTY/MISSING) */
        div[data-testid="stVerticalBlock"] .stButton > button {
            color: #000000 !important; 
            background-color: #FFFFFF !important;
            font-weight: 900 !important;
        }

        /* 3. FIX LOG OUT BUTTON (Dalam Sidebar) */
        /* Kita kekalkan tulisan putih supaya nampak atas butang merah */
        section[data-testid="stSidebar"] .stButton > button {
            color: #FFFFFF !important;
            background-color: rgba(255, 75, 75, 0.2) !important;
            border: 1px solid #ff4b4b !important;
        }
        
        section[data-testid="stSidebar"] .stButton > button:p {
            color: #FFFFFF !important;
        }
        </style>
    """
else:
    bg_style = "radial-gradient(circle at top right, #f8faff, #eef2f7)"
    sidebar_bg = "rgba(255, 255, 255, 0.9)"
    text_color = "#1e293b"
    plotly_theme = "plotly_white"
    custom_dark_css = ""

st.markdown(custom_dark_css, unsafe_allow_html=True)
st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; backdrop-filter: blur(10px); }}
    .main .block-container {{ padding-bottom: 100px !important; }}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS (Warna Table) ---
def color_status(val):
    # Kita paksa warna teks jadi HITAM (#000000) supaya nampak atas hijau/merah
    if val == 'APPROVED': 
        return 'background-color: #d4edda; color: #000000; font-weight: bold;'
    if val == 'REJECTED': 
        return 'background-color: #f8d7da; color: #000000; font-weight: bold;'
    return ''

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        return data
    except: return pd.DataFrame()

# --- 6. DATA LOAD ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
PDF_COL = "UPLOAD REPORT" 

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- 7. SIDEBAR NAVIGATION ---
menu_selection = st.sidebar.radio("Select Category:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
st.sidebar.divider()
st.sidebar.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

st.title("VTSNET: Maintenance & Asset Lifecycle Tracker")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    search_report = st.sidebar.text_input("🔎 Search Site/Type (MET, VHF, etc):")
    search_staff = st.sidebar.text_input("👤 Search Staff Name:")
    
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
            st.plotly_chart(px.pie(df, names='STATUS', hole=0.55, title="Approval Overview", 
                                   color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}, template=plotly_theme), use_container_width=True)
        with c2:
            st.plotly_chart(px.histogram(df, x='REPORT CHECKLIST', color='STATUS', title="Reports by Type",
                                           color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}, template=plotly_theme), use_container_width=True)

        st.subheader("📋 Report Tracking Status")
        styled_df = df.style.map(color_status, subset=['STATUS']) if 'STATUS' in df.columns else df
        st.dataframe(styled_df, use_container_width=True, hide_index=True,
                     column_config={PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")})

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if c.lower() == 'site'), None)
        
        if month_cols:
            c1, c2 = st.columns(2)
            with c1: selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=0)
            
            df_working = df_equip.copy()
            if site_col:
                unique_sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().unique().tolist())
                with c2: selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
                if selected_site != "ALL SITES":
                    df_working = df_working[df_working[site_col] == selected_site]

            st.divider()
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
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered[selected_month].astype(str).str.strip().str.upper() == st.session_state.filter_status]

            col_chart1, col_chart2 = st.columns([0.4, 0.6])
            with col_chart1:
                fig_donut = px.pie(df_working, names=selected_month, hole=0.55, template=plotly_theme, title="Status Overall",
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                st.plotly_chart(fig_donut, use_container_width=True)
            with col_chart2:
                type_col = next((c for c in df_filtered.columns if c.lower() == 'type'), None)
                if type_col and not df_filtered.empty:
                    fig_type = px.bar(df_filtered.groupby([type_col, selected_month]).size().reset_index(name='count'), 
                                      x=type_col, y='count', color=selected_month, template=plotly_theme, title="Analysis by Type",
                                      color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}, barmode='group')
                    st.plotly_chart(fig_type, use_container_width=True)

         # --- INVENTORY ASSET LIST ---
            st.divider()
            st.subheader(f"📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Quick Search (SN, Name, IP):", key="search_eq_box")
            if search_eq:
                df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            year_match = re.search(r'202\d', selected_month)
            curr_yr = year_match.group(0) if year_match else "2025"
            m_up = selected_month.upper()
            if any(m in m_up for m in ['JAN', 'FEB', 'MAR']): q = "Q1"
            elif any(m in m_up for m in ['APR', 'MAY', 'MEI', 'JUN']): q = "Q2"
            elif any(m in m_up for m in ['JUL', 'AUG', 'SEP', 'OGO']): q = "Q3"
            else: q = "Q4"
            actual_remark_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper() and curr_yr in c.upper()), None)

            display_cols = []
            standard_cols = ["Site", "Type", "Equipment", "Serial No", "IP Address"]
            for col in standard_cols:
                match = next((c for c in df_filtered.columns if c.lower() == col.lower()), None)
                if match: display_cols.append(match)
            if selected_month in df_filtered.columns: display_cols.append(selected_month)
            if actual_remark_col: display_cols.append(actual_remark_col)

            if not df_filtered.empty:
                st.dataframe(
                    df_filtered[display_cols].style.map(
                        lambda x: 'background-color: #D4EDDA; color: #155724;' if str(x).upper() == 'OK' else 
                                  ('background-color: #F8D7DA; color: #721C24;' if str(x).upper() == 'MISSING' else 
                                   ('background-color: #FFF3CD; color: #856404;' if str(x).upper() == 'FAULTY' else '')), 
                        subset=[selected_month] if selected_month in display_cols else None
                    ), use_container_width=True, hide_index=True
                )

# --- 8. FOOTER (GLOBAL) ---
st.markdown(f"""
    <div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: {sidebar_bg}; text-align: center; padding: 10px; z-index: 9999; border-top: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(10px);">
        <p style="color: {text_color} !important;">© 2026 GreenFinder VTMS Admin & Inventory Dashboard. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)
