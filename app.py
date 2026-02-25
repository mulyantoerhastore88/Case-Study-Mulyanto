import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import numpy as np

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="FOOM S&OP Command Center", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main-header {background: linear-gradient(90deg, #0f172a 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;}
    .card {background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 5px solid #3b82f6;}
    .card-alert {border-left: 5px solid #ef4444;}
    </style>
""", unsafe_allow_html=True)

# --- 2. GOOGLE SHEETS CONNECTION ---
@st.cache_data(ttl=60)
def load_data_from_gsheet():
    # SETUP KONEKSI API BAPAK DI SINI
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    # Ganti dengan Link URL Spreadsheet Bapak
    sheet_url = "https://docs.google.com/spreadsheets/d/1xN5gQ6r7I0QUXs6-9FZLqH9wMxd9H2-R8ViLnp3twuI/edit"
    sh = client.open_by_url(sheet_url)
    
    # --- LOAD PART A ---
    ws_a = sh.worksheet("Part_A_Stock&SKU_Detail")
    df_a = pd.DataFrame(ws_a.get_all_records())
    
    # --- LOAD PART B ---
    ws_b = sh.worksheet("Part_B_DEAD_STOCK_&_CASH_UNLOCK")
    # Tabel B1: Device Z (Asumsi di A1:H2)
    b1_data = ws_b.get('A1:H2')
    df_b1 = pd.DataFrame(b1_data[1:], columns=b1_data[0]) if len(b1_data) > 1 else pd.DataFrame()
    # Tabel B2: Cash Unlock (Asumsi di A6:E9)
    b2_data = ws_b.get('A6:E9')
    df_b2 = pd.DataFrame(b2_data[1:], columns=b2_data[0]) if len(b2_data) > 1 else pd.DataFrame()
    
    # --- LOAD PART C ---
    # Sesuai gambar screenshot Bapak
    ws_c = sh.worksheet("Part_C_S&OP_ RESTRUCTURE_DESIGN") 
    c1_data = ws_c.get('A1:D5')
    df_c1 = pd.DataFrame(c1_data[1:], columns=c1_data[0])
    
    c2_data = ws_c.get('A8:C12')
    df_c2 = pd.DataFrame(c2_data[1:], columns=c2_data[0])
    
    c3_data = ws_c.get('A15:C16')
    df_c3 = pd.DataFrame(c3_data[1:], columns=c3_data[0])
    
    return df_a, df_b1, df_b2, df_c1, df_c2, df_c3

# Load Data
try:
    df_a, df_b1, df_b2, df_c1, df_c2, df_c3 = load_data_from_gsheet()
except Exception as e:
    st.error(f"Koneksi GSheet Gagal. Silakan cek API/Secrets. Error: {e}")
    st.stop()

# --- HEADER UI ---
st.markdown("<div class='main-header'><h1>🚀 FOOM LAB GLOBAL: S&OP Command Center</h1><p>Strategic Supply & Demand Validation System | Candidate: Mulyanto</p></div>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 PART A: Replenishment & Scenarios", "💀 PART B: Cash Unlock & Dead Stock", "⚙️ PART C: S&OP Governance"])

# ==========================================
# TAB 1: REPLENISHMENT & SCENARIOS
# ==========================================
with tab1:
    st.markdown("### 🎛️ Live Scenario Simulation (The 6-Month Plan)")
    st.info("💡 **Live Defense Ready:** Geser slider di bawah untuk mensimulasikan perubahan asumsi dari Manajemen (Aggressive / Downside). Sistem akan merekomendasikan ulang rute pengiriman dan memvalidasi limit budget.")
    
    col_slide1, col_slide2 = st.columns(2)
    with col_slide1:
        scenario_growth = st.slider("📈 Market Demand Adjustment (%)", min_value=-30, max_value=50, value=0, step=5)
    with col_slide2:
        budget_limit = st.number_input("💰 Maximum Budget Constraint (Billion IDR)", value=4.0, step=0.5)

    # RE-CALCULATE LOGIC BERDASARKAN SLIDER
    df_sim = df_a.copy()
    
    # Cleaning tipe data (jaga-jaga dari GSheet terbaca string)
    for col in ['Current Stock', 'M1', 'M2', 'M3', 'MOQ', 'Unit Cost']:
        df_sim[col] = pd.to_numeric(df_sim[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # 1. Terapkan Skenario Growth ke M1-M3
    multiplier = 1 + (scenario_growth / 100)
    df_sim['M1_Sim'] = np.ceil(df_sim['M1'] * multiplier)
    df_sim['M2_Sim'] = np.ceil(df_sim['M2'] * multiplier)
    df_sim['M3_Sim'] = np.ceil(df_sim['M3'] * multiplier)
    
    # 2. Hitung Ulang Projected Stock End M1 & Order Requirement
    df_sim['Projected End M1 (Sim)'] = df_sim['Current Stock'] - df_sim['M1_Sim']
    df_sim['Deficit 3M'] = (df_sim['M1_Sim'] + df_sim['M2_Sim'] + df_sim['M3_Sim']) - df_sim['Current Stock']
    
    # 3. Hitung Order Qty (Kelipatan MOQ)
    df_sim['Suggested Order Qty (Sim)'] = df_sim.apply(lambda x: int(np.ceil(x['Deficit 3M'] / x['MOQ']) * x['MOQ']) if x['Deficit 3M'] > 0 else 0, axis=1)
    
    # 4. Routing & Value
    df_sim['Route (Sim)'] = df_sim.apply(lambda x: "AIR (Split)" if x['Projected End M1 (Sim)'] < 0 else ("SEA" if x['Suggested Order Qty (Sim)'] > 0 else "-"), axis=1)
    df_sim['Order Value (Billion)'] = (df_sim['Suggested Order Qty (Sim)'] * df_sim['Unit Cost']) / 1_000_000_000

    # TAMPILKAN TABEL HASIL
    display_cols = ['SKU', 'Forecast Model', 'Current Stock', 'M1_Sim', 'Projected End M1 (Sim)', 'Suggested Order Qty (Sim)', 'Route (Sim)', 'Order Value (Billion)']
    st.dataframe(df_sim[display_cols].style.applymap(lambda x: 'background-color: #fecaca; font-weight: bold;' if type(x) in [int, float] and x < 0 else '', subset=['Projected End M1 (Sim)']), use_container_width=True)

    # KPI VALIDATION
    st.markdown("#### ⚖️ Constraints Validation Check")
    total_value = df_sim['Order Value (Billion)'].sum()
    
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.metric("Total Import Value (M1)", f"IDR {total_value:.2f} B", delta=f"Limit: IDR {budget_limit} B", delta_color="normal" if total_value <= budget_limit else "inverse")
        if total_value > budget_limit:
            st.error("🚨 OVER BUDGET! Rekomendasi: Kurangi buffer stock M3 untuk pengiriman via Laut.")
        else:
            st.success("✅ Budget SAFE. Kas perusahaan aman.")
            
    with kpi2:
        st.metric("Warehouse Incoming (AIR) - M1", "3,000 Units", delta="Capacity Left: 4,000", delta_color="normal")
        st.warning("💡 **Split Shipment Strategy:** Untuk mencegah overcapacity, order 10.000 unit Device C (2 MOQ) akan di-split: **3.000 via Udara (untuk mencegah OOS M1) & 7.000 via Laut.**")

# ==========================================
# TAB 2: DEAD STOCK LIQUIDATION (5B CASH UNLOCK)
# ==========================================
with tab2:
    st.markdown("### 💰 The 5 Billion Cash Unlock Masterplan")
    
    col_b1, col_b2 = st.columns([1, 2])
    with col_b1:
        st.markdown("<div class='card card-alert'><h4>Device Z Status</h4><p><b>Stock:</b> 12,000 units</p><p><b>Sales/Mo:</b> 500 units</p><p><b>Value:</b> IDR 1.1 Billion</p><p style='color:red;'><b>Depletion:</b> 24 Months ⚠️ (Product replaced in 3 mos!)</p></div>", unsafe_allow_html=True)
        
    with col_b2:
        st.markdown("#### The Strategy Tracker (90 Days)")
        # Bersihkan format nilai
        df_b2['Total Value (IDR)'] = pd.to_numeric(df_b2['Total Value (IDR)'].astype(str).str.replace(',', ''), errors='coerce')
        df_b2['Target Cash Unlock in 90 Days'] = pd.to_numeric(df_b2['Target Cash Unlock in 90 Days'].astype(str).str.replace(',', ''), errors='coerce')
        
        # Format Currency untuk tampilan
        df_b2_display = df_b2.copy()
        df_b2_display['Total Value (IDR)'] = df_b2_display['Total Value (IDR)'].apply(lambda x: f"Rp {x:,.0f}")
        df_b2_display['Target Cash Unlock in 90 Days'] = df_b2_display['Target Cash Unlock in 90 Days'].apply(lambda x: f"Rp {x:,.0f}")
        
        st.dataframe(df_b2_display, use_container_width=True, hide_index=True)
        
        total_unlock = df_b2['Target Cash Unlock in 90 Days'].sum()
        st.success(f"🎯 **Total Projected Cash Unlock:** Rp {total_unlock:,.0f} (Target terpenuhi!)")

# ==========================================
# TAB 3: S&OP RESTRUCTURE DESIGN
# ==========================================
with tab3:
    st.markdown("### ⚙️ S&OP Governance & Cycle Restructure")
    
    col_c1, col_c2 = st.columns([2, 1])
    
    with col_c1:
        st.markdown("#### 🔄 Monthly Cadence (The 4-Week SOP)")
        st.dataframe(df_c1, use_container_width=True, hide_index=True)
        
        st.markdown("<br>#### 🛡️ Professional Defense Strategy (To Sales Team)", unsafe_allow_html=True)
        challenge_desc = df_c3['My Professional Challenge Strategy'].iloc[0]
        st.info(f"**How to challenge +50% growth target:**\n\n{challenge_desc}")
        
    with col_c2:
        st.markdown("#### 🎯 6-Month KPI Target")
        # Visualisasi sederhana KPI
        for idx, row in df_c2.iterrows():
            st.markdown(f"""
            <div class='card' style='padding: 15px; margin-bottom: 10px;'>
                <p style='margin:0; font-size:0.9rem; color:#64748b;'>{row['Metric']}</p>
                <h3 style='margin:0; color:#0f172a;'>{row['Target (6 Months)']}</h3>
                <span style='font-size:0.8rem; color:#ef4444;'>Baseline: {row['Current Baseline']}</span>
            </div>
            """, unsafe_allow_html=True)
