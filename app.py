import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import os
import requests
from io import BytesIO
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
# 2. AUTO REFRESH
# =========================================================
st_autorefresh(interval=300000, key="vts_refresh")  # 5 minit

# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================
def find_column(df, candidate_names):
    """
    Cari nama column secara flexible (case-insensitive).
    """
    if df.empty:
        return None

    normalized = {str(c).strip().upper(): c for c in df.columns}
    for name in candidate_names:
        key = str(name).strip().upper()
        if key in normalized:
            return normalized[key]
    return None


def has_columns(df, candidate_names):
    """
    Check semua column wujud.
    """
    return all(find_column(df, [c]) is not None for c in candidate_names)


def color_status_report(val):
    val = str(val).strip().upper()
    if val == "APPROVED":
        return "background-color: #d4edda; color: #000000; font-weight: bold;"
    if val == "REJECTED":
        return "background-color: #f8d7da; color: #000000; font-weight: bold;"
    return ""


def color_status_equipment(val):
    val = str(val).strip().upper()
    if val == "OK":
        return "background-color: #D4EDDA; color: #155724; font-weight: bold;"
    elif val == "MISSING":
        return "background-color: #F8D7DA; color: #721C24; font-weight: bold;"
    elif val == "FAULTY":
        return "background-color: #FFF3CD; color: #856404; font-weight: bold;"
    elif val == "UNKNOWN":
        return "background-color: #E2E3E5; color: #383d41; font-weight: bold;"
    return ""


def clean_status_series(series):
    """
    Bersihkan status untuk chart / filter.
    """
    s = series.astype(str).str.strip().str.upper()
    s = s.replace({
        "": "UNKNOWN",
        "NAN": "UNKNOWN",
        "NONE": "UNKNOWN",
        "NULL": "UNKNOWN",
        "-": "UNKNOWN"
    })
    return s


@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines="skip")
        data.columns = data.columns.astype(str).str.strip()
        return data, None
    except Exception as e:
        return pd.DataFrame(), f"Failed to load CSV data: {e}"


@st.cache_data(ttl=300)
def load_excel_sch(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
        df.columns = df.columns.astype(str).str.strip()
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"⚠️ Ralat Teknikal semasa baca fail jadual: {e}"


# =========================================================
# 4. LOGIN SECURITY
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 VTSNET Project Access")
        pwd = st.text_input("Project Access Code:", type="password")

        # UPDATED: tiada fallback hardcoded
        correct_password = st.secrets.get("PROJECT_PASSWORD")

        if not correct_password:
            st.error("PROJECT_PASSWORD is not configured in Streamlit secrets.")
            st.stop()

        if st.button("Unlock Dashboard", use_container_width=True):
            if pwd == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong Password!")
    st.stop()

# =========================================================
# 5. SIDEBAR THEME / LOGOUT
# =========================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)

    dark_mode = st.toggle("Dark Mode View", value=False)
    st.divider()

    if st.button("🔒 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# =========================================================
# 6. THEME / CSS
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
        }
        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        hr {
            border-top: 2px solid rgba(255, 255, 255, 0.2) !important;
        }
        [data-testid="stMetric"] {
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border-radius: 12px !important;
            padding: 20px !important;
        }
        section[data-testid="stSidebar"] .stButton > button {
            color: #FFFFFF !important;
            background-color: rgba(255, 75, 75, 0.2) !important;
            border: 1px solid #ff4b4b !important;
        }
        </style>
    """
else:
    bg_style = "radial-gradient(circle at top right, #f8faff, #eef2f7)"
    sidebar_bg = "rgba(255, 255, 255, 0.9)"
    text_color = "#1e293b"
    plotly_theme = "plotly_white"
    custom_css = ""

st.markdown(custom_css, unsafe_allow_html=True)
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
    h1 {{
        margin-top: -20px !important;
        padding-top: 0px !important;
    }}
    footer {{
        visibility: hidden;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 7. DATA LOAD
# =========================================================
msia_tz = pytz.timezone("Asia/Kuala_Lumpur")
waktu_msia = datetime.now(msia_tz)

SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
PDF_COL_NAME = "UPLOAD REPORT"

df_raw, report_error = load_data(SHEET_REPORT_URL)
df_equip, equip_error = load_data(SHEET_EQUIP_URL)

# =========================================================
# 8. SIDEBAR NAVIGATION
# =========================================================
menu_selection = st.sidebar.radio(
    "Select Category:",
    ["📝 Maintenance Reports", "⚙️ Equipment Status", "📅 Staff Schedule"]
)
st.sidebar.divider()
st.sidebar.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

st.title("VTSNET: Tracker")

# =========================================================
# PAGE 1: MAINTENANCE REPORTS
# =========================================================
if menu_selection == "📝 Maintenance Reports":
    search_report = st.sidebar.text_input("🔎 Search Site/Type (MET, VHF, etc):")
    search_staff = st.sidebar.text_input("👤 Search Staff Name:")

    if report_error:
        st.error(report_error)

    if not df_raw.empty:
        df = df_raw.copy()

        report_checklist_col = find_column(df, ["REPORT CHECKLIST"])
        name_col = find_column(df, ["Name", "NAME", "Staff Name"])
        status_col = find_column(df, ["STATUS"])
        pdf_col = find_column(df, [PDF_COL_NAME])

        # Filter
        if search_report and report_checklist_col:
            df = df[df[report_checklist_col].astype(str).str.contains(search_report, case=False, na=False)]

        if search_staff and name_col:
            df = df[df[name_col].astype(str).str.contains(search_staff, case=False, na=False)]

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))

        if status_col:
            status_clean = clean_status_series(df[status_col])
            m2.metric("Approved ✅", int((status_clean == "APPROVED").sum()))
            m3.metric("Pending ⏳", int((~status_clean.isin(["APPROVED", "REJECTED"])).sum()))
        else:
            m2.metric("Approved ✅", 0)
            m3.metric("Pending ⏳", 0)
            st.warning("Column STATUS not found in report data.")

        # Charts
        if status_col and report_checklist_col and not df.empty:
            chart_df = df.copy()
            chart_df[status_col] = clean_status_series(chart_df[status_col])

            c1, c2 = st.columns(2)
            with c1:
                fig_pie = px.pie(
                    chart_df,
                    names=status_col,
                    hole=0.55,
                    title="Approval Overview",
                    color_discrete_map={
                        "APPROVED": "#2ecc71",
                        "REJECTED": "#e74c3c",
                        "PENDING": "#f1c40f",
                        "UNKNOWN": "#95a5a6"
                    },
                    template=plotly_theme
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                fig_hist = px.histogram(
                    chart_df,
                    x=report_checklist_col,
                    color=status_col,
                    title="Reports by Type",
                    color_discrete_map={
                        "APPROVED": "#2ecc71",
                        "REJECTED": "#e74c3c",
                        "PENDING": "#f1c40f",
                        "UNKNOWN": "#95a5a6"
                    },
                    template=plotly_theme
                )
                st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Chart tidak dapat dipaparkan kerana column penting tiada atau data kosong.")

        # Table
        st.subheader("📋 Report Tracking Status")

        try:
            if status_col:
                styled_df = df.style.map(color_status_report, subset=[status_col])
            else:
                styled_df = df

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
        except Exception as e:
            st.warning(f"Paparan table style fallback digunakan: {e}")
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No maintenance report data available.")

# =========================================================
# PAGE 2: EQUIPMENT STATUS
# =========================================================
elif menu_selection == "⚙️ Equipment Status":
    if equip_error:
        st.error(equip_error)

    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")

        # Flexible month detection
        month_keywords = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        month_cols = [
            c for c in df_equip.columns
            if "REMARK" not in str(c).upper() and (
                any(yr in str(c) for yr in ["2025", "2026", "2027"]) or
                any(m in str(c).upper() for m in month_keywords)
            )
        ]

        site_col = find_column(df_equip, ["Site", "SITE"])

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

            # UPDATED: reset filter status bila context bertukar
            current_filter_context = f"{selected_month}_{selected_site}"
            if st.session_state.get("filter_context") != current_filter_context:
                st.session_state.filter_status = "ALL"
                st.session_state.filter_context = current_filter_context

            st.divider()

            status_series = clean_status_series(df_working[selected_month])

            if "filter_status" not in st.session_state:
                st.session_state.filter_status = "ALL"

            ok_count = int((status_series == "OK").sum())
            faulty_count = int((status_series == "FAULTY").sum())
            missing_count = int((status_series == "MISSING").sum())

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                if st.button(f"🟢 OK: {ok_count}", use_container_width=True):
                    st.session_state.filter_status = "OK"
            with col_m2:
                if st.button(f"🟡 FAULTY: {faulty_count}", use_container_width=True):
                    st.session_state.filter_status = "FAULTY"
            with col_m3:
                if st.button(f"🔴 MISSING: {missing_count}", use_container_width=True):
                    st.session_state.filter_status = "MISSING"
            with col_m4:
                if st.button("🔵 SHOW ALL", use_container_width=True):
                    st.session_state.filter_status = "ALL"

            df_filtered = df_working.copy()
            filtered_status_series = clean_status_series(df_filtered[selected_month])

            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[filtered_status_series == st.session_state.filter_status]

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
                    color_discrete_map={
                        "OK": "#2ecc71",
                        "FAULTY": "#f1c40f",
                        "MISSING": "#e74c3c",
                        "UNKNOWN": "#95a5a6"
                    }
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_chart2:
                type_col = find_column(df_filtered, ["Type", "TYPE"])
                if type_col and not df_filtered.empty:
                    temp_df = df_filtered.copy()
                    temp_df[selected_month] = clean_status_series(temp_df[selected_month])

                    grouped = temp_df.groupby([type_col, selected_month]).size().reset_index(name="count")

                    fig_type = px.bar(
                        grouped,
                        x=type_col,
                        y="count",
                        color=selected_month,
                        template=plotly_theme,
                        title="Analysis by Type",
                        color_discrete_map={
                            "OK": "#2ecc71",
                            "FAULTY": "#f1c40f",
                            "MISSING": "#e74c3c",
                            "UNKNOWN": "#95a5a6"
                        },
                        barmode="group"
                    )
                    st.plotly_chart(fig_type, use_container_width=True)
                else:
                    st.info("Type analysis tidak tersedia.")

            st.divider()
            st.subheader("📦 Inventory Asset List")

            search_eq = st.text_input("🔍 Quick Search (SN, Name, IP):", key="search_eq_box")

            if search_eq:
                mask = df_filtered.astype(str).apply(
                    lambda col: col.str.contains(search_eq, case=False, na=False)
                ).any(axis=1)
                df_filtered = df_filtered[mask]

            display_candidates = ["Site", "Type", "Equipment", "Serial No", "IP Address"]
            actual_display = []

            for candidate in display_candidates:
                found = find_column(df_filtered, [candidate])
                if found and found not in actual_display:
                    actual_display.append(found)

            if selected_month in df_filtered.columns and selected_month not in actual_display:
                actual_display.append(selected_month)

            if not actual_display:
                actual_display = df_filtered.columns.tolist()

            try:
                styled_eq = df_filtered[actual_display].style.map(
                    color_status_equipment,
                    subset=[selected_month] if selected_month in actual_display else None
                )
                st.dataframe(styled_eq, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Paparan styled inventory gagal, fallback table digunakan: {e}")
                st.dataframe(df_filtered[actual_display], use_container_width=True, hide_index=True)
        else:
            st.warning("No valid month columns detected in equipment sheet.")
    else:
        st.warning("No equipment data available.")

# =========================================================
# PAGE 3: STAFF SCHEDULE
# =========================================================
elif menu_selection == "📅 Staff Schedule":
    st.subheader("📅 Staff Duty Schedule - JADUAL VTSAIS (OneDrive Live)")

    DIRECT_URL = "https://onedrive.live.com/download?resid=C3A2991B5C1E3D77&authkey=!AH89HlwbnBoZACA&em=2"

    df_sch, sch_error = load_excel_sch(DIRECT_URL)

    if sch_error:
        st.error(sch_error)

    if not df_sch.empty:
        staff_col = None
        for c in df_sch.columns:
            c_up = str(c).upper()
            if "NAME" in c_up or "STAF" in c_up or "STAFF" in c_up:
                staff_col = c
                break

        if staff_col is None:
            staff_col = df_sch.columns[0]

        staff_list = ["SEMUA STAF"] + sorted(df_sch[staff_col].dropna().astype(str).unique().tolist())

        st.sidebar.subheader("Carian Jadual")
        sel_staff = st.sidebar.selectbox("Pilih Nama Staf:", staff_list)

        df_display = df_sch.copy()
        if sel_staff != "SEMUA STAF":
            df_display = df_display[df_display[staff_col].astype(str) == sel_staff]

        st.dataframe(df_display, use_container_width=True, hide_index=True)
        st.success(f"✅ Jadual dikemaskini secara langsung (Last sync: {datetime.now(msia_tz).strftime('%H:%M:%S')})")
    else:
        st.warning("Jadual tidak dapat dipaparkan. Sila pastikan fail Excel di OneDrive tidak sedang dibuka (locked) atau link masih aktif.")

# =========================================================
# 9. FOOTER
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
