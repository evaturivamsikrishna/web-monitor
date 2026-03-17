"""
HTML Report Generator - Create professional monitoring reports
"""

import json
from pathlib import Path
from datetime import datetime
import statistics

RESULTS_FILE = Path("data") / "results.json"

def get_status_icon_and_color(health_score):
    """Get icon and color based on health score"""
    if health_score >= 90:
        return "✅", "#10b981"  # Green
    elif health_score >= 70:
        return "⚠️", "#f59e0b"   # Amber
    elif health_score >= 50:
        return "⚠️", "#f97316"   # Orange
    else:
        return "❌", "#dc2626"   # Red

def calculate_health_score(site_data):
    """Calculate health score (0-100)"""
    if not site_data:
        return 0
    
    success_rate = site_data.get("success_rate", 0)
    response_time = site_data.get("avg_response_time_ms", 0)
    error_count = site_data.get("error_count", 0)
    timeout_count = site_data.get("timeout_count", 0)
    
    score = success_rate * 0.4
    
    if response_time < 500:
        score += 30
    elif response_time < 1000:
        score += 20
    elif response_time < 2000:
        score += 10
    
    total = site_data.get("total_urls", 1)
    error_rate = (error_count + timeout_count) / total if total > 0 else 0
    score += (1 - error_rate) * 20
    
    if error_count == 0 and timeout_count == 0:
        score += 10
    
    return min(100, max(0, score))

def generate_html_report(results_data=None):
    """Generate professional HTML report"""
    
    if not results_data:
        if RESULTS_FILE.exists():
            with open(RESULTS_FILE) as f:
                results_data = json.load(f)
        else:
            return None
    
    # Process each site
    html_sections = []
    
    for site in results_data.get("sites", []):
        site_id = site.get("site_id", "unknown")
        site_name = site.get("site_name", "Unknown")
        base_url = site.get("base_url", "N/A")
        
        total_urls = site.get("total_urls", 0)
        broken_count = site.get("broken_count", 0)
        timeout_count = site.get("timeout_count", 0)
        error_count = site.get("error_count", 0)
        success_rate = site.get("success_rate", 0)
        avg_response = site.get("avg_response_time_ms", 0)
        p95_response = site.get("p95_response_time_ms", 0)
        
        health_score = calculate_health_score(site)
        icon, color = get_status_icon_and_color(health_score)
        
        # Status text
        if broken_count > 0:
            status_text = f"{broken_count} broken links need attention"
        elif timeout_count > 0:
            status_text = f"{timeout_count} timeouts detected"
        elif success_rate < 80:
            status_text = "Success rate below target"
        else:
            status_text = "All healthy - no issues"
        
        # Error breakdown
        error_types = {}
        for result in site.get("results", []):
            if result.get("status") != "OK":
                error_type = result.get("error_type", "Unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        error_breakdown = "\n".join([
            f"                    <li>{error_type}: {count} occurrences</li>"
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
        ])
        
        # Top broken URLs
        broken_urls = [r for r in site.get("results", []) if r.get("status") != "OK"]
        broken_urls_html = "\n".join([
            f'                    <li><code>{b["url"]}</code> - {b.get("status", "ERROR")}</li>'
            for b in sorted(broken_urls, key=lambda x: x.get("error_type", ""))[:5]
        ])
        
        site_html = f"""
        <div class="site-report">
            <div class="header">
                <h1>{site_name}</h1>
                <p class="subtitle">Monitoring Report</p>
            </div>

            <div class="status-bar" style="border-bottom-color: {color}">
                <div class="status-content">
                    <div class="status-icon">{icon}</div>
                    <div class="status-text">
                        <h2>{status_text}</h2>
                        <p>Health Score: <strong>{health_score:.0f}/100</strong> • {base_url}</p>
                    </div>
                </div>
            </div>

            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-icon">🔗</div>
                    <div class="metric-label">Total URLs</div>
                    <div class="metric-value">{total_urls:,}</div>
                </div>

                <div class="metric-card {'error' if broken_count > 0 else 'success'}">
                    <div class="metric-icon">{'❌' if broken_count > 0 else '✅'}</div>
                    <div class="metric-label">Broken/Timeout</div>
                    <div class="metric-value">{broken_count + timeout_count}</div>
                </div>

                <div class="metric-card success">
                    <div class="metric-icon">📊</div>
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value">{success_rate:.1f}%</div>
                </div>

                <div class="metric-card">
                    <div class="metric-icon">⚡</div>
                    <div class="metric-label">Avg Response</div>
                    <div class="metric-value">{avg_response:.0f}ms</div>
                </div>
            </div>

            <div class="performance-grid">
                <div class="perf-card">
                    <div class="perf-label">P95 Latency</div>
                    <div class="perf-value">{p95_response:.0f}ms</div>
                </div>
                <div class="perf-card">
                    <div class="perf-label">Errors</div>
                    <div class="perf-value">{error_count}</div>
                </div>
                <div class="perf-card">
                    <div class="perf-label">Timeouts</div>
                    <div class="perf-value">{timeout_count}</div>
                </div>
                <div class="perf-card">
                    <div class="perf-label">Health</div>
                    <div class="perf-value">{health_score:.0f}/100</div>
                </div>
            </div>

            {f'''
            <div class="issues-section">
                <div class="issues-box">
                    <div class="issues-title">⚠️ Error Breakdown</div>
                    <ul class="issues-list">
                        {error_breakdown}
                    </ul>
                </div>
            </div>
            ''' if error_types else ''}

            {f'''
            <div class="issues-section">
                <div class="issues-box" style="border-left-color: #ef553b;">
                    <div class="issues-title">🔗 Top Issues (First 5)</div>
                    <ul class="issues-list">
                        {broken_urls_html}
                    </ul>
                </div>
            </div>
            ''' if broken_urls else '<div style="padding: 20px 40px; text-align: center; color: #10b981; font-weight: 600;">✅ All URLs healthy!</div>'}

            <div class="run-details">
                <table class="details-table">
                    <tr>
                        <td>Site URL</td>
                        <td>{base_url}</td>
                    </tr>
                    <tr>
                        <td>URLs Checked</td>
                        <td>{total_urls:,}</td>
                    </tr>
                    <tr>
                        <td>Broken Links</td>
                        <td>{broken_count}</td>
                    </tr>
                    <tr>
                        <td>Report Generated</td>
                        <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                    </tr>
                </table>
            </div>
        </div>
"""
        html_sections.append(site_html)
    
    # Combine all sites into final HTML
    combined_html = f"""
    <div class="page-break">
        {''.join(html_sections)}
    </div>
"""
    
    return combined_html

def create_full_html_report(results_data=None):
    """Create complete HTML page with header and footer"""
    
    if not results_data:
        if RESULTS_FILE.exists():
            with open(RESULTS_FILE) as f:
                results_data = json.load(f)
        else:
            return None
    
    content = generate_html_report(results_data)
    
    # Calculate summary stats
    total_all = sum(s.get("total_urls", 0) for s in results_data.get("sites", []))
    broken_all = sum(s.get("broken_count", 0) for s in results_data.get("sites", []))
    timeout_all = sum(s.get("timeout_count", 0) for s in results_data.get("sites", []))
    sites_count = len(results_data.get("sites", []))
    
    avg_success = sum(s.get("success_rate", 0) for s in results_data.get("sites", [])) / sites_count if sites_count > 0 else 0
    
    # Overall status
    if broken_all > 0 or timeout_all > 0:
        overall_icon, overall_color = "❌", "#dc2626"
        overall_status = f"{broken_all + timeout_all} issues detected"
    elif avg_success < 80:
        overall_icon, overall_color = "⚠️", "#f59e0b"
        overall_status = "Success rate below target"
    else:
        overall_icon, overall_color = "✅", "#10b981"
        overall_status = "All systems healthy"
    
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebMonitor Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f3f4f6;
            padding: 12px;
        }}

        .page-break {{
            page-break-after: always;
        }}

        .site-report {{
            background: white;
            border-radius: 10px;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 16px 24px;
            color: white;
        }}

        .header h1 {{
            font-size: 20px;
            margin-bottom: 2px;
            font-weight: 700;
        }}

        .header .subtitle {{
            font-size: 12px;
            opacity: 0.9;
        }}

        .status-bar {{
            padding: 14px 24px;
            background: #f9fafb;
            border-bottom: 3px solid;
        }}

        .status-content {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .status-icon {{
            font-size: 32px;
        }}

        .status-text h2 {{
            font-size: 16px;
            color: #111827;
            margin-bottom: 2px;
        }}

        .status-text p {{
            color: #6b7280;
            font-size: 12px;
        }}

        .metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            padding: 16px 24px;
        }}

        .metric-card {{
            text-align: center;
            padding: 12px 8px;
            border-radius: 8px;
            border: 1.5px solid #e5e7eb;
        }}

        .metric-card.error {{
            background: #fef2f2;
            border-color: #fecaca;
        }}

        .metric-card.success {{
            background: #f0fdf4;
            border-color: #bbf7d0;
        }}

        .metric-icon {{
            font-size: 20px;
            margin-bottom: 4px;
        }}

        .metric-label {{
            font-size: 10px;
            text-transform: uppercase;
            color: #6b7280;
            font-weight: 600;
            margin-bottom: 4px;
            letter-spacing: 0.5px;
        }}

        .metric-value {{
            font-size: 22px;
            font-weight: 700;
            color: #111827;
        }}

        .metric-card.error .metric-value {{
            color: #dc2626;
        }}

        .metric-card.success .metric-value {{
            color: #16a34a;
        }}

        .performance-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            padding: 0 24px 12px 24px;
        }}

        .perf-card {{
            background: #f0f9ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }}

        .perf-label {{
            font-size: 10px;
            color: #0c4a6e;
            font-weight: 600;
            margin-bottom: 3px;
        }}

        .perf-value {{
            font-size: 18px;
            font-weight: 700;
            color: #075985;
        }}

        .issues-section {{
            padding: 0 24px 12px 24px;
        }}

        .issues-box {{
            background: #fef2f2;
            border-left: 3px solid #dc2626;
            border-radius: 6px;
            padding: 12px;
        }}

        .issues-title {{
            font-size: 13px;
            font-weight: 600;
            color: #991b1b;
            margin-bottom: 8px;
        }}

        .issues-list {{
            list-style: none;
        }}

        .issues-list li {{
            color: #7f1d1d;
            font-size: 12px;
            padding: 3px 0;
            padding-left: 18px;
            position: relative;
        }}

        .issues-list li:before {{
            content: "•";
            position: absolute;
            left: 0;
            color: #dc2626;
            font-weight: bold;
        }}

        .issues-list code {{
            background: #fff5f5;
            padding: 1px 4px;
            border-radius: 3px;
            font-family: 'Monaco', monospace;
            font-size: 11px;
            color: #7f1d1d;
        }}

        .run-details {{
            padding: 0 24px 12px 24px;
        }}

        .details-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}

        .details-table tr {{
            border-bottom: 1px solid #e5e7eb;
        }}

        .details-table td {{
            padding: 8px 0;
        }}

        .details-table td:first-child {{
            color: #6b7280;
            font-weight: 600;
        }}

        .details-table td:last-child {{
            text-align: right;
            color: #111827;
        }}

        .footer {{
            text-align: center;
            padding: 16px;
            color: #6b7280;
            font-size: 11px;
            margin-top: 20px;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .site-report {{
                margin-bottom: 20px;
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
        <div style="text-align: center; margin-bottom: 12px;">
            <h1 style="font-size: 24px; color: #111827; margin-bottom: 4px;">🔗 WebMonitor Report</h1>
            <p style="color: #6b7280; font-size: 12px;">{timestamp}</p>
        </div>

        <div style="background: #f9fafb; border-left: 3px solid {overall_color}; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 28px;">{overall_icon}</div>
                <div>
                    <div style="font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 2px;">{overall_status}</div>
                    <div style="color: #6b7280; font-size: 12px;">{sites_count} site(s) monitored • {total_all:,} URLs checked</div>
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">
            <div style="background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 18px; margin-bottom: 4px;">📊</div>
                <div style="font-size: 10px; color: #0c4a6e; font-weight: 600; margin-bottom: 4px;">TOTAL URLS</div>
                <div style="font-size: 20px; font-weight: 700; color: #075985;">{total_all:,}</div>
            </div>
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 18px; margin-bottom: 4px;">❌</div>
                <div style="font-size: 10px; color: #7f1d1d; font-weight: 600; margin-bottom: 4px;">BROKEN</div>
                <div style="font-size: 20px; font-weight: 700; color: #dc2626;">{broken_all}</div>
            </div>
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 18px; margin-bottom: 4px;">✅</div>
                <div style="font-size: 10px; color: #166534; font-weight: 600; margin-bottom: 4px;">SUCCESS RATE</div>
                <div style="font-size: 20px; font-weight: 700; color: #16a34a;">{avg_success:.1f}%</div>
            </div>
            <div style="background: #fef3c7; border: 1px solid #fde047; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 18px; margin-bottom: 4px;">🌐</div>
                <div style="font-size: 10px; color: #713f12; font-weight: 600; margin-bottom: 4px;">SITES</div>
                <div style="font-size: 20px; font-weight: 700; color: #9a3412;">{sites_count}</div>
            </div>
        </div>
    </div>

    {content}

    <div class="footer">
        <p>🤖 Generated by WebMonitor Pro</p>
        <p>Automated Link Monitoring & Analysis</p>
    </div>
</body>
</html>
"""
    
    return full_html

def save_html_report(output_file=None):
    """Save HTML report to file"""
    if not output_file:
        output_file = Path("reports") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    html_content = create_full_html_report()
    
    if html_content:
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Report generated: {output_file}")
        return str(output_file)
    else:
        print("❌ No results data available")
        return None

if __name__ == "__main__":
    report_path = save_html_report()
    if report_path:
        print(f"📊 Open in browser: file://{Path(report_path).absolute()}")
