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
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1xN5gQ6r7I0QUXs6-9FZLqH9wMxd9H2-R8ViLnp3twuI/edit"
    sh = client.open_by_url(sheet_url)
    
    # LOAD PART A (Membaca seluruh 45 Kolom)
    ws_a = sh.worksheet("Part_A_Stock&SKU_Detail")
    data_a = ws_a.get_all_values()
    df_a = pd.DataFrame(data_a[1:], columns=data_a[0])
    df_a.columns = df_a.columns.str.strip() # Pembersihan spasi nama kolom
    
    return df_a

# Load Data
try:
    df_a = load_data_from_gsheet()
    
    # KONVERSI SEMUA KOLOM ANGKA DARI STRING KE NUMERIC
    numeric_columns = [
        'Unit Cost', 'MOQ', 'Current Stock', 'Stock Value', 
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 
        'Avg Sales (Last 3 Month)', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 
        'Stock Month Cover', 'Projected Stock End M1', 'DOS (Days)', 
        'Lead Time Demand', 'Safety Stock', 'Reorder Point (ROP)', 
        'Suggested Order Qty', 'Order Value (IDR)', 'Air Urgent Qty', 'Sea Qty', 
        'Order Value Air', 'Order Value Sea', 'Total Order Value', 
        'Warehouse Space Impact (M1)', 'Cumulative Cash', 'Cumulative WH', 'Priority Rank'
    ]
    
    for col in numeric_columns:
        if col in df_a.columns:
            # Hapus koma/Rp sebelum konversi
            df_a[col] = df_a[col].astype(str).str.replace(r'[Rp, ]', '', regex=True)
            df_a[col] = pd.to_numeric(df_a[col], errors='coerce').fillna(0)
            
    # SORTING BERDASARKAN PRIORITY RANK AGAR CUMULATIVE BEKERJA TEPAT
    if 'Priority Rank' in df_a.columns:
        df_a = df_a.sort_values(by='Priority Rank', ascending=True).reset_index(drop=True)

    st.success("✅ Data berhasil dimuat dan disinkronisasi dari Google Sheets")
except Exception as e:
    st.error(f"❌ Koneksi GSheet Gagal: {e}")
    st.stop()

# --- HEADER ---
st.markdown("<div class='main-header'><h1>🚀 FOOM LAB GLOBAL: S&OP Command Center</h1><p>Strategic Supply & Demand Validation System | Candidate: Mulyanto</p></div>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 PART A: Replenishment & Scenarios", "💀 PART B: Cash Unlock & Dead Stock", "⚙️ PART C: S&OP Governance"])

# ==========================================
# TAB 1: REPLENISHMENT & SCENARIOS
# ==========================================
with tab1:
    st.markdown("## 📈 PART A: 6-MONTH FORECAST & REPLENISHMENT PLAN")
    st.markdown("---")
    
    # ===== PART 1 & 2: LOGIKA & FORECAST TABLE =====
    st.markdown("### 📐 1. Forecast Methodology & Results")
    
    with st.expander("📊 **Klik untuk melihat logika lengkap forecast**", expanded=False):
        col_logic1, col_logic2 = st.columns(2)
        with col_logic1:
            st.markdown("""
            **Metode Forecast (Backend GSheet):**
            * **Linear Trend:** Untuk produk *growth* eksponensial (Device C). Membaca tren kenaikan 3 bulan terakhir.
            * **Seasonal Method:** Untuk produk musiman (Device B).
            * **Moving Average (60-30-10):** Untuk produk stabil (Device A).
            """)
        with col_logic2:
            st.markdown("""
            **Forward-Looking Inventory Policy:**
            * Safety Stock: 15 Hari (*Buffer*)
            * Lead Time: 45 Hari (Kapal Laut)
            * ROP (Reorder Point): Cover 60 Hari
            """)
            
    # Tampilkan Tabel Forecast
    forecast_cols = ['Item', 'Forecast Model', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    if all(c in df_a.columns for c in forecast_cols):
        df_forecast = df_a[forecast_cols].copy()
        df_forecast['Total 6M'] = df_forecast[['M1', 'M2', 'M3', 'M4', 'M5', 'M6']].sum(axis=1)
        
        # Format angka
        for col in ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'Total 6M']:
            df_forecast[col] = df_forecast[col].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df_forecast, use_container_width=True, hide_index=True)

    # ===== PART 3: 3 SCENARIOS COMPARISON =====
    st.markdown("### 🔄 2. Three Scenarios Comparison (Base vs Aggressive vs Downside)")
    
    df_scenarios = df_a[['Item', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6']].copy()
    df_scenarios['Base_Total'] = df_scenarios[['M1', 'M2', 'M3', 'M4', 'M5', 'M6']].sum(axis=1)
    df_scenarios['Base_Avg'] = (df_scenarios['Base_Total'] / 6).round(0)
    df_scenarios['Agg_Total'] = (df_scenarios['Base_Total'] * 1.2).round(0)
    df_scenarios['Agg_Avg'] = (df_scenarios['Agg_Total'] / 6).round(0)
    df_scenarios['Down_Total'] = (df_scenarios['Base_Total'] * 0.8).round(0)
    df_scenarios['Down_Avg'] = (df_scenarios['Down_Total'] / 6).round(0)
    
    comparison_table = df_scenarios[['Item', 'Base_Avg', 'Base_Total', 'Agg_Avg', 'Agg_Total', 'Down_Avg', 'Down_Total']].copy()
    for col in comparison_table.columns:
        if col != 'Item':
            comparison_table[col] = comparison_table[col].apply(lambda x: f"{x:,.0f}")
            
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)
    
    # ===== VISUALISASI FULL TIMELINE (HISTORICAL + FORECAST) =====
    st.markdown("#### 📈 Full Timeline: Historical & Forecast Scenarios")
    
    col_vis1, col_vis2 = st.columns([1, 3])
    
    with col_vis1:
        st.info("💡 **Gunakan filter di bawah** untuk mensimulasikan proyeksi demand dibandingkan dengan data historis.")
        selected_sku = st.selectbox("1️⃣ Pilih SKU:", df_a['Item'].tolist(), key="sku_selector")
        scenario_filter = st.radio("2️⃣ Tampilkan Skenario:", 
                                   ["Semua Skenario", "Base Scenario", "Aggressive (+20%)", "Downside (-20%)"])
    
    # Ambil data SKU terpilih dari DataFrame asli
    sku_data_full = df_a[df_a['Item'] == selected_sku].iloc[0]
    
    # 1. Siapkan Data Historis (Jan - Dec)
    hist_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    hist_values = [sku_data_full[m] for m in hist_months]
    dec_value = hist_values[-1] # Titik sambung untuk grafik forecast
    
    # 2. Siapkan Data Forecast (M1 - M6)
    fcst_months = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    base_values = [sku_data_full[m] for m in fcst_months]
    agg_values = [v * 1.2 for v in base_values]
    down_values = [v * 0.8 for v in base_values]
    
    # 3. Bentuk DataFrame terpisah untuk Plotly
    df_hist = pd.DataFrame({'Bulan': hist_months, 'Demand': hist_values, 'Tipe': 'Historical (Aktual)'})
    
    # (Catatan: Kita tambahkan 'Dec' di awal forecast agar garisnya tersambung mulus/tidak terputus)
    df_base = pd.DataFrame({'Bulan': ['Dec'] + fcst_months, 'Demand': [dec_value] + base_values, 'Tipe': 'Base Forecast'})
    df_agg = pd.DataFrame({'Bulan': ['Dec'] + fcst_months, 'Demand': [dec_value] + agg_values, 'Tipe': 'Aggressive (+20%)'})
    df_down = pd.DataFrame({'Bulan': ['Dec'] + fcst_months, 'Demand': [dec_value] + down_values, 'Tipe': 'Downside (-20%)'})
    
    # 4. Logika Filter Skenario
    plot_data = [df_hist]
    if scenario_filter == "Semua Skenario":
        plot_data.extend([df_base, df_agg, df_down])
    elif scenario_filter == "Base Scenario":
        plot_data.append(df_base)
    elif scenario_filter == "Aggressive (+20%)":
        plot_data.append(df_agg)
    elif scenario_filter == "Downside (-20%)":
        plot_data.append(df_down)
        
    df_plot_final = pd.concat(plot_data, ignore_index=True)
    
    # 5. Render Grafik dengan Plotly
    all_months_ordered = hist_months + fcst_months # Urutan baku X-Axis
    
    fig_line = px.line(
        df_plot_final, 
        x='Bulan', 
        y='Demand', 
        color='Tipe', 
        title=f"End-to-End Demand Visibility: {selected_sku}",
        markers=True,
        color_discrete_map={
            'Historical (Aktual)': '#64748b', # Abu-abu elegan
            'Base Forecast': '#3b82f6',       # Biru
            'Aggressive (+20%)': '#10b981',   # Hijau
            'Downside (-20%)': '#ef4444'      # Merah
        }
    )
    
    # Kunci urutan bulan dan tambahkan garis batas vertikal di bulan Desember
    fig_line.update_xaxes(categoryorder='array', categoryarray=all_months_ordered)
    fig_line.add_vline(x='Dec', line_width=2, line_dash="dot", line_color="gray", annotation_text="Mulai Forecast ➡️", annotation_position="top left")
    fig_line.update_layout(height=400, hovermode='x unified')
    
    with col_vis2:
        st.plotly_chart(fig_line, use_container_width=True)

    # ===== PART 4: STOCK COVER & INVENTORY EXPOSURE =====
    st.markdown("### 📦 3. Stock Health & Replenishment Trigger")
    
    health_cols = ['Item', 'Current Stock', 'Stock Month Cover', 'DOS (Days)', 'DOS Status', 'Reorder Point (ROP)', 'Stock Status vs ROP']
    if all(c in df_a.columns for c in health_cols):
        df_health = df_a[health_cols].copy()
        
        # Format Angka
        for col in ['Current Stock', 'Reorder Point (ROP)', 'DOS (Days)']:
            df_health[col] = df_health[col].apply(lambda x: f"{x:,.0f}")
            
        st.dataframe(df_health, use_container_width=True, hide_index=True)

    # ===== PART 5: REKOMENDASI IMPORT PLAN (MIRROR GSHEET) =====
    st.markdown("### 🚢 4. Import Plan & Cost Strategy (Landed Cost)")
    
    with st.expander("⚙️ Logistik & Warehouse Constraints (GSheet Sync)", expanded=True):
        col_log1, col_log2, col_log3 = st.columns(3)
        with col_log1:
            st.info("🚢 Sea Freight Cost: **10% dari HPP**")
        with col_log2:
            st.warning("✈️ Air Freight Cost: **40% dari HPP**")
        with col_log3:
            wh_utilization = st.progress(85, text="WH Utilization: 85% (51,000 / 60,000 units)")
            st.caption("Sisa kapasitas aman M1: **4,000 units**")

    # Tarik data eksekusi murni dari GSheet
    order_cols = ['Priority Rank', 'Item', 'Current Stock', 'Suggested Order Qty', 'Route (Sea/Air)', 'Air Urgent Qty', 'Sea Qty', 'Total Order Value', 'Warehouse Space Impact (M1)']
    
    if all(c in df_a.columns for c in order_cols):
        display_order = df_a[order_cols].copy()
        display_order['Cost (Billion IDR)'] = (display_order['Total Order Value'] / 1_000_000_000).round(2)
        
        # Format angka string
        for col in ['Current Stock', 'Suggested Order Qty', 'Air Urgent Qty', 'Sea Qty', 'Warehouse Space Impact (M1)']:
            display_order[col] = display_order[col].apply(lambda x: f"{x:,.0f}")
        display_order['Total Order Value'] = display_order['Total Order Value'].apply(lambda x: f"Rp {x:,.0f}")
        
        st.dataframe(display_order.drop(columns=['Total Order Value']), use_container_width=True, hide_index=True)
        
        # Summary Status
        total_cost_miliar = df_a['Total Order Value'].sum() / 1_000_000_000
        total_wh_impact = df_a['Warehouse Space Impact (M1)'].sum()
        
        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            st.metric("💰 Cumulative Cash Out", f"Rp {total_cost_miliar:.2f} Miliar", delta=f"Limit: 4.0 Miliar", delta_color="normal" if total_cost_miliar <= 4.0 else "inverse")
        with col_rec2:
            st.metric("🏭 Cumulative WH Impact (Air Only)", f"{total_wh_impact:,.0f} units", delta=f"Sisa Gudang: 4,000", delta_color="normal" if total_wh_impact <= 4000 else "inverse")
            
        if total_cost_miliar > 4.0 or total_wh_impact > 4000:
            st.error("🚨 **OVER CONSTRAINT!** Cek GSheet kolom Priority Rank. Tunda item non-prioritas!")
        else:
            st.success("✅ **APPROVED:** Eksekusi Order berada di bawah limit Kas dan Gudang.")

    # ===== PART 6: LIVE DEFENSE SCENARIO SIMULATION =====
    st.markdown("---")
    st.markdown("## 🎯 PART D: LIVE DEFENSE SCENARIO SIMULATION")
    st.info("Simulasi interaktif jika Manajemen tiba-tiba memberikan konstrain mendadak saat presentasi.")
    
    scenario_type = st.radio(
        "⚡ Quick Scenario Presets:",
        ["1️⃣ Normal (Base Plan)", "2️⃣ Cash Reduced by 30% (Budget jadi 2.8 Miliar)", "3️⃣ WH Capacity Reduced to 2,000 units"],
        horizontal=True
    )
    
    sim_budget = 4.0
    sim_wh = 4000
    if "Cash Reduced" in scenario_type: sim_budget = 2.8
    elif "WH Capacity" in scenario_type: sim_wh = 2000
    
    col_s1, col_s2 = st.columns(2)
    with col_s1: budget_limit = st.number_input("💰 Budget Limit (Miliar IDR)", 1.0, 10.0, sim_budget, 0.5)
    with col_s2: wh_capacity = st.number_input("🏭 WH Capacity Left (Units)", 1000, 10000, sim_wh, 500)
    
    # Hitung kelayakan skenario berdasarkan data asli GSheet
    if total_cost_miliar > budget_limit or total_wh_impact > wh_capacity:
        st.error(f"🚨 **SKENARIO GAGAL!** Tagihan (Rp {total_cost_miliar:.2f}M / {total_wh_impact:,.0f} unit) melebihi batas baru. Rekomendasi: Tahan/Hold order Prioritas 2 (Device A).")
    else:
        st.success("✅ **SKENARIO AMAN!** Skenario ini masih sanggup dieksekusi dengan Plan saat ini.")


# ==========================================
# TAB 2: DEAD STOCK & CASH UNLOCK (TETAP SAMA)
# ==========================================
with tab2:
    st.markdown("### 💰 The 5 Billion Cash Unlock Masterplan")
    st.warning("🎯 **Target: Unlock minimum IDR 5 Miliar in 90 days**")
    
    st.markdown("#### 🚀 The 90-Day Liquidation Portfolio (Road to 5 Miliar)")
    
    masterplan_data = pd.DataFrame({
        'Category': ['Device Z (Dead Stock)', 'Other Dead Stock (18% of 25 Miliar - Z)', 'Slow Moving (35% of 25 Miliar)'],
        'Inventory Value': ['Rp 1.10 Miliar', 'Rp 3.40 Miliar', 'Rp 8.75 Miliar'],
        'Proposed Strategy': ['Aggressive Bundling & Clearance (-30%)', 'B2B Wholesale / Export "Take-All"', 'E-Commerce Flash Sale (Double Day)'],
        'Target Cash Unlock (Miliar)': [1.1, 2.5, 1.4] 
    })
    
    total_unlock_target = sum(masterplan_data['Target Cash Unlock (Miliar)'])
    
    col_mp1, col_mp2 = st.columns([2, 1])
    with col_mp1:
        st.dataframe(masterplan_data, use_container_width=True, hide_index=True)
    with col_mp2:
        fig_gauge_5b = go.Figure(go.Indicator(
            mode="gauge+number", value=total_unlock_target, number={'valueformat': '.1f', 'prefix': 'Rp ', 'suffix': ' Miliar'},
            title={'text': "Total Cash Unlock"},
            gauge={'axis': {'range': [None, 6]}, 'bar': {'color': "#10b981"}, 'steps': [{'range': [0, 5], 'color': "#fee2e2"}, {'range': [5, 6], 'color': "#dcfce7"}], 'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 5}}
        ))
        fig_gauge_5b.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge_5b, use_container_width=True)
        st.success("✅ **Target IDR 5 Miliar Terpenuhi!**")

    st.markdown("---")
    st.markdown("### 📱 Device Z - Detailed Analysis")
    col_z_detail1, col_z_detail2, col_z_detail3 = st.columns(3)
    
    stock_z = 12000
    inv_value_z = 1.1e9 
    unit_cost_z = inv_value_z / stock_z 
    monthly_sales_z = 500
    
    with col_z_detail1:
        st.markdown("""<div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'><h4 style='margin-top:0; color:#334155;'>📊 Stock & Value</h4><table style='width:100%'><tr><td>Current Stock</td><td><b>{:,} units</b></td></tr><tr><td>Inventory Value</td><td><b>Rp {:.2f} Miliar</b></td></tr><tr><td>Unit Cost (HPP)</td><td><b>Rp {:,.0f}</b></td></tr></table></div>""".format(stock_z, inv_value_z/1e9, unit_cost_z), unsafe_allow_html=True)
    
    with col_z_detail2:
        st.markdown("""<div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'><h4 style='margin-top:0; color:#334155;'>💰 Sales & Margin</h4>""", unsafe_allow_html=True)
        estimated_selling_price = st.slider("Estimasi Harga Jual Normal (Rp/unit)", min_value=int(unit_cost_z * 1.2), max_value=int(unit_cost_z * 2.5), value=int(unit_cost_z * 1.8), step=5000, format="Rp %d", key="price_z")
        normal_margin = (estimated_selling_price - unit_cost_z) / estimated_selling_price * 100
        monthly_revenue = monthly_sales_z * estimated_selling_price
        annual_revenue_potential = monthly_revenue * 12
        st.markdown("""<table style='width:100%'><tr><td>Harga Jual Estimasi</td><td><b>Rp {:,.0f}</b></td></tr><tr><td>Margin Normal</td><td><b style='color:{};'>{:.1f}%</b></td></tr><tr><td>Monthly Revenue</td><td><b>Rp {:,.0f} Juta</b></td></tr><tr><td>Annual Potential</td><td><b>Rp {:,.0f} Juta</b></td></tr></table></div>""".format(estimated_selling_price, '#22c55e' if normal_margin > 30 else '#eab308' if normal_margin > 15 else '#ef4444', normal_margin, monthly_revenue/1e6, annual_revenue_potential/1e6), unsafe_allow_html=True)
    
    with col_z_detail3:
        months_to_deplete = stock_z / monthly_sales_z
        stock_at_launch = stock_z - (monthly_sales_z * 3) 
        value_at_risk = stock_at_launch * unit_cost_z
        st.markdown("""<div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'><h4 style='margin-top:0; color:#334155;'>⏱️ Depletion & Risk</h4><table style='width:100%'><tr><td>Natural Depletion</td><td><b style='color:#ef4444;'>{:.0f} bulan</b></td></tr><tr><td>Replacement Launch</td><td><b>3 bulan</b></td></tr><tr><td>Stock at Launch</td><td><b>{:,} units</b></td></tr><tr><td>Value at Risk</td><td><b style='color:#ef4444;'>Rp {:,.0f} Juta</b></td></tr></table></div>""".format(months_to_deplete, stock_at_launch, value_at_risk/1e6), unsafe_allow_html=True)
    
    st.markdown("#### ⚖️ Margin vs Cash Trade-off Simulation")
    col_trade1, col_trade2 = st.columns(2)
    
    with col_trade1:
        st.markdown("**🎛️ Strategi Likuidasi Device Z**")
        units_to_liquidate = st.slider("Jumlah unit yang dilikuidasi", min_value=1000, max_value=12000, value=12000, step=1000, key="units_z")
        discount_rate = st.slider("Diskon yang diberikan (%)", min_value=10, max_value=70, value=30, step=5, key="discount_z")
        
        selling_price_after_discount = estimated_selling_price * (1 - discount_rate/100)
        revenue = units_to_liquidate * selling_price_after_discount
        cost = units_to_liquidate * unit_cost_z
        gross_profit = revenue - cost
        margin_after_discount = (gross_profit / revenue * 100) if revenue > 0 else 0
        normal_profit_per_unit = estimated_selling_price - unit_cost_z
        normal_margin_total = units_to_liquidate * normal_profit_per_unit
        margin_erosion = normal_margin_total - gross_profit
        
    with col_trade2:
        st.markdown("**📊 Hasil Simulasi**")
        results_trade = pd.DataFrame({
            'Metric': ['Revenue (Cash Unlock)', 'HPP', 'Gross Profit', 'Margin %', 'Margin Erosion vs Normal'],
            'Value': [f"Rp {revenue/1e6:,.0f} Juta", f"Rp {cost/1e6:,.0f} Juta", f"Rp {gross_profit/1e6:,.0f} Juta", f"{margin_after_discount:.1f}%", f"Rp {margin_erosion/1e6:,.0f} Juta"]
        })
        st.dataframe(results_trade, use_container_width=True, hide_index=True)
        if margin_after_discount > 20: st.success(f"✅ Margin sehat ({margin_after_discount:.1f}%)")
        elif margin_after_discount > 10: st.warning(f"⚠️ Margin tipis ({margin_after_discount:.1f}%)")
        else: st.error(f"🔴 Margin sangat rendah ({margin_after_discount:.1f}%)")

    st.markdown("#### 🛡️ Proposed Portfolio Clean-up Governance")
    st.info("SOP untuk mencegah kejadian Overstock Device Z terulang di masa depan.")
    st.markdown("""
    * **Phase-Out Trigger (T-4 Months):** Segala bentuk aktivitas *Import / Procurement* untuk produk lama wajib dihentikan **4 bulan** sebelum peluncuran generasi pengganti.
    * **Auto-Clearance Mandate (T-2 Months):** Jika H-60 hari produk lama masih memiliki stok >2 bulan, tim *Marketing* diizinkan mengeksekusi *Bundling Promo* otomatis.
    """)

# ==========================================
# TAB 3: S&OP RESTRUCTURE DESIGN (TETAP SAMA)
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
        
        st.markdown("#### 📊 S&OP Timeline")
        timeline_data = pd.DataFrame({
            'Task': ['Demand Review', 'Supply Review', 'Pre-S&OP', 'Executive S&OP'],
            'Start': ['2024-01-01', '2024-01-08', '2024-01-15', '2024-01-22'],
            'Finish': ['2024-01-07', '2024-01-14', '2024-01-21', '2024-01-28'],
            'Owner': ['Sales', 'Supply Chain', 'Lead', 'Management']
        })
        fig_timeline = px.timeline(timeline_data, x_start='Start', x_end='Finish', y='Task', color='Owner', title="S&OP Monthly Cycle", color_discrete_map={'Sales': '#3b82f6', 'Supply Chain': '#10b981', 'Lead': '#f59e0b', 'Management': '#ef4444'})
        fig_timeline.update_layout(xaxis=dict(title="Week of Month", tickformat="%d %b"), yaxis=dict(title="", autorange="reversed"), height=300, showlegend=True)
        st.plotly_chart(fig_timeline, use_container_width=True)
        
    with col_c2:
        st.markdown("#### 🎯 KPI Dashboard")
        kpi_data = pd.DataFrame({'KPI': ['Forecast Accuracy', 'Service Level', 'Inventory Turnover', 'Dead Stock %'], 'Target': ['85%', '98%', '6x', '<5%'], 'Current': ['62%', '85%', '3.2x', '18%'], 'Status': ['🔴', '🟡', '🟡', '🔴']})
        st.dataframe(kpi_data, use_container_width=True, hide_index=True)
        fig_gauge = go.Figure(go.Indicator(mode="gauge+number+delta", value=62, domain={'x': [0, 1], 'y': [0, 1]}, title={'text': "Forecast Accuracy"}, delta={'reference': 85, 'increasing': {'color': "red"}}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#3b82f6"}, 'steps': [{'range': [0, 50], 'color': '#fee2e2'}, {'range': [50, 75], 'color': '#fef9c3'}, {'range': [75, 100], 'color': '#dcfce7'}], 'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 85}}))
        fig_gauge.update_layout(height=200, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 Performance & Gap Analysis")
    col_gap1, col_gap2 = st.columns(2)

    with col_gap1:
        st.markdown("#### 🎯 Historical Forecast Accuracy (62%)")
        acc_data = pd.DataFrame({'Month': ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 'Actual Sales': [9800, 10000, 10200, 10500, 11100, 11800], 'Sales Forecast': [15800, 16100, 16400, 16900, 17900, 19000]})
        acc_data['Overforecast (Error)'] = acc_data['Sales Forecast'] - acc_data['Actual Sales']
        fig_acc = px.bar(acc_data, x='Month', y=['Actual Sales', 'Overforecast (Error)'], title="Actual vs Forecast (Gap = Dead Stock Potential)", barmode='stack', color_discrete_map={'Actual Sales': '#3b82f6', 'Overforecast (Error)': '#ef4444'})
        fig_acc.update_layout(height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_acc, use_container_width=True)

    with col_gap2:
        st.markdown("#### 📉 Target Inventory Reduction (-20%)")
        inv_trajectory = pd.DataFrame({'Month': ['Current', 'M1', 'M2', 'M3 (Unlock Phase)', 'M4', 'M5', 'M6 (Target)'], 'Inventory Value': [25.0, 24.5, 24.0, 20.0, 19.5, 20.0, 20.0], 'Target Line': [25.0, 24.1, 23.3, 22.5, 21.6, 20.8, 20.0]})
        fig_inv = go.Figure()
        fig_inv.add_trace(go.Scatter(x=inv_trajectory['Month'], y=inv_trajectory['Inventory Value'], mode='lines+markers+text', name='Projected Value', line=dict(color='#3b82f6', width=3), text=inv_trajectory['Inventory Value'], textposition="top right"))
        fig_inv.add_trace(go.Scatter(x=inv_trajectory['Month'], y=inv_trajectory['Target Line'], mode='lines', name='-20% Target Path', line=dict(color='#10b981', width=2, dash='dash')))
        fig_inv.update_layout(title="Inventory Trajectory (Billion IDR)", height=300, yaxis_title="IDR (Miliar)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_inv, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🛡️ Professional Challenge Strategy (Menantang Target Sales +50%)")
    col_strat1, col_strat2 = st.columns(2)
    with col_strat1:
        st.markdown("<div class='card'><h4>🔍 Triangulation Method</h4><p><b>Question:</b> \"How does this +50% growth compare to last year's actual + promotion impact?\"</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'><h4>⚠️ Risk Assessment</h4><p><b>Logic:</b> With 62% forecast accuracy, historical error = ±20%. I recommend planning for +30% with upside option.</p></div>", unsafe_allow_html=True)
    with col_strat2:
        st.markdown("<div class='card'><h4>📊 Scenario Planning</h4><p><b>Question:</b> \"What if we only achieve 60% of target? What's the inventory impact?\"</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'><h4>🔄 Phased Commitment</h4><p><b>Logic:</b> Split target. Commit inventory for +25% now. Remaining via air freight if confirmed by M2.</p></div>", unsafe_allow_html=True)
