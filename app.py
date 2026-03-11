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
    col1, col2, col3 = st.columns([1, 2, 1])
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
        .stApp, [data-testid="stSidebar"] *, .stMarkdown p, h1, h2, h3, label {
            color: #FFFFFF !important;
        }
        /* Dropdown/Selectbox Visibility in Dark Mode */
        div[data-baseweb="select"] > div {
            background-color: #2c3e50 !important;
            color: white !important;
        }
        header[data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
            color: white !important;
        }
        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetric"] {
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        /* Button Styling */
        div[data-testid="stVerticalBlock"] .stButton > button {
            color: #000000 !important;
            background-color: #FFFFFF !important;
            font-weight: 900 !important;
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
    .main .block-container {{ padding-top: 2rem !important; padding-bottom: 120px !important; }}
    h1 {{ margin-top: -80px !important; padding-top: 0px !important; }}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
def color_status(val):
    val = str(val).strip().upper()
    if val == 'APPROVED': return 'background-color: #d4edda; color: #000000; font-weight: bold;'
    if val == 'REJECTED': return 'background-color: #f8d7da; color: #000000; font-weight: bold;'
    return ''

def find_col(df, keyword):
    return next((c for c in df.columns if keyword.upper() in c.upper()), None)

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        return data
    except:
        return pd.DataFrame()

# --- 6. DATA LOAD ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- 7. SIDEBAR NAVIGATION ---
menu_selection = st.sidebar.radio("Select Category:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
st.sidebar.divider()
st.sidebar.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

st.title("VTSNET: Maintenance & Asset Tracker")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    st.subheader("📝 Maintenance Reports")
    
    pm_checklist_options = ["ALL"] + [f"VTSNET/PM/Q{q}/{y} YEAR" for y in ["2ND", "3RD", "4TH", "5TH"] for q in range(1,5)]

    with st.container():
        f1, f2, f3 = st.columns([1.5, 1, 1])
        with f1: selected_pm_checklist = st.selectbox("📂 PM Checklist Filter", pm_checklist_options)
        with f2: search_report = st.text_input("🔎 Search Site/Type (MET, VHF, etc):")
        with f3: search_staff = st.text_input("👤 Search Staff Name:")

    st.divider()

    if not df_raw.empty:
        df = df_raw.copy()
        id_col = find_col(df, "ID DOCUMENT")
        checklist_col = find_col(df, "REPORT CHECKLIST")
        name_col = next((c for c in df.columns if c.strip().upper() == "NAME"), None)
        status_col = find_col(df, "STATUS")
        pdf_col = find_col(df, "UPLOAD REPORT")

        # Filtering Logic
        if selected_pm_checklist != "ALL":
            col = id_col if id_col else checklist_col
            df = df[df[col].astype(str).str.upper().str.contains(selected_pm_checklist.upper(), na=False)]
        if search_report and checklist_col:
            df = df[df[checklist_col].astype(str).str.contains(search_report, case=False, na=False)]
        if search_staff and name_col:
            df = df[df[name_col].astype(str).str.contains(search_staff, case=False, na=False)]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        if status_col:
            m2.metric("Approved ✅", len(df[df[status_col].astype(str).str.upper() == 'APPROVED']))
            m3.metric("Pending ⏳", len(df[~df[status_col].astype(str).str.upper().isin(['APPROVED', 'REJECTED'])]))

        c1, c2 = st.columns(2)
        with c1:
            if not df.empty and status_col:
                fig_pie = px.pie(df, names=status_col, hole=0.55, title="Approval Overview", template=plotly_theme,
                                 color_discrete_map={'APPROVED': '#2ecc71', 'REJECTED': '#e74c3c'})
                st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            if not df.empty and checklist_col:
                fig_bar = px.histogram(df, x=checklist_col, color=status_col if status_col else None, title="Reports by Type", template=plotly_theme)
                st.plotly_chart(fig_bar, use_container_width=True)

        st.dataframe(df.style.map(color_status, subset=[status_col]) if status_col else df, use_container_width=True, hide_index=True,
                     column_config={pdf_col: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")} if pdf_col else {})

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = find_col(df_equip, "SITE")

        if month_cols:
            c1, c2 = st.columns(2)
            with c1: selected_month = st.selectbox("📅 Select Report Month:", month_cols)
            with c2:
                unique_sites = ["ALL SITES"] + sorted(df_equip[site_col].dropna().unique().tolist()) if site_col else ["ALL SITES"]
                selected_site = st.selectbox("🏗️ Select Site:", unique_sites)

            df_working = df_equip.copy()
            if selected_site != "ALL SITES":
                df_working = df_working[df_working[site_col] == selected_site]

            st.divider()
            
            # Button Filters
            status_series = df_working[selected_month].astype(str).str.strip().str.upper()
            if 'filter_status' not in st.session_state: st.session_state.filter_status = "ALL"
            
            bm1, bm2, bm3, bm4 = st.columns(4)
            if bm1.button(f"🟢 OK: {len(df_working[status_series == 'OK'])}", use_container_width=True): st.session_state.filter_status = "OK"
            if bm2.button(f"🟡 FAULTY: {len(df_working[status_series == 'FAULTY'])}", use_container_width=True): st.session_state.filter_status = "FAULTY"
            if bm3.button(f"🔴 MISSING: {len(df_working[status_series == 'MISSING'])}", use_container_width=True): st.session_state.filter_status = "MISSING"
            if bm4.button("🔵 SHOW ALL", use_container_width=True): st.session_state.filter_status = "ALL"

            df_filtered = df_working if st.session_state.filter_status == "ALL" else df_working[df_working[selected_month].astype(str).str.strip().str.upper() == st.session_state.filter_status]

            # Charts
            ch1, ch2 = st.columns([0.4, 0.6])
            with ch1:
                st.plotly_chart(px.pie(df_working, names=selected_month, hole=0.55, template=plotly_theme, title="Status Overall",
                                      color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}), use_container_width=True)
            with ch2:
                type_col = find_col(df_filtered, "TYPE")
                if type_col:
                    st.plotly_chart(px.bar(df_filtered.groupby([type_col, selected_month]).size().reset_index(name='count'), 
                                          x=type_col, y='count', color=selected_month, template=plotly_theme, title="Analysis by Type",
                                          color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}, barmode='group'), use_container_width=True)

            st.dataframe(df_filtered, use_container_width=True, hide_index=True)

# --- 8. FOOTER ---
st.markdown(f"""
    <div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: {sidebar_bg}; text-align: center; padding: 15px; z-index: 9999; border-top: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(10px);">
        <p style="color: {text_color} !important; margin: 0; font-size: 14px; font-weight: 500;">© 2026 GreenFinder VTMS Dashboard. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)
