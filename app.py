import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import re
import os
import hmac
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="VTSNET Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. AUTO REFRESH (5 MINIT)
# =========================================================
st_autorefresh(interval=300000, key="vts_refresh")

# =========================================================
# 3. LOGIN SECURITY
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 VTSNET Project Access")
        pwd = st.text_input("Project Access Code:", type="password")
        correct_password = st.secrets.get("PROJECT_PASSWORD")
        if st.button("Unlock Dashboard", use_container_width=True):
            if hmac.compare_digest(str(pwd), str(correct_password)):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong Password!")
    st.stop()

# =========================================================
# 4. THEME & STYLING
# =========================================================
with st.sidebar:
    dark_mode = st.toggle("Dark Mode View", value=False)
    if st.button("🔒 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

if dark_mode:
    bg_style, text_color, plotly_theme = "#1a0a2e", "#FFFFFF", "plotly_dark"
else:
    bg_style, text_color, plotly_theme = "#eef2f6", "#243447", "plotly_white"

st.markdown(f"""<style>
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    [data-testid="stMetric"] {{ background: rgba(255,255,255,0.05); border-radius: 10px; padding: 15px; border: 1px solid rgba(0,0,0,0.1); }}
    </style>""", unsafe_allow_html=True)

# =========================================================
# 5. DATA LOADING
# =========================================================
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines="skip")
        data.columns = data.columns.str.strip()
        return data
    except:
        return pd.DataFrame()

SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1cJAnZVhxY_Nqjkfo39ze9DCAIZwWd_6dIdFgw0a2j_s/export?format=csv"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1IvOj5FqviwhZU7tGdnuh7zK5WUf-RsjUrVVa6HalkVU/export?format=csv"

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# =========================================================
# 6. SIDEBAR MENU
# =========================================================
menu_selection = st.sidebar.radio("Select Category:", ["📝 Maintenance Reports", "⚙️ Equipment Status"])

# =========================================================
# PAGE 1: MAINTENANCE REPORTS
# =========================================================
if menu_selection == "📝 Maintenance Reports":
    st.title("📝 Maintenance Reports")
    if not df_raw.empty:
        st.dataframe(df_raw, use_container_width=True)
    else:
        st.warning("No data available.")

# =========================================================
# PAGE 2: EQUIPMENT STATUS (FIXED WITH CHARTS)
# =========================================================
elif menu_selection == "⚙️ Equipment Status":
    if not df_equip.empty:
        st.title("⚙️ Equipment Status")
        
        # 1. Filter Section
        q_map = {
            "Q1": ["JAN", "FEB", "MAR"],
            "Q2": ["APR", "MAY", "MEI", "JUN"],
            "Q3": ["JUL", "AUG", "SEP", "OGO"],
            "Q4": ["OCT", "NOV", "DEC", "OKT", "DIS"]
        }

        f1, f2, f3 = st.columns(3)
        with f1:
            years = sorted(list(set(re.findall(r"202\d", " ".join(df_equip.columns)))), reverse=True)
            selected_year = st.selectbox("📅 Year:", years if years else ["2025"])
        with f2:
            selected_q = st.selectbox("📂 Quarter:", ["Q1", "Q2", "Q3", "Q4"])
        
        site_col = next((c for c in df_equip.columns if c.lower() == "site"), None)
        df_working = df_equip.copy()
        with f3:
            if site_col:
                sites = ["ALL SITES"] + sorted(df_working[site_col].dropna().unique().tolist())
                sel_site = st.selectbox("🏗️ Site:", sites)
                if sel_site != "ALL SITES":
                    df_working = df_working[df_working[site_col] == sel_site]

        # 2. Status Calculation
        relevant_months = [c for c in df_equip.columns if any(m in c.upper() for m in q_map[selected_q]) and selected_year in str(c) and "REMARK" not in c.upper()]
        
        if relevant_months:
            def get_combined_status(row):
                vals = [str(row[m]).strip().upper() for m in relevant_months if m in row]
                if "FAULTY" in vals: return "FAULTY"
                if "WARNING" in vals: return "WARNING"
                if "OK" in vals: return "OK"
                return "PENDING"

            df_working["STATUS"] = df_working.apply(get_combined_status, axis=1)
            
            if "filter_status" not in st.session_state:
                st.session_state.filter_status = "ALL"

            # 3. Buttons
            st.divider()
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button(f"🟢 OK: {len(df_working[df_working['STATUS']=='OK'])}", use_container_width=True): st.session_state.filter_status = "OK"
            with b2:
                if st.button(f"🔴 FAULTY: {len(df_working[df_working['STATUS']=='FAULTY'])}", use_container_width=True): st.session_state.filter_status = "FAULTY"
            with b3:
                if st.button(f"🟡 WARNING: {len(df_working[df_working['STATUS']=='WARNING'])}", use_container_width=True): st.session_state.filter_status = "WARNING"
            with b4:
                if st.button("🔵 SHOW ALL", use_container_width=True): st.session_state.filter_status = "ALL"

            # 4. Charts (KEMBALIKAN PIE & BAR GRAPH)
            df_filtered = df_working.copy()
            if st.session_state.filter_status != "ALL":
                df_filtered = df_filtered[df_filtered["STATUS"] == st.session_state.filter_status]

            c1, c2 = st.columns([0.4, 0.6])
            with c1:
                fig_pie = px.pie(df_working, names="STATUS", hole=0.5, template=plotly_theme,
                                title="Overall Status Overview",
                                color_discrete_map={"OK": "#2ecc71", "FAULTY": "#e74c3c", "WARNING": "#f1c40f"})
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                type_col = next((c for c in df_filtered.columns if c.lower() == "type"), None)
                if type_col and not df_filtered.empty:
                    fig_bar = px.bar(df_filtered.groupby([type_col, "STATUS"]).size().reset_index(name="count"),
                                    x=type_col, y="count", color="STATUS", barmode="group", template=plotly_theme,
                                    color_discrete_map={"OK": "#2ecc71", "FAULTY": "#e74c3c", "WARNING": "#f1c40f"})
                    st.plotly_chart(fig_bar, use_container_width=True)

            # 5. Search & Table
            st.divider()
            search = st.text_input("🔍 Quick Search (Name/Serial/IP):")
            if search:
                df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]

            # Remark Logic
            rem_col = next((c for c in df_equip.columns if "REMARK" in c.upper() and selected_q in c.upper() and selected_year in c), None)
            
            show_cols = ["Site", "Type", "Equipment", "Serial No", "IP Address", "STATUS"]
            actual_cols = [c for c in show_cols if c in df_filtered.columns]
            if rem_col: actual_cols.append(rem_col)

            st.dataframe(
                df_filtered[actual_cols].style.map(
                    lambda x: "background-color: #d4edda; color: #155724;" if str(x)=="OK" else
                    ("background-color: #f8d7da; color: #721c24;" if str(x)=="FAULTY" else
                     ("background-color: #fff3cd; color: #856404;" if str(x)=="WARNING" else "")),
                    subset=["STATUS"] if "STATUS" in actual_cols else None
                ),
                use_container_width=True, hide_index=True
            )
        else:
            st.warning(f"No columns found for {selected_q} {selected_year}.")
    else:
        st.warning("Equipment data empty.")

# =========================================================
# 7. FOOTER
# =========================================================
st.markdown(f"""<div style="position: fixed; left: 0; bottom: 0; width: 100%; background: {bg_style}; text-align: center; padding: 10px; border-top: 1px solid rgba(0,0,0,0.1);">
    <p style="color: {text_color}; margin:0;">© 2026 VTSNET Dashboard</p>
    </div>""", unsafe_allow_html=True)
