import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="🔗 Web Monitor", layout="wide")

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

# Header
st.title("🔗 Web Monitor")
st.caption("Automated link checker with GitHub Actions + Streamlit")

results = load_results()

if not results:
    st.warning("⏳ No results yet. First check runs automatically in 6 hours.")
    st.info("💡 Tip: Manually trigger check → GitHub Actions → Run workflow")
else:
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total URLs", results.get("total_urls", 0))
    col2.metric("🔴 Broken", results.get("broken_count", 0))
    col3.metric("Success Rate", f"{results.get('success_rate', 0):.1f}%")
    col4.metric("Last Check", "Just now")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Broken Links", "Trends"])
    
    with tab1:
        st.subheader("Status Distribution")
        status_data = {
            "OK": len([r for r in results.get("results", []) if r.get("status") == "OK"]),
            "BROKEN": len([r for r in results.get("results", []) if r.get("status") == "BROKEN"]),
            "TIMEOUT": len([r for r in results.get("results", []) if r.get("status") == "TIMEOUT"])
        }
        
        if sum(status_data.values()) > 0:
            fig = px.pie(labels=list(status_data.keys()), values=list(status_data.values()))
            st.plotly_chart(fig, use_container_width=True)
        
        st.info(f"🌐 **Base URL:** {results.get('base_url', 'N/A')}")
    
    with tab2:
        broken = load_broken()
        if broken:
            st.subheader(f"Broken Links ({len(broken)})")
            df = pd.DataFrame(broken)
            st.dataframe(df[["url", "code", "status"]], use_container_width=True, hide_index=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                "broken_links.csv",
                "text/csv"
            )
        else:
            st.success("✅ No broken links found!")
    
    with tab3:
        history = load_history()
        if history:
            st.subheader("7-Day Trend")
            df = pd.DataFrame(history)
            
            fig = px.line(df, x="date", y="success_rate", markers=True, title="Success Rate")
            st.plotly_chart(fig, use_container_width=True)
            
            fig2 = px.bar(df, x="date", y=["total", "broken"], title="URLs Checked vs Broken")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No history yet. Check back in 6 hours.")

st.divider()
st.caption("Built with GitHub Actions + Streamlit Cloud | $0/month")
