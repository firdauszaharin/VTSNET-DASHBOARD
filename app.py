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
# =========================
# SIMPLE MODERN LOGIN PAGE
# =========================

import hmac
from datetime import datetime, timedelta

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 10

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0

if "lockout_until" not in st.session_state:
    st.session_state.lockout_until = None


def is_locked_out():
    if st.session_state.lockout_until is None:
        return False
    return datetime.now() < st.session_state.lockout_until


# --- LOGIN PAGE ---
if not st.session_state.authenticated:

    st.markdown("""
    <style>
    .login-box {
        background: rgba(255,255,255,0.75);
        border-radius: 18px;
        padding: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        backdrop-filter: blur(10px);
        text-align: center;
    }

    .login-title {
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 8px;
        color: #1f2a44;
    }

    .login-sub {
        color: #5b6474;
        margin-bottom: 20px;
        font-size: 0.95rem;
    }

    div[data-testid="stButton"] > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg,#2563eb,#4f46e5) !important;
        color: white !important;
        height: 48px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1,1.4,1])

    with center:

        st.markdown('<div class="login-box">', unsafe_allow_html=True)

        st.markdown('<div class="login-title">🔐 VTSNET</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Vessel Traffic Monitoring Dashboard</div>', unsafe_allow_html=True)

        if is_locked_out():
            remaining = int((st.session_state.lockout_until - datetime.now()).total_seconds() // 60) + 1
            st.error(f"Too many failed attempts. Try again in {remaining} minute(s).")
            st.stop()

        pwd = st.text_input("Project Access Code", type="password")

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

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()
import hmac
from datetime import datetime, timedelta

# --- SECURITY SETTINGS ---
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 10

# --- SESSION INIT ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0

if "lockout_until" not in st.session_state:
    st.session_state.lockout_until = None


def is_locked_out():
    if st.session_state.lockout_until is None:
        return False
    return datetime.now() < st.session_state.lockout_until


# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🔒 VTSNET Project Access")

        if is_locked_out():
            remaining = int((st.session_state.lockout_until - datetime.now()).total_seconds() // 60) + 1
            st.error(f"Too many failed attempts. Try again in {remaining} minute(s).")
            st.stop()

        pwd = st.text_input("Project Access Code:", type="password")

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

# --- 3. THEME TOGGLE & LOGOUT ---
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
        header[data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
            color: white !important;
        }
        [data-testid="stDecoration"] {
            display: none;
        }
        div[data-testid="stVerticalBlock"] .stButton > button {
            color: #000000 !important;
            background-color: #FFFFFF !important;
            font-weight: 900 !important;
            border: 2px solid #FFFFFF !important;
            opacity: 1 !important;
        }
        div[data-testid="stVerticalBlock"] .stButton > button:hover {
            background-color: #f0f2f6 !important;
            color: #000000 !important;
            border: 2px solid #6c5ce7 !important;
        }
        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        hr {
            border-top: 2px solid rgba(162, 155, 254, 0.5) !important;
            margin: 20px 0 !important;
        }
        [data-testid="stMetric"] {
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        section[data-testid="stSidebar"] .stButton > button {
            color: #FFFFFF !important;
            background-color: rgba(255, 75, 75, 0.2) !important;
            border: 1px solid #ff4b4b !important;
        }
        </style>
    """
else:
    bg_style = "linear-gradient(135deg, #eef2f6 0%, #e3e8ee 100%)"
    sidebar_bg = "rgba(245, 247, 250, 0.96)"
    text_color = "#243447"
    plotly_theme = "plotly_white"

    custom_dark_css = """
        <style>
        .stApp, .stMarkdown p, h1, h2, h3, label {
            color: #243447 !important;
        }
        header[data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }
        [data-testid="stDecoration"] {
            display: none;
        }
        [data-testid="stMetric"] {
            border: 1px solid rgba(36, 52, 71, 0.08) !important;
            background: rgba(255, 255, 255, 0.60) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        [data-testid="stMetricValue"] {
            color: #243447 !important;
            -webkit-text-fill-color: #243447 !important;
            font-weight: 700 !important;
        }
        hr {
            border-top: 1px solid rgba(36, 52, 71, 0.12) !important;
            margin: 20px 0 !important;
        }
        div[data-testid="stVerticalBlock"] .stButton > button {
            background-color: #ffffff !important;
            color: #243447 !important;
            border: 1px solid rgba(36, 52, 71, 0.15) !important;
            font-weight: 700 !important;
        }
        div[data-testid="stVerticalBlock"] .stButton > button:hover {
            background-color: #f2f4f7 !important;
            color: #243447 !important;
            border: 1px solid #7c8ea3 !important;
        }
        section[data-testid="stSidebar"] .stButton > button {
            color: #243447 !important;
            background-color: rgba(255,255,255,0.7) !important;
            border: 1px solid rgba(36, 52, 71, 0.15) !important;
        }
        </style>
    """

st.markdown(custom_dark_css, unsafe_allow_html=True)
st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        backdrop-filter: blur(10px);
    }}
    .main .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 100px !important;
    }}
    h1 {{
        margin-top: -40px !important;
        padding-top: 0px !important;
    }}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPER FUNCTIONS ---
def color_status(val):
    val = str(val).strip().upper()
    if val == 'APPROVED':
        return 'background-color: #d4edda; color: #000000; font-weight: bold;'
    if val == 'REJECTED':
        return 'background-color: #f8d7da; color: #000000; font-weight: bold;'
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
    st.subheader("📝 Maintenance Reports")

    pm_checklist_options = [
        "ALL",
        "VTSNET/PM/Q1/2ND YEAR",
        "VTSNET/PM/Q2/2ND YEAR",
        "VTSNET/PM/Q3/2ND YEAR",
        "VTSNET/PM/Q4/2ND YEAR",
        "VTSNET/PM/Q1/3RD YEAR",
        "VTSNET/PM/Q2/3RD YEAR",
        "VTSNET/PM/Q3/3RD YEAR",
        "VTSNET/PM/Q4/3RD YEAR",
        "VTSNET/PM/Q1/4TH YEAR",
        "VTSNET/PM/Q2/4TH YEAR",
        "VTSNET/PM/Q3/4TH YEAR",
        "VTSNET/PM/Q4/4TH YEAR",
        "VTSNET/PM/Q1/5TH YEAR",
        "VTSNET/PM/Q2/5TH YEAR",
        "VTSNET/PM/Q3/5TH YEAR",
        "VTSNET/PM/Q4/5TH YEAR"
    ]

    with st.container():
        f1, f2, f3 = st.columns([1.5, 1, 1])

        with f1:
            selected_pm_checklist = st.selectbox(
                "📂 PM Checklist Filter",
                pm_checklist_options
            )

        with f2:
            search_report = st.text_input("🔎 Search Site/Type (MET, VHF, etc):")

        with f3:
            search_staff = st.text_input("👤 Search Staff Name:")

    st.divider()

    if not df_raw.empty:
        df = df_raw.copy()

        id_col = find_col(df, "ID DOCUMENT")
        checklist_col = find_col(df, "REPORT CHECKLIST")
        name_col = next(
    (c for c in df.columns if c.strip().upper() in ["TEAM DETAILS", "NAME"]),
    None
)
        status_col = find_col(df, "STATUS")
        pdf_col = next((c for c in df.columns if c.strip().upper() == PDF_COL.upper()), None)

        # FILTER PM CHECKLIST / ID DOCUMENT
        if selected_pm_checklist != "ALL":
            if id_col and checklist_col:
                df = df[
                    df[id_col].astype(str).str.upper().str.contains(selected_pm_checklist.strip().upper(), na=False) |
                    df[checklist_col].astype(str).str.upper().str.contains(selected_pm_checklist.strip().upper(), na=False)
                ]
            elif id_col:
                df = df[
                    df[id_col].astype(str).str.upper().str.contains(selected_pm_checklist.strip().upper(), na=False)
                ]
            elif checklist_col:
                df = df[
                    df[checklist_col].astype(str).str.upper().str.contains(selected_pm_checklist.strip().upper(), na=False)
                ]

        # SEARCH SITE / TYPE
        if search_report:
            if id_col and checklist_col:
                df = df[
                    df[id_col].astype(str).str.contains(search_report, case=False, na=False) |
                    df[checklist_col].astype(str).str.contains(search_report, case=False, na=False)
                ]
            elif id_col:
                df = df[df[id_col].astype(str).str.contains(search_report, case=False, na=False)]
            elif checklist_col:
                df = df[df[checklist_col].astype(str).str.contains(search_report, case=False, na=False)]

        # SEARCH STAFF
        if search_staff and name_col:
            df = df[df[name_col].astype(str).str.contains(search_staff, case=False, na=False)]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric(
            "Approved ✅",
            len(df[df[status_col].astype(str).str.upper() == 'APPROVED']) if status_col else 0
        )
        m3.metric(
            "Pending ⏳",
            len(df[~df[status_col].astype(str).str.upper().isin(['APPROVED', 'REJECTED'])]) if status_col else 0
        )

        c1, c2 = st.columns(2)
        with c1:
            if not df.empty and status_col:
                st.plotly_chart(
                    px.pie(
                        df,
                        names=status_col,
                        hole=0.55,
                        title="Approval Overview",
                        color_discrete_map={'APPROVED': '#2ecc71', 'REJECTED': '#e74c3c'},
                        template=plotly_theme
                    ),
                    use_container_width=True
                )
            else:
                st.info("No data for selected filter.")

        with c2:
            if not df.empty and checklist_col and status_col:
                st.plotly_chart(
                    px.histogram(
                        df,
                        x=checklist_col,
                        color=status_col,
                        title="Reports by Type",
                        color_discrete_map={'APPROVED': '#2ecc71', 'REJECTED': '#e74c3c'},
                        template=plotly_theme
                    ),
                    use_container_width=True
                )
            else:
                st.info("No data for selected filter.")

        st.subheader("📋 Report Tracking Status")
        styled_df = df.style.map(color_status, subset=[status_col]) if status_col else df

        column_config = {}
        if pdf_col:
            column_config[pdf_col] = st.column_config.LinkColumn(
                "Report File",
                display_text="OPEN PDF 📄"
            )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if c.lower() == 'site'), None)

        if month_cols:
            c1, c2 = st.columns(2)
            with c1:
                selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=0)

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
                if st.button(f"🟢 OK: {len(df_working[status_series == 'OK'])}", use_container_width=True):
                    st.session_state.filter_status = "OK"
            with col_m2:
                if st.button(f"🟡 FAULTY: {len(df_working[status_series == 'FAULTY'])}", use_container_width=True):
                    st.session_state.filter_status = "FAULTY"
            with col_m3:
                if st.button(f"🔴 MISSING: {len(df_working[status_series == 'MISSING'])}", use_container_width=True):
                    st.session_state.filter_status = "MISSING"
            with col_m4:
                if st.button("🔵 SHOW ALL", use_container_width=True):
                    st.session_state.filter_status = "ALL"

            df_filtered = df_working.copy()
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered[selected_month].astype(str).str.strip().str.upper() == st.session_state.filter_status]

            col_chart1, col_chart2 = st.columns([0.4, 0.6])
            with col_chart1:
                fig_donut = px.pie(
                    df_working,
                    names=selected_month,
                    hole=0.55,
                    template=plotly_theme,
                    title="Status Overall",
                    color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_chart2:
                type_col = next((c for c in df_filtered.columns if c.lower() == 'type'), None)
                if type_col and not df_filtered.empty:
                    fig_type = px.bar(
                        df_filtered.groupby([type_col, selected_month]).size().reset_index(name='count'),
                        x=type_col,
                        y='count',
                        color=selected_month,
                        template=plotly_theme,
                        title="Analysis by Type",
                        color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'},
                        barmode='group'
                    )
                    st.plotly_chart(fig_type, use_container_width=True)

            st.divider()
            st.subheader("📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Quick Search (SN, Name, IP):", key="search_eq_box")
            if search_eq:
                df_filtered = df_filtered[
                    df_filtered.astype(str).apply(lambda x: x.str.contains(search_eq, case=False, na=False)).any(axis=1)
                ]

            year_match = re.search(r'202\d', selected_month)
            curr_yr = year_match.group(0) if year_match else "2025"
            m_up = selected_month.upper()

            if any(m in m_up for m in ['JAN', 'FEB', 'MAR']):
                q = "Q1"
            elif any(m in m_up for m in ['APR', 'MAY', 'MEI', 'JUN']):
                q = "Q2"
            elif any(m in m_up for m in ['JUL', 'AUG', 'SEP', 'OGO']):
                q = "Q3"
            else:
                q = "Q4"

            actual_remark_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper() and curr_yr in c.upper()), None)

            display_cols = []
            standard_cols = ["Site", "Type", "Equipment", "Serial No", "IP Address"]
            for col in standard_cols:
                match = next((c for c in df_filtered.columns if c.lower() == col.lower()), None)
                if match:
                    display_cols.append(match)

            if selected_month in df_filtered.columns:
                display_cols.append(selected_month)
            if actual_remark_col:
                display_cols.append(actual_remark_col)

            if not df_filtered.empty:
                st.dataframe(
                    df_filtered[display_cols].style.map(
                        lambda x: 'background-color: #D4EDDA; color: #155724;' if str(x).upper() == 'OK' else
                        ('background-color: #F8D7DA; color: #721C24;' if str(x).upper() == 'MISSING' else
                         ('background-color: #FFF3CD; color: #856404;' if str(x).upper() == 'FAULTY' else '')),
                        subset=[selected_month] if selected_month in display_cols else None
                    ),
                    use_container_width=True,
                    hide_index=True
                )

# --- 8. FOOTER (GLOBAL) ---
st.markdown(f"""
    <div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: {sidebar_bg}; text-align: center; padding: 10px; z-index: 9999; border-top: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(10px);">
        <p style="color: {text_color} !important;">© 2026 GreenFinder VTMS Dashboard. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)
