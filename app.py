import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# 1. SETUP & THEME
st.set_page_config(page_title="VTSNET Admin Dashboard", layout="wide", page_icon="📊")

with st.sidebar:
    st.title("📌 VTSNET MENU")
    dark_mode = st.toggle("Dark Mode View", value=False)
    menu_selection = st.radio("Pilih Paparan:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
    msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    st.markdown(f"🕒 **Last Sync:** {datetime.now(msia_tz).strftime('%H:%M:%S')}")

# --- CSS FIX (VISIBILITY & DARK MODE) ---
t_clr = "#FFFFFF" if dark_mode else "#1e293b"
bg_app = "radial-gradient(circle, #1e272e, #0f172a)" if dark_mode else "#f8faff"
card_bg = "#1e293b" if dark_mode else "white"
plotly_theme = "plotly_dark" if dark_mode else "plotly_white"

st.markdown(f"""
    <style>
    .stApp {{ background: {bg_app}; color: {t_clr}; }}
    input, select, textarea, [data-baseweb="select"] {{
        color: {t_clr} !important;
        -webkit-text-fill-color: {t_clr} !important;
    }}
    label, .stWidgetLabel p {{ color: {t_clr} !important; }}
    [data-testid="stMetric"] {{ background: {card_bg} !important; border-radius: 15px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
    div[data-baseweb="popover"] li {{ color: #1e293b !important; }}
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

df_reports = load_data("https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv")
df_equip = load_data("https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    st.title("📝 Maintenance Service Reports")
    if not df_reports.empty:
        df_w = df_reports.copy()
        id_col = next((c for c in df_w.columns if 'ID' in c.upper()), "ID")
        name_col = next((c for c in df_w.columns if 'NAME' in c.upper() or 'NAMA' in c.upper()), "Name")
        pdf_col = next((c for c in df_w.columns if 'UPLOAD' in c.upper() or 'REPORT' in c.upper() and 'CHECKLIST' not in c.upper()), "UPLOAD REPORT")
        
        c1, c2, c3 = st.columns(3)
        with c1: sel_id = st.selectbox("🆔 ID:", ["ALL IDs"] + sorted(df_w[id_col].astype(str).unique().tolist()))
        with c2: sel_staff = st.selectbox("👤 Staff:", ["ALL STAFF"] + sorted(df_w[name_col].dropna().unique().tolist()))
        with c3: search_txt = st.text_input("🔎 Search Site/Type:")

        if sel_id != "ALL IDs": df_w = df_w[df_w[id_col].astype(str) == sel_id]
        if sel_staff != "ALL STAFF": df_w = df_w[df_w[name_col] == sel_staff]
        if search_txt: df_w = df_w[df_w.astype(str).apply(lambda x: x.str.contains(search_txt, case=False)).any(axis=1)]

        st.plotly_chart(px.pie(df_w, names='STATUS', hole=0.4, title="Report Status", template=plotly_theme), use_container_width=True)
        st.dataframe(df_w, use_container_width=True, hide_index=True, column_config={pdf_col: st.column_config.LinkColumn("📄 View Report", display_text="Open PDF")})

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    st.title("⚙️ Inventory & Equipment Status")
    if not df_equip.empty:
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if 'SITE' in c.upper()), "Site")
        
        if month_cols:
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1: selected_month = st.selectbox("📅 Month:", month_cols, index=len(month_cols)-1)
            with c_sel2: sel_site = st.selectbox("🏗️ Site:", ["ALL SITES"] + sorted(df_equip[site_col].dropna().unique().tolist()))
            
            df_filtered = df_equip.copy()
            if sel_site != "ALL SITES": df_filtered = df_filtered[df_filtered[site_col] == sel_site]

            # --- CHART ---
            gc1, gc2 = st.columns([0.4, 0.6])
            with gc1:
                st.plotly_chart(px.pie(df_filtered, names=selected_month, hole=0.5, title=f"Status: {selected_month}",
                                       color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}, template=plotly_theme), use_container_width=True)
            with gc2:
                type_c = next((c for c in df_filtered.columns if 'TYPE' in c.upper()), "Type")
                st.plotly_chart(px.histogram(df_filtered, x=type_c, color=selected_month, barmode='group', title="Status by Type",
                                             color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}, template=plotly_theme), use_container_width=True)

            # --- BUTTON FILTERS ---
            status_series = df_filtered[selected_month].astype(str).str.strip().str.upper()
            if 'f_stat' not in st.session_state: st.session_state.f_stat = "ALL"
            
            b1, b2, b3, b4 = st.columns(4)
            if b1.button(f"🟢 OK: {len(df_filtered[status_series == 'OK'])}", use_container_width=True): st.session_state.f_stat = "OK"
            if b2.button(f"🟡 FAULTY: {len(df_filtered[status_series == 'FAULTY'])}", use_container_width=True): st.session_state.f_stat = "FAULTY"
            if b3.button(f"🔴 MISSING: {len(df_filtered[status_series == 'MISSING'])}", use_container_width=True): st.session_state.f_stat = "MISSING"
            if b4.button("🔵 SHOW ALL", use_container_width=True): st.session_state.f_stat = "ALL"

            if st.session_state.f_stat != "ALL":
                df_filtered = df_filtered[df_filtered[selected_month].astype(str).str.upper() == st.session_state.f_stat]

            # --- TABLE VIEW (IKUT KOD ASAL SEBIJI) ---
            st.divider()
            st.subheader(f"📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Carian Pantas (SN, Nama, IP):", key="search_eq_box")
            if search_eq:
                df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            year_match = re.search(r'202\d', selected_month)
            curr_yr = year_match.group(0) if year_match else "2025"
            m_up = selected_month.upper()
            if any(m in m_up for m in ['JAN', 'FEB', 'MAR']): q = "Q1"
            elif any(m in m_up for m in ['APR', 'MAY', 'MEI', 'JUN']): q = "Q2"
            elif any(m in m_up for m in ['JUL', 'AUG', 'SEP', 'OGO']): q = "Q3"
            else: q = "Q4"
            actual_remark_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper() and curr_yr in c.upper()), None)

            display_cols = []
            standard_cols = ["Site", "Type", "Equipment", "Serial No", "IP Address"]
            for col in standard_cols:
                match = next((c for c in df_filtered.columns if c.lower() == col.lower()), None)
                if match: display_cols.append(match)
            if selected_month in df_filtered.columns: display_cols.append(selected_month)
            if actual_remark_col: display_cols.append(actual_remark_col)

            if not df_filtered.empty:
                st.dataframe(
                    df_filtered[display_cols].style.map(
                        lambda x: 'background-color: #D4EDDA; color: #155724;' if str(x).upper() == 'OK' else 
                                  ('background-color: #F8D7DA; color: #721C24;' if str(x).upper() == 'MISSING' else 
                                   ('background-color: #FFF3CD; color: #856404;' if str(x).upper() == 'FAULTY' else '')), 
                        subset=[selected_month] if selected_month in display_cols else None
                    ), use_container_width=True, hide_index=True
                )
            else: st.info("Tiada rekod untuk paparan ini.")
