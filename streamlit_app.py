import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Configure page FIRST
st.set_page_config(
    page_title="🔗 Web Monitor",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Professional Link Checker Dashboard"}
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
    st.markdown("# 🔗 Web Monitor")
    st.caption("⚡ Professional Link Checker with Real-Time Analysis")

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
- ✅ Async link checking
- ✅ 7-day history tracking
- ✅ Broken link detection
- ✅ Real-time dashboard
- ✅ CSV export
            """)
else:
    # Extract metrics
    total_urls = results.get("total_urls", 0)
    broken_count = results.get("broken_count", 0)
    success_rate = results.get("success_rate", 0)
    timeout_count = results.get("timeout_count", 0)
    base_url = results.get("base_url", "N/A")
    
    # Last check time
    try:
        last_check = datetime.fromisoformat(results.get("last_check", "")).strftime("%b %d, %H:%M UTC")
    except:
        last_check = "Just now"
    
    # Compact KPI Cards
    col1, col2, col3, col4 = st.columns(4, gap="small")
    
    with col1:
        st.metric("📊 Total URLs", f"{total_urls:,}", "links")
    
    with col2:
        st.metric("❌ Broken", broken_count, 
                 f"{(broken_count/total_urls*100 if total_urls > 0 else 0):.1f}%")
    
    with col3:
        st.metric("✅ Success", f"{success_rate:.0f}%", 
                 "Excellent" if success_rate > 90 else "Need Check")
    
    with col4:
        st.metric("⏱️ Timeouts", timeout_count, "reqs")
    
    st.divider()
    
    # Quick Status Info - Compact
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.success(f"✅ Last Check: {last_check}")
    with col2:
        st.info(f"🌐 {base_url.replace('https://', '').split('/')[0]}")
    with col3:
        status = "✨ Healthy" if success_rate > 80 else "⚠️ Issues"
        st.warning(f"Status: {status}")
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔗 Broken Links", "📈 Trends", "ℹ️ Details"])
    
    with tab1:
        st.subheader("Status Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Status counts
            status_data = {
                "✅ OK": len([r for r in results.get("results", []) if r.get("status") == "OK"]),
                "🔴 BROKEN": len([r for r in results.get("results", []) if r.get("status") == "BROKEN"]),
                "⏱️ TIMEOUT": len([r for r in results.get("results", []) if r.get("status") == "TIMEOUT"])
            }
            
            if sum(status_data.values()) > 0:
                fig = px.pie(
                    labels=list(status_data.keys()),
                    values=list(status_data.values()),
                    color_discrete_sequence=['#00ff88', '#ff0055', '#ff00ff'],
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
            fig_gauge = create_gauge_chart(success_rate, "Success Rate (%)", "#00ff88")
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    with tab2:
        st.subheader(f"🔴 Broken Links ({broken_count})")
        
        broken = load_broken()
        if broken:
            df = pd.DataFrame(broken)
            
            # Style the dataframe
            st.dataframe(
                df[["url", "code", "status"]].rename(columns={
                    "url": "🔗 URL",
                    "code": "📊 Status Code",
                    "status": "⚠️ Status"
                }),
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Total broken links: {len(broken)}")
            with col2:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "broken_links.csv",
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
        st.subheader("ℹ️ Detailed Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Check Summary")
            st.write(f"**Total URLs Scanned:** {total_urls:,}")
            st.write(f"**Healthy (OK):** {len([r for r in results.get('results', []) if r.get('status') == 'OK'])}")
            st.write(f"**Broken (4xx/5xx):** {broken_count}")
            st.write(f"**Timeouts:** {timeout_count}")
            st.write(f"**Success Rate:** {success_rate:.2f}%")
        
        with col2:
            st.markdown("### ⏱️ Timing")
            st.write(f"**Last Check:** {last_check}")
            st.write(f"**Frequency:** Every 6 hours")
            st.write(f"**Next Check:** ~6 hours")
            st.write(f"**Check Type:** Async (Parallel)")
        
        st.divider()
        st.markdown("### 🔧 Configuration")
        col1, col2 = st.columns(2)
        with col1:
            st.code(f"Base URL: {base_url}", language="text")
        with col2:
            st.code("Batch Size: 20 URLs/batch", language="text")

st.divider()

# Footer
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🚀 Built with GitHub Actions + Streamlit")
with col2:
    st.caption("💰 Cost: $0/month")
with col3:
    st.caption("📧 Questions? Check GitHub repo")

