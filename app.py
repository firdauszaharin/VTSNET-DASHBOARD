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
    st.title("📌 MENU")
    dark_mode = st.toggle("Dark Mode View", value=False)
    menu_selection = st.radio("Pilih Paparan:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
    st.divider()
    msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    waktu_msia = datetime.now(msia_tz)
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

# --- DYNAMIC CSS ---
text_color = "#FFFFFF" if dark_mode else "#1e293b"
bg_style = "radial-gradient(circle at top right, #1e272e, #0f172a)" if dark_mode else "radial-gradient(circle at top right, #f8faff, #eef2f7)"
card_bg = "#1e293b" if dark_mode else "white"
shadow = "0 10px 25px rgba(0,0,0,0.5)" if dark_mode else "0 10px 25px rgba(0,0,0,0.03)"
plotly_theme = "plotly_dark" if dark_mode else "plotly_white"

st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    input, select, [data-baseweb="select"] {{
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}
    [data-testid="stMetric"] {{ background: {card_bg} !important; padding: 20px !important; border-radius: 20px !important; box-shadow: {shadow} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        return data
    except: return pd.DataFrame()

df_reports = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    st.title("VTSNET Maintenance Dashboard")
    if not df_reports.empty:
        df_w = df_reports.copy()
        c1, c2, c3 = st.columns(3)
        with c1: sel_id = st.selectbox("🆔 ID:", ["ALL IDs"] + sorted(df_w['ID'].astype(str).unique().tolist()))
        with c2: sel_staff = st.selectbox("👤 Staff:", ["ALL STAFF"] + sorted(df_w['Name'].dropna().unique().tolist()))
        with c3: search_txt = st.text_input("🔎 Search Site/Type:")

        if sel_id != "ALL IDs": df_w = df_w[df_w['ID'].astype(str) == sel_id]
        if sel_staff != "ALL STAFF": df_w = df_w[df_w['Name'] == sel_staff]
        if search_txt: df_w = df_w[df_w['REPORT CHECKLIST'].str.contains(search_txt, case=False, na=False)]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df_w))
        m2.metric("Approved ✅", len(df_w[df_w['STATUS'] == 'APPROVED']) if 'STATUS' in df_w.columns else 0)
        m3.metric("Pending ⏳", len(df_w[~df_w['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df_w.columns else 0)

        st.plotly_chart(px.pie(df_w, names='STATUS', hole=0.4, title="Status Overview", template=plotly_theme, color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        st.dataframe(df_w, use_container_width=True, hide_index=True)

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    st.subheader("⚙️ Inventory & Equipment Status")
    if not df_equip.empty:
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if c.lower() == 'site'), "Site")
        
        if month_cols:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1: sel_month = st.selectbox("📅 Select Month:", month_cols, index=len(month_cols)-1)
            with col_sel2: sel_site = st.selectbox("🏗️ Select Site:", ["ALL SITES"] + sorted(df_equip[site_col].dropna().unique().tolist()))
            
            df_eq_w = df_equip.copy()
            if sel_site != "ALL SITES": df_eq_w = df_eq_w[df_eq_w[site_col] == sel_site]

            # --- CHARTS SECTION (NI YANG KAU CARI) ---
            st.markdown("### 📊 Performance Analysis")
            col_c1, col_c2 = st.columns([0.4, 0.6])
            
            with col_c1:
                fig_donut = px.pie(df_eq_w, names=sel_month, hole=0.5, title=f"Overall Status ({sel_month})",
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}, template=plotly_theme)
                st.plotly_chart(fig_donut, use_container_width=True)
            
            with col_c2:
                type_col = next((c for c in df_eq_w.columns if c.lower() == 'type'), None)
                if type_col:
                    fig_bar = px.histogram(df_eq_w, x=type_col, color=sel_month, barmode='group',
                                           title="Status by Equipment Type",
                                           color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}, template=plotly_theme)
                    st.plotly_chart(fig_bar, use_container_width=True)

            st.divider()

            # --- BUTTONS & TABLE ---
            status_series = df_eq_w[sel_month].astype(str).str.strip().str.upper()
            if 'filter_status' not in st.session_state: st.session_state.filter_status = "ALL"

            b1, b2, b3, b4 = st.columns(4)
            if b1.button(f"🟢 OK: {len(df_eq_w[status_series == 'OK'])}", use_container_width=True): st.session_state.filter_status = "OK"
            if b2.button(f"🟡 FAULTY: {len(df_eq_w[status_series == 'FAULTY'])}", use_container_width=True): st.session_state.filter_status = "FAULTY"
            if b3.button(f"🔴 MISSING: {len(df_eq_w[status_series == 'MISSING'])}", use_container_width=True): st.session_state.filter_status = "MISSING"
            if b4.button("🔵 SHOW ALL", use_container_width=True): st.session_state.filter_status = "ALL"

            df_asset = df_eq_w.copy()
            if st.session_state.filter_status != "ALL":
                df_asset = df_asset[df_asset[sel_month].astype(str).str.upper() == st.session_state.filter_status]

            # Remark Logic & Table Display
            m_up = sel_month.upper()
            if any(m in m_up for m in ['JAN', 'FEB', 'MAR']): q = "Q1"
            elif any(m in m_up for m in ['APR', 'MAY', 'JUN', 'MEI']): q = "Q2"
            elif any(m in m_up for m in ['JUL', 'AUG', 'SEP', 'OGO']): q = "Q3"
            else: q = "Q4"
            
            remark_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper()), None)
            display_cols = ["Site", "Type", "Equipment", "Serial No", "IP Address"]
            final_cols = [c for c in display_cols if c in df_asset.columns]
            if sel_month in df_asset.columns: final_cols.append(sel_month)
            if remark_col: final_cols.append(remark_col)

            st.dataframe(df_asset[final_cols].style.applymap(
                lambda x: 'background-color: #d4edda; color: #155724;' if str(x).upper() == 'OK' else
                          ('background-color: #f8d7da; color: #721c24;' if str(x).upper() == 'MISSING' else
                           ('background-color: #fff3cd; color: #856404;' if str(x).upper() == 'FAULTY' else '')),
                subset=[sel_month] if sel_month in final_cols else None
            ), use_container_width=True, hide_index=True)
