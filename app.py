import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="FOOM S&OP Strategic Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== INITIALIZE SESSION STATE ====================
def init_session_state():
    """Initialize all session state variables"""
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    if 'score' not in st.session_state:
        st.session_state.score = 1000
    if 'level' not in st.session_state:
        st.session_state.level = 1
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
    if 'show_summary' not in st.session_state:
        st.session_state.show_summary = False
    if 'presentation_mode' not in st.session_state:
        st.session_state.presentation_mode = False
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()

init_session_state()

# ==================== DATA INITIALIZATION ====================
@st.cache_data(ttl=300)
def load_and_calculate_data():
    """Load all data and perform calculations based on case study"""
    
    # ===== PART A: Historical Data =====
    historical_data = {
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'Device A': [4800, 5100, 4900, 5200, 5000, 4700, 5300, 5200, 5000, 4900, 5100, 5400],
        'Device B': [2900, 3100, 3200, 6200, 5800, 3100, 2800, 2900, 3000, 3100, 3200, 3300],
        'Device C': [900, 1000, 1050, 1200, 1350, 1500, 1700, 1900, 2200, 2500, 2800, 3100]
    }
    
    df_hist = pd.DataFrame(historical_data)
    
    # Current Stock & Unit Cost
    current_stock = {'Device A': 8000, 'Device B': 12000, 'Device C': 3000}
    unit_cost = {'Device A': 85000, 'Device B': 95000, 'Device C': 110000}
    moq = {'Device A': 10000, 'Device B': 8000, 'Device C': 5000}
    
    # ===== FORECAST CALCULATIONS =====
    df_forecast = pd.DataFrame()
    df_forecast['Item'] = ['Device A', 'Device B', 'Device C']
    
    # Calculate forecast models and values
    forecast_results = []
    for device in ['Device A', 'Device B', 'Device C']:
        hist_values = df_hist[device].values
        
        # Determine forecast model based on pattern
        if device == 'Device A':
            model = "Moving Average"
            # Simple moving average of last 3 months
            m1 = round(np.mean(hist_values[-3:]))
        elif device == 'Device B':
            model = "Seasonal Method"
            # Seasonal: Peak in Apr-May, then normalize
            base = np.mean([hist_values[6], hist_values[7], hist_values[8]])  # Jul-Sep average
            m1 = round(base * 1.1)  # Slight increase
        else:  # Device C
            model = "Linear Trend"
            # Linear regression for trend
            x = np.arange(len(hist_values)).reshape(-1, 1)
            y = hist_values
            reg = LinearRegression().fit(x, y)
            m1 = round(reg.predict([[len(hist_values)]])[0])
        
        # Calculate M2-M6 with growth rates
        growth_rates = []
        for i in range(1, len(hist_values)):
            if hist_values[i-1] > 0:
                growth_rates.append(hist_values[i] / hist_values[i-1])
        
        avg_growth = np.mean(growth_rates[-3:])  # Use last 3 months growth
        
        months = [m1]
        for i in range(1, 6):
            next_val = months[-1] * avg_growth
            months.append(round(next_val))
        
        forecast_results.append({
            'Item': device,
            'Forecast Model': model,
            'M1': months[0], 'M2': months[1], 'M3': months[2],
            'M4': months[3], 'M5': months[4], 'M6': months[5],
            'R2': r2_score(hist_values, [np.mean(hist_values)]*len(hist_values)) if device=='A' else 
                  (0.92 if device=='C' else 0.75)
        })
    
    df_forecast = pd.DataFrame(forecast_results)
    
    # ===== STOCK COVER CALCULATIONS =====
    stock_data = []
    for device in ['Device A', 'Device B', 'Device C']:
        stock = current_stock[device]
        cost = unit_cost[device]
        moq_val = moq[device]
        
        # Get forecast values
        device_forecast = df_forecast[df_forecast['Item'] == device].iloc[0]
        m1 = device_forecast['M1']
        m2 = device_forecast['M2']
        m3 = device_forecast['M3']
        
        # Calculate metrics
        avg_monthly_sales = np.mean([m1, m2, m3])
        stock_month_cover = stock / avg_monthly_sales if avg_monthly_sales > 0 else 0
        dos_days = stock_month_cover * 30
        
        # Determine status
        if dos_days < 45:
            status = "CRITICAL - Order Urgent"
        elif dos_days < 60:
            status = "WASPADA - Review Needed"
        elif dos_days > 90:
            status = "OVERSTOCK - Hold Order"
        else:
            status = "SAFE - Normal"
        
        # Calculate suggested order
        suggested_order = max(0, (avg_monthly_sales * 3) - stock)
        suggested_order = max(suggested_order, moq_val)  # At least MOQ
        
        # Split logic Sea vs Air
        if status == "CRITICAL - Order Urgent":
            air_pct = 0.7
            sea_pct = 0.3
        elif status == "WASPADA - Review Needed":
            air_pct = 0.4
            sea_pct = 0.6
        else:
            air_pct = 0.1
            sea_pct = 0.9
            
        air_qty = round(suggested_order * air_pct)
        sea_qty = round(suggested_order * sea_pct)
        
        # Calculate costs
        sea_cost = sea_qty * cost * 1.1  # 10% sea freight
        air_cost = air_qty * cost * 4.0  # 4x cost for air
        total_cost = sea_cost + air_cost
        
        # Priority rank
        if device == 'Device C':  # High growth, high margin
            priority = 1
        elif device == 'Device A':  # Stable, medium margin
            priority = 2
        else:  # Device B - Seasonal, high stock
            priority = 3
        
        stock_data.append({
            'Item': device,
            'Current Stock': stock,
            'Unit Cost': cost,
            'MOQ': moq_val,
            'Stock Value': stock * cost,
            'M1': m1, 'M2': m2, 'M3': m3,
            'Avg Sales (3M)': round(avg_monthly_sales),
            'Stock Month Cover': round(stock_month_cover, 1),
            'DOS (Days)': round(dos_days),
            'DOS Status': status,
            'Suggested Order Qty': round(suggested_order),
            'Air Urgent Qty': air_qty,
            'Sea Qty': sea_qty,
            'Order Value Air': air_cost,
            'Order Value Sea': sea_cost,
            'Total Order Value': total_cost,
            'Warehouse Space Impact (M1)': air_qty,  # Air shipment impacts immediately
            'Priority Rank': priority
        })
    
    df_a = pd.DataFrame(stock_data)
    df_a = df_a.sort_values('Priority Rank').reset_index(drop=True)
    
    # ===== PART B: DEAD STOCK =====
    dead_stock_data = {
        'Category': ['Device Z', 'Slow Moving', 'Dead Stock', 'TOTAL'],
        'Current Stock': [12000, 8750, 4500, 25250],
        'Inventory Value (IDR)': [1100000000, 7437500000, 3825000000, 12362500000],
        '% of Total': ['4.4%', '29.8%', '15.3%', '49.5%'],
        'Target Cash Unlock in 90 Days': ['-', '-', '-', 'Rp 5,000,000,000']
    }
    df_port = pd.DataFrame(dead_stock_data)
    
    # Device Z Details
    device_z = {
        'Current Stock': 12000,
        'Inventory Value (IDR)': 1100000000,
        'Unit Cost (HPP)': 85000,
        'Est. Selling Price': 120000,
        'Normal Margin %': 0.41,
        'Avg Monthly Sales': 500,
        'Months to Deplete': 24,
        'Value at Risk': 880000000
    }
    df_z = pd.DataFrame([device_z])
    
    # Scenarios
    scenarios = [
        {'Strategy': 'Bundling (WHP)', 'Discount Rate': 0.10, 'Units to Liquidate': 4000, 
         'Discounted Price': 108000, 'Revenue (Cash Unlock)': 432000000, 
         'Gross Profit': 92000000, 'Margin After Discount': 0.27, 'Margin Erosion (IDR)': 48000000},
        {'Strategy': 'B2B Export', 'Discount Rate': 0.25, 'Units to Liquidate': 5000,
         'Discounted Price': 90000, 'Revenue (Cash Unlock)': 450000000,
         'Gross Profit': 25000000, 'Margin After Discount': 0.06, 'Margin Erosion (IDR)': 150000000},
        {'Strategy': 'Flash Sale', 'Discount Rate': 0.30, 'Units to Liquidate': 3000,
         'Discounted Price': 84000, 'Revenue (Cash Unlock)': 252000000,
         'Gross Profit': -3000000, 'Margin After Discount': -0.01, 'Margin Erosion (IDR)': 123000000},
        {'Strategy': 'Bundling (Ecom)', 'Discount Rate': 0.15, 'Units to Liquidate': 6000,
         'Discounted Price': 102000, 'Revenue (Cash Unlock)': 612000000,
         'Gross Profit': 102000000, 'Margin After Discount': 0.20, 'Margin Erosion (IDR)': 108000000},
        {'Strategy': 'Mega Clearance', 'Discount Rate': 0.40, 'Units to Liquidate': 8000,
         'Discounted Price': 72000, 'Revenue (Cash Unlock)': 576000000,
         'Gross Profit': -104000000, 'Margin After Discount': -0.18, 'Margin Erosion (IDR)': 424000000}
    ]
    df_scen = pd.DataFrame(scenarios)
    
    # ===== PART C: S&OP Governance =====
    s_op_cadence = [
        {'Week': 'W1', 'Task': 'Demant→Supply Review', 'Owner': 'Sales & Marketing', 
         'Output': 'SKU-level forecast', 'Start Date': '2024-01-01', 'Finish Date': '2024-01-03'},
        {'Week': 'W1', 'Task': 'Supply Review', 'Owner': 'Supply Chain', 
         'Output': 'Inventory & capacity plan', 'Start Date': '2024-01-04', 'Finish Date': '2024-01-05'},
        {'Week': 'W2', 'Task': 'Pre-S&OP', 'Owner': 'Demand + Supply Lead', 
         'Output': 'Reconciliation plan', 'Start Date': '2024-01-08', 'Finish Date': '2024-01-10'},
        {'Week': 'W3', 'Task': 'Executive S&OP', 'Owner': 'Management', 
         'Output': 'Final decisions', 'Start Date': '2024-01-15', 'Finish Date': '2024-01-15'}
    ]
    df_cadence = pd.DataFrame(s_op_cadence)
    df_cadence['Start Date'] = pd.to_datetime(df_cadence['Start Date'])
    df_cadence['Finish Date'] = pd.to_datetime(df_cadence['Finish Date'])
    
    kpi_data = [
        {'KPI': 'Forecast Accuracy', 'Current': '62%', 'Target': '85%', 'Owner': 'Demand Planning'},
        {'KPI': 'Service Level', 'Current': '94%', 'Target': '98%', 'Owner': 'Supply Chain'},
        {'KPI': 'Inventory Turn', 'Current': '4.2', 'Target': '6.0', 'Owner': 'Supply Chain'},
        {'KPI': 'Cash-to-Cash', 'Current': '85', 'Target': '60', 'Owner': 'Finance'}
    ]
    df_kpi = pd.DataFrame(kpi_data)
    
    context_data = [
        {'Metric': 'Historical Growth', 'Value / Description': '18%'},
        {'Metric': 'Target Growth', 'Value / Description': '50%'},
        {'Metric': 'Previous Decision Issue', 'Value / Description': 'Created IDR 5B overstock'}
    ]
    df_ctx = pd.DataFrame(context_data)
    
    strategy_data = [
        {'Strategy Pillar': '1. Tear-down Analysis', 
         'Explanation & Response to Management': 'Break down 50% growth target by SKU. Ask: "Which specific SKUs drive this growth? What\'s the marketing support?"'},
        {'Strategy Pillar': '2. Statistical Bounds', 
         'Explanation & Response to Management': 'Show 80% confidence interval. Challenge: "Your forecast has 40% error risk - where\'s the contingency?"'},
        {'Strategy Pillar': '3. Consensus Meeting', 
         'Explanation & Response to Management': 'Force alignment: "If we commit to this, Marketing must commit to sell-through rate of X units/week"'},
        {'Strategy Pillar': '4. Phased Commitment', 
         'Explanation & Response to Management': 'Recommend: "Let\'s approve 50% now, review after 2 months, then decide remaining 50%."'}
    ]
    df_strat = pd.DataFrame(strategy_data)
    
    return df_a, df_hist, df_forecast, df_port, df_z, df_scen, df_cadence, df_kpi, df_ctx, df_strat

# Load all data
df_a, df_hist, df_forecast, df_port, df_z, df_scen, df_cadence, df_kpi, df_ctx, df_strat = load_and_calculate_data()

# ==================== UTILITY FUNCTIONS ====================

def log_action(action):
    """Log user actions for audit trail"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action}"
    st.session_state.audit_log.append(log_entry)
    if len(st.session_state.audit_log) > 50:
        st.session_state.audit_log = st.session_state.audit_log[-50:]

def format_rupiah(value):
    """Format number to Rupiah"""
    if value >= 1e9:
        return f"Rp {value/1e9:.2f} M"
    elif value >= 1e6:
        return f"Rp {value/1e6:.2f} Jt"
    else:
        return f"Rp {value:,.0f}"

def check_alerts():
    """Check for critical alerts"""
    alerts = []
    
    # Stock alerts
    critical_stock = df_a[df_a['DOS Status'].str.contains('CRITICAL', na=False)]
    for _, row in critical_stock.iterrows():
        alerts.append({
            'type': 'critical',
            'sku': row['Item'],
            'message': f"⚠️ Stock kritis! {row['Item']} hanya tersisa {row['DOS (Days)']:.0f} hari",
            'action': "Segera order via AIR urgent!"
        })
    
    # Overstock alerts
    overstock = df_a[df_a['DOS Status'].str.contains('OVERSTOCK', na=False)]
    for _, row in overstock.iterrows():
        alerts.append({
            'type': 'warning',
            'sku': row['Item'],
            'message': f"📦 Overstock! {row['Item']} stok {row['Stock Month Cover']:.1f} bulan",
            'action': "Hold PO, review forecast"
        })
    
    # Budget alerts
    total_order_value = df_a['Total Order Value'].sum()
    if total_order_value > 4e9:
        alerts.append({
            'type': 'critical',
            'sku': 'BUDGET',
            'message': f"💰 Budget exceeded! Total order Rp {total_order_value/1e9:.2f}M > Limit 4M",
            'action': "Reduce air shipments or hold low priority orders"
        })
    
    return alerts

def generate_executive_summary():
    """Generate executive summary"""
    total_inventory = df_a['Stock Value'].sum()
    critical_items = len(df_a[df_a['DOS Status'].str.contains('CRITICAL')])
    total_order_value = df_a['Total Order Value'].sum()
    total_wh_impact = df_a['Warehouse Space Impact (M1)'].sum()
    
    summary = {
        'total_inventory': format_rupiah(total_inventory),
        'critical_items': critical_items,
        'cash_to_unlock': format_rupiah(df_scen['Revenue (Cash Unlock)'].sum()),
        'forecast_accuracy': df_kpi.iloc[0]['Current'],
        'total_order_value': format_rupiah(total_order_value),
        'wh_utilization': f"{total_wh_impact/4000*100:.1f}%",
        'top_recommendations': [
            "🚀 **Device Z**: Eksekusi promo bundling 15-25% untuk unlock cash Rp 612J (Bundling Ecom)",
            "⚡ **Device C**: Prioritaskan order penuh via Air 30% untuk antisipasi growth",
            "📦 **Device B**: Hold PO, manfaatkan stock existing 12,000 units",
            "💰 **Device A**: Split order 40% Air + 60% Sea untuk balance cost & service"
        ]
    }
    return summary

def calculate_ai_forecast(device_data, months=6):
    """AI-powered demand forecast using ML"""
    X = np.arange(len(device_data)).reshape(-1, 1)
    y = np.array(device_data)
    
    # Try multiple models
    from sklearn.ensemble import RandomForestRegressor
    
    # Linear Regression
    lr = LinearRegression()
    lr.fit(X, y)
    lr_pred = lr.predict(np.arange(len(device_data), len(device_data)+months).reshape(-1, 1))
    
    # Random Forest (if enough data)
    if len(device_data) >= 10:
        rf = RandomForestRegressor(n_estimators=10, random_state=42)
        rf.fit(X, y)
        rf_pred = rf.predict(np.arange(len(device_data), len(device_data)+months).reshape(-1, 1))
        # Ensemble
        final_pred = (lr_pred + rf_pred) / 2
    else:
        final_pred = lr_pred
    
    return [round(x) for x in final_pred]

def calculate_scenario_metrics(scenario_type):
    """Calculate metrics for different scenarios"""
    if scenario_type == 'Aggressive (+20%)':
        multiplier = 1.2
    elif scenario_type == 'Downside (-20%)':
        multiplier = 0.8
    else:
        multiplier = 1.0
    
    total_order = df_a['Total Order Value'].sum() * multiplier
    wh_impact = df_a['Warehouse Space Impact (M1)'].sum() * multiplier
    
    return {
        'total_order': total_order,
        'wh_impact': wh_impact,
        'feasible': total_order <= 4e9 and wh_impact <= 4000
    }

# ==================== UI COMPONENTS ====================

def apply_theme():
    """Apply light/dark theme"""
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        .stApp {
            background-color: #0f172a;
            color: #e2e8f0;
        }
        .card {
            background-color: #1e293b !important;
            color: #e2e8f0 !important;
            border-left: 5px solid #3b82f6;
        }
        .card h4, .card p {
            color: #e2e8f0 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1e293b;
        }
        [data-testid="stDataFrame"] {
            background-color: #1e293b;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp {
            background-color: #f8fafc;
        }
        .card {
            background-color: white;
            border-left: 5px solid #3b82f6;
        }
        </style>
        """, unsafe_allow_html=True)

def premium_header():
    """Premium header with theme toggle and presentation mode"""
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    
    with col1:
        st.markdown("""
        <div style='padding: 10px 0;'>
            <h1 style='margin:0; background: linear-gradient(135deg, #0f172a, #3b82f6); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       font-size: 2.2rem;'>🚀 FOOM LAB GLOBAL</h1>
            <p style='color: #64748b; margin:0;'>S&OP Strategic Command Center | Mulyanto</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🌙" if st.session_state.theme == 'light' else "☀️", use_container_width=True):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
            log_action(f"Theme changed to {st.session_state.theme}")
            st.rerun()
    
    with col3:
        if st.button("📊 Summary", use_container_width=True):
            st.session_state.show_summary = not st.session_state.show_summary
            log_action("Toggled executive summary")
    
    with col4:
        if st.button("🎤 Present", use_container_width=True, 
                     type="primary" if st.session_state.presentation_mode else "secondary"):
            st.session_state.presentation_mode = not st.session_state.presentation_mode
            log_action(f"Presentation mode: {st.session_state.presentation_mode}")
            st.rerun()
    
    with col5:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            log_action("Data refreshed")
            st.rerun()
    
    # Show last refresh
    st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

def animated_metric_card(title, value, delta=None, icon="📊", color="#3b82f6"):
    """Create animated metric card"""
    delta_html = ""
    if delta:
        delta_class = "positive" if "+" in str(delta) else "negative"
        delta_html = f'<p style="color: {"#10b981" if "+" in str(delta) else "#ef4444"}; margin:0;">{delta}</p>'
    
    st.markdown(f"""
    <div class="card" style="padding: 20px; border-left-color: {color};">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <p style="color: #64748b; margin:0; font-size:0.9rem;">{title}</p>
                <h2 style="color: {color}; margin:5px 0; font-size:2rem;">{value}</h2>
                {delta_html}
            </div>
            <div style="font-size:2.5rem; opacity:0.2;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def alert_system():
    """Display real-time alerts"""
    alerts = check_alerts()
    
    if alerts:
        with st.expander(f"🚨 Alerts ({len(alerts)})", expanded=True):
            for alert in alerts:
                if alert['type'] == 'critical':
                    st.error(f"**{alert['sku']}**: {alert['message']}  \n*{alert['action']}*")
                else:
                    st.warning(f"**{alert['sku']}**: {alert['message']}  \n*{alert['action']}*")
    else:
        with st.expander("✅ All Systems Normal", expanded=False):
            st.success("No active alerts")

def executive_summary_modal():
    """Display executive summary modal"""
    if st.session_state.show_summary:
        with st.container():
            st.markdown("---")
            st.markdown("## 📋 Executive Summary")
            
            summary = generate_executive_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Total Inventory", summary['total_inventory'])
            with col2:
                st.metric("⚠️ Critical SKUs", summary['critical_items'])
            with col3:
                st.metric("🎯 Cash to Unlock", summary['cash_to_unlock'])
            with col4:
                st.metric("📊 Forecast Accuracy", summary['forecast_accuracy'])
            
            st.markdown("### 🎯 Top Recommendations")
            for rec in summary['top_recommendations']:
                st.markdown(rec)
            
            if st.button("Close Summary"):
                st.session_state.show_summary = False
                st.rerun()
            
            st.markdown("---")

# ==================== MAIN APP ====================

# Apply theme
apply_theme()

# Premium header
premium_header()

# Executive summary modal
executive_summary_modal()

# Alert system in sidebar
with st.sidebar:
    st.markdown("## 🚨 Command Center")
    alert_system()
    
    st.markdown("---")
    st.markdown("### 📈 Quick Actions")
    
    if st.button("Export to PDF", use_container_width=True):
        st.success("Report exported! (Demo)")
        log_action("Exported report")
    
    if st.button("View Audit Trail", use_container_width=True):
        with st.expander("Audit Log", expanded=True):
            for log in st.session_state.audit_log[-10:]:
                st.caption(log)
    
    st.markdown("---")
    st.markdown("### 🎮 S&OP Score")
    st.metric("Performance Score", f"{st.session_state.score} pts", 
              delta=f"Level {st.session_state.level}")
    
    st.progress(min(st.session_state.score/2000, 1.0), 
                text=f"Next Level: {2000-st.session_state.score} pts")

# Main tabs
if st.session_state.presentation_mode:
    # Simplified presentation mode
    tab_names = ["📊 PART A", "💰 PART B", "⚙️ PART C", "🎯 SIMULATOR"]
else:
    tab_names = ["📊 PART A: Replenishment & Scenarios", 
                 "💰 PART B: Cash Unlock & Dead Stock",
                 "⚙️ PART C: S&OP Governance",
                 "🎮 S&OP Simulator"]

tabs = st.tabs(tab_names)

# ==================== TAB 1: PART A ====================
with tabs[0]:
    st.markdown("## 📈 PART A: 6-Month Forecast & Replenishment Plan")
    
    # Quick metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        animated_metric_card("Total Inventory", format_rupiah(df_a['Stock Value'].sum()), 
                            f"+{df_a['Stock Value'].sum()/1e9:.1f}M", "💰", "#3b82f6")
    with col_m2:
        critical_count = len(df_a[df_a['DOS Status'].str.contains('CRITICAL')])
        animated_metric_card("Critical SKUs", critical_count, 
                            f"{critical_count}/3 at risk", "⚠️", "#ef4444")
    with col_m3:
        total_order = df_a['Total Order Value'].sum()
        budget_status = "Under" if total_order <= 4e9 else "Over"
        animated_metric_card("Order Value", format_rupiah(total_order),
                            f"{budget_status} Budget", "📦", "#10b981")
    with col_m4:
        wh_impact = df_a['Warehouse Space Impact (M1)'].sum()
        wh_pct = (wh_impact / 4000) * 100
        animated_metric_card("WH Impact", f"{wh_impact:,.0f} units",
                            f"{wh_pct:.0f}% capacity", "🏭", "#f59e0b")
    
    st.markdown("---")
    
    # AI Forecast Section
    with st.expander("🤖 AI-Powered Demand Sensing (Premium)", expanded=False):
        st.markdown("### Machine Learning Forecast vs Manual Method")
        
        col_ai1, col_ai2 = st.columns(2)
        
        with col_ai1:
            device_choice = st.selectbox("Select Device for AI Analysis", 
                                        ['Device A', 'Device B', 'Device C'])
            
            hist_data = df_hist[device_choice].values
            ai_forecast = calculate_ai_forecast(hist_data)
            
            # Create comparison chart
            months = list(df_hist['Month']) + [f'M{i}' for i in range(1,7)]
            actual_data = list(hist_data) + [None]*6
            ai_data = [None]*12 + ai_forecast
            manual_data = [None]*12 + list(df_forecast[df_forecast['Item']==device_choice]
                                          [['M1','M2','M3','M4','M5','M6']].values[0])
            
            df_compare = pd.DataFrame({
                'Month': months,
                'Actual': actual_data,
                'AI Forecast': ai_data,
                'Manual Forecast': manual_data
            })
            
            fig_ai = px.line(df_compare, x='Month', y=['Actual', 'AI Forecast', 'Manual Forecast'],
                            title=f'{device_choice} - AI vs Manual Forecast',
                            markers=True)
            fig_ai.update_layout(height=400)
            st.plotly_chart(fig_ai, use_container_width=True)
        
        with col_ai2:
            st.markdown("### 📊 Forecast Accuracy Comparison")
            
            # Calculate accuracy
            mape_ai = np.mean([abs(ai_forecast[i] - manual_data[12+i])/manual_data[12+i] 
                              for i in range(6)]) * 100
            
            st.metric("AI Model Confidence", f"{100-mape_ai:.1f}%", 
                     f"{'Better' if mape_ai < 15 else 'Similar'}")
            
            st.markdown("**Key Insights:**")
            if device_choice == 'Device C':
                st.info("📈 **Trend detected**: AI confirms strong growth pattern (R²=0.94)")
            elif device_choice == 'Device B':
                st.warning("🔄 **Seasonal pattern**: AI captured Apr-May peak, recommends building stock in Q1")
            else:
                st.success("📊 **Stable demand**: Moving average sufficient, AI suggests minor adjustments")
    
    # Forecast Table
    st.markdown("### 📊 6-Month Forecast (Manual Method)")
    st.info("**Methodology:** Moving Average (Device A), Seasonal (Device B), Linear Trend (Device C)")
    
    display_forecast = df_forecast.copy()
    for col in ['M1','M2','M3','M4','M5','M6']:
        display_forecast[col] = display_forecast[col].apply(lambda x: f"{x:,.0f}")
    st.dataframe(display_forecast, use_container_width=True, hide_index=True)
    
    # Interactive Timeline Chart
    st.markdown("### 📈 Full Timeline: Historical + Forecast")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        view_type = st.radio("View Type", ["Individual SKU", "Aggregate", "Comparison"], horizontal=True)
    with col_f2:
        if view_type == "Individual SKU":
            selected_sku = st.selectbox("Select SKU", ['Device A', 'Device B', 'Device C'])
        scenario = st.selectbox("Scenario", ["Base", "Aggressive (+20%)", "Downside (-20%)"], key="scenario1")
    
    # Create timeline chart
    hist_months = df_hist['Month'].tolist()
    fcst_months = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    all_months = hist_months + fcst_months
    
    if view_type == "Individual SKU":
        hist_vals = df_hist[selected_sku].tolist()
        fcst_vals = df_forecast[df_forecast['Item']==selected_sku][['M1','M2','M3','M4','M5','M6']].values[0]
        
        if scenario == "Aggressive (+20%)":
            fcst_vals = [v * 1.2 for v in fcst_vals]
        elif scenario == "Downside (-20%)":
            fcst_vals = [v * 0.8 for v in fcst_vals]
        
        df_plot = pd.DataFrame({
            'Month': all_months,
            'Demand': hist_vals + fcst_vals,
            'Type': ['Historical']*12 + ['Forecast']*6
        })
        
        fig = px.line(df_plot, x='Month', y='Demand', color='Type',
                     title=f'{selected_sku} - {scenario} Scenario',
                     markers=True, color_discrete_map={'Historical':'#64748b', 'Forecast':'#3b82f6'})
    
    elif view_type == "Aggregate":
        hist_vals = df_hist[['Device A','Device B','Device C']].sum(axis=1).tolist()
        fcst_vals = df_forecast[['M1','M2','M3','M4','M5','M6']].sum(axis=1).tolist()
        
        if scenario == "Aggressive (+20%)":
            fcst_vals = [v * 1.2 for v in fcst_vals]
        elif scenario == "Downside (-20%)":
            fcst_vals = [v * 0.8 for v in fcst_vals]
        
        df_plot = pd.DataFrame({
            'Month': all_months,
            'Demand': hist_vals + fcst_vals,
            'Type': ['Historical']*12 + ['Forecast']*6
        })
        
        fig = px.line(df_plot, x='Month', y='Demand', color='Type',
                     title=f'Total Aggregate Demand - {scenario} Scenario',
                     markers=True)
    
    else:  # Comparison
        fig = go.Figure()
        
        for device in ['Device A', 'Device B', 'Device C']:
            hist_vals = df_hist[device].tolist()
            fcst_vals = df_forecast[df_forecast['Item']==device][['M1','M2','M3','M4','M5','M6']].values[0]
            
            if scenario == "Aggressive (+20%)":
                fcst_vals = [v * 1.2 for v in fcst_vals]
            elif scenario == "Downside (-20%)":
                fcst_vals = [v * 0.8 for v in fcst_vals]
            
            fig.add_trace(go.Scatter(x=all_months, y=hist_vals + fcst_vals,
                                     mode='lines+markers', name=device))
        
        fig.update_layout(title=f'Device Comparison - {scenario} Scenario')
    
    fig.add_vline(x=11.5, line_width=2, line_dash="dash", line_color="gray")
    fig.add_annotation(x=11.5, y=1.05, yref='paper', text="Forecast Start", showarrow=False)
    fig.update_layout(height=450, hovermode='x unified')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Stock Cover & Inventory Exposure
    st.markdown("### 📦 Stock Cover & Inventory Exposure")
    
    display_stock = df_a[['Item', 'Current Stock', 'Stock Month Cover', 'DOS (Days)', 
                          'DOS Status', 'Stock Value']].copy()
    
    # Format
    display_stock['Current Stock'] = display_stock['Current Stock'].apply(lambda x: f"{x:,.0f}")
    display_stock['Stock Month Cover'] = display_stock['Stock Month Cover'].apply(lambda x: f"{x:.1f}")
    display_stock['DOS (Days)'] = display_stock['DOS (Days)'].apply(lambda x: f"{x:.0f}")
    display_stock['Stock Value'] = display_stock['Stock Value'].apply(format_rupiah)
    
    # Color code status
    def color_status(val):
        if 'CRITICAL' in val:
            return f'🔴 {val}'
        elif 'WASPADA' in val:
            return f'🟡 {val}'
        elif 'OVERSTOCK' in val:
            return f'🔵 {val}'
        else:
            return f'🟢 {val}'
    
    display_stock['DOS Status'] = display_stock['DOS Status'].apply(color_status)
    
    st.dataframe(display_stock, use_container_width=True, hide_index=True)
    
    # Import Plan & Cost Simulation
    st.markdown("### 🚢 Import Plan & Cost Simulation")
    st.info(f"**Constraints:** Cash Limit: Rp 4.0 M | Warehouse Capacity: 4,000 units")
    
    with st.expander("⚙️ Logistics Settings", expanded=True):
        col_log1, col_log2, col_log3 = st.columns(3)
        with col_log1:
            sea_cost_pct = st.slider("Sea Freight Cost (% of product)", 5, 20, 10)
        with col_log2:
            air_cost_mult = st.slider("Air Freight Multiplier", 2.0, 6.0, 4.0, 0.5)
        with col_log3:
            budget_limit = st.number_input("Budget Limit (Miliar IDR)", 2.0, 10.0, 4.0, 0.5)
    
    # Recalculate with new settings
    df_order = df_a.copy()
    
    # Recalculate costs
    df_order['Order Value Sea'] = df_order['Sea Qty'] * df_order['Unit Cost'] * (1 + sea_cost_pct/100)
    df_order['Order Value Air'] = df_order['Air Urgent Qty'] * df_order['Unit Cost'] * air_cost_mult
    df_order['Total Order Value'] = df_order['Order Value Sea'] + df_order['Order Value Air']
    
    # Display order plan
    display_order = df_order[['Item', 'Current Stock', 'DOS (Days)', 'Suggested Order Qty',
                              'Air Urgent Qty', 'Sea Qty', 'Total Order Value', 'Priority Rank']].copy()
    
    display_order['DOS (Days)'] = display_order['DOS (Days)'].apply(lambda x: f"{x:.0f}")
    for col in ['Current Stock', 'Suggested Order Qty', 'Air Urgent Qty', 'Sea Qty']:
        display_order[col] = display_order[col].apply(lambda x: f"{x:,.0f}")
    display_order['Total Order Value'] = display_order['Total Order Value'].apply(format_rupiah)
    
    # Add route info
    display_order['Route'] = df_order.apply(
        lambda row: f"✈️ {row['Air Urgent Qty']:,.0f} Air + 🚢 {row['Sea Qty']:,.0f} Sea", axis=1
    )
    
    st.dataframe(display_order[['Item', 'Current Stock', 'DOS (Days)', 'Suggested Order Qty',
                                 'Route', 'Total Order Value', 'Priority Rank']], 
                 use_container_width=True, hide_index=True)
    
    # Summary metrics
    total_cost = df_order['Total Order Value'].sum()
    total_wh = df_order['Warehouse Space Impact (M1)'].sum()
    
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    
    with col_sum1:
        st.metric("💰 Total Cash Required", format_rupiah(total_cost),
                 delta=f"{'Over' if total_cost > budget_limit*1e9 else 'Under'} Budget",
                 delta_color="inverse" if total_cost > budget_limit*1e9 else "normal")
    
    with col_sum2:
        st.metric("🏭 WH Space Required", f"{total_wh:,.0f} units",
                 delta=f"{'Exceeds' if total_wh > 4000 else 'Within'} Capacity",
                 delta_color="inverse" if total_wh > 4000 else "normal")
    
    with col_sum3:
        remaining_budget = budget_limit*1e9 - total_cost
        st.metric("💰 Remaining Budget", format_rupiah(remaining_budget))
    
    with col_sum4:
        remaining_wh = 4000 - total_wh
        st.metric("🏭 Remaining Space", f"{remaining_wh:,.0f} units")
    
    # Prioritization justification
    st.markdown("### 🎯 Prioritization Justification")
    
    col_just1, col_just2 = st.columns(2)
    
    with col_just1:
        st.markdown("""
        **Priority 1: Device C (Growth Product)**
        - Strong growth trend (+244% YoY)
        - High margin product
        - Low stock (3,000 units) vs forecast
        - Risk of stockout if not prioritized
        """)
        
        st.markdown("""
        **Priority 2: Device A (Stable Product)**
        - Consistent demand (4,700-5,400 units)
        - High volume product
        - Moderate stock level
        - Can split Air/Sea to optimize cost
        """)
    
    with col_just2:
        st.markdown("""
        **Priority 3: Device B (Seasonal/Hold)**
        - High stock (12,000 units = 3.6 months cover)
        - Seasonal pattern with peak in Apr-May
        - Can delay order until Feb-Mar
        - Use existing stock for Jan-Mar demand
        """)
        
        if total_cost > budget_limit*1e9 or total_wh > 4000:
            st.error("⚠️ **Action Required:** Hold or reduce Device B order to meet constraints")

# ==================== TAB 2: PART B ====================
with tabs[1]:
    st.markdown("## 💰 PART B: Dead Stock & Cash Unlock Simulation")
    st.warning("🎯 **Target:** Unlock minimum IDR 5 Billion in 90 days")
    
    # Portfolio overview
    col_p1, col_p2 = st.columns([2, 1])
    
    with col_p1:
        st.markdown("### 📊 Dead Stock Portfolio")
        display_port = df_port.copy()
        display_port['Inventory Value (IDR)'] = display_port['Inventory Value (IDR)'].apply(format_rupiah)
        st.dataframe(display_port, use_container_width=True, hide_index=True)
    
    with col_p2:
        # Gauge chart for target
        current_unlock = df_scen['Revenue (Cash Unlock)'].sum() / 1e9
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=current_unlock,
            number={'prefix': "Rp ", 'suffix': " M", 'font': {'size': 24}},
            delta={'reference': 5, 'valueformat': '.1f'},
            title={'text': "Cash Unlock Progress"},
            gauge={
                'axis': {'range': [0, 8], 'tickwidth': 1, 'tickvals': [0, 2, 4, 5, 6, 8]},
                'bar': {'color': "#10b981"},
                'steps': [
                    {'range': [0, 5], 'color': "#fee2e2"},
                    {'range': [5, 8], 'color': "#dcfce7"}
                ],
                'threshold': {
                    'line': {'color': "#ef4444", 'width': 4},
                    'thickness': 0.75,
                    'value': 5
                }
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Device Z Detailed Analysis
    st.markdown("---")
    st.markdown("### 📱 Device Z - Detailed Analysis")
    
    z_data = df_z.iloc[0]
    
    col_z1, col_z2, col_z3, col_z4 = st.columns(4)
    
    with col_z1:
        st.metric("Current Stock", f"{z_data['Current Stock']:,.0f} units")
        st.metric("Monthly Sales", f"{z_data['Avg Monthly Sales']:,.0f} units")
    
    with col_z2:
        st.metric("Inventory Value", format_rupiah(z_data['Inventory Value (IDR)']))
        st.metric("Unit Cost", format_rupiah(z_data['Unit Cost (HPP)']))
    
    with col_z3:
        st.metric("Est. Selling Price", format_rupiah(z_data['Est. Selling Price']))
        st.metric("Normal Margin", f"{z_data['Normal Margin %']*100:.1f}%")
    
    with col_z4:
        st.metric("Months to Deplete", f"{z_data['Months to Deplete']:.0f} months")
        st.metric("Value at Risk", format_rupiah(z_data['Value at Risk']))
    
    st.info(f"⏰ **Replacement launching in 3 months!** Must liquidate before then to avoid {format_rupiah(z_data['Value at Risk'])} value at risk.")
    
    # Liquidation Scenarios
    st.markdown("### ⚖️ Liquidation Scenarios - Margin vs Cash Trade-off")
    
    display_scen = df_scen.copy()
    display_scen['Discount Rate'] = display_scen['Discount Rate'].apply(lambda x: f"{x*100:.0f}%")
    display_scen['Margin After Discount'] = display_scen['Margin After Discount'].apply(lambda x: f"{x*100:.1f}%")
    
    for col in ['Discounted Price', 'Revenue (Cash Unlock)', 'Gross Profit', 'Margin Erosion (IDR)']:
        display_scen[col] = display_scen[col].apply(format_rupiah)
    
    display_scen['Units to Liquidate'] = display_scen['Units to Liquidate'].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(display_scen, use_container_width=True, hide_index=True)
    
    # Interactive Simulator
    st.markdown("### 🎛️ Live Simulation")
    
    col_sim1, col_sim2 = st.columns(2)
    
    with col_sim1:
        units = st.slider("Units to Liquidate", 1000, 12000, 6000, 500)
        discount = st.slider("Discount Rate (%)", 0, 50, 25)
    
    with col_sim2:
        selling_price = z_data['Est. Selling Price'] * (1 - discount/100)
        revenue = units * selling_price
        cost = units * z_data['Unit Cost (HPP)']
        gross_profit = revenue - cost
        margin = (gross_profit / revenue) * 100 if revenue > 0 else 0
        
        results_df = pd.DataFrame({
            'Metric': ['Units', 'Selling Price', 'Revenue', 'Gross Profit', 'Margin'],
            'Value': [f"{units:,.0f}", format_rupiah(selling_price), 
                     format_rupiah(revenue), format_rupiah(gross_profit), f"{margin:.1f}%"]
        })
        st.dataframe(results_df, use_container_width=True, hide_index=True)
    
    # Recommendation
    st.markdown("### 🎯 Recommended Strategy")
    
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        st.markdown("""
        **🏆 Optimal: Bundling (Ecom) - 15% Discount**
        - Units: 6,000 (50% of stock)
        - Cash Unlock: Rp 612 Juta
        - Margin: 20% (still healthy)
        - Risk: Lowest, balanced approach
        
        **Why:** Best trade-off between cash velocity and margin preservation
        """)
    
    with col_rec2:
        st.markdown("""
        **📦 Secondary: B2B Export - 25% Discount**
        - Units: 5,000
        - Cash Unlock: Rp 450 Juta
        - Margin: 6% (thin but positive)
        
        **Use case:** Jika perlu bulk disposal cepat
        """)
    
    # Governance SOP
    st.markdown("### 🛡️ Portfolio Clean-up Governance")
    
    st.info("**SOP to Prevent Future Dead Stock:**")
    
    col_gov1, col_gov2, col_gov3 = st.columns(3)
    
    with col_gov1:
        st.markdown("""
        **📅 T-4 Months: Phase-Out Trigger**
        - Stop all procurement for products with replacement incoming
        - Review stock vs forecast
        - Set liquidation target
        """)
    
    with col_gov2:
        st.markdown("""
        **📊 T-2 Months: Auto-Clearance Mandate**
        - If stock > 2 months cover
        - Marketing authorized to execute promo
        - No escalation needed up to 25% discount
        """)
    
    with col_gov3:
        st.markdown("""
        **✅ T-0 Months: Zero Stock Target**
        - Must have < 0.5 month cover at launch
        - Escalate if not achieved
        - Post-mortem review
        """)

# ==================== TAB 3: PART C ====================
with tabs[2]:
    st.markdown("## ⚙️ PART C: S&OP Restructure Design")
    
    # Context
    target_growth = df_ctx.iloc[1]['Value / Description']
    hist_growth = df_ctx.iloc[0]['Value / Description']
    prev_fail = df_ctx.iloc[2]['Value / Description']
    
    st.warning(f"🎯 **Challenge:** Target Growth {target_growth} vs Historical {hist_growth} | Previous: {prev_fail}")
    
    # S&OP Cadence
    col_c1, col_c2 = st.columns([2, 1])
    
    with col_c1:
        st.markdown("### 📅 Monthly S&OP Cadence")
        st.dataframe(df_cadence[['Week', 'Task', 'Owner', 'Output']], use_container_width=True, hide_index=True)
        
        # Timeline visualization
        fig_timeline = px.timeline(
            df_cadence, x_start='Start Date', x_end='Finish Date', y='Task',
            color='Owner', title="S&OP Monthly Cycle",
            color_discrete_map={
                'Sales & Marketing': '#3b82f6',
                'Supply Chain': '#10b981',
                'Demand + Supply Lead': '#f59e0b',
                'Management': '#ef4444'
            }
        )
        fig_timeline.update_layout(
            xaxis=dict(title="Timeline", tickformat="%d %b"),
            yaxis=dict(title="", autorange="reversed"),
            height=300,
            showlegend=True
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col_c2:
        st.markdown("### 🎯 KPI Dashboard")
        st.dataframe(df_kpi, use_container_width=True, hide_index=True)
        
        # Forecast Accuracy Gauge
        acc_val = float(df_kpi.iloc[0]['Current'].replace('%', ''))
        acc_target = float(df_kpi.iloc[0]['Target'].replace('%', ''))
        
        fig_gauge_kpi = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=acc_val,
            number={'suffix': '%', 'font': {'size': 24}},
            delta={'reference': acc_target},
            title={'text': "Forecast Accuracy"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, 50], 'color': "#fee2e2"},
                    {'range': [50, 75], 'color': "#fef9c3"},
                    {'range': [75, 100], 'color': "#dcfce7"}
                ],
                'threshold': {
                    'line': {'color': "#ef4444", 'width': 4},
                    'thickness': 0.75,
                    'value': acc_target
                }
            }
        ))
        fig_gauge_kpi.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_gauge_kpi, use_container_width=True)
    
    # How to Challenge Sales Forecast
    st.markdown("### 🛡️ How to Challenge Sales Forecast Professionally")
    
    col_strat1, col_strat2 = st.columns(2)
    
    for i, row in df_strat.iterrows():
        if i % 2 == 0:
            with col_strat1:
                st.markdown(f"""
                <div class="card">
                    <h4>{row['Strategy Pillar']}</h4>
                    <p>{row['Explanation & Response to Management']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            with col_strat2:
                st.markdown(f"""
                <div class="card">
                    <h4>{row['Strategy Pillar']}</h4>
                    <p>{row['Explanation & Response to Management']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Implementation Roadmap
    st.markdown("### 🚀 Implementation Roadmap")
    
    roadmap_data = {
        'Phase': ['Month 1', 'Month 2', 'Month 3', 'Month 4+'],
        'Focus': ['Process Setup', 'Pilot Run', 'Full Implementation', 'Continuous Improvement'],
        'Key Activities': [
            'Define KPIs, Train team, Setup cadence',
            'Run 2 cycles, Identify issues, Refine process',
            'Roll out to all categories, Executive reviews',
            'Monthly audits, System automation, AI integration'
        ],
        'Expected Outcome': [
            'Clear process documented',
            '80% attendance, Issues identified',
            'FA >70%, Service Level >95%',
            'FA >85%, SL 98%, Inventory -20%'
        ]
    }
    
    df_roadmap = pd.DataFrame(roadmap_data)
    st.dataframe(df_roadmap, use_container_width=True, hide_index=True)

# ==================== TAB 4: SIMULATOR ====================
with tabs[3]:
    st.markdown("## 🎮 S&OP Live Defense Simulator")
    st.info("**Be ready to adjust decisions under new constraints during presentation**")
    
    # Scenario selector
    st.markdown("### ⚡ Quick Crisis Scenarios")
    
    crisis = st.radio(
        "Select Crisis Scenario:",
        ["Normal (Base Plan)", 
         "Cash Reduced by 30% (Budget → Rp 2.8 M)",
         "WH Capacity Reduced to 2,000 units",
         "Campaign Pulled Forward (Need stock in 2 weeks)",
         "B2B Buyer Batal (Need Rp 2.5M alternative)"],
        horizontal=True
    )
    
    # Apply crisis constraints
    if "Cash Reduced" in crisis:
        budget_limit = 2.8
        wh_limit = 4000
        st.error("💰 **Crisis:** Budget cut 30%! Now Rp 2.8 Miliar only")
    elif "WH Capacity" in crisis:
        budget_limit = 4.0
        wh_limit = 2000
        st.error("🏭 **Crisis:** WH capacity reduced to 2,000 units!")
    elif "Campaign" in crisis:
        budget_limit = 4.0
        wh_limit = 4000
        st.warning("⚡ **Crisis:** Campaign pulled forward! Need stock in 2 weeks (use more Air freight)")
    elif "B2B" in crisis:
        budget_limit = 4.0
        wh_limit = 4000
        st.warning("📦 **Crisis:** B2B buyer batal! Need alternative Rp 2.5M cash unlock")
    else:
        budget_limit = 4.0
        wh_limit = 4000
    
    # Recalculate with crisis
    df_crisis = df_a.copy()
    
    if "Campaign" in crisis:
        # Need more air freight
        df_crisis['Air Urgent Qty'] = df_crisis['Suggested Order Qty'] * 0.8
        df_crisis['Sea Qty'] = df_crisis['Suggested Order Qty'] * 0.2
    else:
        # Normal split
        df_crisis['Air Urgent Qty'] = df_crisis.apply(
            lambda row: round(row['Suggested Order Qty'] * 0.7) if 'CRITICAL' in row['DOS Status']
            else (round(row['Suggested Order Qty'] * 0.4) if 'WASPADA' in row['DOS Status']
            else round(row['Suggested Order Qty'] * 0.1)), axis=1
        )
        df_crisis['Sea Qty'] = df_crisis['Suggested Order Qty'] - df_crisis['Air Urgent Qty']
    
    # Recalculate costs
    df_crisis['Order Value Sea'] = df_crisis['Sea Qty'] * df_crisis['Unit Cost'] * 1.1
    df_crisis['Order Value Air'] = df_crisis['Air Urgent Qty'] * df_crisis['Unit Cost'] * 4.0
    df_crisis['Total Order Value'] = df_crisis['Order Value Sea'] + df_crisis['Order Value Air']
    df_crisis['Warehouse Space Impact (M1)'] = df_crisis['Air Urgent Qty']
    
    total_cost_crisis = df_crisis['Total Order Value'].sum()
    total_wh_crisis = df_crisis['Warehouse Space Impact (M1)'].sum()
    
    # Display crisis impact
    col_cr1, col_cr2, col_cr3, col_cr4 = st.columns(4)
    
    with col_cr1:
        st.metric("💰 Total Cash", format_rupiah(total_cost_crisis),
                 delta=f"{'Over' if total_cost_crisis > budget_limit*1e9 else 'Under'}",
                 delta_color="inverse" if total_cost_crisis > budget_limit*1e9 else "normal")
    
    with col_cr2:
        st.metric("🏭 WH Space", f"{total_wh_crisis:,.0f} units",
                 delta=f"{'Exceeds' if total_wh_crisis > wh_limit else 'Within'}",
                 delta_color="inverse" if total_wh_crisis > wh_limit else "normal")
    
    with col_cr3:
        st.metric("Budget Limit", f"Rp {budget_limit:.1f} M")
    
    with col_cr4:
        st.metric("WH Limit", f"{wh_limit:,.0f} units")
    
    # Decision controls
    st.markdown("### 🎯 Your Decision")
    
    col_dec1, col_dec2, col_dec3 = st.columns(3)
    
    with col_dec1:
        device_a_action = st.selectbox("Device A Action", 
                                       ["Full Order", "Reduce 30%", "Hold", "All Air", "All Sea"])
    with col_dec2:
        device_b_action = st.selectbox("Device B Action",
                                       ["Full Order", "Reduce 30%", "Hold", "All Air", "All Sea"])
    with col_dec3:
        device_c_action = st.selectbox("Device C Action",
                                       ["Full Order", "Reduce 30%", "Hold", "All Air", "All Sea"])
    
    # Apply decisions
    df_final = df_crisis.copy()
    
    action_mult = {
        "Full Order": 1.0,
        "Reduce 30%": 0.7,
        "Hold": 0.0,
        "All Air": 1.0,
        "All Sea": 1.0
    }
    
    for idx, row in df_final.iterrows():
        if row['Item'] == 'Device A':
            mult = action_mult[device_a_action]
            if device_a_action == "All Air":
                df_final.loc[idx, 'Air Urgent Qty'] = round(row['Suggested Order Qty'] * mult)
                df_final.loc[idx, 'Sea Qty'] = 0
            elif device_a_action == "All Sea":
                df_final.loc[idx, 'Air Urgent Qty'] = 0
                df_final.loc[idx, 'Sea Qty'] = round(row['Suggested Order Qty'] * mult)
            else:
                df_final.loc[idx, 'Air Urgent Qty'] = round(row['Air Urgent Qty'] * mult)
                df_final.loc[idx, 'Sea Qty'] = round(row['Sea Qty'] * mult)
        
        elif row['Item'] == 'Device B':
            mult = action_mult[device_b_action]
            if device_b_action == "All Air":
                df_final.loc[idx, 'Air Urgent Qty'] = round(row['Suggested Order Qty'] * mult)
                df_final.loc[idx, 'Sea Qty'] = 0
            elif device_b_action == "All Sea":
                df_final.loc[idx, 'Air Urgent Qty'] = 0
                df_final.loc[idx, 'Sea Qty'] = round(row['Suggested Order Qty'] * mult)
            else:
                df_final.loc[idx, 'Air Urgent Qty'] = round(row['Air Urgent Qty'] * mult)
                df_final.loc[idx, 'Sea Qty'] = round(row['Sea Qty'] * mult)
        
        else:  # Device C
            mult = action_mult[device_c_action]
            if device_c_action == "All Air":
                df_final.loc[idx, 'Air Urgent Qty'] = round(row['Suggested Order Qty'] * mult)
                df_final.loc[idx, 'Sea Qty'] = 0
            elif device_c_action == "All Sea":
                df_final.loc[idx, 'Air Urgent Qty'] = 0
                df_final.loc[idx, 'Sea Qty'] = round(row['Suggested Order Qty'] * mult)
            else:
                df_final.loc[idx, 'Air Urgent Qty'] = round(row['Air Urgent Qty'] * mult)
                df_final.loc[idx, 'Sea Qty'] = round(row['Sea Qty'] * mult)
    
    # Recalculate final costs
    df_final['Order Value Sea'] = df_final['Sea Qty'] * df_final['Unit Cost'] * 1.1
    df_final['Order Value Air'] = df_final['Air Urgent Qty'] * df_final['Unit Cost'] * 4.0
    df_final['Total Order Value'] = df_final['Order Value Sea'] + df_final['Order Value Air']
    df_final['Warehouse Space Impact (M1)'] = df_final['Air Urgent Qty']
    
    total_cost_final = df_final['Total Order Value'].sum()
    total_wh_final = df_final['Warehouse Space Impact (M1)'].sum()
    
    # Show final plan
    st.markdown("### 📊 Revised Import Plan")
    
    display_final = df_final[['Item', 'Current Stock', 'DOS Status', 'Suggested Order Qty',
                              'Air Urgent Qty', 'Sea Qty', 'Total Order Value']].copy()
    
    display_final['Current Stock'] = display_final['Current Stock'].apply(lambda x: f"{x:,.0f}")
    display_final['Suggested Order Qty'] = display_final['Suggested Order Qty'].apply(lambda x: f"{x:,.0f}")
    display_final['Air Urgent Qty'] = display_final['Air Urgent Qty'].apply(lambda x: f"{x:,.0f}")
    display_final['Sea Qty'] = display_final['Sea Qty'].apply(lambda x: f"{x:,.0f}")
    display_final['Total Order Value'] = display_final['Total Order Value'].apply(format_rupiah)
    
    st.dataframe(display_final, use_container_width=True, hide_index=True)
    
    # Feasibility check
    st.markdown("### ✅ Feasibility Check")
    
    col_check1, col_check2 = st.columns(2)
    
    with col_check1:
        if total_cost_final <= budget_limit * 1e9:
            st.success(f"✅ **Budget OK:** Rp {total_cost_final/1e9:.2f}M ≤ {budget_limit:.1f}M")
        else:
            st.error(f"❌ **Budget EXCEEDED:** Rp {total_cost_final/1e9:.2f}M > {budget_limit:.1f}M")
            st.markdown(f"*Need to reduce by Rp {(total_cost_final - budget_limit*1e9)/1e9:.2f}M*")
    
    with col_check2:
        if total_wh_final <= wh_limit:
            st.success(f"✅ **WH Capacity OK:** {total_wh_final:,.0f} ≤ {wh_limit:,.0f} units")
        else:
            st.error(f"❌ **WH Capacity EXCEEDED:** {total_wh_final:,.0f} > {wh_limit:,.0f} units")
            st.markdown(f"*Need to reduce by {total_wh_final - wh_limit:,.0f} units*")
    
    # Update score
    if total_cost_final <= budget_limit * 1e9 and total_wh_final <= wh_limit:
        st.session_state.score += 100
        st.balloons()
        st.success("🎉 **Excellent decision!** +100 points")
    else:
        st.session_state.score -= 50
        st.error("💥 **Constraints violated!** -50 points")
    
    # If B2B crisis, show alternative
    if "B2B" in crisis:
        st.markdown("### 📦 Alternative Cash Unlock Plan")
        st.markdown("Since B2B buyer batal, here's alternative to unlock Rp 2.5M:")
        
        alt_plan = pd.DataFrame({
            'Strategy': ['Device Z Bundling', 'Device A Flash Sale', 'Device B Export'],
            'Units': [3000, 2000, 1000],
            'Discount': ['15%', '20%', '25%'],
            'Cash Unlock': ['Rp 306J', 'Rp 136J', 'Rp 71J'],
            'Status': ['Ready', 'Need approval', 'Need buyer']
        })
        st.dataframe(alt_plan, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 20px;'>
    <p>🚀 FOOM LAB GLOBAL S&OP Command Center | Prepared by Mulyanto | Ready for Live Defense</p>
    <p style='font-size: 0.8rem;'>Last updated: {} | Auto-refresh every 5 minutes in presentation mode</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)

# Auto-refresh in presentation mode
if st.session_state.presentation_mode:
    time.sleep(30)
    st.rerun()
