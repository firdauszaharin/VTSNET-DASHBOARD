import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import os
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
# 2. AUTO REFRESH (Setiap 5 Minit)
# =========================================================
st_autorefresh(interval=300000, key="vts_refresh")

# =========================================================
# 3. HELPER FUNCTIONS
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
    return ""

def clean_status_series(series):
    s = series.astype(str).str.strip().str.upper()
    s = s.replace({"": "UNKNOWN", "NAN": "UNKNOWN", "NONE": "UNKNOWN"})
    return s

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines="skip")
        data.columns = data.columns.astype(str).str.strip()
        return data, None
    except Exception as e:
        return pd.DataFrame(), f"Failed to load CSV: {e}"

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
        correct_password = st.secrets.get("PROJECT_PASSWORD", "vtsnet2026")
        
        if st.button("Unlock Dashboard", use_container_width=True):
            if pwd == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong Password!")
    st.stop()

# =========================================================
# 5. SIDEBAR & THEME
# =========================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    dark_mode = st.toggle("Dark Mode View", value=False)
    st.divider()
    if st.button("🔒 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

if dark_mode:
    bg_style, text_color, plotly_theme = "linear-gradient(135deg, #1a0a2e 0%, #2c3e50 100%)", "#FFFFFF", "plotly_dark"
    sidebar_bg = "rgba(15, 10, 25, 0.98)"
    custom_css = """<style>
        .stApp, [data-testid="stSidebar"] *, .stMarkdown p, h1, h2, h3, label { color: #FFFFFF !important; }
        [data-testid="stMetric"] { border: 1px solid rgba(255, 255, 255, 0.2); background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 15px; }
    </style>"""
else:
    bg_style, text_color, plotly_theme = "radial-gradient(circle at top right, #f8faff, #eef2f7)", "#1e293b", "plotly_white"
    sidebar_bg = "rgba(255, 255, 255, 0.9)"
    custom_css = ""

st.markdown(custom_css, unsafe_allow_html=True)
st.markdown(f"""<style>
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; }}
    footer {{ visibility: hidden; }}
</style>""", unsafe_allow_html=True)

# =========================================================
# 6. DATA SOURCE URLS
# =========================================================
msia_tz = pytz.timezone("Asia/Kuala_Lumpur")
waktu_msia = datetime.now(msia_tz)

SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
# Gunakan Google Sheet CSV Export untuk kestabilan jadual
SHEET_SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1h9_vOwZWTrXTWo1m907T9g23LW211qcjCOw03q2kc3I/export?format=csv"

df_raw, report_error = load_data(SHEET_REPORT_URL)
df_equip, equip_error = load_data(SHEET_EQUIP_URL)

# =========================================================
# 7. NAVIGATION
# =========================================================
menu_selection = st.sidebar.radio("Select Category:", ["📝 Maintenance Reports", "⚙️ Equipment Status", "📅 Staff Schedule"])
st.sidebar.divider()
st.sidebar.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

st.title("VTSNET: Tracker")

# =========================================================
# PAGE 1: MAINTENANCE REPORTS
# =========================================================
if menu_selection == "📝 Maintenance Reports":
    st.sidebar.subheader("🔍 Filter Options")
    search_staff = st.sidebar.text_input("👤 Search Staff Name:")
    
    pm_checklist_options = ["ALL"] + [f"VTSNET/PM/Q{q}/{y} YEAR" for y in ["2ND", "3RD", "4TH", "5TH"] for q in range(1,5)]
    selected_pm_checklist = st.sidebar.selectbox("📂 Filter PM Checklist:", pm_checklist_options)
    search_report = st.sidebar.text_input("🔎 Search Site/Type (MET, VHF, etc):")

    if not df_raw.empty:
        df = df_raw.copy()
        
        # Mapping Columns
        report_col = find_column(df, ["REPORT CHECKLIST"])
        name_col = find_column(df, ["Name", "NAME"])
        status_col = find_column(df, ["STATUS"])
        pdf_col = find_column(df, ["UPLOAD REPORT"])

        # Apply Filters
        if search_staff and name_col:
            df = df[df[name_col].astype(str).str.contains(search_staff, case=False, na=False)]
        if selected_pm_checklist != "ALL" and report_col:
            df = df[df[report_col].astype(str).str.contains(selected_pm_checklist, case=False, na=False)]
        if search_report and report_col:
            df = df[df[report_col].astype(str).str.contains(search_report, case=False, na=False)]

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        if status_col:
            s_clean = clean_status_series(df[status_col])
            m2.metric("Approved ✅", int((s_clean == "APPROVED").sum()))
            m3.metric("Pending ⏳", int((~s_clean.isin(["APPROVED", "REJECTED"])).sum()))

        # Table
        st.subheader("📋 Maintenance Report List")
        styled_df = df.style.map(color_status_report, subset=[status_col]) if status_col else df
        st.dataframe(styled_df, use_container_width=True, hide_index=True,
                     column_config={pdf_col: st.column_config.LinkColumn("Report", display_text="OPEN PDF 📄")} if pdf_col else {})

# =========================================================
# PAGE 2: EQUIPMENT STATUS
# =========================================================
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(m in str(c).upper() for m in ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"])]
        
        if month_cols:
            sel_month = st.selectbox("📅 Select Month:", month_cols)
            df_filtered = df_equip.copy()
            
            # Status Metrics
            status_s = clean_status_series(df_filtered[sel_month])
            c1, c2, c3 = st.columns(3)
            c1.metric("🟢 OK", int((status_s == "OK").sum()))
            c2.metric("🟡 FAULTY", int((status_s == "FAULTY").sum()))
            c3.metric("🔴 MISSING", int((status_s == "MISSING").sum()))
            
            # Table
            st.dataframe(df_filtered.style.map(color_status_equipment, subset=[sel_month]), use_container_width=True, hide_index=True)

# =========================================================
# PAGE 3: STAFF SCHEDULE
# =========================================================
elif menu_selection == "📅 Staff Schedule":
    st.subheader("📅 Staff Duty Schedule (Live)")
    df_sch, sch_err = load_data(SHEET_SCHEDULE_URL)
    
    if not df_sch.empty:
        staff_col = next((c for c in df_sch.columns if "NAME" in c.upper() or "STAF" in c.upper()), df_sch.columns[0])
        staff_list = ["SEMUA STAF"] + sorted(df_sch[staff_col].dropna().unique().tolist())
        sel_staff = st.sidebar.selectbox("Pilih Nama Staf:", staff_list)
        
        df_disp = df_sch.copy()
        if sel_staff != "SEMUA STAF":
            df_disp = df_disp[df_disp[staff_col] == sel_staff]
            
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        st.success("✅ Jadual VTSAIS berjaya dimuatkan dari Google Sheets.")
    else:
        st.warning("Jadual tidak dapat diakses.")

# =========================================================
# 8. FOOTER
# =========================================================
st.markdown(f"""<div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: {sidebar_bg}; text-align: center; padding: 10px; border-top: 1px solid rgba(0,0,0,0.1);">
    <p style="color: {text_color} !important; margin: 0;">© 2026 GreenFinder VTMS Dashboard. All rights reserved.</p>
</div>""", unsafe_allow_html=True)
