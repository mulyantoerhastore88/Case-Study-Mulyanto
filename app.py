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
    
    st.markdown("### 📐 1. Forecast Methodology & Data Interpretation")
    
    with st.expander("📊 **Klik untuk melihat logika lengkap forecast**", expanded=True):
        
        # HEADER METODE
        st.markdown("#### 🧮 Metode Forecast yang Digunakan")
        
        col_logic1, col_logic2 = st.columns(2)
        
        with col_logic1:
            st.markdown("""
            **Rumus Excel di GSheet:**
            
            **1. Klasifikasi Model (Kolom T):**
            ```
            =IF(RSQ(F2:Q2, {1..12}) > 0.8, "Linear Trend",
               IF(MAX(F2:Q2)/MEDIAN(F2:Q2) > 1.5, "Seasonal Method",
               "Moving Average"))
            ```
            
            **2. M1 - Weighted Moving Average (60-30-10):**
            ```
            =ROUNDUP((Q2*0.6) + (P2*0.3) + (O2*0.1), 0)
            ```
            - Desember (60%) + November (30%) + Oktober (10%)
            
            **3. M2-M6 - Mirror Growth:**
            ```
            M2 = U2 × (G2/F2)  # Growth Feb/Jan
            M3 = V2 × (H2/G2)  # Growth Mar/Feb
            M4 = W2 × (I2/H2)  # Growth Apr/Mar
            M5 = X2 × (J2/I2)  # Growth May/Apr
            M6 = Y2 × (K2/J2)  # Growth Jun/May
            ```
            """)
        
        with col_logic2:
            st.markdown("""
            **Alasan Pemilihan Metode:**
            
            - **Moving Average:** Untuk data stabil tanpa trend (Device A)
            - **Seasonal Detection:** Untuk data dengan pola berulang (Device B)
            - **Linear Trend:** Untuk data dengan trend naik/turun konsisten (Device C)
            
            **Month to Month Mirror Growth dipilih karena:**
            - Menangkap pola musiman dari tahun sebelumnya
            - Sederhana dan mudah dijelaskan ke management
            - Cocok untuk FMCG dengan siklus tahunan
            """)
        
        st.markdown("---")
        
        # ===== INTERPRETASI DATA HISTORIS =====
        st.markdown("#### 📈 Interpretasi Data Historis per SKU")
        
        # Buat tabel interpretasi dengan format yang lebih menarik
        col_table1, col_table2, col_table3 = st.columns([1, 2, 3])
        
        # Header tabel
        st.markdown("""
        | Item | Pola Data | Metode | Rationale | Visual Pattern |
        |------|-----------|--------|-----------|----------------|
        """)
        
        # Device A
        st.markdown("""
        | **Device A** | Stabil (4.700 - 5.400 unit) | **Moving Average** | Tidak ada trend signifikan, pola flat sepanjang tahun | 📊▬▬▬▬▬ |
        """)
        
        # Device B (dengan penjelasan seasonal)
        st.markdown("""
        | **Device B** | **Spike di Apr-Mei** (6.200 / 5.800) <br> Normal: 2.800 - 3.300 | **Seasonal Method** | **🔴 Pattern: Lonjakan saat Lebaran** <br> • April-Mei 2024: +100% dari normal <br> • Data dinormalisasi untuk forecast | 📈📊📈 |
        """)
        
        # Device C
        st.markdown("""
        | **Device C** | **Naik Konsisten** (900 → 3.100) | **Linear Trend** | • R² = 0.92 (korelasi kuat) <br> • Growth 200 unit/bulan <br> • Produk dalam fase growth | 📈↗️↗️ |
        """)
        
        st.markdown("---")
        
        # ===== NORMALISASI DEVICE B =====
        st.markdown("#### 🎯 Normalisasi Data Device B (Seasonal Adjustment)")
        
        col_norm1, col_norm2 = st.columns([1, 1])
        
        with col_norm1:
            # Toggle untuk normalisasi
            normalize_b = st.radio(
                "**Pilih Opsi Data Device B:**",
                options=[
                    "✅ Normalisasi (Asumsi Seasonal Lebaran) - RECOMMENDED",
                    "⚠️ Gunakan Data Asli (Termasuk Outlier)"
                ],
                index=0
            )
            
            if "Normalisasi" in normalize_b:
                st.success("""
                **Data Device B telah dinormalisasi:**
                - April: 6,200 → **3,150** (rata-rata Feb-Mar)
                - Mei: 5,800 → **3,150** - Forecast menjadi lebih stabil dan akurat
                - Risiko overstock: **RENDAH**
                """)
            else:
                st.warning("""
                **Menggunakan data asli Device B:**
                - April: 6,200 (outlier)
                - Mei: 5,800 (outlier)
                - Forecast akan overestimate
                - Risiko overstock: **TINGGI**
                """)
        
        with col_norm2:
            # Visualisasi perbandingan
            st.markdown("**Perbandingan Forecast:**")
            
            # Data sederhana
            data_compare = pd.DataFrame({
                'Bulan': ['Apr', 'Mei', 'Jun', 'Jul', 'Agu'],
                'Asli': [6200, 5800, 3100, 2800, 2900],
                'Normalisasi': [3150, 3150, 3100, 2800, 2900]
            })
            
            fig_compare = px.line(
                data_compare, 
                x='Bulan', 
                y=['Asli', 'Normalisasi'],
                title="Dampak Normalisasi Device B",
                markers=True,
                color_discrete_map={'Asli': '#ef4444', 'Normalisasi': '#10b981'}
            )
            fig_compare.update_layout(height=250)
            st.plotly_chart(fig_compare, use_container_width=True)
        
        st.markdown("---")
        
        # ===== 3 SKENARIO =====
        st.markdown("#### 🎲 Tiga Skenario Forecast")
        
        col_scen1, col_scen2, col_scen3 = st.columns(3)
        
        with col_scen1:
            st.markdown("""
            <div style='background-color:#dbeafe; padding:15px; border-radius:10px; border-left:5px solid #3b82f6'>
                <h4 style='color:#1e40af; margin:0'>📊 BASE SCENARIO</h4>
                <p style='font-size:12px; margin:5px 0'>Asumsi Normal</p>
                <hr style='margin:10px 0'>
                <p><b>Forecast:</b> Hasil perhitungan rumus (data normalisasi)</p>
                <p><b>Asumsi:</b> Tidak ada perubahan signifikan di pasar</p>
                <p><b>Probabilitas:</b> 60%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_scen2:
            st.markdown("""
            <div style='background-color:#dcfce7; padding:15px; border-radius:10px; border-left:5px solid #10b981'>
                <h4 style='color:#166534; margin:0'>📈 AGGRESSIVE (+20%)</h4>
                <p style='font-size:12px; margin:5px 0'>Asumsi Optimis</p>
                <hr style='margin:10px 0'>
                <p><b>Forecast:</b> Base × 1.2</p>
                <p><b>Asumsi:</b> Lebaran kedua, campaign besar, ekspansi pasar</p>
                <p><b>Probabilitas:</b> 25%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_scen3:
            st.markdown("""
            <div style='background-color:#fee2e2; padding:15px; border-radius:10px; border-left:5px solid #ef4444'>
                <h4 style='color:#991b1b; margin:0'>📉 DOWNSIDE (-20%)</h4>
                <p style='font-size:12px; margin:5px 0'>Asumsi Konservatif</p>
                <hr style='margin:10px 0'>
                <p><b>Forecast:</b> Base × 0.8</p>
                <p><b>Asumsi:</b> Regulasi baru, kompetitor agresif, ekonomi melambat</p>
                <p><b>Probabilitas:</b> 15%</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ===== KESIMPULAN METODOLOGI =====
        st.markdown("""
        <div style='background-color:#f8fafc; padding:20px; border-radius:10px; border:1px solid #cbd5e1'>
            <h4 style='margin-top:0'>📌 Kesimpulan Metodologi Forecast</h4>
            <ul>
                <li><b>Device A:</b> Moving Average - stabil, tidak perlu adjustment</li>
                <li><b>Device B:</b> Seasonal Method - data dinormalisasi untuk menghilangkan efek Lebaran</li>
                <li><b>Device C:</b> Linear Trend - R² 0.92, growth konsisten 200 unit/bulan</li>
                <li><b>3 Skenario:</b> Base (normal), Aggressive (+20%), Downside (-20%) untuk antisipasi berbagai kondisi pasar</li>
            </ul>
            <p style='margin-bottom:0; color:#475569'><i>Metode ini dipilih karena sederhana, mudah direplikasi di Excel, dan sesuai dengan karakteristik FMCG.</i></p>
        </div>
        """, unsafe_allow_html=True)
        
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
    
    # PENTING: Bersihkan nama kolom dari spasi tersembunyi agar tidak salah narik data
    df_a.columns = df_a.columns.str.strip()
    
    # Ambil data yang diperlukan
    df_cover = df_a[['Item', 'Current Stock', 'Unit Cost', 'M1', 'M2', 'M3']].copy()
    
    # Konversi ke numerik secara aman (ubah string jadi angka)
    for col in ['Current Stock', 'Unit Cost', 'M1', 'M2', 'M3']:
        df_cover[col] = pd.to_numeric(df_cover[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # Hitung Forward-Looking Average Forecast (M1-M3)
    df_cover['Avg_Forecast'] = (df_cover['M1'] + df_cover['M2'] + df_cover['M3']) / 3
    
    # Stock Cover (bulan) - Membagi Current Stock dengan Proyeksi M1-M3
    df_cover['Stock Cover (bulan)'] = df_cover.apply(
        lambda x: round(x['Current Stock'] / x['Avg_Forecast'], 1) if x['Avg_Forecast'] > 0 else 0,
        axis=1
    )
    
    # Stock Cover (hari)
    df_cover['Stock Cover (hari)'] = (df_cover['Stock Cover (bulan)'] * 30).round(0)
    
    # Status Logic
    def get_status(cover):
        if cover < 45:
            return "🔴 KRITIS (OOS Risk)"
        elif cover < 60:
            return "🟡 WASPADA"
        elif cover < 90:
            return "🟢 AMAN"
        else:
            return "🔵 OVERSTOCK"
    
    df_cover['Status'] = df_cover['Stock Cover (hari)'].apply(get_status)
    
    # Inventory Exposure (IDR)
    df_cover['Inventory Value'] = df_cover['Current Stock'] * df_cover['Unit Cost']
    
    # Siapkan tabel TAMPILAN (Ubah ke format string agar ada koma)
    display_cover = df_cover[['Item', 'Current Stock', 'Avg_Forecast', 'Stock Cover (bulan)', 'Stock Cover (hari)', 'Status', 'Inventory Value']].copy()
    
    for col in ['Current Stock', 'Avg_Forecast', 'Stock Cover (hari)']:
        display_cover[col] = display_cover[col].apply(lambda x: f"{x:,.0f}")
        
    display_cover['Inventory Value'] = display_cover['Inventory Value'].apply(lambda x: f"Rp {x:,.0f}")
    
    st.dataframe(display_cover, use_container_width=True, hide_index=True)
    
    # Summary metrics
    total_inventory = df_cover['Inventory Value'].sum()
    total_stock_units = df_cover['Current Stock'].sum()
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    with col_met1:
        st.metric("💰 Total Inventory Value", f"Rp {total_inventory:,.0f}")
    with col_met2:
        st.metric("📦 Total Stock (units)", f"{total_stock_units:,.0f}")
    with col_met3:
        kritis_count = len(df_cover[df_cover['Status'].str.contains('KRITIS')])
        st.metric("⚠️ SKU Kritis", kritis_count)
    with col_met4:
        aman_count = len(df_cover[df_cover['Status'].str.contains('AMAN')])
        st.metric("✅ SKU Aman", aman_count)
    
    # ===== PART 5: REKOMENDASI IMPORT PLAN =====
    st.markdown("### 🚢 5. Import Plan Recommendation (Cash Limit: IDR 4B | WH Capacity: 4,000 units)")
    
    # Persiapan Data Order
    df_order = df_a[['Item', 'Current Stock', 'Unit Cost', 'MOQ', 'M1', 'M2', 'M3']].copy()
    
    # Konversi ke numerik
    for col in ['Current Stock', 'Unit Cost', 'MOQ', 'M1', 'M2', 'M3']:
        df_order[col] = pd.to_numeric(df_order[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # Kebutuhan 3 bulan & Defisit
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
    
    # Siapkan tabel TAMPILAN (Format Koma)
    display_order = df_order[['Item', 'Current Stock', 'DOS', 'M1', 'Order_Qty', 'Air_Qty', 'Sea_Qty', 'Route', 'Total_Cost']].copy()
    display_order['Cost (B IDR)'] = (display_order['Total_Cost'] / 1_000_000_000).round(2)
    
    # Ubah format angka menjadi string berkoma
    for col in ['Current Stock', 'DOS', 'M1', 'Order_Qty', 'Air_Qty', 'Sea_Qty']:
        display_order[col] = display_order[col].apply(lambda x: f"{x:,.0f}")
        
    display_order['Total_Cost'] = display_order['Total_Cost'].apply(lambda x: f"Rp {x:,.0f}")
    
    st.dataframe(display_order, use_container_width=True, hide_index=True)
    
    # Summary rekomendasi
    total_cost_b = df_order['Total_Cost'].sum() / 1_000_000_000
    total_air_qty = df_order['Air_Qty'].sum()
    total_sea_qty = df_order['Sea_Qty'].sum()
    
    col_rec1, col_rec2, col_rec3 = st.columns(3)
    with col_rec1:
        st.metric("💰 Total Import Cost", f"Rp {total_cost_b:.2f} B", 
                 delta=f"Sisa: Rp {4 - total_cost_b:.2f} B",
                 delta_color="normal" if total_cost_b <= 4 else "inverse")
    with col_rec2:
        st.metric("✈️ Air Freight (M1 Incoming)", f"{total_air_qty:,.0f} units",
                 delta=f"Sisa Gudang: {4000 - total_air_qty:,.0f} units",
                 delta_color="normal" if total_air_qty <= 4000 else "inverse")
    with col_rec3:
        st.metric("🚢 Sea Freight (Tiba M2)", f"{total_sea_qty:,.0f} units")
    
    # Alert Constraints (Budget & Gudang)
    if total_cost_b > 4:
        st.error("🚨 **OVER BUDGET!** Total biaya melebihi limit IDR 4B.")
    if total_air_qty > 4000:
        st.error("🚨 **OVER CAPACITY!** Kedatangan via udara melebihi sisa kapasitas gudang 4.000 unit. Wajib Split Shipment!")
        
    # Justifikasi Prioritas
    st.markdown("#### 🎯 Prioritization Justification")
    st.markdown("""
    <div style='display: flex; gap: 15px; margin-bottom: 20px;'>
        <div style='flex: 1; background-color: #fef2f2; padding: 15px; border-radius: 8px; border-left: 5px solid #ef4444;'>
            <b style='color: #991b1b;'>1. PRIORITY 1: Device C (URGENT - AIR)</b><br>
            <i>Kenapa?</i> Trend eksponensial menyebabkan risiko OOS bulan ini. Prioritas <b>1.000 unit via Udara</b> untuk mengisi kekosongan instan dan memaksimalkan sisa gudang (4.000 unit). Sisa order dikirim via Laut.
        </div>
        <div style='flex: 1; background-color: #f0fdf4; padding: 15px; border-radius: 8px; border-left: 5px solid #22c55e;'>
            <b style='color: #166534;'>2. PRIORITY 2: Device A (SAFE - SEA)</b><br>
            <i>Kenapa?</i> Stok meng-cover 1.5 bulan. Amankan stok M3 dengan order via Laut (hemat biaya, tidak memakan sisa gudang bulan ini).
        </div>
        <div style='flex: 1; background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 5px solid #64748b;'>
            <b style='color: #334155;'>3. PRIORITY 3: Device B (HOLD)</b><br>
            <i>Kenapa?</i> Status Overstock (>3 bulan). Menahan order Device B adalah kunci kita bisa menyelamatkan Kas perusahaan di bawah limit 4 Miliar.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    st.caption("✅ Dashboard Ready")

# ==========================================
# TAB 2: DEAD STOCK & CASH UNLOCK
# ==========================================
with tab2:
    st.markdown("### 💰 The 5 Billion Cash Unlock Masterplan")
    st.warning("🎯 **Target: Unlock minimum IDR 5 Billion in 90 days**")
    
    # --- TAMBAHAN BARU: MASTERPLAN 5 MILIAR ---
    st.markdown("#### 🚀 The 90-Day Liquidation Portfolio (Road to 5B)")
    
    # Data Masterplan sesuai pembahasan GSheet
    masterplan_data = pd.DataFrame({
        'Category': ['Device Z (Dead Stock)', 'Other Dead Stock (18% of 25B - Z)', 'Slow Moving (35% of 25B)'],
        'Inventory Value': ['Rp 1.10 B', 'Rp 3.40 B', 'Rp 8.75 B'],
        'Proposed Strategy': ['Aggressive Bundling & Clearance (-30%)', 'B2B Wholesale / Export "Take-All"', 'E-Commerce Flash Sale (Double Day)'],
        'Target Cash Unlock': [1100, 2500, 1400] # In Millions
    })
    
    # Visualisasi Progress Bar 5 Miliar
    total_unlock_target = sum(masterplan_data['Target Cash Unlock'])
    
    col_mp1, col_mp2 = st.columns([2, 1])
    with col_mp1:
        st.dataframe(masterplan_data, use_container_width=True, hide_index=True)
    with col_mp2:
        fig_gauge_5b = go.Figure(go.Indicator(
            mode="gauge+number",
            value=total_unlock_target,
            title={'text': "Total Cash Unlock (Rp Juta)"},
            gauge={
                'axis': {'range': [None, 6000]},
                'bar': {'color': "#10b981"},
                'steps': [
                    {'range': [0, 5000], 'color': "#fee2e2"},
                    {'range': [5000, 6000], 'color': "#dcfce7"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 5000}
            }
        ))
        fig_gauge_5b.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge_5b, use_container_width=True)
        st.success("✅ **Target IDR 5B Terpenuhi!**")

    st.markdown("---")
    
    st.markdown("### 📱 Device Z - Detailed Analysis")
    
    col_z_detail1, col_z_detail2, col_z_detail3 = st.columns(3)
    
    # Data Device Z
    stock_z = 12000
    inv_value_z = 1.1e9  # Rp 1.1 Miliar
    unit_cost_z = inv_value_z / stock_z  # Rp 91,667
    monthly_sales_z = 500
    
    with col_z_detail1:
        st.markdown("""
        <div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'>
            <h4 style='margin-top:0; color:#334155;'>📊 Stock & Value</h4>
            <table style='width:100%'>
                <tr><td>Current Stock</td><td><b>{:,} units</b></td></tr>
                <tr><td>Inventory Value</td><td><b>Rp {:.2f} Miliar</b></td></tr>
                <tr><td>Unit Cost (HPP)</td><td><b>Rp {:,.0f}</b></td></tr>
            </table>
        </div>
        """.format(stock_z, inv_value_z/1e9, unit_cost_z), unsafe_allow_html=True)
    
    # Estimasi harga jual (kita buat slider untuk simulasi)
    with col_z_detail2:
        st.markdown("""
        <div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'>
            <h4 style='margin-top:0; color:#334155;'>💰 Sales & Margin</h4>
        """, unsafe_allow_html=True)
        
        estimated_selling_price = st.slider(
            "Estimasi Harga Jual Normal (Rp/unit)",
            min_value=int(unit_cost_z * 1.2),  # Minimal margin 20%
            max_value=int(unit_cost_z * 2.5),  # Max margin 150%
            value=int(unit_cost_z * 1.8),  # Default margin 80%
            step=5000,
            format="Rp %d",
            key="price_z"
        )
        
        normal_margin = (estimated_selling_price - unit_cost_z) / estimated_selling_price * 100
        monthly_revenue = monthly_sales_z * estimated_selling_price
        annual_revenue_potential = monthly_revenue * 12
        
        st.markdown("""
            <table style='width:100%'>
                <tr><td>Harga Jual Estimasi</td><td><b>Rp {:,.0f}</b></td></tr>
                <tr><td>Margin Normal</td><td><b style='color:{};'>{:.1f}%</b></td></tr>
                <tr><td>Monthly Revenue</td><td><b>Rp {:.2f} M</b></td></tr>
                <tr><td>Annual Potential</td><td><b>Rp {:.2f} M</b></td></tr>
            </table>
        </div>
        """.format(
            estimated_selling_price,
            '#22c55e' if normal_margin > 30 else '#eab308' if normal_margin > 15 else '#ef4444',
            normal_margin,
            monthly_revenue/1e6,
            annual_revenue_potential/1e6
        ), unsafe_allow_html=True)
    
    with col_z_detail3:
        st.markdown("""
        <div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'>
            <h4 style='margin-top:0; color:#334155;'>⏱️ Depletion & Risk</h4>
        """, unsafe_allow_html=True)
        
        months_to_deplete = stock_z / monthly_sales_z
        stock_at_launch = stock_z - (monthly_sales_z * 3)  # 3 bulan lagi replacement
        value_at_risk = stock_at_launch * unit_cost_z
        
        st.markdown("""
            <table style='width:100%'>
                <tr><td>Natural Depletion</td><td><b style='color:#ef4444;'>{:.0f} months</b></td></tr>
                <tr><td>Replacement Launch</td><td><b>3 months</b></td></tr>
                <tr><td>Stock at Launch</td><td><b>{:,} units</b></td></tr>
                <tr><td>Value at Risk (if not sold)</td><td><b style='color:#ef4444;'>Rp {:.2f} M</b></td></tr>
            </table>
        </div>
        """.format(
            months_to_deplete,
            stock_at_launch,
            value_at_risk/1e9
        ), unsafe_allow_html=True)
    
    # ===== MARGIN VS CASH TRADE-OFF SIMULATION =====
    st.markdown("#### ⚖️ Margin vs Cash Trade-off Simulation")
    st.info("💡 **Management Constraint:** Maintain margin where possible. Tapi dead stock harus segera dicairkan.")
    
    col_trade1, col_trade2 = st.columns(2)
    
    with col_trade1:
        st.markdown("**🎛️ Strategi Likuidasi Device Z**")
        
        units_to_liquidate = st.slider(
            "Jumlah unit yang akan dilikuidasi",
            min_value=1000,
            max_value=12000,
            value=12000, # Set default ke 12000 agar habis
            step=1000,
            key="units_z"
        )
        
        discount_rate = st.slider(
            "Diskon yang diberikan (%)",
            min_value=10,
            max_value=70,
            value=30, # Set default 30% sesuai masterplan
            step=5,
            key="discount_z"
        )
        
        # Hitung impact
        selling_price_after_discount = estimated_selling_price * (1 - discount_rate/100)
        revenue = units_to_liquidate * selling_price_after_discount
        cost = units_to_liquidate * unit_cost_z
        gross_profit = revenue - cost
        margin_after_discount = (gross_profit / revenue * 100) if revenue > 0 else 0
        
        # Compare dengan margin normal
        normal_profit_per_unit = estimated_selling_price - unit_cost_z
        normal_margin_total = units_to_liquidate * normal_profit_per_unit
        margin_erosion = normal_margin_total - gross_profit
        
    with col_trade2:
        st.markdown("**📊 Hasil Simulasi**")
        
        results_trade = pd.DataFrame({
            'Metric': ['Revenue', 'HPP', 'Gross Profit', 'Margin %', 'Margin Erosion', 'Cash Unlock'],
            'Value': [
                f"Rp {revenue/1e6:.0f} M",
                f"Rp {cost/1e6:.0f} M",
                f"Rp {gross_profit/1e6:.0f} M",
                f"{margin_after_discount:.1f}%",
                f"Rp {margin_erosion/1e6:.0f} M (vs normal)",
                f"Rp {revenue/1e6:.0f} M"
            ]
        })
        st.dataframe(results_trade, use_container_width=True, hide_index=True)
        
        # Visual indicator
        if margin_after_discount > 20:
            st.success(f"✅ Margin masih sehat ({margin_after_discount:.1f}%)")
        elif margin_after_discount > 10:
            st.warning(f"⚠️ Margin tipis ({margin_after_discount:.1f}%)")
        else:
            st.error(f"🔴 Margin sangat rendah ({margin_after_discount:.1f}%) - hampir rugi")
    
    # ===== BREAK-EVEN ANALYSIS =====
    st.markdown("#### 📈 Break-even Analysis")
    
    # Data untuk chart
    discount_rates = list(range(10, 71, 5))
    margins = []
    cash_unlock = []
    
    for disc in discount_rates:
        price = estimated_selling_price * (1 - disc/100)
        rev = units_to_liquidate * price
        profit = rev - (units_to_liquidate * unit_cost_z)
        margin_pct = (profit / rev * 100) if rev > 0 else 0
        margins.append(margin_pct)
        cash_unlock.append(rev/1e6)
    
    fig_tradeoff = go.Figure()
    
    fig_tradeoff.add_trace(go.Scatter(
        x=discount_rates,
        y=margins,
        name='Margin %',
        yaxis='y',
        line=dict(color='#3b82f6', width=3),
        mode='lines+markers'
    ))
    
    fig_tradeoff.add_trace(go.Scatter(
        x=discount_rates,
        y=cash_unlock,
        name='Cash Unlock (Rp M)',
        yaxis='y2',
        line=dict(color='#10b981', width=3, dash='dash'),
        mode='lines+markers'
    ))
    
    fig_tradeoff.add_vline(x=discount_rate, line_dash="dot", line_color="red",
                          annotation_text=f"Selected: {discount_rate}%")
    
    fig_tradeoff.add_hline(y=20, line_dash="dot", line_color="orange",
                          annotation_text="Min Margin 20%", annotation_position="bottom right")
    
    fig_tradeoff.update_layout(
        title=f"Trade-off Analysis: {units_to_liquidate:,} units Device Z",
        xaxis=dict(title="Discount Rate (%)"),
        yaxis=dict(title="Margin (%)", side="left", range=[0, 100]),
        yaxis2=dict(title="Cash Unlock (Rp M)", side="right", overlaying="y", range=[0, max(cash_unlock)*1.1]),
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_tradeoff, use_container_width=True)
    
    # ===== RECOMMENDATION BASED ON MARGIN CONSTRAINT =====
    st.markdown("#### ✅ Recommendation Based on Margin Constraint")
    
    if discount_rate <= 30:
        rec_color = "green"
        rec_text = "Margin terjaga dengan baik"
    elif discount_rate <= 45:
        rec_color = "orange"
        rec_text = "Margin mulai tertekan tapi masih acceptable untuk dead stock"
    else:
        rec_color = "red"
        rec_text = "Margin sangat rendah - hanya untuk likuidasi darurat"
    
    st.markdown(f"""
    <div style='background-color:#f8fafc; padding:20px; border-radius:10px; border-left:5px solid {rec_color}; margin-bottom: 20px;'>
        <h4 style='margin-top:0;'>📌 Kesimpulan untuk Device Z</h4>
        <p><b>Unit Cost:</b> Rp {unit_cost_z:,.0f} | <b>Estimasi Harga Jual Normal:</b> Rp {estimated_selling_price:,.0f} (margin {normal_margin:.1f}%)</p>
        <p><b>Strategi Terpilih:</b> Diskon {discount_rate}% untuk {units_to_liquidate:,} unit (Bundling dengan Liquid)</p>
        <p><b>Hasil:</b> Cash Unlock Rp {revenue/1e6:.0f}M dengan margin {margin_after_discount:.1f}%</p>
        <p><b style='color:{rec_color};'>{rec_text}</b></p>
        <p><b>Trade-off Justification:</b> <i>"Mengorbankan margin Erosion senilai Rp {margin_erosion/1e6:.0f}M saat ini jauh lebih logis secara finansial daripada membiarkan nilai inventory Rp {value_at_risk/1e9:.2f} Miliar hangus menjadi nol (write-off) saat produk pengganti rilis 3 bulan lagi."</i></p>
    </div>
    """, unsafe_allow_html=True)

    # --- TAMBAHAN BARU: GOVERNANCE (SOP) ---
    st.markdown("#### 🛡️ Proposed Portfolio Clean-up Governance")
    st.info("SOP untuk mencegah kejadian Overstock Device Z terulang di masa depan.")
    st.markdown("""
    * **Phase-Out Trigger (T-4 Months):** Segala bentuk aktivitas *Import / Procurement* untuk produk kategori lama wajib dihentikan **4 bulan** sebelum tanggal peluncuran (*launching*) produk generasi pengganti.
    * **Auto-Clearance Mandate (T-2 Months):** Jika pada H-60 hari sebelum peluncuran produk baru masih terdapat stok produk lama yang melebihi *cover* 2 bulan, tim *Marketing & Sales* diizinkan secara sistem untuk mengeksekusi *Bundling Promo* (hingga batas margin minimum 15%) **tanpa memerlukan eskalasi / approval berlapis dari Manajemen**.
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
