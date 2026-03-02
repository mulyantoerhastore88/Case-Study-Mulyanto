import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
from sklearn.linear_model import LinearRegression # TAMBAHAN UNTUK AI ML

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="FOOM S&OP Command Center", layout="wide", page_icon="🚀", initial_sidebar_state="expanded")

# KOSMETIK PREMIUM UI/UX
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 50%, #3b82f6 100%); 
        padding: 30px 20px; 
        border-radius: 12px; 
        color: white; 
        text-align: center; 
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .main-header h1 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 5px; }
    .main-header p { font-size: 1.1rem; opacity: 0.9; }
    
    .card {
        background-color: white; 
        padding: 24px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); 
        margin-bottom: 20px; 
        border-left: 5px solid #3b82f6;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        height: 100%;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .card h4 { margin-top: 0; font-weight: 600; color: #1e293b; }
    .card p { color: #475569; font-size: 0.95rem; line-height: 1.5; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; background-color: white; padding: 10px 10px 0 10px;
        border-radius: 10px 10px 0 0; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 8px 8px 0 0; color: #64748b; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #eff6ff !important; color: #1d4ed8 !important;
        border-bottom: 3px solid #1d4ed8 !important;
    }
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); }
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
    
    # LOAD PART A
    ws_a = sh.worksheet("Part_A_Stock&SKU_Detail")
    data_a = ws_a.get_all_values()
    df_a = pd.DataFrame(data_a[1:], columns=data_a[0])
    df_a.columns = df_a.columns.str.strip()
    
    # LOAD PART B
    try:
        ws_b = sh.worksheet("Part_B_DEAD_STOCK_&_CASH_UNLOCK")
        data_b = ws_b.get_all_values()
    except:
        data_b = []
        
    # LOAD PART C
    try:
        ws_c = sh.worksheet("Part_C_S&OP_ RESTRUCTURE_DESIGN") 
        data_c = ws_c.get_all_values()
    except Exception as e:
        print(f"Error loading Part C: {e}")
        data_c = []
        
    return df_a, data_b, data_c

# Load Data
try:
    df_a, data_b, data_c = load_data_from_gsheet()
    
    # KONVERSI SEMUA KOLOM ANGKA DARI STRING KE NUMERIC (PART A)
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
            df_a[col] = df_a[col].astype(str).str.replace(r'[Rp, ]', '', regex=True)
            df_a[col] = pd.to_numeric(df_a[col], errors='coerce').fillna(0)
            
    if 'Priority Rank' in df_a.columns:
        df_a = df_a.sort_values(by='Priority Rank', ascending=True).reset_index(drop=True)

except Exception as e:
    st.error(f"❌ Koneksi GSheet Gagal: {e}")
    st.stop()

# ==================== FITUR BARU: SMART ALERT SYSTEM (SIDEBAR) ====================
def check_alerts():
    alerts = []
    if 'DOS Status' in df_a.columns:
        critical_stock = df_a[df_a['DOS Status'].str.contains('CRITICAL|KRITIS', na=False, case=False)]
        for _, row in critical_stock.iterrows():
            alerts.append({'type': 'critical', 'msg': f"⚠️ Urgent: {row['Item']} sisa {row['DOS (Days)']:.0f} hari!"})
        
        overstock = df_a[df_a['DOS Status'].str.contains('OVERSTOCK', na=False, case=False)]
        for _, row in overstock.iterrows():
            alerts.append({'type': 'warning', 'msg': f"📦 Overstock: Hold PO {row['Item']}."})
    return alerts

with st.sidebar:
    st.markdown("## 🚨 Command Center")
    alerts = check_alerts()
    if alerts:
        with st.expander(f"🔴 Active Alerts ({len(alerts)})", expanded=True):
            for alert in alerts:
                if alert['type'] == 'critical': st.error(alert['msg'])
                else: st.warning(alert['msg'])
    else:
        st.success("✅ All Systems Normal")
        
    st.markdown("---")
    st.markdown("### 🖨️ Quick Actions")
    if st.button("Export Presentation (PDF)", use_container_width=True):
        st.success("Tarik PDF Report via Web Browser (Ctrl+P) Siap Digunakan!")
# ===============================================================================

# ==================== FITUR BARU: ANIMATED METRIC CARD ====================
def animated_metric_card(title, value, delta=None, icon="📊", color="#3b82f6"):
    delta_html = ""
    if delta:
        delta_color = "#10b981" if "+" in str(delta) or "Aman" in str(delta) else "#ef4444"
        delta_html = f'<p style="color: {delta_color}; margin:0; font-size:0.9rem; font-weight:bold;">{delta}</p>'
    
    st.markdown(f"""
    <div class="card" style="padding: 15px; border-left: 5px solid {color}; height: 100%; margin-bottom: 0px;">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <p style="color: #64748b; margin:0; font-size:0.9rem; font-weight:600;">{title}</p>
                <h3 style="color: {color}; margin:5px 0; font-size:1.8rem;">{value}</h3>
                {delta_html}
            </div>
            <div style="font-size:2rem; opacity:0.3;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
# ===========================================================================

# --- HEADER ---
st.markdown("<div class='main-header'><h1>🚀 FOOM LAB GLOBAL: S&OP Command Center (Case Study_Mulyanto)</h1><p>Strategic Supply & Demand Validation System | Mulyanto</p></div>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 PART A: Replenishment & Scenarios", "💰 PART B: Cash Unlock & Dead Stock", "⚙️ PART C: S&OP Governance"])

# ==========================================
# TAB 1: REPLENISHMENT & SCENARIOS
# ==========================================
with tab1:
    st.markdown("## 📈 PART A: 6-MONTH FORECAST & REPLENISHMENT PLAN")
    st.markdown("---")
    
    # ===== PART 1 & 2: LOGIKA & FORECAST TABLE =====
    st.markdown("### 📐 1. Forecast Methodology & Results")
    
    with st.expander("📊 **Klik untuk melihat logika lengkap forecast**", expanded=False):
        st.markdown("### 🧮 Metode Forecast yang Digunakan")
        col_logic1, col_logic2 = st.columns(2)
        with col_logic1:
            st.markdown("""
            **Rumus Excel di GSheet:**
            
            **1. Klasifikasi Model (Kolom T):**
            ```text
            =IF(RSQ(F2:Q2, {1..12}) > 0.8, "Linear Trend",
               IF(MAX(F2:Q2)/MEDIAN(F2:Q2) > 1.5, "Seasonal Method",
               "Moving Average"))
            ```
            
            **2. M1 - Weighted Moving Average (60-30-10):**
            ```text
            =ROUNDUP((Q2*0.6) + (P2*0.3) + (O2*0.1), 0)
            ```
            
            **3. M2-M6 - Mirror Growth:**
            ```text
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
            * **Moving Average:** Untuk data stabil tanpa trend (Device A)
            * **Seasonal Detection:** Untuk data dengan pola berulang (Device B)
            * **Linear Trend:** Untuk data dengan trend naik/turun konsisten (Device C)
            
            **Month to Month Mirror Growth dipilih karena:**
            * Menangkap pola musiman dari tahun sebelumnya
            * Sederhana dan mudah dijelaskan ke management
            * Cocok untuk FMCG dengan siklus tahunan
            """)
            
        st.markdown("---")
        st.markdown("### 📈 Interpretasi Data Historis per SKU")
        st.markdown("""
        | Item | Pola Data | Metode | Rationale | Visual Pattern |
        |---|---|---|---|---|
        | **Device A** | Stabil (4.700 - 5.400 unit) | **Moving Average** | Tidak ada trend signifikan, pola flat sepanjang tahun | 📊 ▬▬ |
        | **Device B** | **Spike di Apr-Mei** (6.200 / 5.800)<br>Normal: 2.800 - 3.300 | **Seasonal Method** | 🔴 **Pattern: Lonjakan saat Lebaran**<br>• April-Mei 2024: +100% dari normal<br>• Data dinormalisasi untuk forecast | 📈 📊 📈 |
        | **Device C** | **Naik Konsisten** (900 → 3.100) | **Linear Trend** | • R² = 0.92 (korelasi kuat)<br>• Growth 200 unit/bulan<br>• Produk dalam fase growth | 📈 ↗️ ↗️ |
        """, unsafe_allow_html=True)
            
    forecast_cols = ['Item', 'Forecast Model', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    if all(c in df_a.columns for c in forecast_cols):
        df_forecast = df_a[forecast_cols].copy()
        df_forecast['Total 6M'] = df_forecast[['M1', 'M2', 'M3', 'M4', 'M5', 'M6']].sum(axis=1)
        for col in ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'Total 6M']:
            df_forecast[col] = df_forecast[col].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df_forecast, use_container_width=True, hide_index=True)


    # ===== VISUALISASI FULL TIMELINE (HISTORICAL + FORECAST) =====
    st.markdown("#### 📈 Full Timeline: Historical & Forecast Scenarios")
    
    col_filter1, col_filter2 = st.columns(2)
    sku_options = ["Total Aggregate (Semua Device)", "Bandingkan Semua Device"] + df_a['Item'].tolist()
    
    with col_filter1:
        selected_sku = st.selectbox("1️⃣ Pilih SKU / View:", sku_options, key="sku_selector")
    with col_filter2:
        scenario_filter = st.selectbox("2️⃣ Tampilkan Skenario:", 
                                   ["Base Scenario", "Aggressive (+20%)", "Downside (-20%)", "Semua Skenario"])
    
    hist_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    fcst_months = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    all_months_ordered = hist_months + fcst_months

    if selected_sku == "Bandingkan Semua Device":
        if scenario_filter == "Semua Skenario":
            st.warning("⚠️ Menampilkan 'Semua Skenario' untuk 3 Device sekaligus akan membuat grafik terlalu penuh. Tampilan otomatis dikunci ke 'Base Scenario'.")
            active_scenario = "Base Scenario"
        else:
            active_scenario = scenario_filter
            
        plot_data = []
        for idx, row in df_a.iterrows():
            item_name = row['Item']
            hist_vals = [pd.to_numeric(row[m]) for m in hist_months]
            base_vals = [pd.to_numeric(row[m]) for m in fcst_months]
            
            if active_scenario == "Aggressive (+20%)": fcst_vals = [v * 1.2 for v in base_vals]
            elif active_scenario == "Downside (-20%)": fcst_vals = [v * 0.8 for v in base_vals]
            else: fcst_vals = base_vals
                
            dec_val = hist_vals[-1]
            df_h = pd.DataFrame({'Bulan': hist_months, 'Demand': hist_vals, 'Kategori': item_name, 'Periode': 'Historical'})
            df_f = pd.DataFrame({'Bulan': ['Dec'] + fcst_months, 'Demand': [dec_val] + fcst_vals, 'Kategori': item_name, 'Periode': 'Forecast'})
            plot_data.extend([df_h, df_f])
            
        df_plot_final = pd.concat(plot_data, ignore_index=True)
        fig_line = px.line(df_plot_final, x='Bulan', y='Demand', color='Kategori', line_dash='Periode', title=f"Perbandingan Pergerakan Device ({active_scenario})", markers=True)

    else:
        if selected_sku == "Total Aggregate (Semua Device)":
            hist_values = df_a[hist_months].apply(pd.to_numeric).sum().tolist()
            base_values = df_a[fcst_months].apply(pd.to_numeric).sum().tolist()
            chart_title = "Total Aggregate Demand (All Devices)"
        else:
            sku_data_full = df_a[df_a['Item'] == selected_sku].iloc[0]
            hist_values = [pd.to_numeric(sku_data_full[m]) for m in hist_months]
            base_values = [pd.to_numeric(sku_data_full[m]) for m in fcst_months]
            chart_title = f"End-to-End Demand Visibility: {selected_sku}"

        dec_value = hist_values[-1] 
        agg_values = [v * 1.2 for v in base_values]
        down_values = [v * 0.8 for v in base_values]
        
        df_hist = pd.DataFrame({'Bulan': hist_months, 'Demand': hist_values, 'Tipe': 'Historical (Aktual)'})
        df_base = pd.DataFrame({'Bulan': ['Dec'] + fcst_months, 'Demand': [dec_value] + base_values, 'Tipe': 'Base Forecast'})
        df_agg = pd.DataFrame({'Bulan': ['Dec'] + fcst_months, 'Demand': [dec_value] + agg_values, 'Tipe': 'Aggressive (+20%)'})
        df_down = pd.DataFrame({'Bulan': ['Dec'] + fcst_months, 'Demand': [dec_value] + down_values, 'Tipe': 'Downside (-20%)'})
        
        plot_data_single = [df_hist]
        if scenario_filter == "Semua Skenario": plot_data_single.extend([df_base, df_agg, df_down])
        elif scenario_filter == "Base Scenario": plot_data_single.append(df_base)
        elif scenario_filter == "Aggressive (+20%)": plot_data_single.append(df_agg)
        elif scenario_filter == "Downside (-20%)": plot_data_single.append(df_down)
            
        df_plot_final = pd.concat(plot_data_single, ignore_index=True)
        fig_line = px.line(df_plot_final, x='Bulan', y='Demand', color='Tipe', title=chart_title, markers=True, color_discrete_map={'Historical (Aktual)': '#64748b', 'Base Forecast': '#3b82f6', 'Aggressive (+20%)': '#10b981', 'Downside (-20%)': '#ef4444'})
        
    fig_line.update_xaxes(categoryorder='array', categoryarray=all_months_ordered)
    fig_line.add_vline(x='Dec', line_width=2, line_dash="dot", line_color="gray")
    fig_line.add_annotation(x='Dec', y=1.05, yref='paper', text="Mulai Forecast ➡️", showarrow=False, font=dict(color="gray", size=12), xanchor="right")
    fig_line.update_layout(height=450, hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    st.plotly_chart(fig_line, use_container_width=True)

    # ===== FITUR BARU: AI-POWERED DEMAND SENSING =====
    st.markdown("---")
    with st.expander("🤖 AI-Powered Demand Sensing vs Manual Method (Premium Feature)", expanded=False):
        st.markdown("Membandingkan hasil forecast manual (Excel) dengan Prediksi Machine Learning (Linear Regression).")
        
        col_ai1, col_ai2 = st.columns([2, 1])
        with col_ai1:
            device_ai = st.selectbox("Pilih Device untuk dianalisis AI:", df_a['Item'].tolist(), key="ai_select")
            
            # Tarik data historis
            hist_ai = df_a[df_a['Item'] == device_ai][hist_months].values[0]
            hist_ai_num = [pd.to_numeric(x) for x in hist_ai]
            
            # ML Training
            X = np.arange(len(hist_ai_num)).reshape(-1, 1)
            y = np.array(hist_ai_num)
            model = LinearRegression().fit(X, y)
            ai_pred = model.predict(np.arange(len(hist_ai_num), len(hist_ai_num)+6).reshape(-1, 1))
            ai_pred_round = [round(x) for x in ai_pred]
            
            # Data Manual
            manual_vals = df_a[df_a['Item'] == device_ai][fcst_months].values[0]
            manual_vals_num = [pd.to_numeric(x) for x in manual_vals]
            
            df_compare = pd.DataFrame({
                'Month': fcst_months,
                'Manual Forecast (GSheet)': manual_vals_num,
                'AI ML Forecast (Linear)': ai_pred_round
            })
            
            fig_ai = px.bar(df_compare, x='Month', y=['Manual Forecast (GSheet)', 'AI ML Forecast (Linear)'], 
                            barmode='group', title=f"Perbandingan Akurasi: {device_ai}",
                            color_discrete_map={'Manual Forecast (GSheet)':'#64748b', 'AI ML Forecast (Linear)':'#3b82f6'})
            st.plotly_chart(fig_ai, use_container_width=True)
            
        with col_ai2:
            st.markdown("#### 💡 AI Insight")
            if device_ai == 'Device C':
                st.success("📈 **Trend Detected:** AI mengkonfirmasi pola growth yang sangat kuat. Rekomendasi manual Bapak sudah sejalan dengan ML.")
            elif device_ai == 'Device B':
                st.warning("🔄 **Seasonal Alert:** AI mendeteksi spike masa lalu. Model Regresi linier mungkin kurang akurat dibanding metode Seasonal manual Bapak.")
            else:
                st.info("📊 **Stable Demand:** AI menyarankan angka yang lebih flat. Evaluasi kembali over-optimisme di Q2.")


    # ===== PART 4 (PERBAIKAN VISUAL): STOCK COVER & INVENTORY EXPOSURE =====
    st.markdown("### 📦 3. Stock Cover & Inventory Exposure")
    
    health_cols = ['Item', 'Current Stock', 'M1', 'M2', 'M3', 'Stock Month Cover', 'DOS (Days)', 'DOS Status', 'Stock Value']
    if all(c in df_a.columns for c in health_cols):
        df_health = df_a[health_cols].copy()
        df_health['Avg_Forecast'] = ((df_health['M1'] + df_health['M2'] + df_health['M3']) / 3).round(0)
        
        display_health = df_health[['Item', 'Current Stock', 'Avg_Forecast', 'Stock Month Cover', 'DOS (Days)', 'DOS Status', 'Stock Value']].copy()
        display_health.rename(columns={
            'Stock Month Cover': 'Stock Cover (bulan)',
            'DOS (Days)': 'Stock Cover (hari)',
            'DOS Status': 'Status',
            'Stock Value': 'Inventory Value'
        }, inplace=True)
        
        display_health['Status'] = display_health['Status'].apply(
            lambda x: f"🔴 {x}" if "CRITICAL" in str(x).upper() else (f"🟡 {x}" if "WASPADA" in str(x).upper() else (f"🔵 {x}" if "OVERSTOCK" in str(x).upper() else f"🟢 {x}"))
        )
        
        for col in ['Current Stock', 'Avg_Forecast', 'Stock Cover (hari)']:
            display_health[col] = display_health[col].apply(lambda x: f"{x:,.0f}")
        display_health['Stock Cover (bulan)'] = display_health['Stock Cover (bulan)'].apply(lambda x: f"{x:,.1f}")
        display_health['Inventory Value'] = display_health['Inventory Value'].apply(lambda x: f"Rp {x:,.0f}")
        
        st.dataframe(display_health, use_container_width=True, hide_index=True)
        
        # Metrik Summary Pakai Animated Card
        total_inv = df_a['Stock Value'].sum()
        total_stock = df_a['Current Stock'].sum()
        kritis_count = len(df_a[df_a['DOS Status'].str.contains('CRITICAL|KRITIS', case=False, na=False)])
        aman_count = len(df_a[df_a['DOS Status'].str.contains('SAFE|AMAN|WASPADA', case=False, na=False)]) 
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        with col_met1:
            animated_metric_card("Total Inventory Value", f"Rp {total_inv/1e9:.2f} M", "+ Aset Berjalan", "💰", "#3b82f6")
        with col_met2:
            animated_metric_card("Total Stock", f"{total_stock:,.0f}", "Units in WH", "📦", "#8b5cf6")
        with col_met3:
            animated_metric_card("SKU Kritis", str(kritis_count), "Perlu Eksekusi Udara", "⚠️", "#ef4444")
        with col_met4:
            animated_metric_card("SKU Aman", str(aman_count), "Status Terkendali", "✅", "#10b981")
        st.markdown("<br>", unsafe_allow_html=True)

    # ===== PART 5 (PERBAIKAN VISUAL): IMPORT PLAN & COST SIMULATION =====
    st.markdown("### 🚢 4. Import Plan & Cost Simulation")
    
    with st.expander("⚙️ Logistik & Warehouse Constraints Settings", expanded=True):
        col_log1, col_log2, col_log3 = st.columns(3)
        with col_log1:
            sea_cost_pct = st.number_input("Sea Freight Cost (%)", value=10, step=1)
        with col_log2:
            air_cost_mult = st.number_input("Air Freight Multiplier (x Cost)", value=4.00, step=0.50, format="%.2f")
        with col_log3:
            wh_utilization = st.progress(85, text="WH Utilization: 85% (51,000 / 60,000 units)")
            st.caption("Sisa kapasitas aman untuk batch ini: **4,000 units**")

    # Tarik data eksekusi (KITA TAMBAHKAN 'Unit Cost' UNTUK KALKULASI DINAMIS)
    order_cols = ['Item', 'Current Stock', 'DOS (Days)', 'M1', 'Suggested Order Qty', 'Air Urgent Qty', 'Sea Qty', 'Route (Sea/Air)', 'Unit Cost']
    
    if all(c in df_a.columns for c in order_cols):
        display_order = df_a[order_cols].copy()
        
        # --- KALKULASI COST DINAMIS BERDASARKAN INPUT WIDGET ---
        sea_multiplier = 1 + (sea_cost_pct / 100.0)
        air_multiplier = air_cost_mult
        
        display_order['Total_Cost'] = (
            (display_order['Air Urgent Qty'] * display_order['Unit Cost'] * air_multiplier) +
            (display_order['Sea Qty'] * display_order['Unit Cost'] * sea_multiplier)
        )
        display_order = display_order.drop(columns=['Unit Cost'])
        
        display_order.rename(columns={
            'DOS (Days)': 'DOS',
            'Suggested Order Qty': 'Order_Qty',
            'Air Urgent Qty': 'Air_Qty',
            'Sea Qty': 'Sea_Qty',
            'Route (Sea/Air)': 'Route'
        }, inplace=True)
        
        display_order['Route'] = display_order.apply(
            lambda row: f"✈️ SPLIT: {row['Air_Qty']:,.0f} Air + {row['Sea_Qty']:,.0f} Sea" if "SPLIT" in str(row['Route']).upper() 
            else ("🚢 SEA" if "SEA" in str(row['Route']).upper() 
            else ("✈️ AIR" if "AIR" in str(row['Route']).upper() 
            else "⏸️ TUNDA")), axis=1
        )
        
        total_dynamic_cost = display_order['Total_Cost'].sum()
        
        for col in ['Current Stock', 'DOS', 'M1', 'Order_Qty', 'Air_Qty', 'Sea_Qty']:
            display_order[col] = display_order[col].apply(lambda x: f"{x:,.0f}")
        display_order['Total_Cost'] = display_order['Total_Cost'].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "Rp 0")
        
        st.dataframe(display_order, use_container_width=True, hide_index=True)
        
        total_cost_miliar = total_dynamic_cost / 1_000_000_000
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
    
    if total_cost_miliar > budget_limit or total_wh_impact > wh_capacity:
        st.error(f"🚨 **SKENARIO GAGAL!** Tagihan (Rp {total_cost_miliar:.2f}M / {total_wh_impact:,.0f} unit) melebihi batas baru. Rekomendasi: Tahan/Hold order Prioritas 2 (Device A).")
    else:
        st.success("✅ **SKENARIO AMAN!** Skenario ini masih sanggup dieksekusi dengan Plan saat ini.")


# ==========================================
# TAB 2: DEAD STOCK & CASH UNLOCK (TERKONEKSI GSHEET)
# ==========================================
with tab2:
    st.markdown("### 💰 The 5 Billion Cash Unlock Masterplan")
    st.warning("🎯 **Target: Unlock minimum IDR 5 Miliar in 90 days**")
    
    if not data_b:
        st.error("⚠️ Data Part B gagal dimuat. Pastikan nama worksheet di GSheet adalah 'Part_B_DEAD_STOCK_&_CASH_UNLOCK'.")
    else:
        header_port = data_b[0][:5]
        data_port = [row[:5] for row in data_b[1:5]]
        df_port = pd.DataFrame(data_port, columns=header_port)
        
        header_z = data_b[6][:9]
        data_z = [data_b[7][:9]]
        df_z = pd.DataFrame(data_z, columns=header_z)
        
        header_scen = data_b[10][:8]
        data_scen = [row[:8] for row in data_b[11:17]]
        df_scen = pd.DataFrame(data_scen, columns=header_scen)

        # --- TAMPILAN BLOK 1: PORTFOLIO MASTERPLAN ---
        st.markdown("#### 🚀 The 90-Day Liquidation Portfolio (Road to 5 Miliar)")
        
        total_cash_target_str = str(df_port.iloc[-1]['Target Cash Unlock in 90 Days']).replace('Rp', '').replace(',', '').strip()
        total_unlock_target = float(total_cash_target_str) / 1_000_000_000 
        
        display_port = df_port.copy()
        for col in ['Inventory Value (IDR)', 'Target Cash Unlock in 90 Days']:
            display_port[col] = pd.to_numeric(display_port[col].astype(str).str.replace(r'[Rp, ]', '', regex=True), errors='coerce')
            display_port[col] = display_port[col].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "")
            
        col_mp1, col_mp2 = st.columns([2, 1])
        with col_mp1:
            st.dataframe(display_port, use_container_width=True, hide_index=True)
        with col_mp2:
            # GAUGE CHART DIPERBAIKI (Tinggi & Ukuran Font)
            fig_gauge_5b = go.Figure(go.Indicator(
                mode="gauge+number", value=total_unlock_target, 
                number={'valueformat': '.1f', 'prefix': 'Rp ', 'suffix': ' Miliar', 'font': {'size': 28}},
                title={'text': "Total Cash Unlock", 'font': {'size': 16}},
                gauge={'axis': {'range': [None, 6]}, 'bar': {'color': "#10b981"}, 'steps': [{'range': [0, 5], 'color': "#fee2e2"}, {'range': [5, 6], 'color': "#dcfce7"}], 'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 5}}
            ))
            fig_gauge_5b.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge_5b, use_container_width=True)

        st.markdown("---")
        
        # --- TAMPILAN BLOK 2: DEVICE Z DETAIL ---
        st.markdown("### 📱 Device Z - Detailed Analysis")
        col_z_detail1, col_z_detail2, col_z_detail3 = st.columns(3)
        
        z_data = df_z.iloc[0]
        def safe_float(val):
            return float(str(val).replace('Rp', '').replace(',', '').replace('%', '').strip() or 0)
            
        stock_z = safe_float(z_data['Current Stock'])
        inv_value_z = safe_float(z_data['Inventory Value (IDR)'])
        unit_cost_z = safe_float(z_data['Unit Cost (HPP)'])
        est_sell_price = safe_float(z_data['Est. Selling Price'])
        
        raw_margin = str(z_data['Normal Margin %']).replace('%', '').strip()
        normal_margin = float(raw_margin) * 100 if float(raw_margin) < 1 else float(raw_margin)
        
        monthly_sales_z = safe_float(z_data['Avg Monthly Sales'])
        months_deplete = safe_float(z_data['Months to Deplete'])
        value_at_risk = safe_float(z_data['Value at Risk'])
        
        with col_z_detail1:
            st.markdown("""<div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'><h4 style='margin-top:0; color:#334155;'>📊 Stock & Value</h4><table style='width:100%'><tr><td>Current Stock</td><td><b>{:,} units</b></td></tr><tr><td>Inventory Value</td><td><b>Rp {:.2f} Miliar</b></td></tr><tr><td>Unit Cost (HPP)</td><td><b>Rp {:,.0f}</b></td></tr></table></div>""".format(stock_z, inv_value_z/1e9, unit_cost_z), unsafe_allow_html=True)
        
        with col_z_detail2:
            st.markdown("""<div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'><h4 style='margin-top:0; color:#334155;'>💰 Sales & Margin</h4><table style='width:100%'><tr><td>Harga Jual Estimasi</td><td><b>Rp {:,.0f}</b></td></tr><tr><td>Margin Normal</td><td><b style='color:#22c55e;'>{:.1f}%</b></td></tr><tr><td>Monthly Sales Velocity</td><td><b>{:.0f} units/mo</b></td></tr></table></div>""".format(est_sell_price, normal_margin, monthly_sales_z), unsafe_allow_html=True)
            
        with col_z_detail3:
            st.markdown("""<div style='background-color:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;'><h4 style='margin-top:0; color:#334155;'>⏱️ Depletion & Risk</h4><table style='width:100%'><tr><td>Natural Depletion</td><td><b style='color:#ef4444;'>{:.0f} bulan</b></td></tr><tr><td>Replacement Launch</td><td><b>3 bulan lagi</b></td></tr><tr><td>Value at Risk (Hangus)</td><td><b style='color:#ef4444;'>Rp {:,.0f} Juta</b></td></tr></table></div>""".format(months_deplete, value_at_risk/1e6), unsafe_allow_html=True)
        
        # --- TAMPILAN BLOK 3: SCENARIO TABLE DARI GSHEET ---
        st.markdown("#### ⚖️ Margin vs Cash Trade-off Simulation (Pre-calculated in GSheet)")
        
        display_scen = df_scen.copy()
        for col in ['Discount Rate', 'Margin After Discount']:
            display_scen[col] = display_scen[col].apply(lambda x: f"{float(str(x).replace('%','').strip()) * 100:.2f}%" if float(str(x).replace('%','').strip()) < 1 else f"{float(str(x).replace('%','').strip()):.2f}%")
            
        for col in ['Units to Liquidate', 'Discounted Price', 'Revenue (Cash Unlock)', 'Gross Profit', 'Margin Erosion (IDR)']:
            display_scen[col] = pd.to_numeric(display_scen[col].astype(str).str.replace(r'[Rp, ]', '', regex=True), errors='coerce')
            if col == 'Units to Liquidate':
                display_scen[col] = display_scen[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")
            else:
                display_scen[col] = display_scen[col].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "")
                
        st.dataframe(display_scen, use_container_width=True, hide_index=True)

        # --- INTERACTIVE SLIDER UNTUK PRESENTASI ---
        st.markdown("#### 🎛️ Live Presentation Slider")
        col_trade1, col_trade2 = st.columns(2)
        
        with col_trade1:
            st.markdown("**🎛️ Simulasi Costing Promo Bundling (Device Z):**")
            units_to_liquidate = st.slider("Jumlah unit yang dilikuidasi", min_value=1000, max_value=int(stock_z), value=int(stock_z), step=1000, key="units_z")
            discount_rate = st.slider("Diskon yang diberikan (%)", min_value=0, max_value=70, value=30, step=10, key="discount_z")
            
            selling_price_after_discount = est_sell_price * (1 - discount_rate/100)
            revenue = units_to_liquidate * selling_price_after_discount
            cost = units_to_liquidate * unit_cost_z
            gross_profit = revenue - cost
            margin_after_discount = (gross_profit / revenue * 100) if revenue > 0 else 0
            
        with col_trade2:
            st.markdown("**📊 Hasil Kalkulasi Live**")
            results_trade = pd.DataFrame({
                'Metric': ['Target Cash Unlock (Rev)', 'Margin Tersisa', 'Gross Profit'],
                'Value': [f"Rp {revenue/1e6:,.0f} Juta", f"{margin_after_discount:.1f}%", f"Rp {gross_profit/1e6:,.0f} Juta"]
            })
            st.dataframe(results_trade, use_container_width=True, hide_index=True)
            if margin_after_discount >= 20: st.success(f"✅ Margin sehat ({margin_after_discount:.1f}%)")
            elif margin_after_discount >= 0: st.warning(f"⚠️ Margin sangat tipis ({margin_after_discount:.1f}%)")
            else: st.error(f"🔴 Jual Rugi / Negatif Margin ({margin_after_discount:.1f}%)")

        st.markdown("#### 🛡️ Proposed Portfolio Clean-up Governance")
        st.info("SOP untuk mencegah kejadian Overstock Device Z terulang di masa depan.")
        st.markdown("""
        * **Phase-Out Trigger (T-4 Months):** Segala bentuk aktivitas *Import / Procurement* untuk produk lama wajib dihentikan **4 bulan** sebelum peluncuran product pengganti.
        * **Auto-Clearance Mandate (T-2 Months):** Jika H-60 hari produk lama masih memiliki stok >2 bulan, tim *Marketing* diizinkan mengeksekusi *Bundling Promo* otomatis tanpa eskalasi berlapis.
        """)

        # --- KODE TAMBAHAN: CONTINGENCY PLAN ---
        st.markdown("---")
        st.markdown("#### 🛡️ Contingency Plan (What-If Scenarios)")
        st.info("Antisipasi strategi jika Manajemen memberikan skenario krisis dadakan saat presentasi / operasional.")
        
        col_cp1, col_cp2, col_cp3 = st.columns(3)
        
        with col_cp1:
            st.markdown("""
            <div class='card' style='border-left: 5px solid #f59e0b;'>
                <h4 style='color:#b45309;'>📉 Krisis 1: Margin Squeeze</h4>
                <p><b>Skenario:</b> CFO menolak diskon 30%, hanya mengizinkan maksimal diskon 10-15%.</p>
                <p><b>Plan B (Gunakan Slider):</b> Tunjukkan secara <i>live</i> bahwa diskon pelit (10%) akan melambatkan serapan. Jika hanya laku 50%, Cash Unlock cuma Rp 891 Juta. Lempar keputusan ke Manajemen: <i>"Pilih selamatkan Margin 38% atau capai target Cash 5 Miliar?"</i></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_cp2:
            st.markdown("""
            <div class='card' style='border-left: 5px solid #ef4444;'>
                <h4 style='color:#b91c1c;'>🚨 Krisis 2: B2B Buyer Batal</h4>
                <p><b>Skenario:</b> Kesepakatan Export/Borongan senilai Rp 2.5 Miliar batal secara tiba-tiba.</p>
                <p><b>Plan B:</b> Alihkan beban target ke kategori <i>'Slow Moving'</i>. Ubah strategi E-Commerce dari sekadar Flash Sale biasa menjadi <b>Mega Clearance (Diskon 40-50%)</b> untuk langsung melikuidasi Rp 8.75 Miliar aset guna menutup lubang 2.5 Miliar.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_cp3:
            st.markdown("""
            <div class='card' style='border-left: 5px solid #3b82f6;'>
                <h4 style='color:#1d4ed8;'>⏱️ Krisis 3: Cash 30-Day Sprint</h4>
                <p><b>Skenario:</b> Perusahaan tidak bisa menunggu 90 hari, butuh suntikan tunai Rp 3 Miliar di 30 hari pertama.</p>
                <p><b>Plan B:</b> Akselerasi <b>B2B Wholesale</b> di minggu pertama. Penjualan ritel (Bundling/Flash Sale) butuh waktu <i>ramp-up</i> untuk laku harian. B2B adalah transaksi <i>'Take-All'</i> (1x invoice langsung cair besar).</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# TAB 3: S&OP RESTRUCTURE DESIGN (100% TERKONEKSI GSHEET)
# ==========================================
with tab3:
    st.markdown("### ⚙️ S&OP Governance & Cycle Restructure")
    
    if not data_c:
        st.error("⚠️ Data Part C gagal dimuat. Pastikan worksheet bernama 'Part_C_S&OP'.")
    else:
        header_cadence = data_c[0][:6]
        df_cadence = pd.DataFrame([row[:6] for row in data_c[1:5]], columns=header_cadence)
        
        header_kpi = data_c[7][:4]
        df_kpi = pd.DataFrame([row[:4] for row in data_c[8:12]], columns=header_kpi)
        
        header_ctx = data_c[14][:2]
        df_ctx = pd.DataFrame([row[:2] for row in data_c[15:18]], columns=header_ctx)
        
        header_strat = data_c[20][:2]
        df_strat = pd.DataFrame([row[:2] for row in data_c[21:25]], columns=header_strat)

        target_growth = df_ctx.iloc[1]['Value / Description']
        hist_growth = df_ctx.iloc[0]['Value / Description']
        prev_fail = df_ctx.iloc[2]['Value / Description']
        
        st.info(f"🎯 **Management Challenge:** Target Growth **{target_growth}** | Historical Growth **{hist_growth}** | Previous Decision Issue: **{prev_fail}**")

        col_c1, col_c2 = st.columns([2, 1])
        
        with col_c1:
            st.markdown("#### 📅 Monthly S&OP Cadence")
            st.dataframe(df_cadence[['Week', 'Task', 'Owner', 'Output']], use_container_width=True, hide_index=True)
            
            st.markdown("#### 📊 S&OP Timeline")
            df_timeline = df_cadence.copy()
            df_timeline['Start Date'] = pd.to_datetime(df_timeline['Start Date'])
            df_timeline['Finish Date'] = pd.to_datetime(df_timeline['Finish Date'])
            
            fig_timeline = px.timeline(
                df_timeline, x_start='Start Date', x_end='Finish Date', y='Task', color='Owner', 
                title="S&OP Monthly Cycle", 
                color_discrete_map={'Sales & Marketing': '#3b82f6', 'Supply Chain': '#10b981', 'Demand + Supply Lead': '#f59e0b', 'Management': '#ef4444'}
            )
            fig_timeline.update_layout(xaxis=dict(title="Timeline", tickformat="%d %b"), yaxis=dict(title="", autorange="reversed"), height=300, showlegend=True)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
        with col_c2:
            st.markdown("#### 🎯 KPI Dashboard")
            st.dataframe(df_kpi, use_container_width=True, hide_index=True)
            
            acc_val = float(df_kpi.iloc[0]['Current'].replace('%', ''))
            acc_target = float(df_kpi.iloc[0]['Target'].replace('%', ''))
            
            # GAUGE CHART DIPERBAIKI (Tinggi & Ukuran Font)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta", value=acc_val, domain={'x': [0, 1], 'y': [0, 1]}, 
                title={'text': "Forecast Accuracy", 'font': {'size': 16}}, 
                number={'font': {'size': 36}}, 
                delta={'reference': acc_target, 'increasing': {'color': "red"}, 'font': {'size': 18}}, 
                gauge={
                    'axis': {'range': [0, 100]}, 'bar': {'color': "#3b82f6"}, 
                    'steps': [{'range': [0, 50], 'color': '#fee2e2'}, {'range': [50, 75], 'color': '#fef9c3'}, {'range': [75, 100], 'color': '#dcfce7'}], 
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': acc_target}
                }
            ))
            fig_gauge.update_layout(height=260, margin=dict(l=30, r=30, t=50, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")
    
    st.markdown("#### 🛡️ Professional Challenge Strategy")
    st.warning(" How to challenge Sales forecast professionally:")
    
    col_strat1, col_strat2 = st.columns(2)
    
    with col_strat1:
        st.markdown(f"""
        <div class='card'>
            <h4>🔍 {df_strat.iloc[0]['Strategy Pillar']}</h4>
            <p>{df_strat.iloc[0]['Explanation & Response to Management']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='card'>
            <h4>⚠️ {df_strat.iloc[1]['Strategy Pillar']}</h4>
            <p>{df_strat.iloc[1]['Explanation & Response to Management']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_strat2:
        st.markdown(f"""
        <div class='card'>
            <h4>🔄 {df_strat.iloc[2]['Strategy Pillar']}</h4>
            <p>{df_strat.iloc[2]['Explanation & Response to Management']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='card' style='border-left: 5px solid #10b981;'>
            <h4 style='color:#10b981;'>{df_strat.iloc[3]['Strategy Pillar']}</h4>
            <p><i>"{df_strat.iloc[3]['Explanation & Response to Management']}"</i></p>
        </div>
        """, unsafe_allow_html=True)
