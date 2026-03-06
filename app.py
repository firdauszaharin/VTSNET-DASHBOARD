# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# ========= 1. PAGE CONFIGURATION =========
st.set_page_config(
    page_title="GreenFinder VTMS Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- MALAYSIA TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# ========= 2. GLOBAL CSS (GLASSMORPHISM) =========
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #020617, #020617, #111827);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        color: #f9fafb;
    }

    /* Sidebar glass */
    [data-testid="stSidebar"] {
        background: rgba(15,23,42,0.85) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(148,163,184,0.25);
    }

    /* Metric cards - floating glass */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,64,175,0.9)) !important;
        padding: 18px 20px !important;
        border-radius: 18px !important;
        box-shadow: 0 18px 45px rgba(15,23,42,0.70) !important;
        border: 1px solid rgba(148,163,184,0.45) !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-6px);
        box-shadow: 0 28px 70px rgba(59,130,246,0.45) !important;
    }

    /* Tabs - modern pill style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        padding: 0 18px;
        border-radius: 999px;
        background: rgba(15,23,42,0.6);
        border: 1px solid rgba(148,163,184,0.35);
        color: #e5e7eb;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #22c55e, #22c55e, #a3e635) !important;
        color: #020617 !important;
        font-weight: 700 !important;
        box-shadow: 0 14px 35px rgba(34,197,94,0.45);
    }

    /* Hide default menu/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Nice dataframe scrollbar */
    .stDataFrame div[role="grid"] {
        border-radius: 14px;
        overflow: hidden;
    }
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(148,163,184,0.7);
        border-radius: 999px;
    }

    /* Simple gradient title bar */
    .hero-card {
        background: linear-gradient(120deg, #22c55e, #22c55e, #0ea5e9);
        padding: 20px 24px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 22px 55px rgba(15,23,42,0.7);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-title {
        color: #ecfdf5;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.04em;
    }
    .hero-subtitle {
        color: rgba(240,253,250,0.9);
        font-size: 15px;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ========= 3. DATA LINKS =========
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv&gid=296214979"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/export?format=csv&gid=416421947"
PDF_COL = "UPLOAD REPORT"

# AIS sheet (anda perlu set gid yang betul untuk setiap sheet)
# buat sementara, saya letak gid=0 utk kedua-dua; tukar ikut sheet sebenar anda
AISVDES_URL = "https://docs.google.com/spreadsheets/d/1HQUV7NXuhAKtKW-weSwAmhIMOde8CZM8XiTiaF1P7K4/export?format=csv&gid=0"
AISVTS_URL  = "https://docs.google.com/spreadsheets/d/1HQUV7NXuhAKtKW-weSwAmhIMOde8CZM8XiTiaF1P7K4/export?format=csv&gid=0"

# ========= 4. DATA LOAD FUNCTIONS =========
@st.cache_data(ttl=60)
def load_data(url: str) -> pd.DataFrame:
    try:
        data = pd.read_csv(url, on_bad_lines="skip")
        data.columns = data.columns.str.strip()
        time_col = next(
            (c for c in data.columns if any(x in c.lower() for x in ["timestamp", "time", "date", "tarikh"])),
            None,
        )
        if time_col:
            data[time_col] = pd.to_datetime(data[time_col], errors="coerce")
            data["Year"] = data[time_col].dt.year
        else:
            data["Year"] = None
        return data
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_ais_status(url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(url, on_bad_lines="skip")
        df.columns = df.columns.str.strip()
        time_col = next(
            (c for c in df.columns if any(x in c.lower() for x in ["timestamp", "time", "date", "tarikh"])),
            None,
        )
        if time_col:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)
df_aisvdes = load_ais_status(AISVDES_URL)
df_aisvts = load_ais_status(AISVTS_URL)

# ========= 5. ICON MAP UNTUK MAINTENANCE =========
icon_map = {
    "MET REPORT": "https://cdn-icons-png.flaticon.com/512/1146/1146869.png",
    "OPERATOR WORKSTATION": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "WALL DISPLAY REPORT": "https://cdn-icons-png.flaticon.com/512/1035/1035688.png",
    "VHF PTP FLOOR 8": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "SERVER ROOM REPORT (PTP/LPJ)": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png",
}

if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None

# ========= 6. SIDEBAR =========
with st.sidebar:
    # Logo
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("### GreenFinder VTMS")

    st.divider()
    st.markdown(f"🕒 **Last Sync (MYT):** {waktu_msia.strftime('%d-%m-%Y %H:%M:%S')}")
    st.divider()

    st.markdown("### 🔍 Global Filters (Reports)")
    if not df_raw.empty and "Year" in df_raw.columns:
        year_list = sorted(df_raw["Year"].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Select Year:", ["All Years"] + [int(t) for t in year_list])
    else:
        sel_year = st.selectbox("📅 Select Year:", ["All Years"])

    search_report = st.text_input("🔎 Report Type:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Staff Name:")

    st.divider()
    st.link_button(
        "📂 Open Drive Folder",
        "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4jUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy",
        use_container_width=True,
    )

# ========= 7. HEADER (BRANDING + CLOCK) =========
col_logo, col_title, col_clock = st.columns([1, 3, 2])

with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=False)

with col_title:
    st.markdown(
        "<div class='hero-card'>"
        "<div>"
        "<h1 class='hero-title'>GreenFinder VTMS Admin &amp; Inventory</h1>"
        "<p class='hero-subtitle'>Electronic Data Management System &mdash; Going Forward</p>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with col_clock:
    st.write("")
    st.write("")
    st.markdown(
        f"**Malaysia Time (MYT)**  \n`{waktu_msia.strftime('%d %b %Y %H:%M:%S')}`"
    )

# ========= 8. TABS =========
tab1, tab2, tab3 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status", "📡 AIS Monitoring"])

# --- TAB 1: MAINTENANCE REPORTS ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()

        if sel_year != "All Years":
            df = df[df["Year"] == sel_year]
        if search_report:
            if "REPORT CHECKLIST" in df.columns:
                df = df[df["REPORT CHECKLIST"].str.contains(search_report, case=False, na=False)]
        if search_staff:
            if "Name" in df.columns:
                df = df[df["Name"].str.contains(search_staff, case=False, na=False)]

        time_col = next(
            (c for c in df.columns if any(x in c.lower() for x in ["timestamp", "time", "date", "tarikh"])),
            None,
        )
        display_df = df.sort_values(by=time_col, ascending=False).reset_index(drop=True) if time_col else df.reset_index(drop=True)

        # Metric cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Reports", len(display_df))
        if "STATUS" in display_df.columns:
            m2.metric("Approved ✅", (display_df["STATUS"] == "APPROVED").sum())
            m3.metric("Rejected ❌", (display_df["STATUS"] == "REJECTED").sum())
            m4.metric("Pending ⏳", (~display_df["STATUS"].isin(["APPROVED", "REJECTED"])).sum())
        else:
            m2.metric("Approved ✅", 0)
            m3.metric("Rejected ❌", 0)
            m4.metric("Pending ⏳", 0)

        st.markdown("### 🎯 Maintenance Performance Overview")
        col_p, col_b = st.columns(2)
        if "STATUS" in display_df.columns:
            with col_p:
                fig_pie = px.pie(
                    display_df,
                    names="STATUS",
                    title="Approval Status Distribution",
                    hole=0.45,
                    color_discrete_map={"APPROVED": "#22c55e", "REJECTED": "#ef4444"},
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        if "REPORT CHECKLIST" in display_df.columns and "STATUS" in display_df.columns:
            with col_b:
                fig_hist = px.histogram(
                    display_df,
                    x="REPORT CHECKLIST",
                    color="STATUS",
                    title="Report Frequency by Type",
                    color_discrete_map={"APPROVED": "#22c55e", "REJECTED": "#ef4444"},
                )
                fig_hist.update_xaxes(categoryorder="category ascending")
                st.plotly_chart(fig_hist, use_container_width=True)

        st.divider()
        st.subheader("📋 Submitted Reports Record")

        def highlight_status(val):
            if val == "REJECTED":
                return "background-color: #F8D7DA; color: #721C24;"
            if val == "APPROVED":
                return "background-color: #D4EDDA; color: #155724;"
            return ""

        if "REPORT CHECKLIST" in display_df.columns:
            display_df.insert(
                0,
                "ICON",
                display_df["REPORT CHECKLIST"].map(icon_map).fillna(
                    "https://cdn-icons-png.flaticon.com/512/2991/2991108.png"
                ),
            )

        if "STATUS" in display_df.columns:
            styled_df = display_df.style.map(highlight_status, subset=["STATUS"])
        else:
            styled_df = display_df

        event = st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Type"),
                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄"),
            },
            on_select="rerun",
            selection_mode="single-row",
        )

        if len(event.selection.rows) > 0:
            st.session_state.selected_row_idx = event.selection.rows[0]

        if st.session_state.selected_row_idx is not None:
            idx = st.session_state.selected_row_idx
            if 0 <= idx < len(display_df):
                row = display_df.iloc[idx]
                link = row.get(PDF_COL, "")
                if isinstance(link, str) and "drive.google.com" in link:
                    match = re.search(r"[-\w]{25,}", link)
                    if match:
                        file_id = match.group()
                        st.markdown(
                            f"""
                            <iframe src="https://drive.google.com/file/d/{file_id}/preview"
                                    width="100%" height="600px" style="border-radius:16px;border:none;">
                            </iframe>
                            """,
                            unsafe_allow_html=True,
                        )

# --- TAB 2: EQUIPMENT STATUS ---
with tab2:
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]

        if month_cols:
            c_sel, _ = st.columns([0.4, 0.6])
            with c_sel:
                selected_month = st.selectbox(
                    "📅 Select Report Month:", month_cols, index=len(month_cols) - 1
                )

            st.divider()

            if selected_month in df_equip.columns:
                status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
                df_pie = df_equip.copy()
                df_pie[selected_month] = status_series

                me1, me2, me3 = st.columns(3)
                me1.metric("Equipment OK", (status_series == "OK").sum())
                me2.metric("Faulty ⚠️", (status_series == "FAULTY").sum())
                me3.metric("Missing ❌", (status_series == "MISSING").sum())

                st.markdown(f"### 🎯 Equipment Performance Overview ({selected_month})")

                col_left, col_right = st.columns(2)
                with col_left:
                    fig_donut = px.pie(
                        df_pie,
                        names=selected_month,
                        title="Condition Overview",
                        hole=0.55,
                        color_discrete_map={
                            "OK": "#22c55e",
                            "FAULTY": "#eab308",
                            "MISSING": "#ef4444",
                        },
                    )
                    fig_donut.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig_donut, use_container_width=True)

                with col_right:
                    if "Site" in df_pie.columns:
                        fig_site = px.histogram(
                            df_pie,
                            x="Site",
                            color=selected_month,
                            barmode="group",
                            title="Status by Location",
                            color_discrete_map={
                                "OK": "#22c55e",
                                "FAULTY": "#eab308",
                                "MISSING": "#ef4444",
                            },
                        )
                        fig_site.update_xaxes(categoryorder="category ascending")
                        st.plotly_chart(fig_site, use_container_width=True)

                if "Type" in df_pie.columns:
                    fig_type = px.histogram(
                        df_pie,
                        x="Type",
                        color=selected_month,
                        barmode="group",
                        title="Status by Equipment Category",
                        color_discrete_map={
                            "OK": "#22c55e",
                            "FAULTY": "#eab308",
                            "MISSING": "#ef4444",
                        },
                    )
                    fig_type.update_xaxes(categoryorder="category ascending")
                    st.plotly_chart(fig_type, use_container_width=True)

                st.divider()
                st.subheader("📦 Inventory Asset List")
                search_eq = st.text_input("🔍 Search Asset (SN, Name, Site):", key="search_eq_tab")

                essential_cols = ["Site", "Type", "Serial No", "IP Address", selected_month]
                df_eq_show = df_equip[[c for c in essential_cols if c in df_equip.columns]].copy()

                if search_eq:
                    df_eq_show = df_eq_show[
                        df_eq_show.astype(str).apply(
                            lambda x: x.str.contains(search_eq, case=False)
                        ).any(axis=1)
                    ]

                def eq_color(v):
                    v = str(v).upper()
                    if v == "OK":
                        return "background-color: #D4EDDA"
                    if v == "MISSING":
                        return "background-color: #F8D7DA"
                    if v == "FAULTY":
                        return "background-color: #FFF3CD"
                    return ""

                st.dataframe(
                    df_eq_show.style.map(eq_color, subset=[selected_month]),
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("Tiada kolum bulan 2025 / 2026 ditemui dalam sheet Equipment.")

# --- TAB 3: AIS MONITORING ---
with tab3:
    st.subheader("📡 AISVDES & AIS VTS Monitoring")

    if df_aisvdes.empty and df_aisvts.empty:
        st.info(
            "Tiada data AISVDES / AIS VTS dapat dibaca. "
            "Sila semak permission atau URL gid sheet AIS anda."
        )
    else:
        col1, col2 = st.columns(2)

        # AISVDES
        with col1:
            st.markdown("#### AISVDES Status")
            if not df_aisvdes.empty:
                # cuba cari kolum status
                status_col = next(
                    (c for c in df_aisvdes.columns if "status" in c.lower()), None
                )
                if status_col is None:
                    st.dataframe(df_aisvdes, use_container_width=True, hide_index=True)
                else:
                    s = df_aisvdes[status_col].astype(str).str.upper()
                    total_ok = (s == "OK").sum()
                    total_faulty = (s == "FAULTY").sum()
                    total_down = s.isin(["DOWN", "OFFLINE"]).sum()

                    m1, m2, m3 = st.columns(3)
                    m1.metric("OK", total_ok)
                    m2.metric("FAULTY", total_faulty)
                    m3.metric("DOWN/OFF", total_down)

                    def ais_color(v):
                        v = str(v).upper()
                        if v == "OK":
                            return "background-color: #D4EDDA; color:#155724"
                        if v == "FAULTY":
                            return "background-color: #FFF3CD; color:#856404"
                        if v in ["DOWN", "OFFLINE"]:
                            return "background-color: #F8D7DA; color:#721C24"
                        return ""

                    st.dataframe(
                        df_aisvdes.style.map(ais_color, subset=[status_col]),
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.warning("Tiada data AISVDES.")

        # AIS VTS
        with col2:
            st.markdown("#### AIS VTS Monitoring")
            if not df_aisvts.empty:
                status_col2 = next(
                    (c for c in df_aisvts.columns if "status" in c.lower()), None
                )
                if status_col2 is None:
                    st.dataframe(df_aisvts, use_container_width=True, hide_index=True)
                else:
                    s2 = df_aisvts[status_col2].astype(str).str.upper()
                    total_ok2 = (s2 == "OK").sum()
                    total_faulty2 = (s2 == "FAULTY").sum()
                    total_down2 = s2.isin(["DOWN", "OFFLINE"]).sum()

                    n1, n2, n3 = st.columns(3)
                    n1.metric("OK", total_ok2)
                    n2.metric("FAULTY", total_faulty2)
                    n3.metric("DOWN/OFF", total_down2)

                    def ais_color2(v):
                        v = str(v).upper()
                        if v == "OK":
                            return "background-color: #D4EDDA; color:#155724"
                        if v == "FAULTY":
                            return "background-color: #FFF3CD; color:#856404"
                        if v in ["DOWN", "OFFLINE"]:
                            return "background-color: #F8D7DA; color:#721C24"
                        return ""

                    st.dataframe(
                        df_aisvts.style.map(ais_color2, subset=[status_col2]),
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.warning("Tiada data AIS VTS.")

# ========= 9. SIMPLE FOOTER =========
st.markdown(
    "<p style='text-align:center; color:#9ca3af; margin-top:24px; font-size:12px;'>"
    "© 2025 GreenFinder VTMS Admin & Inventory Dashboard. All rights reserved."
    "</p>",
    unsafe_allow_html=True,
)
