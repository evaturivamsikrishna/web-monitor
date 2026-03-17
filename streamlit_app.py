import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
try:
    from html_report import create_full_html_report, save_html_report
except ImportError:
    pass

# Configure page FIRST
st.set_page_config(
    page_title="🔗 WebMonitor Pro",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Enterprise Link Monitoring with AI Insights"}
)

# Inject CSS IMMEDIATELY after page config
st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0a0e27;
        }
        
        body {
            background-color: #0a0e27;
            color: #e0e0ff;
        }
        
        /* Hide default streamlit theming to use our own */
        [data-testid="stAppViewContainer"] {
            background-color: #0a0e27;
        }
        
        /* Metric styling - Compact Cards */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #16213e 0%, #1a2851 100%);
            border: 1.5px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.25), inset 0 0 10px rgba(0, 255, 255, 0.05);
            transition: all 0.3s ease;
        }
        
        [data-testid="metric-container"]:hover {
            border-color: #00ffff;
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.4), inset 0 0 10px rgba(0, 255, 255, 0.1);
            transform: translateY(-2px);
        }
        
        [data-testid="metric-value"] {
            color: #00ffff;
            font-size: 1.8em;
            font-weight: 900 !important;
            letter-spacing: 1px;
        }
        
        [data-testid="metric-label"] {
            color: #00ff88;
            font-weight: 600 !important;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Headers */
        h1 {
            color: #00ff88 !important;
            text-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
            font-size: 2.5em;
            margin-bottom: 5px;
        }
        
        h2, h3 {
            color: #00ff88 !important;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
            margin-top: 0;
        }
        
        /* Tab styling - Enhanced */
        [data-baseweb="tab-list"] {
            background-color: #16213e;
            border-bottom: 2px solid rgba(0, 255, 136, 0.2);
            padding: 10px;
            border-radius: 10px 10px 0 0;
            gap: 5px;
        }
        
        [data-baseweb="tab"] {
            background-color: #1a2851;
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 8px;
            color: #a0a0ff !important;
            font-weight: 600 !important;
            padding: 12px 20px !important;
            margin: 0 5px;
            transition: all 0.3s ease;
        }
        
        [data-baseweb="tab"]:hover {
            background-color: #16213e;
            border-color: #00ffff;
            color: #00ffff !important;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
        }
        
        [aria-selected="true"] {
            background: linear-gradient(135deg, #00ff88 0%, #00ffff 100%) !important;
            color: #0a0e27 !important;
            border-color: #00ff88 !important;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
            font-weight: 700 !important;
        }
        
        /* Tab content - Nice background */
        [data-baseweb="tab-panel"] {
            background-color: #16213e;
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-top: none;
            border-radius: 0 0 10px 10px;
            padding: 20px;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, #00ff88 0%, #00ffff 100%) !important;
            color: #0a0e27 !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.5);
            transform: translateY(-2px);
        }
        
        .stButton > button:active {
            transform: translateY(0);
        }
        
        /* Alerts & Containers */
        .stAlert {
            background-color: #16213e;
            border-left: 4px solid #00ff88;
            border-radius: 8px;
            color: #e0e0ff;
        }
        
        /* Divider */
        hr {
            border: 1px solid rgba(0, 255, 136, 0.2);
            margin: 20px 0;
        }
        
        /* Text color */
        [data-testid="stMarkdownContainer"] {
            color: #e0e0ff;
        }
        
        /* Caption styling */
        .stCaption {
            color: #a0a0ff;
        }
        
        /* Container background */
        [data-testid="stContainer"] {
            background-color: transparent;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_results():
    try:
        with open("data/results.json") as f:
            return json.load(f)
    except:
        return None

@st.cache_data(ttl=300)
def load_broken():
    try:
        with open("data/broken_urls.json") as f:
            return json.load(f)
    except:
        return []

@st.cache_data(ttl=300)
def load_history():
    history = []
    history_dir = Path("data/history")
    if history_dir.exists():
        for file in sorted(history_dir.glob("*.json"), reverse=True)[:7]:
            with open(file) as f:
                data = json.load(f)
                history.append({
                    "date": file.stem,
                    "total": data.get("total_urls", 0),
                    "broken": data.get("broken_count", 0),
                    "success_rate": data.get("success_rate", 0)
                })
    return history

@st.cache_data(ttl=300)
def load_ai_insights():
    """Load AI-generated insights if available"""
    try:
        import ai_insights
        return ai_insights.get_ai_insights()
    except:
        return None

@st.cache_data(ttl=300)
def load_sites_config():
    """Load multi-site configuration"""
    try:
        with open("data/sites_config.json") as f:
            return json.load(f)
    except:
        return [{"id": "primary", "name": "Primary Site", "url": "N/A", "enabled": True}]

def calculate_health_score(site_data):
    """Calculate overall health score (0-100)"""
    if not site_data:
        return 0
    
    success_rate = site_data.get("success_rate", 0)
    response_time = site_data.get("avg_response_time_ms", 0)
    error_count = site_data.get("error_count", 0)
    timeout_count = site_data.get("timeout_count", 0)
    
    # Base score from success rate (40%)
    score = success_rate * 0.4
    
    # Response time penalty (30%), penalize if >1000ms
    if response_time < 500:
        score += 30
    elif response_time < 1000:
        score += 20
    elif response_time < 2000:
        score += 10
    
    # Error rate penalty (20%)
    total = site_data.get("total_urls", 1)
    error_rate = (error_count + timeout_count) / total if total > 0 else 0
    score += (1 - error_rate) * 20
    
    # Bonus for no recent errors (10%)
    if error_count == 0 and timeout_count == 0:
        score += 10
    
    return min(100, max(0, score))

def get_health_color(score):
    """Get color based on health score"""
    if score >= 90:
        return "#00ff88"  # Green
    elif score >= 70:
        return "#00ffff"  # Cyan
    elif score >= 50:
        return "#ffaa00"  # Orange
    else:
        return "#ff0055"  # Red

def get_anomalies(current_results):
    """Detect anomalies in current results"""
    anomalies = []
    
    if not current_results:
        return anomalies
    
    sites = current_results.get("sites", [])
    
    for site in sites:
        # High latency check
        p95 = site.get("p95_response_time_ms", 0)
        avg = site.get("avg_response_time_ms", 0)
        
        if p95 > 5000:
            anomalies.append({
                "type": "high_latency",
                "site": site["site_name"],
                "value": f"{p95:.0f}ms P95",
                "severity": "high" if p95 > 10000 else "medium"
            })
        
        # High error rate check
        total = site.get("total_urls", 1)
        broken = site.get("broken_count", 0)
        error_rate = broken / total if total > 0 else 0
        
        if error_rate > 0.1:  # >10% broken
            anomalies.append({
                "type": "high_error_rate",
                "site": site["site_name"],
                "value": f"{error_rate*100:.1f}% broken",
                "severity": "high" if error_rate > 0.2 else "medium"
            })
        
        # High timeout rate check
        timeouts = site.get("timeout_count", 0)
        timeout_rate = timeouts / total if total > 0 else 0
        
        if timeout_rate > 0.05:  # >5% timeouts
            anomalies.append({
                "type": "high_timeout_rate",
                "site": site["site_name"],
                "value": f"{timeout_rate*100:.1f}% timeouts",
                "severity": "medium"
            })
    
    return anomalies


def create_gauge_chart(value, title, color):
    """Create a professional gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title, 'font': {'size': 20, 'color': '#00ff88'}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#00ff88'},
            'bar': {'color': color},
            'bgcolor': '#16213e',
            'borderwidth': 2,
            'bordercolor': '#00ff88',
            'steps': [
                {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.1)'},
                {'range': [50, 80], 'color': 'rgba(255, 165, 0, 0.1)'},
                {'range': [80, 100], 'color': 'rgba(0, 255, 136, 0.1)'}
            ],
            'threshold': {
                'line': {'color': '#ff00ff', 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    fig.update_layout(
        font={'color': '#e0e0ff', 'size': 12},
        plot_bgcolor='#16213e',
        paper_bgcolor='rgba(0,0,0,0)',
        margin={'b': 20, 'l': 20, 'r': 20, 't': 60}
    )
    return fig

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# 🔗 WebMonitor Pro")
    st.caption("⚡ Enterprise Link Checking with AI Insights & Alerts")

# Sidebar - Site Selector & Settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    sites_config = load_sites_config()
    site_names = [s["name"] for s in sites_config if s.get("enabled", True)]
    
    if len(site_names) > 1:
        selected_site_name = st.selectbox("📍 Select Site", site_names)
    else:
        selected_site_name = site_names[0] if site_names else "Primary Site"
    
    st.divider()
    
    st.markdown("### 🔔 Alert Configuration")
    
    slack_enabled = st.checkbox("Slack Alerts", value=bool(os.getenv("SLACK_WEBHOOK")))
    discord_enabled = st.checkbox("Discord Alerts", value=bool(os.getenv("DISCORD_WEBHOOK")))
    
    if slack_enabled:
        st.info("✅ Slack alerts configured")
    if discord_enabled:
        st.info("✅ Discord alerts configured")
    
    if not (slack_enabled or discord_enabled):
        st.warning("⚠️ No alerts configured. Set SLACK_WEBHOOK or DISCORD_WEBHOOK in secrets.")
    
    st.divider()
    
    st.markdown("### 📊 Quick Stats")
    results = load_results()
    if results and results.get("sites"):
        sites = results["sites"]
        total_broken = sum(s.get("broken_count", 0) for s in sites)
        total_urls = sum(s.get("total_urls", 0) for s in sites)
        avg_success = sum(s.get("success_rate", 0) for s in sites) / len(sites) if sites else 0
        
        st.metric("📊 Total URLs", f"{total_urls:,}")
        st.metric("🔴 Broken", total_broken)
        st.metric("✅ Avg Success", f"{avg_success:.1f}%")

results = load_results()

if not results:
    st.warning("⏳ No check results yet")
    st.info("💡 To start: Set BASE_URL in GitHub Secrets → Run GitHub Actions workflow")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📋 Quick Setup")
            st.code("""
1. Go to GitHub repo Settings
2. Secrets & variables → Actions
3. Add: BASE_URL = your-site.com
4. Run workflow manually
            """)
        with col2:
            st.markdown("### 🚀 Features")
            st.markdown("""
- ✅ Multi-site checking
- ✅ AI insights & anomaly detection
- ✅ Alert notifications (Slack/Discord)
- ✅ Health scoring
- ✅ Performance percentiles
- ✅ 7-day trend tracking
            """)
else:
    # Handle both old (single-site) and new (multi-site) formats
    if "sites" in results:
        sites_data = results["sites"]
        selected_site = next((s for s in sites_data if s.get("site_name") == selected_site_name), sites_data[0] if sites_data else None)
    else:
        # Old format - convert to new format
        selected_site = {
            "site_id": "primary",
            "site_name": "Primary Site",
            "base_url": results.get("base_url", "N/A"),
            "total_urls": results.get("total_urls", 0),
            "broken_count": results.get("broken_count", 0),
            "timeout_count": results.get("timeout_count", 0),
            "error_count": 0,
            "success_rate": results.get("success_rate", 0),
            "avg_response_time_ms": 0,
            "p50_response_time_ms": 0,
            "p95_response_time_ms": 0,
            "p99_response_time_ms": 0,
            "results": results.get("results", [])
        }
    
    if not selected_site:
        st.error("❌ No site data available")
    else:
        # Extract metrics
        total_urls = selected_site.get("total_urls", 0)
        broken_count = selected_site.get("broken_count", 0)
        success_rate = selected_site.get("success_rate", 0)
        timeout_count = selected_site.get("timeout_count", 0)
        error_count = selected_site.get("error_count", 0)
        avg_response_time = selected_site.get("avg_response_time_ms", 0)
        p50_response_time = selected_site.get("p50_response_time_ms", 0)
        p95_response_time = selected_site.get("p95_response_time_ms", 0)
        p99_response_time = selected_site.get("p99_response_time_ms", 0)
        base_url = selected_site.get("base_url", "N/A")
        
        # Calculate health score
        health_score = calculate_health_score(selected_site)
        health_color = get_health_color(health_score)
        
        # Last check time
        try:
            last_check = datetime.fromisoformat(results.get("timestamp", "")).strftime("%b %d, %H:%M UTC")
        except:
            last_check = "Just now"
        
        # Display Health Score Prominently
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {health_color}20 0%, {health_color}10 100%); 
                    border: 2px solid {health_color}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
            <h2 style="color: {health_color}; margin: 0 0 10px 0;">💪 Health Score: {health_score:.0f}/100</h2>
            <p style="color: #e0e0ff; margin: 5px 0;">
                {'✅ Excellent' if health_score >= 90 else '⚠️ Good' if health_score >= 70 else '🔴 Needs Attention' if health_score >= 50 else '❌ Critical'}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact KPI Cards with Performance Metrics
        col1, col2, col3, col4, col5 = st.columns(5, gap="small")
        
        with col1:
            st.metric("📊 Total", f"{total_urls:,}", "links")
        with col2:
            st.metric("❌ Broken", broken_count, 
                     f"{(broken_count/total_urls*100 if total_urls > 0 else 0):.1f}%")
        with col3:
            st.metric("✅ Success", f"{success_rate:.0f}%")
        with col4:
            st.metric("⏱️ Avg", f"{avg_response_time:.0f}ms")
        with col5:
            st.metric("P95", f"{p95_response_time:.0f}ms")
        
        st.divider()
        
        # Anomalies Section
        anomalies = get_anomalies(results)
        if anomalies:
            st.markdown("### ⚠️ Detected Anomalies")
            for anomaly in anomalies:
                severity = anomaly.get("severity", "medium")
                icon = "🔴" if severity == "high" else "🟡"
                st.warning(f"{icon} **{anomaly['type'].replace('_', ' ').title()}** - {anomaly['value']}")
        
        st.divider()
        
        # Quick Status Info
        col1, col2, col3 = st.columns(3, gap="small")
        with col1:
            st.success(f"✅ Last Check: {last_check}")
        with col2:
            st.info(f"🌐 {base_url.replace('https://', '').split('/')[0]}")
        with col3:
            status = "✨ Healthy" if health_score > 80 else "⚠️ Issues" if health_score > 50 else "🚨 Critical"
            if health_score > 80:
                st.success(status)
            elif health_score > 50:
                st.warning(status)
            else:
                st.error(status)
        
        st.divider()
        
        # Tabs - Enhanced with new sections
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Overview", 
            "🔗 Broken Links", 
            "📈 Trends", 
            "⚡ Performance", 
            "🤖 AI Insights",
            "ℹ️ Details",
            "📄 Report"
        ])
    
        with tab1:
            st.subheader("Status Distribution")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Status counts
                status_data = {
                    "✅ OK": len([r for r in selected_site.get("results", []) if r.get("status") == "OK"]),
                    "🔴 BROKEN": len([r for r in selected_site.get("results", []) if r.get("status") == "BROKEN"]),
                    "⏱️ TIMEOUT": len([r for r in selected_site.get("results", []) if r.get("status") == "TIMEOUT"]),
                    "❌ ERROR": len([r for r in selected_site.get("results", []) if r.get("status") == "ERROR"])
                }
                
                if sum(status_data.values()) > 0:
                    fig = px.pie(
                        labels=list(status_data.keys()),
                        values=list(status_data.values()),
                        color_discrete_sequence=['#00ff88', '#ff0055', '#ff00ff', '#ffaa00'],
                        title="Link Status Breakdown"
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(
                        font={'color': '#e0e0ff'},
                        plot_bgcolor='#16213e',
                        paper_bgcolor='rgba(0,0,0,0)',
                        title_font_size=16,
                        title_font_color='#00ff88'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Success rate gauge
                fig_gauge = create_gauge_chart(success_rate, "Success Rate (%)", health_color)
                st.plotly_chart(fig_gauge, use_container_width=True)
        
        with tab2:
            st.subheader(f"🔴 Broken Links ({broken_count})")
            
            broken = load_broken()
            
            # Filter broken links for selected site
            if broken and "site_id" in broken[0]:
                broken = [b for b in broken if b.get("site_id") == selected_site.get("site_id")]
            
            if broken:
                df = pd.DataFrame(broken)
                
                # Advanced filtering
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_filter = st.multiselect(
                        "Filter by Status", 
                        ["BROKEN", "TIMEOUT", "ERROR"],
                        default=["BROKEN", "TIMEOUT", "ERROR"]
                    )
                with col2:
                    error_type_filter = st.multiselect(
                        "Filter by Error Type",
                        df["error_type"].unique() if "error_type" in df.columns else [],
                        default=df["error_type"].unique() if "error_type" in df.columns else []
                    )
                with col3:
                    search_term = st.text_input("🔍 Search URLs", "")
                
                # Apply filters
                if status_filter:
                    df = df[df["status"].isin(status_filter)]
                if error_type_filter and "error_type" in df.columns:
                    df = df[df["error_type"].isin(error_type_filter)]
                if search_term:
                    df = df[df["url"].str.contains(search_term, case=False, na=False)]
                
                # Display filtered dataframe
                st.dataframe(
                    df[["url", "code", "status", "error_type"] if "error_type" in df.columns else ["url", "code", "status"]].rename(columns={
                        "url": "🔗 URL",
                        "code": "📊 Status",
                        "status": "⚠️ Type",
                        "error_type": "📝 Error"
                    }),
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Showing {len(df)} broken links")
                with col2:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"broken_links_{selected_site.get('site_id', 'export')}.csv",
                        "text/csv"
                    )
            else:
                st.success("✨ No broken links found! All URLs are healthy.")
        
        with tab3:
            st.subheader("📈 7-Day Trend Analysis")
            
            history = load_history()
            if history:
                df_history = pd.DataFrame(history)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Success rate trend
                    fig_line = px.line(
                        df_history,
                        x="date",
                        y="success_rate",
                        markers=True,
                        title="Success Rate Trend",
                        labels={"success_rate": "Success Rate (%)"},
                        line_shape="spline"
                    )
                    fig_line.update_traces(
                        line_color='#00ff88',
                        marker_size=10,
                        marker_color='#00ffff'
                    )
                    fig_line.update_layout(
                        font={'color': '#e0e0ff'},
                        plot_bgcolor='#16213e',
                        paper_bgcolor='rgba(0,0,0,0)',
                        hovermode='x unified',
                        title_font_color='#00ff88'
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                
                with col2:
                    # URLs checked trend
                    fig_bar = px.bar(
                        df_history,
                        x="date",
                        y=["total", "broken"],
                        title="URLs Checked vs Broken",
                        barmode='group',
                        labels={"date": "Date", "value": "Count", "variable": "Type"}
                    )
                    fig_bar.update_traces(
                        marker_color=['#00ff88', '#ff0055']
                    )
                    fig_bar.update_layout(
                        font={'color': '#e0e0ff'},
                        plot_bgcolor='#16213e',
                        paper_bgcolor='rgba(0,0,0,0)',
                        hovermode='x unified',
                        title_font_color='#00ff88',
                        legend={'font': {'color': '#e0e0ff'}}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("📊 Historical data will appear after more checks")
        
        with tab4:
            st.subheader("⚡ Performance Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Response Time Percentiles")
                st.metric("Average", f"{avg_response_time:.0f}ms")
                st.metric("P50 (Median)", f"{p50_response_time:.0f}ms")
                st.metric("P95 (95th %ile)", f"{p95_response_time:.0f}ms")
                st.metric("P99 (99th %ile)", f"{p99_response_time:.0f}ms")
            
            with col2:
                # Response time distribution
                results_list = selected_site.get("results", [])
                response_times = [r.get("response_time_ms", 0) for r in results_list if r.get("response_time_ms", 0) > 0]
                
                if response_times:
                    fig_hist = px.histogram(
                        {"response_time": response_times},
                        x="response_time",
                        nbins=30,
                        title="Response Time Distribution",
                        labels={"response_time": "Response Time (ms)"}
                    )
                    fig_hist.update_traces(marker_color='#00ff88')
                    fig_hist.update_layout(
                        font={'color': '#e0e0ff'},
                        plot_bgcolor='#16213e',
                        paper_bgcolor='rgba(0,0,0,0)',
                        title_font_color='#00ff88',
                        showlegend=False
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No response time data available")
            
            st.divider()
            
            # Error classification
            st.markdown("### 📋 Error Type Breakdown")
            error_types = {}
            for result in selected_site.get("results", []):
                if result.get("status") != "OK":
                    error_type = result.get("error_type", "Unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            if error_types:
                df_errors = pd.DataFrame(list(error_types.items()), columns=["Error Type", "Count"])
                fig_errors = px.bar(
                    df_errors,
                    x="Error Type",
                    y="Count",
                    title="Errors by Type",
                    color_discrete_sequence=['#ff0055']
                )
                fig_errors.update_layout(
                    font={'color': '#e0e0ff'},
                    plot_bgcolor='#16213e',
                    paper_bgcolor='rgba(0,0,0,0)',
                    title_font_color='#00ff88',
                    xaxis_title="Error Type",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig_errors, use_container_width=True)
        
        with tab5:
            st.subheader("🤖 AI-Powered Insights")
            
            try:
                import ai_insights
                insights = ai_insights.get_ai_insights()
                
                if insights:
                    # Display recommendations
                    if insights.get("recommendations"):
                        st.markdown("### 💡 Recommendations")
                        for rec in insights["recommendations"][:5]:
                            priority_color = "🔴" if rec.get("priority") == "high" else "🟡"
                            with st.container():
                                st.markdown(f"**{priority_color} {rec.get('title', 'N/A')}**")
                                st.write(rec.get('details', ''))
                                if rec.get('urls'):
                                    for url in rec['urls'][:3]:
                                        st.code(url, language="text")
                    
                    # AI Summary
                    if insights.get("ai_summary"):
                        st.markdown("### 📝 AI Summary")
                        st.write(insights["ai_summary"])
                    
                    # Patterns
                    if insights.get("patterns"):
                        patterns = insights["patterns"]
                        st.markdown("### 📊 Detected Patterns")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Consistently Broken", patterns.get("consistently_broken", 0))
                        with col2:
                            st.metric("Intermittent Issues", patterns.get("intermittent_issues", 0))
                        with col3:
                            st.metric("Latency Trend", patterns.get("latency_trend", "Unknown").title())
                else:
                    st.info("💡 Enable OpenAI API key in GitHub Secrets to get AI insights")
            except ImportError:
                st.warning("⚠️ OpenAI integration not available")
        
        with tab6:
            st.subheader("ℹ️ Detailed Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 Check Summary")
                st.write(f"**Total URLs Scanned:** {total_urls:,}")
                st.write(f"**Healthy (OK):** {len([r for r in selected_site.get('results', []) if r.get('status') == 'OK'])}")
                st.write(f"**Broken (4xx/5xx):** {broken_count}")
                st.write(f"**Timeouts:** {timeout_count}")
                st.write(f"**Errors:** {error_count}")
                st.write(f"**Success Rate:** {success_rate:.2f}%")
                st.write(f"**Health Score:** {health_score:.0f}/100")
            
            with col2:
                st.markdown("### ⏱️ Timing")
                st.write(f"**Last Check:** {last_check}")
                st.write(f"**Frequency:** Every 6 hours")
                st.write(f"**Check Type:** Async (Parallel)")
                st.write(f"**Batch Size:** 20 URLs/batch")
                st.write(f"**Site ID:** {selected_site.get('site_id', 'N/A')}")
            
            st.divider()
            st.markdown("### 🔧 Configuration")
            col1, col2 = st.columns(2)
            with col1:
                st.code(f"Base URL:\n{base_url}", language="text")
            with col2:
                st.code(f"""Retry Count: {selected_site.get('retry_count', 3)}
Timeout: {selected_site.get('timeout', 10)}s""", language="text")
        
        with tab7:
            st.subheader("📄 Professional HTML Report")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("Generate a professional HTML report that can be shared, printed, or emailed to stakeholders.")
            with col2:
                if st.button("🔄 Generate Report", key="gen_report"):
                    with st.spinner("Generating report..."):
                        html_content = create_full_html_report(results_data)
                        if html_content:
                            st.success("✅ Report generated!")
                            
                            # Download button
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"webmonitor_report_{timestamp}.html"
                            st.download_button(
                                label="📥 Download HTML Report",
                                data=html_content,
                                file_name=filename,
                                mime="text/html",
                                key="download_report"
                            )
                        else:
                            st.error("❌ Failed to generate report")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📋 Report Features")
                features = [
                    "✅ Multi-site summary with health scores",
                    "📊 Performance metrics and percentiles",
                    "🔗 Broken links and error breakdown",
                    "📈 Success rates and trends",
                    "🎨 Professional styling for stakeholders",
                    "🖨️ Print-friendly formatting",
                    "📧 Email-ready HTML",
                    "⏰ Timestamped reports"
                ]
                for feature in features:
                    st.write(feature)
            
            with col2:
                st.markdown("### 🎯 Use Cases")
                use_cases = [
                    "**Executive Dashboards**: Share with leadership team",
                    "**Email Reports**: Automated daily/weekly summaries",
                    "**Print Reports**: Archive for compliance",
                    "**Stakeholder Updates**: Professional communication",
                    "**Incident Reports**: Document issues and resolutions",
                    "**Trend Analysis**: Historical report comparison",
                    "**API Documentation**: Link health status",
                    "**SLA Verification**: Compliance documentation"
                ]
                for use_case in use_cases:
                    st.write(use_case)
            
            st.divider()
            st.markdown("### 🚀 Automation")
            st.info("💡 **Pro Tip**: Set up GitHub Actions to automatically generate and email HTML reports on a scheduled basis. Check DEPLOYMENT.md for details on configuring email alerts.")

st.divider()

# Footer
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.caption("🚀 GitHub Actions + Streamlit + AI")
with col2:
    st.caption("💰 Cost: $0/month")
with col3:
    st.caption("🤖 AI Insights & Anomaly Detection")
with col4:
    st.caption("📧 Slack/Discord Alerts")

