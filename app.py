import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import os
from streamlit_autorefresh import st_autorefresh

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="VTSNET Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(interval=300000, key="vts_refresh")  # 5 minit

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def find_column(df, candidate_names):
    if df.empty:
        return None
    normalized = {str(c).strip().upper(): c for c in df.columns}
    for name in candidate_names:
        key = str(name).strip().upper()
        if key in normalized:
            return normalized[key]
    return None


def clean_status_series(series):
    s = series.astype(str).str.strip().str.upper()
    s = s.replace({
        "": "UNKNOWN",
        "NAN": "UNKNOWN",
        "NONE": "UNKNOWN",
        "NULL": "UNKNOWN",
        "-": "UNKNOWN"
    })
    return s


def style_report_status(val):
    val = str(val).strip().upper()
    if val == "APPROVED":
        return "background-color:#d4edda;color:#000;font-weight:bold;"
    if val == "REJECTED":
        return "background-color:#f8d7da;color:#000;font-weight:bold;"
    if val in ["PENDING", "IN PROGRESS", "SUBMITTED"]:
        return "background-color:#fff3cd;color:#000;font-weight:bold;"
    return ""


def style_equipment_status(val):
    val = str(val).strip().upper()
    if val == "OK":
        return "background-color:#D4EDDA;color:#155724;font-weight:bold;"
    if val == "FAULTY":
        return "background-color:#FFF3CD;color:#856404;font-weight:bold;"
    if val == "MISSING":
        return "background-color:#F8D7DA;color:#721C24;font-weight:bold;"
    if val == "UNKNOWN":
        return "background-color:#E2E3E5;color:#383d41;font-weight:bold;"
    return ""


@st.cache_data(ttl=60)
def load_csv_data(url):
    try:
        df = pd.read_csv(url, on_bad_lines="skip")
        df.columns = df.columns.astype(str).str.strip()
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"Failed to load data: {e}"


# =========================================================
# LOGIN
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🔒 VTSNET Project Access")
        pwd = st.text_input("Project Access Code", type="password")

        correct_password = st.secrets.get("PROJECT_PASSWORD")
        if not correct_password:
            st.error("PROJECT_PASSWORD is not configured in Streamlit secrets.")
            st.stop()

        if st.button("Unlock Dashboard", use_container_width=True):
            if pwd == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)

    dark_mode = st.toggle("Dark Mode View", value=False)
    st.divider()

    if st.button("🔒 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# =========================================================
# THEME
# =========================================================
if dark_mode:
    plotly_theme = "plotly_dark"
    bg_style = "linear-gradient(135deg, #1a0a2e 0%, #2c3e50 100%)"
    sidebar_bg = "rgba(15,10,25,0.98)"
    text_color = "#FFFFFF"
    extra_css = """
    <style>
    .stApp, [data-testid="stSidebar"] *, .stMarkdown p, h1, h2, h3, label {
        color: #FFFFFF !important;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    [data-testid="stMetric"] {
        border: 1px solid rgba(255,255,255,0.2) !important;
        background: rgba(255,255,255,0.03) !important;
        border-radius: 14px !important;
        padding: 16px !important;
    }
    </style>
    """
else:
    plotly_theme = "plotly_white"
    bg_style = "radial-gradient(circle at top right, #f8faff, #eef2f7)"
    sidebar_bg = "rgba(255,255,255,0.92)"
    text_color = "#1e293b"
    extra_css = ""

st.markdown(extra_css, unsafe_allow_html=True)
st.markdown(
    f"""
    <style>
    .stApp {{
        background: {bg_style};
        color: {text_color};
    }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        backdrop-filter: blur(10px);
    }}
    .main .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 100px !important;
    }}
    footer {{
        visibility: hidden;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# DATA SOURCE
# =========================================================
REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1h9_vOwZWTrXTWo1m907T9g23LW211qcjCOw03q2kc3I/export?format=csv"

PDF_COL_NAME = "UPLOAD REPORT"

df_report, report_error = load_csv_data(REPORT_URL)
df_equip, equip_error = load_csv_data(EQUIP_URL)
df_schedule, schedule_error = load_csv_data(SCHEDULE_URL)

# =========================================================
# HEADER
# =========================================================
msia_tz = pytz.timezone("Asia/Kuala_Lumpur")
now_msia = datetime.now(msia_tz)

st.title("VTSNET Dashboard")
st.caption(f"Last Sync: {now_msia.strftime('%d-%m-%Y %H:%M:%S')}")

# =========================================================
# NAVIGATION
# =========================================================
menu = st.sidebar.radio(
    "Select Category",
    [
        "📝 Maintenance Reports",
        "⚙️ Equipment Status",
        "📅 Staff Schedule"
    ]
)

# =========================================================
# PAGE 1: MAINTENANCE REPORTS
# =========================================================
if menu == "📝 Maintenance Reports":
    st.subheader("📝 Maintenance Reports")

    if report_error:
        st.error(report_error)

    if df_report.empty:
        st.warning("No maintenance report data available.")
        st.stop()

    report_col = find_column(df_report, ["REPORT CHECKLIST"])
    status_col = find_column(df_report, ["STATUS"])
    staff_col = find_column(df_report, ["NAME", "Name", "STAFF NAME"])
    site_col = find_column(df_report, ["SITE", "STATION", "LOCATION"])
    pdf_col = find_column(df_report, [PDF_COL_NAME])

    pm_options = [
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
        "VTSNET/PM/Q4/5TH YEAR",
    ]

    st.sidebar.subheader("Maintenance Filter")
    pm_filter = st.sidebar.selectbox("📂 PM Checklist", pm_options)
    staff_search = st.sidebar.text_input("👤 Search Staff")
    report_search = st.sidebar.text_input("🔎 Search Report / Type")

    df = df_report.copy()

    if pm_filter != "ALL" and report_col:
        df = df[df[report_col].astype(str).str.strip().str.upper() == pm_filter.strip().upper()]

    if report_search and report_col:
        df = df[df[report_col].astype(str).str.contains(report_search, case=False, na=False)]

    if staff_search and staff_col:
        df = df[df[staff_col].astype(str).str.contains(staff_search, case=False, na=False)]

    if site_col:
        site_list = ["ALL SITES"] + sorted(df[site_col].dropna().astype(str).unique().tolist())
        selected_site = st.sidebar.selectbox("🏗️ Site", site_list)
        if selected_site != "ALL SITES":
            df = df[df[site_col].astype(str) == selected_site]

    if status_col:
        status_clean = clean_status_series(df[status_col])
    else:
        status_clean = pd.Series([], dtype="object")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Approved", int((status_clean == "APPROVED").sum()) if not status_clean.empty else 0)
    col3.metric("Rejected", int((status_clean == "REJECTED").sum()) if not status_clean.empty else 0)
    col4.metric("Pending", int((~status_clean.isin(["APPROVED", "REJECTED"])).sum()) if not status_clean.empty else 0)

    chart_left, chart_right = st.columns(2)

    with chart_left:
        if status_col and not df.empty:
            chart_df = df.copy()
            chart_df[status_col] = clean_status_series(chart_df[status_col])

            fig_pie = px.pie(
                chart_df,
                names=status_col,
                hole=0.55,
                title="Approval Overview",
                template=plotly_theme,
                color=status_col,
                color_discrete_map={
                    "APPROVED": "#2ecc71",
                    "REJECTED": "#e74c3c",
                    "PENDING": "#f1c40f",
                    "UNKNOWN": "#95a5a6"
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Status chart not available.")

    with chart_right:
        if report_col and status_col and not df.empty:
            chart_df = df.copy()
            chart_df[status_col] = clean_status_series(chart_df[status_col])

            fig_hist = px.histogram(
                chart_df,
                x=report_col,
                color=status_col,
                title="Reports by Type",
                template=plotly_theme,
                color_discrete_map={
                    "APPROVED": "#2ecc71",
                    "REJECTED": "#e74c3c",
                    "PENDING": "#f1c40f",
                    "UNKNOWN": "#95a5a6"
                }
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Report type chart not available.")

    if site_col and status_col and not df.empty:
        st.subheader("📍 Site Approval Summary")
        site_summary = df.copy()
        site_summary[status_col] = clean_status_series(site_summary[status_col])
        grouped_site = site_summary.groupby([site_col, status_col]).size().reset_index(name="count")

        fig_site = px.bar(
            grouped_site,
            x=site_col,
            y="count",
            color=status_col,
            barmode="group",
            template=plotly_theme,
            title="Status by Site",
            color_discrete_map={
                "APPROVED": "#2ecc71",
                "REJECTED": "#e74c3c",
                "PENDING": "#f1c40f",
                "UNKNOWN": "#95a5a6"
            }
        )
        st.plotly_chart(fig_site, use_container_width=True)

    st.subheader("📋 Report Tracking Status")

    try:
        styled_df = df.style
        if status_col:
            styled_df = styled_df.map(style_report_status, subset=[status_col])

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
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True)

# =========================================================
# PAGE 2: EQUIPMENT STATUS
# =========================================================
elif menu == "⚙️ Equipment Status":
    st.subheader("⚙️ Equipment Status")

    if equip_error:
        st.error(equip_error)

    if df_equip.empty:
        st.warning("No equipment data available.")
        st.stop()

    month_keywords = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    month_cols = [
        c for c in df_equip.columns
        if "REMARK" not in str(c).upper() and (
            any(yr in str(c) for yr in ["2025", "2026", "2027"]) or
            any(m in str(c).upper() for m in month_keywords)
        )
    ]

    site_col = find_column(df_equip, ["SITE"])
    type_col = find_column(df_equip, ["TYPE"])
    equip_col = find_column(df_equip, ["EQUIPMENT", "NAME"])
    serial_col = find_column(df_equip, ["SERIAL NO", "SERIAL NUMBER"])
    ip_col = find_column(df_equip, ["IP ADDRESS", "IP"])

    if not month_cols:
        st.warning("No valid month columns detected in equipment sheet.")
        st.stop()

    col_a, col_b = st.columns(2)
    with col_a:
        selected_month = st.selectbox("📅 Select Month", month_cols, index=0)

    df_work = df_equip.copy()

    if site_col:
        site_list = ["ALL SITES"] + sorted(df_work[site_col].dropna().astype(str).unique().tolist())
        with col_b:
            selected_site = st.selectbox("🏗️ Select Site", site_list)
        if selected_site != "ALL SITES":
            df_work = df_work[df_work[site_col].astype(str) == selected_site]

    status_series = clean_status_series(df_work[selected_month])

    eq1, eq2, eq3, eq4 = st.columns(4)
    eq1.metric("OK", int((status_series == "OK").sum()))
    eq2.metric("FAULTY", int((status_series == "FAULTY").sum()))
    eq3.metric("MISSING", int((status_series == "MISSING").sum()))
    eq4.metric("TOTAL", len(df_work))

    chart1, chart2 = st.columns([0.4, 0.6])

    with chart1:
        pie_df = status_series.value_counts().reset_index()
        pie_df.columns = ["Status", "Count"]

        fig_eq = px.pie(
            pie_df,
            names="Status",
            values="Count",
            hole=0.55,
            template=plotly_theme,
            title="Equipment Status Overview",
            color="Status",
            color_discrete_map={
                "OK": "#2ecc71",
                "FAULTY": "#f1c40f",
                "MISSING": "#e74c3c",
                "UNKNOWN": "#95a5a6"
            }
        )
        st.plotly_chart(fig_eq, use_container_width=True)

    with chart2:
        if type_col and not df_work.empty:
            temp_df = df_work.copy()
            temp_df[selected_month] = clean_status_series(temp_df[selected_month])
            grouped = temp_df.groupby([type_col, selected_month]).size().reset_index(name="count")

            fig_type = px.bar(
                grouped,
                x=type_col,
                y="count",
                color=selected_month,
                template=plotly_theme,
                barmode="group",
                title="Analysis by Equipment Type",
                color_discrete_map={
                    "OK": "#2ecc71",
                    "FAULTY": "#f1c40f",
                    "MISSING": "#e74c3c",
                    "UNKNOWN": "#95a5a6"
                }
            )
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.info("Equipment type analysis not available.")

    st.subheader("📦 Inventory Asset List")

    filter_col1, filter_col2 = st.columns([0.4, 0.6])
    with filter_col1:
        status_filter = st.selectbox("Filter Status", ["ALL", "OK", "FAULTY", "MISSING", "UNKNOWN"])
    with filter_col2:
        search_eq = st.text_input("🔍 Quick Search (SN, Name, IP)")

    df_filtered = df_work.copy()
    filtered_status = clean_status_series(df_filtered[selected_month])

    if status_filter != "ALL":
        df_filtered = df_filtered[filtered_status == status_filter]
        filtered_status = clean_status_series(df_filtered[selected_month])

    if search_eq:
        mask = df_filtered.astype(str).apply(
            lambda col: col.str.contains(search_eq, case=False, na=False)
        ).any(axis=1)
        df_filtered = df_filtered[mask]

    display_cols = []
    for c in [site_col, type_col, equip_col, serial_col, ip_col]:
        if c and c not in display_cols:
            display_cols.append(c)

    if selected_month not in display_cols:
        display_cols.append(selected_month)

    if not display_cols:
        display_cols = df_filtered.columns.tolist()

    try:
        styled_eq = df_filtered[display_cols].style.map(
            style_equipment_status,
            subset=[selected_month]
        )
        st.dataframe(styled_eq, use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)

# =========================================================
# PAGE 3: STAFF SCHEDULE
# =========================================================
elif menu == "📅 Staff Schedule":
    st.subheader("📅 Staff Schedule")

    if schedule_error:
        st.error(schedule_error)

    if df_schedule.empty:
        st.warning("No staff schedule data available.")
        st.stop()

    staff_col = None
    for c in df_schedule.columns:
        c_up = str(c).upper()
        if "NAME" in c_up or "STAF" in c_up or "STAFF" in c_up:
            staff_col = c
            break

    if staff_col is None:
        staff_col = df_schedule.columns[0]

    st.sidebar.subheader("Schedule Filter")
    staff_list = ["ALL STAFF"] + sorted(df_schedule[staff_col].dropna().astype(str).unique().tolist())
    selected_staff = st.sidebar.selectbox("👤 Select Staff", staff_list)

    df_sch = df_schedule.copy()
    if selected_staff != "ALL STAFF":
        df_sch = df_sch[df_sch[staff_col].astype(str) == selected_staff]

    st.metric("Total Schedule Rows", len(df_sch))
    st.dataframe(df_sch, use_container_width=True, hide_index=True)
    st.success(f"✅ Schedule updated live (Last sync: {datetime.now(msia_tz).strftime('%H:%M:%S')})")

# =========================================================
# FOOTER
# =========================================================
st.markdown(
    f"""
    <div style="
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: {sidebar_bg};
        text-align: center;
        padding: 10px;
        z-index: 9999;
        border-top: 1px solid rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    ">
        <p style="color: {text_color} !important; margin: 0;">
            © 2026 GreenFinder VTMS Dashboard. All rights reserved.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
