import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="VTSNET Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR: THEME & NAV ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.title("📌 VTSNET MENU")
    dark_mode = st.toggle("Dark Mode View", value=False)
    menu_selection = st.radio("Pilih Paparan:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
    st.divider()
    msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    st.markdown(f"🕒 **Last Sync:** {datetime.now(msia_tz).strftime('%H:%M:%S')}")

# --- DYNAMIC CSS (FIX TYPING VISIBILITY & UI) ---
text_color = "#FFFFFF" if dark_mode else "#1e293b"
bg_style = "radial-gradient(circle at top right, #1e272e, #0f172a)" if dark_mode else "radial-gradient(circle at top right, #f8faff, #eef2f7)"
card_bg = "#1e293b" if dark_mode else "white"
shadow = "0 10px 25px rgba(0,0,0,0.5)" if dark_mode else "0 10px 25px rgba(0,0,0,0.03)"
plotly_theme = "plotly_dark" if dark_mode else "plotly_white"

st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; color: {text_color}; font-family: 'Inter', sans-serif; }}
    input, select, textarea, [data-baseweb="select"] {{
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}
    label, .stWidgetLabel p {{ color: {text_color} !important; }}
    [data-testid="stMetric"] {{ 
        background: {card_bg} !important; 
        padding: 20px !important; 
        border-radius: 20px !important; 
        box-shadow: {shadow} !important; 
    }}
    [data-testid="stMetricValue"] {{ color: {text_color} !important; }}
    header[data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip() # Clean column names
        return data
    except Exception as e:
        return pd.DataFrame()

df_reports = load_data("https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv")
df_equip = load_data("https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    st.title("📝 Maintenance Service Dashboard")
    if not df_reports.empty:
        df_w = df_reports.copy()
        
        # Smart Column Finder (Elak KeyError)
        id_col = next((c for c in df_w.columns if 'ID' in c.upper()), None)
        name_col = next((c for c in df_w.columns if 'NAME' in c.upper() or 'NAMA' in c.upper()), None)
        type_col = next((c for c in df_w.columns if 'CHECKLIST' in c.upper()), 'REPORT CHECKLIST')
        status_col = next((c for c in df_w.columns if 'STATUS' in c.upper()), 'STATUS')

        # Filter UI
        c1, c2, c3 = st.columns(3)
        with c1: 
            ids = ["ALL IDs"] + sorted(df_w[id_col].astype(str).unique().tolist()) if id_col else ["ALL IDs"]
            sel_id = st.selectbox("🆔 Select ID:", ids)
        with c2: 
            staffs = ["ALL STAFF"] + sorted(df_w[name_col].dropna().unique().tolist()) if name_col else ["ALL STAFF"]
            sel_staff = st.selectbox("👤 Select Staff:", staffs)
        with c3: 
            search_txt = st.text_input("🔎 Search Site/Type:", placeholder="Search...")

        # Filter Logic
        if id_col and sel_id != "ALL IDs": df_w = df_w[df_w[id_col].astype(str) == sel_id]
        if name_col and sel_staff != "ALL STAFF": df_w = df_w[df_w[name_col] == sel_staff]
        if search_txt: df_w = df_w[df_w[type_col].str.contains(search_txt, case=False, na=False)]

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df_w))
        m2.metric("Approved ✅", len(df_w[df_w[status_col] == 'APPROVED']) if status_col in df_w.columns else 0)
        m3.metric("Pending ⏳", len(df_w[~df_w[status_col].isin(['APPROVED', 'REJECTED'])]) if status_col in df_w.columns else 0)

        # Chart
        st.plotly_chart(px.pie(df_w, names=status_col, hole=0.4, title="Report Status Distribution", 
                               template=plotly_theme, color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        
        # Table
        st.subheader("📋 Detailed Records")
        st.dataframe(df_w, use_container_width=True, hide_index=True)
    else: st.warning("Data report tidak dijumpai.")

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    st.title("⚙️ Inventory & Equipment Status")
    if not df_equip.empty:
        # Find Date Columns (2025/26/27)
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if 'SITE' in c.upper()), "Site")
        
        if month_cols:
            cs1, cs2 = st.columns(2)
            with cs1: sel_month = st.selectbox("📅 Select Month:", month_cols, index=len(month_cols)-1)
            with cs2: sel_site = st.selectbox("🏗️ Select Site:", ["ALL SITES"] + sorted(df_equip[site_col].dropna().unique().tolist()))
            
            df_eq_w = df_equip.copy()
            if sel_site != "ALL SITES": df_eq_w = df_eq_w[df_eq_w[site_col] == sel_site]

            # --- CHARTS SECTION ---
            st.markdown("### 📊 Performance Overview")
            gc1, gc2 = st.columns([0.4, 0.6])
            with gc1:
                st.plotly_chart(px.pie(df_eq_w, names=sel_month, hole=0.5, title=f"Status: {sel_month}",
                                       color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}, template=plotly_theme), use_container_width=True)
            with gc2:
                t_col = next((c for c in df_eq_w.columns if 'TYPE' in c.upper()), None)
                if t_col:
                    st.plotly_chart(px.histogram(df_eq_w, x=t_col, color=sel_month, barmode='group', title="Status by Type",
                                                 color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}, template=plotly_theme), use_container_width=True)

            st.divider()

            # --- BUTTON FILTER LOGIC ---
            status_series = df_eq_w[sel_month].astype(str).str.strip().str.upper()
            if 'f_stat' not in st.session_state: st.session_state.f_stat = "ALL"

            b1, b2, b3, b4 = st.columns(4)
            if b1.button(f"🟢 OK: {len(df_eq_w[status_series == 'OK'])}", use_container_width=True): st.session_state.f_stat = "OK"
            if b2.button(f"🟡 FAULTY: {len(df_eq_w[status_series == 'FAULTY'])}", use_container_width=True): st.session_state.f_stat = "FAULTY"
            if b3.button(f"🔴 MISSING: {len(df_eq_w[status_series == 'MISSING'])}", use_container_width=True): st.session_state.f_stat = "MISSING"
            if b4.button("🔵 SHOW ALL", use_container_width=True): st.session_state.f_stat = "ALL"

            df_asset = df_eq_w.copy()
            if st.session_state.f_stat != "ALL":
                df_asset = df_asset[df_asset[sel_month].astype(str).str.upper() == st.session_state.f_stat]

            # Quick Search
            q_search = st.text_input("🔍 Search SN/IP/Equipment:", key="q_search")
            if q_search:
                df_asset = df_asset[df_asset.astype(str).apply(lambda x: x.str.contains(q_search, case=False)).any(axis=1)]

            # --- REMARK QUARTER LOGIC ---
            m_up = sel_month.upper()
            year_match = re.search(r'202\d', sel_month)
            curr_yr = year_match.group(0) if year_match else "2025"
            if any(m in m_up for m in ['JAN', 'FEB', 'MAR']): q = "Q1"
            elif any(m in m_up for m in ['APR', 'MAY', 'JUN', 'MEI']): q = "Q2"
            elif any(m in m_up for m in ['JUL', 'AUG', 'SEP', 'OGO']): q = "Q3"
            else: q = "Q4"
            
            remark_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper() and curr_yr in c.upper()), None)

            # --- ASSET TABLE DISPLAY ---
            st.subheader(f"📦 Asset List ({st.session_state.f_stat})")
            main_cols = ["Site", "Type", "Equipment", "Serial No", "IP Address"]
            final_cols = [c for c in main_cols if c in df_asset.columns]
            if sel_month in df_asset.columns: final_cols.append(sel_month)
            if remark_col: final_cols.append(remark_col)

            st.dataframe(
                df_asset[final_cols].style.applymap(
                    lambda x: 'background-color: #d4edda; color: #155724;' if str(x).upper() == 'OK' else
                              ('background-color: #f8d7da; color: #721c24;' if str(x).upper() == 'MISSING' else
                               ('background-color: #fff3cd; color: #856404;' if str(x).upper() == 'FAULTY' else '')),
                    subset=[sel_month] if sel_month in final_cols else None
                ),
                use_container_width=True, hide_index=True
            )
    else: st.warning("Data equipment tidak dijumpai.")
