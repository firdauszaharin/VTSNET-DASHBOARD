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
    page_icon="📊"
)

# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(interval=300000, key="vts_refresh")

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def clean_status(series):
    return series.astype(str).str.strip().str.upper()

@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# =========================================================
# LOGIN
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:

    col1,col2,col3 = st.columns([1,2,1])

    with col2:

        st.title("🔒 VTSNET Project Access")

        pwd = st.text_input("Project Access Code", type="password")

        correct_password = st.secrets.get("PROJECT_PASSWORD")

        if st.button("Unlock Dashboard"):

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
        st.image("logo.png")

    dark_mode = st.toggle("Dark Mode")

    st.divider()

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# =========================================================
# THEME
# =========================================================
if dark_mode:
    plotly_theme="plotly_dark"
else:
    plotly_theme="plotly_white"

# =========================================================
# DATA SOURCE
# =========================================================
REPORT_URL="https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"

EQUIP_URL="https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"

SCHEDULE_URL="https://docs.google.com/spreadsheets/d/1h9_vOwZWTrXTWo1m907T9g23LW211qcjCOw03q2kc3I/export?format=csv"

df_report = load_data(REPORT_URL)
df_equip = load_data(EQUIP_URL)
df_schedule = load_data(SCHEDULE_URL)

# =========================================================
# SIDEBAR NAV
# =========================================================
menu = st.sidebar.radio(
"Select Category",
[
"📝 Maintenance Reports",
"⚙️ Equipment Status",
"📅 Staff Schedule"
])

# =========================================================
# HEADER
# =========================================================
msia_tz = pytz.timezone("Asia/Kuala_Lumpur")
now = datetime.now(msia_tz)

st.title("VTSNET Dashboard")
st.caption(f"Last Sync: {now.strftime('%H:%M:%S')}")

# =========================================================
# PAGE 1 MAINTENANCE REPORT
# =========================================================
if menu=="📝 Maintenance Reports":

    if df_report.empty:
        st.warning("No report data")
        st.stop()

    report_col = "REPORT CHECKLIST"
    status_col = "STATUS"

    # ================================
    # FILTER
    # ================================

    pm_options=[
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

    pm_filter = st.sidebar.selectbox("PM Checklist Filter", pm_options)

    staff_search = st.sidebar.text_input("Search Staff")

    df=df_report.copy()

    if pm_filter!="ALL":
        df=df[df[report_col].str.upper()==pm_filter.upper()]

    if staff_search:
        df=df[df["Name"].str.contains(staff_search,case=False,na=False)]

    # ================================
    # METRIC
    # ================================

    status = clean_status(df[status_col])

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Report",len(df))

    col2.metric("Approved",(status=="APPROVED").sum())

    col3.metric("Pending",(status!="APPROVED").sum())

    # ================================
    # CHART
    # ================================

    c1,c2 = st.columns(2)

    with c1:

        fig = px.pie(
        df,
        names=status_col,
        title="Approval Status",
        hole=0.5,
        template=plotly_theme)

        st.plotly_chart(fig,use_container_width=True)

    with c2:

        fig = px.histogram(
        df,
        x=report_col,
        color=status_col,
        template=plotly_theme)

        st.plotly_chart(fig,use_container_width=True)

    # ================================
    # TABLE
    # ================================

    st.subheader("Report List")

    st.dataframe(df,use_container_width=True)

# =========================================================
# PAGE 2 EQUIPMENT
# =========================================================
elif menu=="⚙️ Equipment Status":

    if df_equip.empty:
        st.warning("No equipment data")
        st.stop()

    st.subheader("Equipment Inventory")

    month_cols=[c for c in df_equip.columns if "202" in str(c)]

    month = st.selectbox("Select Month",month_cols)

    status = clean_status(df_equip[month])

    col1,col2,col3 = st.columns(3)

    col1.metric("OK",(status=="OK").sum())
    col2.metric("FAULTY",(status=="FAULTY").sum())
    col3.metric("MISSING",(status=="MISSING").sum())

    fig=px.pie(
    status.value_counts().reset_index(),
    names="index",
    values=month,
    template=plotly_theme)

    st.plotly_chart(fig,use_container_width=True)

    st.dataframe(df_equip,use_container_width=True)

# =========================================================
# PAGE 3 STAFF SCHEDULE
# =========================================================
elif menu=="📅 Staff Schedule":

    if df_schedule.empty:
        st.warning("No schedule data")
        st.stop()

    staff_col=df_schedule.columns[0]

    staff_list=["ALL"]+df_schedule[staff_col].dropna().unique().tolist()

    staff=st.sidebar.selectbox("Select Staff",staff_list)

    if staff!="ALL":
        df_schedule=df_schedule[df_schedule[staff_col]==staff]

    st.dataframe(df_schedule,use_container_width=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown(
"""
<hr>
<center>
© 2026 GreenFinder VTMS Dashboard
</center>
""",
unsafe_allow_html=True
)
