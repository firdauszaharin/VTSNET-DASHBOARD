import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import re
import os
import hmac
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="VTSNET Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. AUTO REFRESH (5 MINIT)
# =========================================================
st_autorefresh(interval=300000, key="vts_refresh")

# =========================================================
# 3. LOGIN SECURITY
# =========================================================
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 10

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0

if "lockout_until" not in st.session_state:
    st.session_state.lockout_until = None

def is_locked_out() -> bool:
    if st.session_state.lockout_until is None:
        return False
    return datetime.now() < st.session_state.lockout_until

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 VTSNET Project Access")
        pwd = st.text_input("Project Access Code:", type="password")

        if is_locked_out():
            remaining = int((st.session_state.lockout_until - datetime.now()).total_seconds() // 60) + 1
            st.error(f"Too many failed attempts. Try again in {remaining} minute(s).")
            st.stop()

        correct_password = st.secrets.get("PROJECT_PASSWORD")
        if not correct_password:
            st.error("PROJECT_PASSWORD not configured in secrets.toml")
            st.stop()

        if st.button("Unlock Dashboard", use_container_width=True):
            if hmac.compare_digest(str(pwd), str(correct_password)):
                st.session_state.authenticated = True
                st.session_state.login_attempts = 0
                st.session_state.lockout_until = None
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                    st.session_state.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
                    st.error("Too many failed attempts. Access temporarily locked.")
                else:
                    remaining = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
                    st.error(f"Wrong Password! Remaining attempts: {remaining}")
    st.stop()

# =========================================================
# 4. THEME TOGGLE & LOGOUT
# =========================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    dark_mode = st.toggle("Dark Mode View", value=False)
    st.divider()
    if st.button("🔒 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.login_attempts = 0
        st.session_state.lockout_until = None
        st.rerun()

# =========================================================
# 5. DYNAMIC CSS LOGIC
# =========================================================
if dark_mode:
    bg_style = "linear-gradient(135deg, #1a0a2e 0%, #2c3e50 100%)"
    sidebar_bg = "rgba(15, 10, 25, 0.98)"
    text_color = "#FFFFFF"
    plotly_theme = "plotly_dark"
    custom_css = """
        <style>
        .stApp, [data-testid="stSidebar"] *, .stMarkdown p, h1, h2, h3, label { color: #FFFFFF !important; }
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; color: white !important; }
        [data-testid="stDecoration"] { display: none; }
        [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 700 !important; }
        [data-testid="stMetric"] { border: 1px solid rgba(255, 255, 255, 0.2) !important; background: rgba(255, 255, 255, 0.03) !important; border-radius: 12px !important; }
        </style>
    """
else:
    bg_style = "linear-gradient(135deg, #eef2f6 0%, #e3e8ee 100%)"
    sidebar_bg = "rgba(245, 247, 250, 0.96)"
    text_color = "#243447"
    plotly_theme = "plotly_white"
    custom_css = """
        <style>
        .stApp, .stMarkdown p, h1, h2, h3, label { color: #243447 !important; }
        [data-testid="stMetric"] { border: 1px solid rgba(36, 52, 71, 0.08) !important; background: rgba(255, 255, 255, 0.60) !important; border-radius: 12px !important; }
        </style>
    """

st.markdown(custom_css, unsafe_allow_html=True)
st.markdown(f"""<style>
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; backdrop-filter: blur(10px); }}
    footer {{ visibility: hidden; }}
    </style>""", unsafe_allow_html=True)

# =========================================================
# 6. HELPER FUNCTIONS
# =========================================================
def color_status(val):
    val = str(val).strip().upper()
    if val == "APPROVED": return "background-color: #d4edda; color: #000000; font-weight: bold;"
    if val == "REJECTED": return "background-color: #f8d7da; color: #000000; font-weight: bold;"
    return ""

def find_col(df, keyword):
    return next((c for c in df.columns if keyword.upper() in c.upper()), None)

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines="skip")
        data.columns = data.columns.str.strip()
        return data
    except:
        return pd.DataFrame()

# =========================================================
# 7. DATA LOAD
# =========================================================
msia_tz = pytz.timezone("Asia/Kuala_Lumpur")
waktu_msia = datetime.now(msia_tz)

SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
PDF_COL = "UPLOAD REPORT"

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# =========================================================
# 8. SIDEBAR NAVIGATION
# =========================================================
menu_selection = st.sidebar.radio("Select Category:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
st.sidebar.divider()
st.sidebar.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

st.title("VTSNET: Tracker Dashboard")

# =========================================================
# PAGE 1: MAINTENANCE REPORTS
# =========================================================
if menu_selection == "📝 Maintenance Reports":
    st.subheader("📝 Maintenance Reports")
    if not df_raw.empty:
        df = df_raw.copy()
        status_col = find_col(df, "STATUS")
        st.dataframe(df.style.map(color_status, subset=[status_col]) if status_col else df, use_container_width=True)
    else:
        st.warning("No report data available.")

# =========================================================
# PAGE 2: EQUIPMENT STATUS
# =========================================================
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        
        q_map = {"Q1": ["JAN", "FEB", "MAR"], "Q2": ["APR", "MAY", "MEI", "JUN"], 
                 "Q3": ["JUL", "AUG", "SEP", "OGO"], "Q4": ["OCT", "NOV", "DEC", "OKT", "DIS"]}

        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            available_years = sorted(list(set(re.findall(r"202\d", " ".join(df_equip.columns)))), reverse=True)
            if not available_years: available_years = ["2025"]
            selected_year = st.selectbox("📅 Select Year:", available_years)
        with f_col2:
            selected_q = st.selectbox("📂 Select Quarter:", ["Q1", "Q2", "Q3", "Q4"])

        df_working = df_equip.copy()
        site_col = next((c for c in df_equip.columns if c.lower() == "site"), None)
        if site_col:
            unique_sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().unique().tolist())
            with f_col3:
                selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
            if selected_site != "ALL SITES":
                df_working = df_working[df_working[site_col] == selected_site]

        relevant_months = [c for c in df_equip.columns if any(m in c.upper() for m in q_map[selected_q]) and selected_year in str(c) and "REMARK" not in c.upper()]
        
        if relevant_months:
            def get_combined_status(row):
                statuses = [str(row[m]).strip().upper() for m in relevant_months if m in row]
                if "FAULTY" in statuses: return "FAULTY"
                if "WARNING" in statuses: return "WARNING"
                if "OK" in statuses: return "OK"
                return "PENDING"

            df_working["STATUS"] = df_working.apply(get_combined_status, axis=1)
            
            if "filter_status" not in st.session_state:
                st.session_state.filter_status = "ALL"

            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                if st.button(f"🟢 OK: {len(df_working[df_working['STATUS'] == 'OK'])}", use_container_width=True):
                    st.session_state.filter_status = "OK"
            with m2:
                if st.button(f"🔴 FAULTY: {len(df_working[df_working['STATUS'] == 'FAULTY'])}", use_container_width=True):
                    st.session_state.filter_status = "FAULTY"
            with m3:
                if st.button(f"🟡 WARNING: {len(df_working[df_working['STATUS'] == 'WARNING'])}", use_container_width=True):
                    st.session_state.filter_status = "WARNING"
            with m4:
                if st.button("🔵 SHOW ALL", use_container_width=True):
                    st.session_state.filter_status = "ALL"

            df_filtered = df_working.copy()
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered["STATUS"] == st.session_state.filter_status]

            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found for the selected period.")
    else:
        st.warning("No equipment data available.")

# =========================================================
# 9. FOOTER (Letakkan di luar if/else)
# =========================================================
st.markdown(f"""
    <div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: {sidebar_bg}; text-align: center; padding: 10px; z-index: 9999; border-top: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(10px);">
        <p style="color: {text_color} !important;">© 2026 GreenFinder VTMS Dashboard. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)
