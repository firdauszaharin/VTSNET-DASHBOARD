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
    
    st.title("📌 DASHBOARD MENU")
    dark_mode = st.toggle("Dark Mode View", value=False)
    menu_selection = st.radio("Pilih Paparan:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
    st.divider()
    
    # Timezone Malaysia
    msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    waktu_msia = datetime.now(msia_tz)
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

# --- DYNAMIC CSS (FIX VISIBILITY & TYPING) ---
text_color = "#FFFFFF" if dark_mode else "#1e293b"
bg_style = "radial-gradient(circle at top right, #1e272e, #0f172a)" if dark_mode else "radial-gradient(circle at top right, #f8faff, #eef2f7)"
card_bg = "#1e293b" if dark_mode else "white"
shadow = "0 10px 25px rgba(0,0,0,0.5)" if dark_mode else "0 10px 25px rgba(0,0,0,0.03)"
plotly_theme = "plotly_dark" if dark_mode else "plotly_white"

st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; font-family: 'Inter', sans-serif; color: {text_color}; }}
    /* Fix tulisan dalam input box & selectbox supaya nampak masa menaip */
    input, select, textarea, [data-baseweb="select"] {{
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}
    label, .stWidgetLabel p {{ color: {text_color} !important; }}
    [data-testid="stMetric"] {{ background: {card_bg} !important; border-radius: 20px !important; box-shadow: {shadow} !important; }}
    [data-testid="stMetricValue"] {{ color: {text_color} !important; }}
    .stMarkdown p, h1, h2, h3, h4 {{ color: {text_color} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
PDF_COL = "UPLOAD REPORT"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        return data
    except: return pd.DataFrame()

df_reports = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

def color_status(val):
    if val == 'APPROVED': return 'background-color: #d4edda; color: #155724;'
    if val == 'REJECTED': return 'background-color: #f8d7da; color: #721c24;'
    return ''

st.title("VTSNET Management Dashboard")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    if not df_reports.empty:
        df_working = df_reports.copy()
        
        # --- FILTER AREA (DALAM COLUMNS) ---
        c1, c2, c3 = st.columns(3)
        with c1:
            id_list = ["ALL IDs"] + sorted(df_working['ID'].astype(str).unique().tolist()) if 'ID' in df_working.columns else ["ALL IDs"]
            selected_id = st.selectbox("🆔 Select Document ID:", id_list)
        with c2:
            staff_list = ["ALL STAFF"] + sorted(df_working['Name'].dropna().unique().tolist()) if 'Name' in df_working.columns else ["ALL STAFF"]
            selected_staff = st.selectbox("👤 Filter by Staff:", staff_list)
        with c3:
            search_manual = st.text_input("🔎 Search Site/Type:", placeholder="Type to filter...")

        # Apply Filters
        if selected_id != "ALL IDs":
            df_working = df_working[df_working['ID'].astype(str) == selected_id]
        if selected_staff != "ALL STAFF":
            df_working = df_working[df_working['Name'] == selected_staff]
        if search_manual:
            df_working = df_working[df_working['REPORT CHECKLIST'].str.contains(search_manual, case=False, na=False)]

        st.divider()

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df_working))
        m2.metric("Approved ✅", len(df_working[df_working['STATUS'] == 'APPROVED']) if 'STATUS' in df_working.columns else 0)
        m3.metric("Pending ⏳", len(df_working[~df_working['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df_working.columns else 0)

        # Charts
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.plotly_chart(px.pie(df_working, names='STATUS', hole=0.4, title="Status Overview", template=plotly_theme,
                                   color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        with col_chart2:
            st.plotly_chart(px.histogram(df_working, x='REPORT CHECKLIST', color='STATUS', title="Report Types", template=plotly_theme), use_container_width=True)

        st.subheader("📋 Record Table")
        styled_df = df_working.style.map(color_status, subset=['STATUS']) if 'STATUS' in df_working.columns else df_working
        st.dataframe(styled_df, use_container_width=True, hide_index=True,
                    column_config={PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")})
    else: st.info("Waiting for data from Google Sheets...")

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if c.lower() == 'site'), None)
        
        if month_cols:
            c1, c2 = st.columns(2)
            with c1: selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=len(month_cols)-1)
            
            df_working_eq = df_equip.copy()
            if site_col:
                unique_sites = ["ALL SITES"] + sorted(df_working_eq[site_col].dropna().unique().tolist())
                with c2: selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
                if selected_site != "ALL SITES":
                    df_working_eq = df_working_eq[df_working_eq[site_col] == selected_site]

            st.divider()
            
            # Button Filtering Logic
            status_series = df_working_eq[selected_month].astype(str).str.strip().str.upper()
            if 'filter_status' not in st.session_state: st.session_state.filter_status = "ALL"

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1: 
                if st.button(f"🟢 OK: {len(df_working_eq[status_series == 'OK'])}", use_container_width=True): st.session_state.filter_status = "OK"
            with col_m2: 
                if st.button(f"🟡 FAULTY: {len(df_working_eq[status_series == 'FAULTY'])}", use_container_width=True): st.session_state.filter_status = "FAULTY"
            with col_m3: 
                if st.button(f"🔴 MISSING: {len(df_working_eq[status_series == 'MISSING'])}", use_container_width=True): st.session_state.filter_status = "MISSING"
            with col_m4: 
                if st.button("🔵 SHOW ALL", use_container_width=True): st.session_state.filter_status = "ALL"

            df_filtered = df_working_eq.copy()
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered[selected_month].astype(str).str.upper() == st.session_state.filter_status]

            st.markdown(f"### 🎯 Performance Overview: {selected_site} ({st.session_state.filter_status})")
            col_chart1, col_chart2 = st.columns([0.3, 0.7])
            with col_chart1:
                fig_donut = px.pie(df_working, names=selected_month, hole=0.6, template=plotly_theme,
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_donut, use_container_width=True)
            with col_chart2:
                type_col = next((c for c in df_filtered.columns if c.lower() == 'type'), None)
                if type_col and not df_filtered.empty:
                    df_type_status = df_filtered.groupby([type_col, selected_month]).size().reset_index(name='count')
                    fig_type = px.bar(df_type_status, x=type_col, y='count', color=selected_month, template=plotly_theme,
                                     color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}, barmode='group')
                    st.plotly_chart(fig_type, use_container_width=True)

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
