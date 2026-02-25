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
# TAB 1: REPLENISHMENT & SCENARIOS
# ==========================================
with tab1:
    st.markdown("### 🎛️ Live Scenario Simulation (The 6-Month Plan)")
    
    # PARAMETER INTERAKTIF
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        scenario_growth = st.slider("📈 Market Demand Adjustment (%)", -30, 50, 0, 5)
    with col_p2:
        budget_limit = st.number_input("💰 Budget Limit (Billion IDR)", 1.0, 10.0, 4.0, 0.5)
    with col_p3:
        wh_capacity = st.number_input("🏭 Warehouse Capacity Left (units)", 1000, 10000, 4000, 500)
    
    # KONVERSI DATA NUMERIK
    df_sim = df_a.copy()
    
    # Kolom numerik yang ada di data Bapak (A-AE)
    numeric_cols = ['Unit Cost', 'MOQ', 'Current Stock', 'Stock Value', 
                    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                    'Avg Sales (Last 3 Month)', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6',
                    'Projected Stock End M1', 'Suggested Order Qty', 'Order Value (IDR)',
                    'Warehouse Space Impact (M1)']
    
    for col in numeric_cols:
        if col in df_sim.columns:
            df_sim[col] = pd.to_numeric(df_sim[col].astype(str).str.replace(',', '').str.replace('Rp', ''), errors='coerce').fillna(0)
    
    # TERAPKAN SKENARIO GROWTH ke M1-M6
    multiplier = 1 + (scenario_growth / 100)
    for month in ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']:
        if month in df_sim.columns:
            df_sim[f'{month}_Sim'] = np.ceil(df_sim[month] * multiplier)
    
    # HITUNG METRIK TAMBAHAN (karena tidak ada di GSheet)
    df_sim['Avg_Forecast_3M'] = (df_sim['M1_Sim'] + df_sim['M2_Sim'] + df_sim['M3_Sim']) / 3
    
    # Stock Cover dalam Hari
    df_sim['DOS_Hari'] = np.ceil(df_sim['Current Stock'] / (df_sim['Avg_Forecast_3M'] / 30))
    
    # Klasifikasi Risiko
    def get_risk_status(dos):
        if dos < 45:
            return "🔴 KRITIS"
        elif dos < 60:
            return "🟡 WASPADA"
        elif dos < 90:
            return "🟢 AMAN"
        else:
            return "🔵 BERLEBIH"
    
    df_sim['Risk Status'] = df_sim['DOS_Hari'].apply(get_risk_status)
    
    # SPLIT ORDER LOGIC (Air vs Sea)
    df_sim['Air Qty'] = df_sim.apply(
        lambda x: min(x['Suggested Order Qty'], 
                     int(np.ceil(max(0, x['M1_Sim'] - x['Current Stock']) / 1000) * 1000))
        if x['DOS_Hari'] < 45 and x['Suggested Order Qty'] > 0 else 0, axis=1
    )
    df_sim['Sea Qty'] = df_sim['Suggested Order Qty'] - df_sim['Air Qty']
    
    # CASH IMPACT
    air_cost_multiplier = 4.0  # Air 4x cost
    df_sim['Air Cost (B)'] = (df_sim['Air Qty'] * df_sim['Unit Cost'] * air_cost_multiplier) / 1_000_000_000
    df_sim['Sea Cost (B)'] = (df_sim['Sea Qty'] * df_sim['Unit Cost'] * 1.1) / 1_000_000_000
    df_sim['Total Cost (B)'] = df_sim['Air Cost (B)'] + df_sim['Sea Cost (B)']
    
    # FINAL ROUTE DECISION
    def get_final_route(row):
        if row['Air Qty'] > 0 and row['Sea Qty'] > 0:
            return f"✈️ SPLIT: {row['Air Qty']:,.0f} Air + {row['Sea Qty']:,.0f} Sea"
        elif row['Air Qty'] > 0:
            return "✈️ AIR (URGENT)"
        elif row['Sea Qty'] > 0:
            return "🚢 SEA"
        else:
            return "⏸️ TUNDA"
    
    df_sim['Final Route'] = df_sim.apply(get_final_route, axis=1)
    
    # CUMULATIVE TRACKING
    df_sim['Cumulative Cash'] = df_sim['Total Cost (B)'].cumsum()
    df_sim['Cumulative WH'] = df_sim['Warehouse Space Impact (M1)'].cumsum()
    
    # --- DISPLAY TABLE ---
    st.markdown("#### 📋 SKU Replenishment Plan")
    
    display_cols = ['Item', 'Forecast Model', 'Current Stock', 'DOS_Hari', 
                   'Risk Status', 'Air Qty', 'Sea Qty', 'Final Route', 
                   'Total Cost (B)', 'Warehouse Space Impact (M1)']
    
    # Pastikan kolom yang ditampilkan ada di dataframe
    available_cols = [col for col in display_cols if col in df_sim.columns]
    
    # Styling berdasarkan risk
    def highlight_risk(row):
        if row['Risk Status'] == '🔴 KRITIS':
            return ['background-color: #fee2e2'] * len(row)
        elif row['Risk Status'] == '🟡 WASPADA':
            return ['background-color: #fef9c3'] * len(row)
        elif row['Risk Status'] == '🟢 AMAN':
            return ['background-color: #dcfce7'] * len(row)
        else:
            return [''] * len(row)
    
    st.dataframe(
        df_sim[available_cols].style.apply(highlight_risk, axis=1),
        use_container_width=True,
        column_config={
            "Total Cost (B)": st.column_config.NumberColumn(format="Rp %.2f B"),
            "Warehouse Space Impact (M1)": st.column_config.NumberColumn(format="%d units")
        }
    )
    
    # --- CONSTRAINTS VALIDATION ---
    st.markdown("#### ⚖️ Constraints Validation")
    
    total_cost = df_sim['Total Cost (B)'].sum()
    total_wh = df_sim['Warehouse Space Impact (M1)'].sum()
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("💰 Total Import Value", f"Rp {total_cost:.2f} B", 
                 delta=f"Limit: Rp {budget_limit:.1f} B",
                 delta_color="normal" if total_cost <= budget_limit else "inverse")
    
    with col_m2:
        st.metric("🏭 WH Incoming M1", f"{total_wh:,.0f} units",
                 delta=f"Capacity: {wh_capacity:,.0f} units",
                 delta_color="normal" if total_wh <= wh_capacity else "inverse")
    
    with col_m3:
        cash_remaining = budget_limit - total_cost
        st.metric("💵 Sisa Kas", f"Rp {cash_remaining:.2f} B",
                 delta="Aman" if cash_remaining >= 0 else "Defisit")
    
    with col_m4:
        wh_remaining = wh_capacity - total_wh
        st.metric("📦 Sisa Gudang", f"{wh_remaining:,.0f} units",
                 delta="Tersedia" if wh_remaining >= 0 else "Overcapacity")
    
    # ALERTS
    if total_cost > budget_limit:
        st.error("🚨 **OVER BUDGET!** Rekomendasi: Kurangi Air Freight atau negosiasi split order.")
    
    if total_wh > wh_capacity:
        st.error("🏭 **GUDANG PENUH!** Rekomendasi: Jadwalkan pengiriman bertahap.")
    
    # --- VISUALISASI ---
    st.markdown("#### 📊 Cash Allocation by SKU")
    
    fig_cash = px.bar(
        df_sim[df_sim['Total Cost (B)'] > 0],
        x='Item', 
        y=['Air Cost (B)', 'Sea Cost (B)'],
        title="Import Value Breakdown (Air vs Sea)",
        labels={'value': 'Billion IDR', 'variable': 'Route'},
        color_discrete_map={'Air Cost (B)': '#ef4444', 'Sea Cost (B)': '#3b82f6'},
        barmode='stack'
    )
    fig_cash.add_hline(y=budget_limit, line_dash="dash", line_color="red",
                      annotation_text=f"Budget Limit: Rp {budget_limit}B")
    st.plotly_chart(fig_cash, use_container_width=True)
    
    # --- DOS CHART ---
    st.markdown("#### 📈 Stock Cover (Days of Supply)")
    
    fig_dos = px.bar(
        df_sim,
        x='Item',
        y='DOS_Hari',
        color='Risk Status',
        title="Days of Supply per SKU",
        color_discrete_map={
            '🔴 KRITIS': '#ef4444',
            '🟡 WASPADA': '#f59e0b',
            '🟢 AMAN': '#10b981',
            '🔵 BERLEBIH': '#3b82f6'
        }
    )
    fig_dos.add_hline(y=45, line_dash="dash", line_color="red", annotation_text="Kritis <45 hr")
    fig_dos.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Waspada 45-60 hr")
    fig_dos.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Aman 60-90 hr")
    st.plotly_chart(fig_dos, use_container_width=True)

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
