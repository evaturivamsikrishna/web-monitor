import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="🔗 Web Monitor",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Professional Link Checker Dashboard"}
)

# Custom CSS for dark theme with neon colors
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    body {
        background-color: #0a0e27;
        color: #e0e0ff;
    }
    
    .main {
        background: linear-gradient(135deg, #0a0e27 0%, #16213e 100%);
    }
    
    /* Header Styling */
    .header-container {
        background: linear-gradient(90deg, #00ff88 0%, #00ffff 50%, #ff00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
        margin-bottom: 10px;
    }
    
    /* Metric Cards */
    [data-testid="metric-container"] {
        background-color: #16213e;
        border: 2px solid #00ff88;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #00ffff;
        font-size: 2.5em;
        font-weight: 900;
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: #00ff88;
        font-weight: 600;
    }
    
    /* Tabs */
    [data-baseweb="tab-list"] {
        background-color: #16213e !important;
        border-bottom: 2px solid #00ff88;
    }
    
    [data-baseweb="tab"] {
        color: #e0e0ff !important;
        font-weight: 600;
    }
    
    [aria-selected="true"] {
        color: #00ff88 !important;
        border-bottom: 3px solid #00ff88 !important;
    }
    
    /* Data Frame */
    [data-testid="dataframe"] {
        background-color: #16213e !important;
    }
    
    /* Subheader */
    h2, h3 {
        color: #00ff88;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00ff88 0%, #00ffff 100%);
        color: #0a0e27;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.6);
    }
    
    /* Info/Warning/Success Boxes */
    .stAlert {
        background-color: #16213e;
        border-left: 4px solid #00ff88;
        color: #e0e0ff;
    }
    
    /* Divider */
    hr {
        border: 1px solid rgba(0, 255, 136, 0.3);
    }
    
    /* Download Button */
    [data-testid="downloadButton"] {
        background: linear-gradient(90deg, #ff00ff 0%, #00ffff 100%);
        color: white;
        font-weight: 700;
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
    st.markdown('<h1 class="header-container">🔗 Web Monitor</h1>', unsafe_allow_html=True)
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
    
    # KPI Row - Professional Cards
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        st.metric("📊 Total URLs", f"{total_urls:,}", "checked")
    
    with col2:
        st.metric("🔴 Broken Links", broken_count, 
                 f"{(broken_count/total_urls*100 if total_urls > 0 else 0):.1f}%")
    
    with col3:
        st.metric("✅ Success Rate", f"{success_rate:.1f}%", 
                 "↑ Excellent" if success_rate > 90 else "⚠ Check needed")
    
    with col4:
        st.metric("⏱️ Timeouts", timeout_count, "requests")
    
    st.divider()
    
    # Info Box
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"✅ Last Check: {last_check}")
    with col2:
        st.info(f"🌐 Base URL: {base_url}")
    with col3:
        st.caption(f"📈 Response: Healthy" if success_rate > 80 else "⚠️ Needs Attention")
    
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

