import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os
from streamlit_autorefresh import st_autorefresh

# 1. PAGE CONFIGURATION (MESTI PALING ATAS)
st.set_page_config(
    page_title="VTSNET: MAL Tracker",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# 2. AUTO REFRESH (5 MINUTES)
st_autorefresh(interval=300000, key="vts_refresh")

# 3. LOGIN SECURITY
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

with st.sidebar:
    if not st.session_state.authenticated:
        st.title("🔒 Project Access")
        pwd = st.text_input("Project Access Code:", type="password")
        if st.button("Unlock Dashboard"):
            if pwd == "vtsnet2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong Password!")
        st.stop() 

# --- DATA LOAD & TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

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

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- THEME & CSS ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    dark_mode = st.toggle("Dark Mode View", value=False)
    st.divider()

if dark_mode:
    bg_style, sidebar_bg, card_bg, text_color = "linear-gradient(135deg, #1a0a2e 0%, #2c3e50 100%)", "rgba(15, 10, 25, 0.98)", "rgba(255, 255, 255, 0.05)", "#E0E0E0"
    shadow, plotly_theme = "0 8px 32px rgba(108, 92, 231, 0.15)", "plotly_dark"
    custom_dark_css = f"""
        .stApp, .stMarkdown p, h1, h2, h3, h4, label {{ color: white !important; }}
        .stButton > button {{ background-color: #1e293b !important; color: white !important; border: 1px solid #3e4e63 !important; }}
    """
else:
    bg_style, sidebar_bg, card_bg, text_color = "radial-gradient(circle at top right, #f8faff, #eef2f7,#f8faff)", "rgba(255, 255, 255, 0.8)", "white", "#1e293b"
    shadow, plotly_theme = "0 10px 25px rgba(0,0,0,0.03)", "plotly_white"
    custom_dark_css = ""

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    h1 {{ margin-top: 40px !important; font-size: 3.2rem !important; font-weight: 800; }}
    header[data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; backdrop-filter: blur(10px); }}
    [data-testid="stMetric"] {{ background: {card_bg} !important; padding: 20px !important; border-radius: 20px !important; box-shadow: {shadow} !important; }}
    {custom_dark_css}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    menu_selection = st.radio("Select Category:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    if menu_selection == "📝 Maintenance Reports":
        search_report = st.text_input("🔎 Search Site/Type:")
        search_staff = st.text_input("👤 Search Staff Name:")
        search_id = st.text_input("🆔 Search Document ID:") 
    else:
        search_report = search_staff = search_id = ""

st.title("VTSNET: Maintenance & Asset Lifecycle Tracker")

# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    if not df_raw.empty:
        df = df_raw.copy()
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df, names='STATUS', hole=0.55, title="Approval Overview", 
                                   color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}, template=plotly_theme), use_container_width=True)
        with c2:
            st.plotly_chart(px.histogram(df, x='REPORT CHECKLIST', color='STATUS', title="Reports by Type",
                                         color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}, template=plotly_theme), use_container_width=True)

        st.subheader("📊 Report Tracking Status")
        def color_status(val):
            if val == 'APPROVED': return 'background-color: #d4edda; color: #155724;'
            if val == 'REJECTED': return 'background-color: #f8d7da; color: #721c24;'
            return ''
        styled_df = df.style.map(color_status, subset=['STATUS']) if 'STATUS' in df.columns else df
        st.dataframe(styled_df, use_container_width=True, hide_index=True,
                     column_config={PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")})

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if c.lower() == 'site'), None)
        
        if month_cols:
            c1, c2 = st.columns(2)
            with c1: selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=0)
            
            df_working = df_equip.copy()
            if site_col:
                unique_sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().unique().tolist())
                with c2: 
                    selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
                    if selected_site != "ALL SITES": df_working = df_working[df_working[site_col] == selected_site]

            st.divider()
            status_series = df_working[selected_month].astype(str).str.strip().str.upper()
            if 'filter_status' not in st.session_state: st.session_state.filter_status = "ALL"

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            if col_m1.button(f"🟢 OK: {len(df_working[status_series == 'OK'])}", use_container_width=True): st.session_state.filter_status = "OK"
            if col_m2.button(f"🟡 FAULTY: {len(df_working[status_series == 'FAULTY'])}", use_container_width=True): st.session_state.filter_status = "FAULTY"
            if col_m3.button(f"🔴 MISSING: {len(df_working[status_series == 'MISSING'])}", use_container_width=True): st.session_state.filter_status = "MISSING"
            if col_m4.button("🔵 SHOW ALL", use_container_width=True): st.session_state.filter_status = "ALL"

            df_filtered = df_working.copy()
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered[selected_month].astype(str).str.strip().str.upper() == st.session_state.filter_status]

            # CHARTS SECTION
            col_chart1, col_chart2 = st.columns([0.4, 0.6])
            with col_chart1:
                fig_donut = px.pie(df_working, names=selected_month, hole=0.55, template=plotly_theme, title="Status Overall",
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                fig_donut.update_layout(title_x=0.4, legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
                st.plotly_chart(fig_donut, use_container_width=True)
            with col_chart2:
                type_col = next((c for c in df_filtered.columns if c.lower() == 'type'), None)
                if type_col and not df_filtered.empty:
                    fig_type = px.bar(df_filtered.groupby([type_col, selected_month]).size().reset_index(name='count'), 
                                      x=type_col, y='count', color=selected_month, template=plotly_theme, title=f"Analysis Equipment: {selected_month}",
                                      color_discrete_map={'OK': '#2ecc71', 'FAULTY': '#f1c40f', 'MISSING': '#e74c3c'}, barmode='group')
                    fig_type.update_layout(title_x=0.4)
                    st.plotly_chart(fig_type, use_container_width=True)

            # INVENTORY ASSET LIST
            st.divider()
            st.subheader(f"📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Quick Search (SN, Name, IP):", key="search_eq_box")
            if search_eq:
                df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            # QUARTER & REMARK LOGIC
            year_match = re.search(r'202\d', selected_month)
            curr_yr = year_match.group(0) if year_match else "2025"
            m_up = selected_month.upper()
            if any(m in m_up for m in ['JAN', 'FEB', 'MAR']): q = "Q1"
            elif any(m in m_up for m in ['APR', 'MAY', 'MEI', 'JUN']): q = "Q2"
            elif any(m in m_up for m in ['JUL', 'AUG', 'SEP', 'OGO']): q = "Q3"
            else: q = "Q4"
            actual_remark_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper() and curr_yr in c.upper()), None)

            display_cols = []
            for col in ["Site", "Type", "Equipment", "Serial No", "IP Address"]:
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
