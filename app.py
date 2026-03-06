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
        # 1. Pilih Bulan
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026"])]
        if month_cols:
            selected_month = st.selectbox("📅 Pilih Bulan Laporan:", month_cols, index=len(month_cols)-1)
            
            df_q = df_equip.copy()
            
            # Filter Search (jika ada)
            if search_report:
                df_q = df_q[df_q.astype(str).apply(lambda x: x.str.contains(search_report, case=False)).any(axis=1)]

            # 2. Ringkasan Metrik
            status_series = df_q[selected_month].astype(str).str.strip().str.upper()
            e1, e2, e3 = st.columns(3)
            e1.metric("🟢 OK", len(df_q[status_series == 'OK']))
            e2.metric("🟡 FAULTY", len(df_q[status_series == 'FAULTY']))
            e3.metric("🔴 MISSING", len(df_q[status_series == 'MISSING']))

            st.divider()

            # 3. VISUALISASI BARU (By Site & By Category)
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                if 'Site' in df_q.columns:
                    st.markdown("### 🏗️ Status by Site")
                    fig_site = px.histogram(
                        df_q, x='SITE', color=selected_month,
                        barmode='group',
                        color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'},
                        height=400
                    )
                    st.plotly_chart(fig_site, use_container_width=True)
                else:
                    st.warning("Kolum 'SITE' tidak dijumpai dalam Google Sheets.")

            with col_chart2:
                if 'Detail' in df_q.columns:
                    st.markdown("### 🗂️ Status by Category")
                    fig_cat = px.histogram(
                        df_q, x='CATEGORY', color=selected_month,
                        barmode='group',
                        color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'},
                        height=400
                    )
                    st.plotly_chart(fig_cat, use_container_width=True)
                else:
                    st.warning("Kolum 'CATEGORY' tidak dijumpai dalam Google Sheets.")

            # 4. Carta Individu Equipment (Jika data banyak, kita buat horizontal bar)
            st.markdown("### 🛠️ Individual Equipment Health")
            if 'EQUIPMENT' in df_q.columns:
                fig_equip = px.bar(
                    df_q, y='EQUIPMENT', x=selected_month, color=selected_month,
                    orientation='h',
                    color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'},
                    height=max(400, len(df_q)*20) # Auto-adjust height ikut jumlah barang
                )
                st.plotly_chart(fig_equip, use_container_width=True)

            st.divider()
            
            # 5. Jadual Data
            def color_equip(val):
                if val == 'OK': return 'background-color: #d4edda;'
                if val == 'FAULTY': return 'background-color: #fff3cd;'
                if val == 'MISSING': return 'background-color: #f8d7da;'
                return ''

            st.dataframe(
                df_q.style.applymap(color_equip, subset=[selected_month]), 
                use_container_width=True, 
                hide_index=True
            )
