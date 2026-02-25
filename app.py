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
    # SETUP KONEKSI API
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    # Ganti dengan URL spreadsheet Bapak
    sheet_url = "https://docs.google.com/spreadsheets/d/1xN5gQ6r7I0QUXs6-9FZLqH9wMxd9H2-R8ViLnp3twuI/edit"
    sh = client.open_by_url(sheet_url)
    
    # LOAD PART A (sesuai struktur Bapak: kolom A-AE)
    ws_a = sh.worksheet("Part_A_Stock&SKU_Detail")
    data_a = ws_a.get_all_values()
    df_a = pd.DataFrame(data_a[1:], columns=data_a[0])
    
    # LOAD PART B (akan dibuat)
    try:
        ws_b = sh.worksheet("Part_B_DEAD_STOCK")
        data_b = ws_b.get_all_values()
        df_b = pd.DataFrame(data_b[1:], columns=data_b[0]) if len(data_b) > 1 else pd.DataFrame()
    except:
        df_b = pd.DataFrame()
    
    # LOAD PART C (akan dibuat)
    try:
        ws_c = sh.worksheet("Part_C_S&OP")
        data_c = ws_c.get_all_values()
        df_c = pd.DataFrame(data_c[1:], columns=data_c[0]) if len(data_c) > 1 else pd.DataFrame()
    except:
        df_c = pd.DataFrame()
    
    return df_a, df_b, df_c

# Load Data
try:
    df_a, df_b, df_c = load_data_from_gsheet()
    st.success("✅ Data berhasil dimuat dari Google Sheets")
except Exception as e:
    st.error(f"❌ Koneksi GSheet Gagal: {e}")
    st.stop()

# --- HEADER ---
st.markdown("<div class='main-header'><h1>🚀 FOOM LAB GLOBAL: S&OP Command Center</h1><p>Strategic Supply & Demand Validation System | Candidate: Mulyanto</p></div>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 PART A: Replenishment & Scenarios", "💀 PART B: Cash Unlock & Dead Stock", "⚙️ PART C: S&OP Governance"])

# ==========================================
# TAB 1: REPLENISHMENT & SCENARIOS (FULL VERSION)
# ==========================================
with tab1:
    # ===== PART 1: 6-MONTH FORECAST & LOGIKA =====
    st.markdown("## 📈 PART A: 6-MONTH FORECAST & REPLENISHMENT PLAN")
    st.markdown("---")
    
    st.markdown("### 📐 1. Forecast Methodology")
    
    with st.expander("📊 **Klik untuk melihat logika lengkap forecast**", expanded=True):
        col_logic1, col_logic2 = st.columns(2)
        
        with col_logic1:
            st.markdown("""
            **🧮 Rumus Excel yang digunakan:**
            
            **1. Klasifikasi Model (Kolom T):**
            ```
            =IF(RSQ(F2:Q2, {1..12}) > 0.8, "Linear Trend",
               IF(MAX(F2:Q2)/MEDIAN(F2:Q2) > 1.5, "Seasonal",
               "Moving Average"))
            ```
            
            **2. M1 - Weighted Moving Average (60-30-10):**
            ```
            =ROUNDUP((Q2*0.6) + (P2*0.3) + (O2*0.1), 0)
            ```
            - Des (60%) + Nov (30%) + Okt (10%)
            
            **3. M2-M6 - Mirror Growth:**
            ```
            M2 = U2 × (G2/F2)  # Feb/Jan
            M3 = V2 × (H2/G2)  # Mar/Feb
            M4 = W2 × (I2/H2)  # Apr/Mar
            M5 = X2 × (J2/I2)  # May/Apr
            M6 = Y2 × (K2/J2)  # Jun/May
            ```
            """)
        
        with col_logic2:
            st.markdown("""
            **📈 Interpretasi Data Historis:**
            
            | Item | Pola | Metode | Rationale |
            |------|------|--------|-----------|
            | **Device A** | Stabil (4.7K-5.4K) | Moving Average | Tidak ada trend signifikan |
            | **Device B** | Spike Apr-Mei | Moving Average (excl outlier) | Anomali campaign, exclude dari trend |
            | **Device C** | Naik konsisten | Linear Trend | R² = 0.92, growth 200 unit/bulan |
            
            **🎯 3 Skenario:**
            - **Base Scenario:** Forecast asli dari rumus
            - **Aggressive (+20%):** Base × 1.2 (optimis)
            - **Downside (-20%):** Base × 0.8 (konservatif)
            """)
    
    # ===== PART 2: 6-MONTH FORECAST TABLE =====
    st.markdown("### 📊 2. 6-Month Forecast (Base Scenario)")
    
    # Kolom forecast yang ada di GSheet
    forecast_cols = ['Item', 'Forecast Model'] + [f'M{i}' for i in range(1, 7)]
    available_forecast = [col for col in forecast_cols if col in df_a.columns]
    
    if len(available_forecast) > 1:
        df_forecast = df_a[available_forecast].copy()
        
        # Konversi ke numerik
        for col in [f'M{i}' for i in range(1, 7)]:
            if col in df_forecast.columns:
                df_forecast[col] = pd.to_numeric(df_forecast[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # Hitung Total 6 Bulan
        df_forecast['Total 6 Bulan'] = df_forecast[[f'M{i}' for i in range(1, 7)]].sum(axis=1)
        df_forecast['Rata-rata'] = (df_forecast['Total 6 Bulan'] / 6).round(0)
        
        # Format untuk display
        display_forecast = df_forecast.copy()
        for col in [f'M{i}' for i in range(1, 7)] + ['Total 6 Bulan', 'Rata-rata']:
            if col in display_forecast.columns:
                display_forecast[col] = display_forecast[col].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(display_forecast, use_container_width=True, hide_index=True)
    
    # ===== PART 3: 3 SCENARIOS COMPARISON =====
    st.markdown("### 🔄 3. Three Scenarios Comparison (Base vs Aggressive vs Downside)")
    
    # Buat data untuk 3 skenario
    df_scenarios = df_a[['Item'] + [f'M{i}' for i in range(1, 7)]].copy()
    
    # Konversi ke numerik
    for col in [f'M{i}' for i in range(1, 7)]:
        if col in df_scenarios.columns:
            df_scenarios[col] = pd.to_numeric(df_scenarios[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # Hitung metrik per SKU
    df_scenarios['Base_Total'] = df_scenarios[[f'M{i}' for i in range(1, 7)]].sum(axis=1)
    df_scenarios['Base_Avg'] = (df_scenarios['Base_Total'] / 6).round(0)
    df_scenarios['Agg_Total'] = (df_scenarios['Base_Total'] * 1.2).round(0)
    df_scenarios['Agg_Avg'] = (df_scenarios['Agg_Total'] / 6).round(0)
    df_scenarios['Down_Total'] = (df_scenarios['Base_Total'] * 0.8).round(0)
    df_scenarios['Down_Avg'] = (df_scenarios['Down_Total'] / 6).round(0)
    
    # Tabel perbandingan
    comparison_table = df_scenarios[['Item', 
                                     'Base_Avg', 'Base_Total',
                                     'Agg_Avg', 'Agg_Total',
                                     'Down_Avg', 'Down_Total']].copy()
    
    # Format angka
    for col in comparison_table.columns:
        if col != 'Item':
            comparison_table[col] = comparison_table[col].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(
        comparison_table,
        use_container_width=True,
        column_config={
            "Base_Avg": "Base (avg/mo)",
            "Base_Total": "Base 6M",
            "Agg_Avg": "Agg +20%",
            "Agg_Total": "Agg 6M",
            "Down_Avg": "Down -20%",
            "Down_Total": "Down 6M"
        }
    )
    
    # Visualisasi per SKU
    st.markdown("#### 📈 Visualisasi per SKU")
    selected_sku = st.selectbox("Pilih SKU untuk detail scenario:", df_a['Item'].tolist(), key="sku_selector")
    
    # Filter untuk SKU terpilih
    sku_data = df_scenarios[df_scenarios['Item'] == selected_sku].iloc[0]
    
    # Data untuk line chart
    months = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    base_values = [sku_data[m] for m in months]
    agg_values = [v * 1.2 for v in base_values]
    down_values = [v * 0.8 for v in base_values]
    
    plot_df = pd.DataFrame({
        'Month': months,
        'Base': base_values,
        'Aggressive (+20%)': agg_values,
        'Downside (-20%)': down_values
    })
    
    plot_df_melted = plot_df.melt(id_vars=['Month'], var_name='Scenario', value_name='Forecast')
    
    fig_line = px.line(
        plot_df_melted,
        x='Month',
        y='Forecast',
        color='Scenario',
        title=f"6-Month Forecast Scenarios: {selected_sku}",
        markers=True,
        color_discrete_map={
            'Base': '#3b82f6',
            'Aggressive (+20%)': '#10b981',
            'Downside (-20%)': '#ef4444'
        }
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Bar chart comparison all SKUs
    st.markdown("#### 📊 Total 6-Month Forecast by SKU")
    
    fig_bar = go.Figure()
    for idx, row in df_scenarios.iterrows():
        fig_bar.add_trace(go.Bar(
            name=row['Item'],
            x=['Base', 'Aggressive', 'Downside'],
            y=[row['Base_Total'], row['Agg_Total'], row['Down_Total']],
            text=[f"{row['Base_Total']:,.0f}", f"{row['Agg_Total']:,.0f}", f"{row['Down_Total']:,.0f}"],
            textposition='auto',
        ))
    
    fig_bar.update_layout(
        title="6-Month Total Forecast Comparison",
        barmode='group',
        yaxis_title="Total Units"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # ===== PART 4: STOCK COVER & INVENTORY EXPOSURE =====
    st.markdown("### 📦 4. Stock Cover & Inventory Exposure")
    
    # Hitung stock cover
    df_cover = df_a[['Item', 'Current Stock', 'Unit Cost']].copy()
    
    # Konversi numerik
    df_cover['Current Stock'] = pd.to_numeric(df_cover['Current Stock'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df_cover['Unit Cost'] = pd.to_numeric(df_cover['Unit Cost'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # Ambil forecast M1-M3 untuk rata-rata
    df_cover['Avg_Forecast'] = 0
    for i, row in df_cover.iterrows():
        item = row['Item']
        m1 = pd.to_numeric(df_a[df_a['Item'] == item]['M1'].values[0] if len(df_a[df_a['Item'] == item]) > 0 else 0, errors='coerce')
        m2 = pd.to_numeric(df_a[df_a['Item'] == item]['M2'].values[0] if len(df_a[df_a['Item'] == item]) > 0 else 0, errors='coerce')
        m3 = pd.to_numeric(df_a[df_a['Item'] == item]['M3'].values[0] if len(df_a[df_a['Item'] == item]) > 0 else 0, errors='coerce')
        df_cover.loc[i, 'Avg_Forecast'] = (m1 + m2 + m3) / 3
    
    # Stock Cover (bulan)
    df_cover['Stock Cover (bulan)'] = df_cover.apply(
        lambda x: round(x['Current Stock'] / x['Avg_Forecast'], 1) if x['Avg_Forecast'] > 0 else 0,
        axis=1
    )
    
    # Stock Cover (hari)
    df_cover['Stock Cover (hari)'] = (df_cover['Stock Cover (bulan)'] * 30).round(0)
    
    # Status
    def get_status(cover):
        if cover < 45:
            return "🔴 KRITIS"
        elif cover < 60:
            return "🟡 WASPADA"
        elif cover < 90:
            return "🟢 AMAN"
        else:
            return "🔵 BERLEBIH"
    
    df_cover['Status'] = df_cover['Stock Cover (hari)'].apply(get_status)
    
    # Inventory Exposure (IDR)
    df_cover['Inventory Value'] = df_cover['Current Stock'] * df_cover['Unit Cost']
    
    # Tampilkan
    st.dataframe(
        df_cover[['Item', 'Current Stock', 'Avg_Forecast', 'Stock Cover (bulan)', 'Stock Cover (hari)', 'Status', 'Inventory Value']],
        use_container_width=True,
        column_config={
            "Inventory Value": st.column_config.NumberColumn(format="Rp %d")
        }
    )
    
    # Summary metrics
    total_inventory = df_cover['Inventory Value'].sum()
    total_stock_units = df_cover['Current Stock'].sum()
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    with col_met1:
        st.metric("💰 Total Inventory Value", f"Rp {total_inventory:,.0f}")
    with col_met2:
        st.metric("📦 Total Stock (units)", f"{total_stock_units:,.0f}")
    with col_met3:
        kritis_count = len(df_cover[df_cover['Status'] == '🔴 KRITIS'])
        st.metric("⚠️ SKU Kritis", kritis_count)
    with col_met4:
        aman_count = len(df_cover[df_cover['Status'] == '🟢 AMAN'])
        st.metric("✅ SKU Aman", aman_count)
    
    # ===== PART 5: REKOMENDASI IMPORT PLAN =====
    st.markdown("### 🚢 5. Import Plan Recommendation (Cash Limit: IDR 4B | WH Capacity: 4,000 units)")
    
    # Hitung kebutuhan order
    df_order = df_a[['Item', 'Current Stock', 'Unit Cost', 'MOQ', 'M1', 'M2', 'M3']].copy()
    
    # Konversi numerik
    for col in df_order.columns:
        if col != 'Item':
            df_order[col] = pd.to_numeric(df_order[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # Kebutuhan 3 bulan
    df_order['Kebutuhan_3M'] = df_order['M1'] + df_order['M2'] + df_order['M3']
    df_order['Defisit'] = df_order['Kebutuhan_3M'] - df_order['Current Stock']
    df_order['Defisit'] = df_order['Defisit'].apply(lambda x: max(0, x))
    
    # Order quantity (kelipatan MOQ)
    df_order['Order_Qty'] = df_order.apply(
        lambda x: int(np.ceil(x['Defisit'] / x['MOQ']) * x['MOQ']) if x['Defisit'] > 0 else 0,
        axis=1
    )
    
    # Split logic (Air untuk yang kritis)
    df_order['DOS'] = df_cover['Stock Cover (hari)'].values
    df_order['Air_Qty'] = df_order.apply(
        lambda x: min(x['Order_Qty'], int(np.ceil(max(0, x['M1'] - x['Current Stock']) / 1000) * 1000))
        if x['DOS'] < 45 and x['Order_Qty'] > 0 else 0,
        axis=1
    )
    df_order['Sea_Qty'] = df_order['Order_Qty'] - df_order['Air_Qty']
    
    # Cost calculation
    air_multiplier = 4.0
    df_order['Air_Cost'] = df_order['Air_Qty'] * df_order['Unit Cost'] * air_multiplier
    df_order['Sea_Cost'] = df_order['Sea_Qty'] * df_order['Unit Cost'] * 1.1
    df_order['Total_Cost'] = df_order['Air_Cost'] + df_order['Sea_Cost']
    
    # Route decision
    def get_route(row):
        if row['Air_Qty'] > 0 and row['Sea_Qty'] > 0:
            return f"✈️ SPLIT: {row['Air_Qty']:,.0f} Air + {row['Sea_Qty']:,.0f} Sea"
        elif row['Air_Qty'] > 0:
            return "✈️ AIR (URGENT)"
        elif row['Sea_Qty'] > 0:
            return "🚢 SEA"
        else:
            return "⏸️ TUNDA"
    
    df_order['Route'] = df_order.apply(get_route, axis=1)
    
    # Tampilkan rekomendasi
    display_order = df_order[['Item', 'Current Stock', 'DOS', 'M1', 'Order_Qty', 'Air_Qty', 'Sea_Qty', 'Route', 'Total_Cost']].copy()
    display_order['Total_Cost_B'] = (display_order['Total_Cost'] / 1_000_000_000).round(2)
    
    st.dataframe(
        display_order,
        use_container_width=True,
        column_config={
            "DOS": "Cover (hari)",
            "Total_Cost": st.column_config.NumberColumn(format="Rp %d"),
            "Total_Cost_B": "Cost (B IDR)"
        }
    )
    
    # Summary rekomendasi
    total_cost_b = display_order['Total_Cost_B'].sum()
    total_air_qty = display_order['Air_Qty'].sum()
    total_sea_qty = display_order['Sea_Qty'].sum()
    
    col_rec1, col_rec2, col_rec3 = st.columns(3)
    with col_rec1:
        st.metric("💰 Total Import Cost", f"Rp {total_cost_b:.2f} B", 
                 delta=f"Sisa: Rp {4 - total_cost_b:.2f} B",
                 delta_color="normal" if total_cost_b <= 4 else "inverse")
    with col_rec2:
        st.metric("✈️ Air Freight (M1)", f"{total_air_qty:,.0f} units")
    with col_rec3:
        st.metric("🚢 Sea Freight", f"{total_sea_qty:,.0f} units")
    
    # Alert jika over budget
    if total_cost_b > 4:
        st.error("🚨 **OVER BUDGET!** Total biaya melebihi limit IDR 4B. Rekomendasi: Kurangi air freight atau negosiasi split order.")
    
    # ===== PART 6: LIVE DEFENSE SIMULATION =====
    st.markdown("---")
    st.markdown("## 🎯 LIVE DEFENSE SCENARIO SIMULATION")
    st.info("Geser slider di bawah untuk simulasi perubahan asumsi manajemen (cash turun / kapasitas gudang berkurang)")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        scenario_growth = st.slider("📈 Demand Adjustment (%)", -30, 50, 0, 5)
    with col_s2:
        budget_limit = st.number_input("💰 Budget Limit (B IDR)", 1.0, 10.0, 4.0, 0.5)
    with col_s3:
        wh_capacity = st.number_input("🏭 WH Capacity Left", 1000, 10000, 4000, 500)
    
    # Terapkan skenario
    multiplier = 1 + (scenario_growth / 100)
    
    df_live = df_order.copy()
    df_live['M1_Sim'] = df_live['M1'] * multiplier
    df_live['M2_Sim'] = df_live['M2'] * multiplier
    df_live['M3_Sim'] = df_live['M3'] * multiplier
    df_live['Kebutuhan_Sim'] = df_live['M1_Sim'] + df_live['M2_Sim'] + df_live['M3_Sim']
    df_live['Defisit_Sim'] = df_live['Kebutuhan_Sim'] - df_live['Current Stock']
    df_live['Defisit_Sim'] = df_live['Defisit_Sim'].apply(lambda x: max(0, x))
    
    # Order ulang
    df_live['Order_Sim'] = df_live.apply(
        lambda x: int(np.ceil(x['Defisit_Sim'] / x['MOQ']) * x['MOQ']) if x['Defisit_Sim'] > 0 else 0,
        axis=1
    )
    
    # Split ulang
    df_live['DOS_Sim'] = df_live['Current Stock'] / ((df_live['M1_Sim'] + df_live['M2_Sim'] + df_live['M3_Sim'])/3) * 30
    df_live['Air_Sim'] = df_live.apply(
        lambda x: min(x['Order_Sim'], int(np.ceil(max(0, x['M1_Sim'] - x['Current Stock']) / 1000) * 1000))
        if x['DOS_Sim'] < 45 and x['Order_Sim'] > 0 else 0,
        axis=1
    )
    df_live['Sea_Sim'] = df_live['Order_Sim'] - df_live['Air_Sim']
    
    # Cost ulang
    df_live['Cost_Sim'] = (df_live['Air_Sim'] * df_live['Unit Cost'] * air_multiplier + 
                           df_live['Sea_Sim'] * df_live['Unit Cost'] * 1.1) / 1_000_000_000
    
    # Tampilkan hasil live
    st.markdown("#### 📊 Adjusted Plan dengan Asumsi Baru")
    
    display_live = df_live[['Item', 'Current Stock', 'DOS_Sim', 'M1_Sim', 'Order_Sim', 'Air_Sim', 'Sea_Sim', 'Cost_Sim']].copy()
    display_live['DOS_Sim'] = display_live['DOS_Sim'].round(0)
    display_live['M1_Sim'] = display_live['M1_Sim'].round(0)
    
    st.dataframe(display_live, use_container_width=True)
    
    # Validasi
    total_cost_live = df_live['Cost_Sim'].sum()
    total_wh_live = df_live['Air_Sim'].sum()
    
    col_v1, col_v2, col_v3, col_v4 = st.columns(4)
    with col_v1:
        st.metric("💰 Total Cost", f"Rp {total_cost_live:.2f} B", 
                 delta=f"Limit: {budget_limit:.1f} B",
                 delta_color="normal" if total_cost_live <= budget_limit else "inverse")
    with col_v2:
        st.metric("🏭 WH Incoming", f"{total_wh_live:,.0f} units",
                 delta=f"Cap: {wh_capacity:,.0f}",
                 delta_color="normal" if total_wh_live <= wh_capacity else "inverse")
    with col_v3:
        st.metric("💵 Sisa Kas", f"Rp {budget_limit - total_cost_live:.2f} B")
    with col_v4:
        st.metric("📦 Sisa Gudang", f"{wh_capacity - total_wh_live:,.0f} units")
    
    # Final recommendation
    st.markdown("#### ✅ Final Recommendation")
    
    if total_cost_live <= budget_limit and total_wh_live <= wh_capacity:
        st.success("""
        **Plan ini AMAN untuk dieksekusi:**
        - Budget terpenuhi
        - Kapasitas gudang mencukupi
        - SKU kritis (Device C) diutamakan dengan air freight
        """)
    else:
        st.error("""
        **Plan perlu PENYESUAIAN:**
        - Prioritaskan hanya Device C untuk air freight
        - Device A negosiasi split order (kirim 3.000 air, sisanya laut)
        - Device B tunda order
        """)
    
    # Export ready note
    st.caption("✅ Dashboard siap untuk presentasi & live defense Q&A")

# ==========================================
# TAB 2: DEAD STOCK & CASH UNLOCK
# ==========================================
with tab2:
    st.markdown("### 💰 The 5 Billion Cash Unlock Masterplan")
    st.warning("🎯 **Target: Unlock minimum IDR 5 Billion in 90 days**")
    
    # Device Z Status (hardcoded karena data dari case study)
    col_z1, col_z2 = st.columns(2)
    
    with col_z1:
        st.markdown("""
        <div class='card card-alert'>
            <h4>📱 Device Z Status</h4>
            <table style='width:100%'>
                <tr><td>Current Stock</td><td><b>12,000 units</b></td></tr>
                <tr><td>Monthly Sales</td><td><b>500 units</b></td></tr>
                <tr><td>Stock Value</td><td><b>Rp 1.1 Billion</b></td></tr>
                <tr><td>Depletion Time</td><td><b style='color:red;'>24 Months ⚠️</b></td></tr>
                <tr><td>Replacement Launch</td><td><b>3 Months</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # Depletion Calculator
        st.markdown("#### 📉 Without Intervention")
        months = list(range(1, 25))
        stock_left = [max(0, 12000 - 500 * m) for m in months]
        
        fig_depletion = px.line(
            x=months, y=stock_left,
            title="Natural Depletion Timeline",
            labels={'x': 'Month', 'y': 'Stock (units)'}
        )
        fig_depletion.add_vline(x=3, line_dash="dash", line_color="orange",
                               annotation_text="Launch Replacement")
        fig_depletion.add_hline(y=0, line_dash="dot", line_color="gray")
        st.plotly_chart(fig_depletion, use_container_width=True)
    
    with col_z2:
        st.markdown("#### 🎯 Liquidation Strategies")
        
        # Strategy Matrix
        strategies = pd.DataFrame({
            'Strategy': ['Bundle with A', 'Flash Sale 30%', 'Export (Malaysia)', 'B2B Corporate'],
            'Discount': ['20%', '30%', '15%', '25%'],
            'Target Units': ['3,000', '2,500', '8,000', '3,500'],
            'Cash Unlock (M)': ['Rp 440M', 'Rp 825M', 'Rp 935M', 'Rp 770M'],
            'Speed': ['🔥🔥🔥', '⚡⚡⚡⚡', '🚢🚢', '🤝🤝🤝']
        })
        
        st.dataframe(strategies, use_container_width=True, hide_index=True)
        
        # Cash Unlock Calculation
        total_unlock = 440 + 825 + 935 + 770  # in Million
        target = 5000  # 5 Billion
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=total_unlock,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Cash Unlock Progress (Rp Million)"},
            delta={'reference': target},
            gauge={
                'axis': {'range': [None, 6000]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 2500], 'color': "#fee2e2"},
                    {'range': [2500, 5000], 'color': "#fef9c3"},
                    {'range': [5000, 6000], 'color': "#dcfce7"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': target
                }
            }
        ))
        fig_gauge.update_layout(height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        st.success(f"""
        **Total Projected Cash Unlock:** Rp {total_unlock:,.0f} Million (Rp {total_unlock/1000:.2f} Billion)
        
        **Gap to Target:** Rp {target - total_unlock:,.0f} Million
        
        **Recommendation:** Kombinasikan strategi di atas + negosiasi buyback dengan supplier
        """)

# ==========================================
# TAB 3: S&OP RESTRUCTURE DESIGN (FIXED)
# ==========================================
with tab3:
    st.markdown("### ⚙️ S&OP Governance & Cycle Restructure")
    st.info(f"🎯 **Target Growth: +50%** (Historical: +18%) | Current Forecast Accuracy: 62%")
    
    col_c1, col_c2 = st.columns([2, 1])
    
    with col_c1:
        st.markdown("#### 📅 Monthly S&OP Cadence")
        
        cadence = pd.DataFrame({
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Activity': ['Demand Review', 'Supply Review', 'Pre-S&OP', 'Executive S&OP'],
            'Owner': ['Sales & Marketing', 'Supply Chain', 'Demand + Supply Lead', 'Management'],
            'Output': ['Consensus Forecast', 'Inventory Plan', 'Scenario Analysis', 'Final Decision']
        })
        
        st.dataframe(cadence, use_container_width=True, hide_index=True)
        
        # --- PERBAIKAN: TIMELINE VISUAL DENGAN FORMAT YANG BENAR ---
        st.markdown("#### 📊 S&OP Timeline")
        
        # Buat data untuk timeline
        timeline_data = pd.DataFrame({
            'Task': ['Demand Review', 'Supply Review', 'Pre-S&OP', 'Executive S&OP'],
            'Start': ['2024-01-01', '2024-01-08', '2024-01-15', '2024-01-22'],
            'Finish': ['2024-01-07', '2024-01-14', '2024-01-21', '2024-01-28'],
            'Owner': ['Sales', 'Supply Chain', 'Lead', 'Management']
        })
        
        # Konversi ke datetime
        timeline_data['Start'] = pd.to_datetime(timeline_data['Start'])
        timeline_data['Finish'] = pd.to_datetime(timeline_data['Finish'])
        
        # Buat timeline chart dengan cara yang benar
        fig_timeline = px.timeline(
            timeline_data,
            x_start='Start',
            x_end='Finish',
            y='Task',
            color='Owner',
            title="S&OP Monthly Cycle",
            color_discrete_map={
                'Sales': '#3b82f6',
                'Supply Chain': '#10b981',
                'Lead': '#f59e0b',
                'Management': '#ef4444'
            }
        )
        
        # PERBAIKAN: Gunakan update_layout untuk mengatur axis
        fig_timeline.update_layout(
            xaxis=dict(
                title="Week of Month",
                tickformat="%d %b"  # Format tanggal: day month
            ),
            yaxis=dict(
                title="",
                autorange="reversed"  # Biar task teratas di grafik
            ),
            height=300,
            showlegend=True
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col_c2:
        st.markdown("#### 🎯 KPI Dashboard")
        
        kpi_data = pd.DataFrame({
            'KPI': ['Forecast Accuracy', 'Service Level', 'Inventory Turnover', 'Dead Stock %'],
            'Target': ['85%', '98%', '6x', '<5%'],
            'Current': ['62%', '85%', '3.2x', '18%'],
            'Status': ['🔴', '🟡', '🟡', '🔴']
        })
        
        st.dataframe(kpi_data, use_container_width=True, hide_index=True)
        
        # Gauge chart untuk Forecast Accuracy
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=62,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Forecast Accuracy", 'font': {'size': 16}},
            delta={'reference': 85, 'increasing': {'color': "red"}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, 50], 'color': '#fee2e2'},
                    {'range': [50, 75], 'color': '#fef9c3'},
                    {'range': [75, 100], 'color': '#dcfce7'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        fig_gauge.update_layout(height=200, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # RACI Matrix
    st.markdown("#### 🏛️ RACI Matrix: Who Decides What?")
    
    raci = pd.DataFrame({
        'Role': ['Demand Owner (Sales)', 'Supply Owner (Supply Chain)', 'S&OP Lead', 'Final Decision Maker (Management)'],
        'Responsibility': [
            '📊 Sales Forecast, Promotion Plan, Market Intelligence',
            '📦 Inventory Plan, Procurement, Warehouse Allocation',
            '🔄 Facilitate Process, Scenario Planning, Conflict Resolution',
            '✅ Budget Approval, Strategic Decisions, Final Sign-off'
        ],
        'Decision Rights': [
            'Challenge & Adjust Forecast, Input Promo',
            'Allocate Inventory, Order Placement',
            'Recommend Best Option, Escalate Issues',
            'Final Decision on Budget & Inventory'
        ]
    })
    
    st.dataframe(raci, use_container_width=True, hide_index=True)
    
    # Professional Challenge Strategy
    st.markdown("#### 🛡️ Professional Challenge Strategy (Menantang Target Sales +50%)")
    
    col_strat1, col_strat2 = st.columns(2)
    
    with col_strat1:
        st.markdown("""
        <div class='card'>
            <h4>🔍 Triangulation Method</h4>
            <p><b>Question:</b> "How does this +50% growth compare to last year's actual + promotion impact?"</p>
            <p><b>Logic:</b> Last year growth 18% with 2 major campaigns. To achieve +50%, we need 32% incremental growth.</p>
            <p><b>Example:</b> "Can we map which campaigns will cover the 32% gap? If not, we risk overstock."</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class='card'>
            <h4>⚠️ Risk Assessment</h4>
            <p><b>Question:</b> "What's the probability (P10/P50/P90) of achieving this target?"</p>
            <p><b>Logic:</b> With 62% forecast accuracy, historical error = ±20%.</p>
            <p><b>Example:</b> "Based on data, P50 = +25%, P10 = +40%. I recommend planning for +30% with upside option."</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_strat2:
        st.markdown("""
        <div class='card'>
            <h4>📊 Scenario Planning</h4>
            <p><b>Question:</b> "What if we only achieve 60% of target? What's the inventory impact?"</p>
            <p><b>Logic:</b> Previous overstock IDR 5B happened because optimistic forecast.</p>
            <p><b>Example:</b> "If we miss by 20%, we'll have Rp 5-7B excess stock. Let's phase the procurement."</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class='card'>
            <h4>🔄 Phased Commitment</h4>
            <p><b>Question:</b> "Can we split the target into firm vs optional buckets?"</p>
            <p><b>Logic:</b> Match inventory commitment with sales certainty.</p>
            <p><b>Example:</b> "I'll commit inventory for +25% now. The remaining +25% we can do with air freight if confirmed by M2."</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Summary
    st.success("""
    **🎯 Final Professional Challenge Summary:**
    
    "Management, saya paham target +50% adalah aspirasi yang baik. Tapi dengan forecast accuracy 62% dan histori 18%,
    saya usul pendekatan bertahap:
    
    1. **Base Case:** Siapkan inventory untuk +30% (lebih realistis)
    2. **Upside Option:** Jika sales menunjukkan tren positif di M1-M2, akselerasi dengan air freight
    3. **Downside Protection:** Jika meleset, kita hanya terikat 60% inventory commitment
    
    Ini menjaga cash flow dan menghindari overstock seperti kejadian sebelumnya (IDR 5B)."
    """)
