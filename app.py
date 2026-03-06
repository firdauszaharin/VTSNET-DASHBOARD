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

# --- SET MALAYSIA TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# 2. MODERN CSS (VERSI FIX SIDEBAR BUTTON)
st.markdown("""
    <style>
    /* Latar Belakang & Font */
    .stApp { 
        background: radial-gradient(circle at top right, #f8faff, #eef2f7,#f8faff); 
        font-family: 'Inter', sans-serif; 
    }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] { 
        background-color: rgba(255, 255, 255, 0.8) !important; 
        backdrop-filter: blur(10px); 
    }

    /* Metric Cards */
    [data-testid="stMetric"] { 
        background: white !important; 
        padding: 20px !important; 
        border-radius: 20px !important; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.03) !important; 
    }

    /* --- FIX: KEKALKAN BUTANG SIDEBAR TAPI SOROK HEADER PUTIH --- */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important; /* Buat header lutsinar */
        color: #0984E3 !important; /* Warnakan butang menu */
    }
    
    /* Pastikan butang "Open Sidebar" (Chevron) sentiasa nampak */
    .st-emotion-cache-hp888a {
        color: #0984E3 !important;
    }

    /* Sembunyikan menu Streamlit (tiga titik) & footer sahaja */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"
PDF_COL = "UPLOAD REPORT" 

# 4. DATA LOAD FUNCTION
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        time_col = next((c for c in data.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        if time_col and not data.empty:
            data[time_col] = pd.to_datetime(data[time_col], errors='coerce')
            data['Year'] = data[time_col].dt.year
        return data
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- HELPER FUNCTION FOR STYLING ---
def color_status(val):
    if val == 'APPROVED': return 'background-color: #d4edda; color: #155724;'
    if val == 'REJECTED': return 'background-color: #f8d7da; color: #721c24;'
    return ''

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.title("📌 MENU")
    menu_selection = st.radio("Pilih Paparan:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    search_report = st.text_input("🔎 Search Site/Type:")
    search_staff = st.text_input("👤 Search Staff Name:")

# --- HEADER BANNER ---
st.title("VTSNET Management Dashboard")

if not df_equip.empty:
    month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026"])]
    latest_month = month_cols[-1] if month_cols else None
    
    if latest_month:
        # Logic untuk detect faulty masih jalan, tapi banner visual sudah dibuang
        status_check = df_equip[latest_month].astype(str).str.strip().str.upper()
        faulty_data = df_equip[status_check.isin(['FAULTY', 'MISSING'])]
        
        if len(faulty_data) > 0:
            st.error(f"⚠️ Dikesan {len(faulty_data)} aset bermasalah pada bulan {latest_month}!")
            st.download_button("📥 Download Faulty List", faulty_data.to_csv(index=False), "faulty_assets.csv")


# --- PAGE 1: MAINTENANCE REPORTS ---
if menu_selection == "📝 Maintenance Reports":
    if not df_raw.empty:
        df = df_raw.copy()
        
        # Filter Logic
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        # Graphs
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df, names='STATUS', hole=0.4, title="Status Distribution", 
                                   color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        with c2:
            st.plotly_chart(px.histogram(df, x='REPORT CHECKLIST', color='STATUS', title="Reports by Type",
                                         color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)

        st.subheader("📋 Record Table")
        
        # --- FIX: STYLING & PDF LINK ---
        styled_df = df.style.map(color_status, subset=['STATUS']) if 'STATUS' in df.columns else df
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
            }
        )
    else:
        st.info("Waiting for data...")

# --- PAGE 2: EQUIPMENT STATUS ---
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        
        # 1. DETECT KOLUM (Bulan & Site)
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026", "2027"]) 
                      and "REMARK" not in c.upper()]
        site_col = next((c for c in df_equip.columns if c.lower() == 'site'), None)
        
        if not month_cols:
            st.warning("Tiada kolum status bulanan dijumpai.")
        else:
            # --- ROW FILTER (BULAN & SITE) ---
            c1, c2 = st.columns(2)
            with c1:
                selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=len(month_cols)-1)
            
            df_working = df_equip.copy()
            if site_col:
                unique_sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().unique().tolist())
                with c2:
                    selected_site = st.selectbox("🏗️ Select Site:", unique_sites)
                
                if selected_site != "ALL SITES":
                    df_working = df_working[df_working[site_col] == selected_site]

            st.divider()

            # Clean status data
            status_series = df_working[selected_month].astype(str).str.strip().str.upper()
            
            # --- 2. METRICS DENGAN FUNGSI KLIK (DRILL-DOWN) ---
            if 'filter_status' not in st.session_state:
                st.session_state.filter_status = "ALL"

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            total_ok = len(df_working[status_series == 'OK'])
            total_faulty = len(df_working[status_series == 'FAULTY'])
            total_missing = len(df_working[status_series == 'MISSING'])

            with col_m1:
                if st.button(f"🟢 OK: {total_ok}", use_container_width=True):
                    st.session_state.filter_status = "OK"
            with col_m2:
                if st.button(f"🟡 FAULTY: {total_faulty}", use_container_width=True):
                    st.session_state.filter_status = "FAULTY"
            with col_m3:
                if st.button(f"🔴 MISSING: {total_missing}", use_container_width=True):
                    st.session_state.filter_status = "MISSING"
            with col_m4:
                if st.button("🔵 SHOW ALL", use_container_width=True):
                    st.session_state.filter_status = "ALL"

            # --- PREPARE FILTERED DATA FOR CHARTS & TABLE ---
            df_filtered = df_working.copy()
            # Tukar status column kepada format seragam (OK/FAULTY/MISSING)
            df_filtered[selected_month] = df_filtered[selected_month].astype(str).str.strip().str.upper()
            
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered[selected_month] == st.session_state.filter_status]

            # --- 3. VISUALISASI ---
            st.markdown(f"### 🎯 Performance Overview: {selected_site} ({st.session_state.filter_status})")
            col_chart1, col_chart2 = st.columns([0.3, 0.7])
            
            with col_chart1:
                # Donut Chart (Sentiasa tunjuk pecahan asal df_working)
                fig_donut = px.pie(
                    df_working, names=selected_month, hole=0.6, 
                    title=f'Overall Condition',
                    color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}
                )
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_chart2:
                # Histogram mengikut Type (Guna data yang dah ditapis butang)
                type_col = next((c for c in df_filtered.columns if c.lower() == 'type'), None)
                if type_col and not df_filtered.empty:
                    df_type_count = df_filtered.groupby(type_col).size().reset_index(name='count')
                    df_type_count = df_type_count.sort_values('count', ascending=False)

                    fig_type = px.bar(
                        df_type_count, x=type_col, y='count',
                        title=f'Equipment Detail by Type',
                        color_discrete_sequence=['#0984E3'],
                        text_auto=True
                    )
                    fig_type.update_layout(xaxis_tickangle=-45, yaxis_title="Quantity")
                    st.plotly_chart(fig_type, use_container_width=True)
                else:
                    st.info("Tiada data untuk dipaparkan dalam carta bar.")

            # --- 4. DATA TABLE ---
            st.divider()
            st.subheader(f"📦 Inventory Asset List")
            
            search_eq = st.text_input("🔍 Carian Pantas (SN, Nama, IP):", key="search_eq_box")
            
            if search_eq:
                df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            # Logik Remark
            year_match = re.search(r'202\d', selected_month)
            curr_yr = year_match.group(0) if year_match else "2025"
            m_up = selected_month.upper()
            if any(m in m_up for m in ['JAN', 'FEB', 'MAR']): q = "Q1"
            elif any(m in m_up for m in ['APR', 'MAY', 'MEI', 'JUN']): q = "Q2"
            elif any(m in m_up for m in ['JUL', 'AUG', 'SEP', 'OGO']): q = "Q3"
            else: q = "Q4"

            actual_remark_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and q in c.upper() and curr_yr in c.upper()), None)

            # Susun Kolum
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
            else:
                st.info("Tiada rekod untuk paparan ini.")
