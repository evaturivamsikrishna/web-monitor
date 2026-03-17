"""
AI Insights - Generate intelligent insights using LLM
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import openai
except ImportError:
    openai = None

RESULTS_FILE = Path("data") / "results.json"
HISTORY_DIR = Path("data") / "history"

def get_historical_data(days=7):
    """Load historical data from past N days"""
    history = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        hist_file = HISTORY_DIR / f"{date}.json"
        
        if hist_file.exists():
            try:
                with open(hist_file) as f:
                    history.append(json.load(f))
            except:
                pass
    
    return history

def analyze_patterns(current_results, history):
    """Identify patterns in monitoring data"""
    patterns = {
        "consistently_failing_urls": [],
        "intermittent_failures": [],
        "latency_trend": "stable",
        "affected_domains": defaultdict(list)
    }
    
    # Track URL failures across time
    url_failures = defaultdict(lambda: {"total": 0, "failures": 0})
    
    for day_result in history + [current_results]:
        for site in day_result.get('sites', []):
            for result in site.get('results', []):
                url = result['url']
                url_failures[url]["total"] += 1
                if result['status'] != 'OK':
                    url_failures[url]["failures"] += 1
    
    # Identify failure patterns
    for url, stats in sorted(url_failures.items(), key=lambda x: x[1]['failures'], reverse=True):
        if stats['failures'] >= len(history) * 0.7:  # Fails >70% of time
            patterns["consistently_failing_urls"].append({
                "url": url,
                "failure_rate": round(stats['failures'] / stats['total'] * 100, 1)
            })
        elif stats['failures'] > 0 and stats['failures'] < len(history) * 0.7:  # Intermittent
            patterns["intermittent_failures"].append({
                "url": url,
                "failure_rate": round(stats['failures'] / stats['total'] * 100, 1)
            })
    
    # Analyze latency trend
    current_p95 = current_results.get('sites', [{}])[0].get('p95_response_time_ms', 0)
    if len(history) > 0:
        older_p95 = history[0].get('sites', [{}])[0].get('p95_response_time_ms', 0)
        if current_p95 > older_p95 * 1.5:
            patterns["latency_trend"] = "increasing"
        elif current_p95 < older_p95 * 0.7:
            patterns["latency_trend"] = "decreasing"
    
    # Affected domains
    for site in current_results.get('sites', []):
        broken = [r for r in site.get('results', []) if r['status'] == 'BROKEN']
        domain_counts = defaultdict(int)
        for b in broken:
            try:
                domain = b['url'].split('/')[2]
                domain_counts[domain] += 1
            except:
                pass
        
        for domain, count in domain_counts.items():
            patterns["affected_domains"][site['site_id']].append({
                "domain": domain,
                "broken_count": count
            })
    
    return patterns

def generate_insights_prompt(current_results, patterns, history):
    """Generate LLM prompt for insights"""
    
    current_site = current_results.get('sites', [{}])[0]
    
    context = f"""
Website Monitoring Data Analysis
==================================

Current Status ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):
- Site: {current_site.get('site_name', 'Unknown')}
- Total URLs Checked: {current_site.get('total_urls', 0)}
- Broken Links: {current_site.get('broken_count', 0)}
- Timeouts: {current_site.get('timeout_count', 0)}
- Errors: {current_site.get('error_count', 0)}
- Success Rate: {current_site.get('success_rate', 0)}%
- Avg Response Time: {current_site.get('avg_response_time_ms', 0)}ms
- P95 Response Time: {current_site.get('p95_response_time_ms', 0)}ms
- P99 Response Time: {current_site.get('p99_response_time_ms', 0)}ms

Trends (Last {len(history)} days):
- Latency Trend: {patterns.get('latency_trend', 'unknown')}
- Consistently Broken URLs: {len(patterns.get('consistently_failing_urls', []))}
- Intermittent Failures: {len(patterns.get('intermittent_failures', []))}

Most Problematic URLs:
{json.dumps(patterns.get('consistently_failing_urls', [])[:5], indent=2)}

Task: Provide a concise, 3-4 sentence professional summary of:
1. Current health status
2. Key issues to address
3. Recommended actions

Be specific and actionable. Target an SRE or DevOps engineer.
"""
    
    return context

def call_openai_api(prompt):
    """Call OpenAI API for insights"""
    if not openai:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return None

def get_ai_insights():
    """Generate AI-powered insights"""
    if not RESULTS_FILE.exists():
        return None
    
    with open(RESULTS_FILE) as f:
        current = json.load(f)
    
    history = get_historical_data(days=7)
    patterns = analyze_patterns(current, history)
    
    # Try OpenAI if available
    prompt = generate_insights_prompt(current, patterns, history)
    ai_summary = call_openai_api(prompt)
    
    insights = {
        "generated_at": datetime.now().isoformat(),
        "patterns": {
            "latency_trend": patterns.get("latency_trend"),
            "consistently_broken": len(patterns.get("consistently_failing_urls", [])),
            "intermittent_issues": len(patterns.get("intermittent_failures", [])),
            "top_issues": patterns.get("consistently_failing_urls", [])[:3]
        },
        "ai_summary": ai_summary,
        "recommendations": generate_recommendations(patterns, current)
    }
    
    return insights

def generate_recommendations(patterns, current_results):
    """Generate actionable recommendations"""
    recommendations = []
    
    current_site = current_results.get('sites', [{}])[0]
    
    # Recommendation 1: Consistently broken URLs
    if patterns.get("consistently_failing_urls"):
        urls = patterns["consistently_failing_urls"][:3]
        recommendations.append({
            "priority": "high",
            "category": "broken_links",
            "title": f"Fix {len(urls)} consistently broken links",
            "details": f"These URLs have been failing for >70% of checks. Access them to verify they exist.",
            "urls": [u["url"] for u in urls]
        })
    
    # Recommendation 2: Latency issues
    if patterns.get("latency_trend") == "increasing" and current_site.get('p95_response_time_ms', 0) > 1000:
        recommendations.append({
            "priority": "medium",
            "category": "performance",
            "title": "Investigate latency increase",
            "details": f"P95 response time is {current_site.get('p95_response_time_ms', 0)}ms and rising. Check server load."
        })
    
    # Recommendation 3: High timeout rate
    if current_site.get('timeout_count', 0) > current_site.get('total_urls', 0) * 0.05:
        recommendations.append({
            "priority": "high",
            "category": "timeouts",
            "title": f"Reduce timeout threshold ({current_site.get('timeout_count', 0)} timeouts)",
            "details": "High timeout rate suggests network issues or slow endpoints. Consider increasing timeout or investigating endpoints."
        })
    
    # Recommendation 4: Monitor external domains
    if patterns.get("affected_domains"):
        domains = patterns["affected_domains"]
        if domains:
            domain_list = list(domains.values())[0]
            if domain_list:
                recommendations.append({
                    "priority": "medium",
                    "category": "external_services",
                    "title": f"Monitor external service health",
                    "details": f"External domains are experiencing issues. Set up separate monitoring for: {', '.join([d['domain'] for d in domain_list[:3]])}"
                })
    
    return recommendations

if __name__ == "__main__":
    insights = get_ai_insights()
    if insights:
        print(json.dumps(insights, indent=2))
