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
        .stApp, [data-testid="stSidebar"] *, .stMarkdown p, h1, h2, h3, label { color: #FFFFFF !important; }
        [data-testid="stMetric"] { border: 1px solid rgba(255, 255, 255, 0.2) !important; background: rgba(255, 255, 255, 0.03) !important; border-radius: 12px !important; padding: 20px !important; }
        [data-testid="stMetricValue"] { color: #FFFFFF !important; }
        .stDataFrame { background-color: rgba(0,0,0,0) !important; }
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
SHEET_SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1h9_vOwZWTrXTWo1m907T9g23LW211qcjCOw03q2kc3I/export?format=csv"

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- 7. SIDEBAR NAVIGATION ---
menu_selection = st.sidebar.radio("Select Category:", ["📝 Maintenance Reports", "⚙️ Equipment Status", "📅 Staff Schedule"])
st.sidebar.divider()
st.sidebar.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

st.title("VTSNET Dashboard")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    st.subheader("📝 Maintenance Reports")
    pm_checklist_options = ["ALL"] + [f"VTSNET/PM/Q{q}/{y} YEAR" for y in ["2ND", "3RD", "4TH", "5TH"] for q in range(1, 5)]

    f1, f2, f3 = st.columns([1.5, 1, 1])
    with f1: selected_pm_checklist = st.selectbox("📂 PM Checklist Filter", pm_checklist_options)
    with f2: search_report = st.text_input("🔎 Search Site/Type (MET, VHF, etc):")
    with f3: search_staff = st.text_input("👤 Search Staff Name:")

    if not df_raw.empty:
        df = df_raw.copy()
        id_col = find_col(df, "ID DOCUMENT")
        checklist_col = find_col(df, "REPORT CHECKLIST")
        name_col = next((c for c in df.columns if c.strip().upper() == "NAME"), None)
        status_col = find_col(df, "STATUS")
        pdf_col = next((c for c in df.columns if c.strip().upper() == "UPLOAD REPORT"), None)

        if selected_pm_checklist != "ALL":
            col_check = id_col if id_col else checklist_col
            df = df[df[col_check].astype(str).str.upper().str.contains(selected_pm_checklist.upper(), na=False)]
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
                st.plotly_chart(px.pie(df, names=status_col, hole=0.5, title="Approval Overview", template=plotly_theme,
                                      color_discrete_map={'APPROVED': '#2ecc71', 'REJECTED': '#e74c3c'}), use_container_width=True)
        with c2:
            if not df.empty and checklist_col:
                st.plotly_chart(px.histogram(df, x=checklist_col, color=status_col if status_col else None, title="Reports by Type", template=plotly_theme), use_container_width=True)

        st.dataframe(df.style.map(color_status, subset=[status_col]) if status_col else df, use_container_width=True, hide_index=True,
                     column_config={pdf_col: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")} if pdf_col else {})

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"])]
        if month_cols:
            sel_month = st.selectbox("📅 Select Month:", month_cols)
            df_filtered = df_equip.copy()
            
            # --- Donuts & Bar Charts (Sama seperti kod anda) ---
            ec1, ec2 = st.columns([0.4, 0.6])
            with ec1:
                st.plotly_chart(px.pie(df_filtered, names=sel_month, hole=0.5, title="Status Overall", template=plotly_theme,
                                      color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}), use_container_width=True)
            with ec2:
                type_col = find_col(df_filtered, "TYPE")
                if type_col:
                    st.plotly_chart(px.bar(df_filtered, x=type_col, color=sel_month, barmode="group", template=plotly_theme,
                                          color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}), use_container_width=True)
            
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)

# --- PAGE 3: STAFF SCHEDULE (NEWLY ADDED) ---
elif menu_selection == "📅 Staff Schedule":
    st.subheader("📅 Staff Duty Schedule")
    df_sch = load_data(SHEET_SCHEDULE_URL)
    if not df_sch.empty:
        staff_col = next((c for c in df_sch.columns if "NAME" in c.upper() or "STAF" in c.upper()), df_sch.columns[0])
        staff_list = ["ALL"] + sorted(df_sch[staff_col].dropna().unique().tolist())
        sel_staff = st.sidebar.selectbox("Filter Staff Name:", staff_list)
        
        df_disp = df_sch.copy()
        if sel_staff != "ALL":
            df_disp = df_disp[df_disp[staff_col] == sel_staff]
        
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
    else:
        st.error("Schedule data not found.")

# --- 8. FOOTER ---
st.markdown(f"""
    <div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: {sidebar_bg}; text-align: center; padding: 10px; border-top: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(10px);">
        <p style="color: {text_color} !important; margin: 0;">© 2026 GreenFinder VTMS Dashboard. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)
