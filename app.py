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
        
        # Detect kolum bulan (2025/2026)
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026"])]
        
        if not month_cols:
            st.warning("Tiada kolum bulan (2025/2026) dijumpai dalam fail Equipment.")
        else:
            c_sel, _ = st.columns([0.4, 0.6])
            with c_sel:
                selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=len(month_cols)-1)
            
            st.divider()

            # Clean data untuk charting
            status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
            df_plot = df_equip.copy()
            df_plot[selected_month] = status_series
            
            # 1. METRICS
            me1, me2, me3 = st.columns(3)
            me1.metric("Equipment OK", len(df_equip[status_series == 'OK']))
            me2.metric("Faulty ⚠️", len(df_equip[status_series == 'FAULTY']))
            me3.metric("Missing ❌", len(df_equip[status_series == 'MISSING']))

            st.markdown(f"### 🎯 Performance Overview ({selected_month})")
            
            # 2. CHARTS (BY SITE & CATEGORY)
            col_left, col_right = st.columns(2)
            
            with col_left:
                # Donut Chart
                fig_donut = px.pie(
                    df_plot, names=selected_month, hole=0.55, title='Overall Condition',
                    color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_right:
                # Site Chart (Guna 'Site' atau 'SITE')
                site_col = next((c for c in df_plot.columns if c.lower() == 'site'), None)
                if site_col:
                    fig_site = px.histogram(
                        df_plot, x=site_col, color=selected_month, barmode='group', title='Status by Location',
                        color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}
                    )
                    st.plotly_chart(fig_site, use_container_width=True)

            # Category/Type Chart
            type_col = next((c for c in df_plot.columns if c.lower() in ['type', 'category']), None)
            if type_col:
                fig_type = px.histogram(
                    df_plot, x=type_col, color=selected_month, barmode='group', title='Status by Equipment Category',
                    color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}
                )
                st.plotly_chart(fig_type, use_container_width=True)
            
            # 3. DATA TABLE
            st.divider()
            st.subheader("📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Search Asset (SN, Name, Site):", key="search_eq_box")
            
            df_eq_show = df_equip.copy()
            if search_eq:
                df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            # Styling untuk table
            st.dataframe(
                df_eq_show.style.map(
                    lambda x: 'background-color: #D4EDDA' if x=='OK' else 
                              ('background-color: #F8D7DA' if x=='MISSING' else 
                               ('background-color: #FFF3CD' if x=='FAULTY' else '')), 
                    subset=[selected_month]
                ), 
                use_container_width=True, 
                hide_index=True
            )
    else:
        st.info("Sila pastikan SHEET_EQUIP_URL disambungkan dengan betul.")
