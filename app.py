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

    custom_css = """
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

st.markdown(custom_css, unsafe_allow_html=True)
st.markdown(
    f"""
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
    footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 6. HELPER FUNCTIONS
# =========================================================
def color_status(val):
    val = str(val).strip().upper()
    if val == "APPROVED":
        return "background-color: #d4edda; color: #000000; font-weight: bold;"
    if val == "REJECTED":
        return "background-color: #f8d7da; color: #000000; font-weight: bold;"
    return ""


def color_equipment_status(val):
    val = str(val).strip().upper()
    if val == "OK":
        return "background-color: #D4EDDA; color: #155724;"
    if val == "MISSING":
        return "background-color: #F8D7DA; color: #721C24;"
    if val == "FAULTY":
        return "background-color: #FFF3CD; color: #856404;"
    return ""


def find_col(df, keyword):
    return next((c for c in df.columns if keyword.upper() in c.upper()), None)


def find_first_matching_col(df, candidates):
    for candidate in candidates:
        match = next((c for c in df.columns if c.strip().upper() == candidate.strip().upper()), None)
        if match:
            return match
    return None


def clean_status_series(series):
    return series.astype(str).str.strip().str.upper()


def extract_pm_options(df):
    """
    Ambil checklist PM auto dari data.
    Cari dalam ID DOCUMENT dan REPORT CHECKLIST.
    """
    values = []

    id_col = find_col(df, "ID DOCUMENT")
    checklist_col = find_col(df, "REPORT CHECKLIST")

    pattern = re.compile(r"VTSNET\s*/\s*PM\s*/\s*Q[1-4]\s*/\s*[2-5](?:ND|RD|TH)\s*YEAR", re.IGNORECASE)

    for col in [id_col, checklist_col]:
        if col and col in df.columns:
            for val in df[col].dropna().astype(str):
                matches = pattern.findall(val.upper())
                for m in matches:
                    cleaned = re.sub(r"\s+", "", m.upper())
                    cleaned = cleaned.replace("VTSNET/PM/", "VTSNET/PM/")
                    cleaned = cleaned.replace("/Q", "/Q")
                    # Normalise back with slashes only
                    cleaned = cleaned.replace(" ", "")
                    values.append(cleaned)

    unique_values = sorted(set(values))
    return ["ALL"] + unique_values if unique_values else ["ALL"]


def build_quarter_from_month(selected_month):
    year_match = re.search(r"202\d", selected_month)
    curr_yr = year_match.group(0) if year_match else "2025"
    m_up = selected_month.upper()

    if any(m in m_up for m in ["JAN", "FEB", "MAR"]):
        q = "Q1"
    elif any(m in m_up for m in ["APR", "MAY", "MEI", "JUN"]):
        q = "Q2"
    elif any(m in m_up for m in ["JUL", "AUG", "SEP", "OGO"]):
        q = "Q3"
    else:
        q = "Q4"

    return q, curr_yr


@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines="skip")
        data.columns = data.columns.str.strip()
        return data
    except Exception:
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

st.title("VTSNET: Maintenance & Asset Lifecycle Tracker")

# =========================================================
# PAGE 1: MAINTENANCE REPORTS
# =========================================================
if menu_selection == "📝 Maintenance Reports":
    st.subheader("📝 Maintenance Reports")

    pm_checklist_options = extract_pm_options(df_raw) if not df_raw.empty else ["ALL"]

    with st.container():
        f1, f2, f3 = st.columns([1.5, 1, 1])

        with f1:
            selected_pm_checklist = st.selectbox("📂 PM Checklist Filter", pm_checklist_options)

        with f2:
            search_report = st.text_input("🔎 Search Site/Type (MET, VHF, etc):")

        with f3:
            search_staff = st.text_input("👤 Search Team / Staff Name:")

    st.divider()

    if not df_raw.empty:
        df = df_raw.copy()

        id_col = find_col(df, "ID DOCUMENT")
        checklist_col = find_col(df, "REPORT CHECKLIST")
        name_col = find_first_matching_col(df, ["TEAM DETAILS", "NAME"])
        status_col = find_col(df, "STATUS")
        pdf_col = find_first_matching_col(df, [PDF_COL])

        if selected_pm_checklist != "ALL":
            if id_col and checklist_col:
                df = df[
                    df[id_col].astype(str).str.upper().str.contains(selected_pm_checklist, na=False) |
                    df[checklist_col].astype(str).str.upper().str.contains(selected_pm_checklist, na=False)
                ]
            elif id_col:
                df = df[df[id_col].astype(str).str.upper().str.contains(selected_pm_checklist, na=False)]
            elif checklist_col:
                df = df[df[checklist_col].astype(str).str.upper().str.contains(selected_pm_checklist, na=False)]

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

        if search_staff and name_col:
            df = df[df[name_col].astype(str).str.contains(search_staff, case=False, na=False)]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric(
            "Approved ✅",
            len(df[df[status_col].astype(str).str.upper() == "APPROVED"]) if status_col else 0
        )
        m3.metric(
            "Pending ⏳",
            len(df[~df[status_col].astype(str).str.upper().isin(["APPROVED", "REJECTED"])]) if status_col else 0
        )

        c1, c2 = st.columns(2)

        with c1:
            if not df.empty and status_col:
                pie_df = df.copy()
                pie_df[status_col] = clean_status_series(pie_df[status_col])

                st.plotly_chart(
                    px.pie(
                        pie_df,
                        names=status_col,
                        hole=0.55,
                        title="Approval Overview",
                        color_discrete_map={"APPROVED": "#2ecc71", "REJECTED": "#e74c3c"},
                        template=plotly_theme
                    ),
                    use_container_width=True
                )
            else:
                st.info("No data for selected filter.")

        with c2:
            if not df.empty and checklist_col and status_col:
                hist_df = df.copy()
                hist_df[status_col] = clean_status_series(hist_df[status_col])

                st.plotly_chart(
                    px.histogram(
                        hist_df,
                        x=checklist_col,
                        color=status_col,
                        title="Reports by Type",
                        color_discrete_map={"APPROVED": "#2ecc71", "REJECTED": "#e74c3c"},
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
    else:
        st.warning("No maintenance report data available.")

# =========================================================
# PAGE 2: EQUIPMENT STATUS
# =========================================================
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")

        month_cols = [
            c for c in df_equip.columns
            if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()
        ]
        site_col = next((c for c in df_equip.columns if c.lower() == "site"), None)

        if month_cols:
            c1, c2 = st.columns(2)

            with c1:
                selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=0)

            df_working = df_equip.copy()
            selected_site = "ALL SITES"

            if site_col:
                unique_sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().astype(str).unique().tolist())
                with c2:
                    selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
                if selected_site != "ALL SITES":
                    df_working = df_working[df_working[site_col].astype(str) == selected_site]

            # Reset filter status bila month/site bertukar
            current_context = f"{selected_month}|{selected_site}"
            if st.session_state.get("equipment_filter_context") != current_context:
                st.session_state.filter_status = "ALL"
                st.session_state.equipment_filter_context = current_context

            st.divider()
            status_series = clean_status_series(df_working[selected_month])

            if "filter_status" not in st.session_state:
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
                df_filtered = df_filtered[
                    clean_status_series(df_filtered[selected_month]) == st.session_state.filter_status
                ]

            col_chart1, col_chart2 = st.columns([0.4, 0.6])

            with col_chart1:
                pie_df = status_series.value_counts().reset_index()
                pie_df.columns = ["Status", "Count"]

                fig_donut = px.pie(
                    pie_df,
                    names="Status",
                    values="Count",
                    hole=0.55,
                    template=plotly_theme,
                    title="Status Overall",
                    color="Status",
                    color_discrete_map={"OK": "#2ecc71", "FAULTY": "#f1c40f", "MISSING": "#e74c3c"}
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_chart2:
                type_col = next((c for c in df_filtered.columns if c.lower() == "type"), None)
                if type_col and not df_filtered.empty:
                    chart_df = df_filtered.copy()
                    chart_df[selected_month] = clean_status_series(chart_df[selected_month])

                    fig_type = px.bar(
                        chart_df.groupby([type_col, selected_month]).size().reset_index(name="count"),
                        x=type_col,
                        y="count",
                        color=selected_month,
                        template=plotly_theme,
                        title="Analysis by Type",
                        color_discrete_map={"OK": "#2ecc71", "FAULTY": "#f1c40f", "MISSING": "#e74c3c"},
                        barmode="group"
                    )
                    st.plotly_chart(fig_type, use_container_width=True)

            st.divider()
            st.subheader("📦 Inventory Asset List")

            search_eq = st.text_input("🔍 Quick Search (SN, Name, IP):", key="search_eq_box")
            if search_eq:
                df_filtered = df_filtered[
                    df_filtered.astype(str).apply(
                        lambda x: x.str.contains(search_eq, case=False, na=False)
                    ).any(axis=1)
                ]

            q, curr_yr = build_quarter_from_month(selected_month)

            actual_remark_col = next(
                (c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper() and curr_yr in c.upper()),
                None
            )

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

            if not df_filtered.empty and display_cols:
                st.dataframe(
                    df_filtered[display_cols].style.map(
                        color_equipment_status,
                        subset=[selected_month] if selected_month in display_cols else None
                    ),
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.warning("No equipment data available.")

# =========================================================
# 9. FOOTER
# =========================================================
st.markdown(
    f"""
    <div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: {sidebar_bg}; text-align: center; padding: 10px; z-index: 9999; border-top: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(10px);">
        <p style="color: {text_color} !important;">© 2026 GreenFinder VTMS Dashboard. All rights reserved.</p>
    </div>
    """,
    unsafe_allow_html=True
)
