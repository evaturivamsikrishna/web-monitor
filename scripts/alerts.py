"""
Alert Engine - Send notifications to Slack, Discord, Email
"""

import json
import os
import smtplib
from datetime import datetime
from pathlib import Path
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

RESULTS_FILE = Path("data") / "results.json"
ALERTS_LOG = Path("data") / "alerts_log.json"

def load_previous_results():
    """Load previous check results to compare"""
    prev_file = Path("data") / "previous_results.json"
    if prev_file.exists():
        with open(prev_file) as f:
            return json.load(f)
    return None

def save_current_results(results):
    """Save results as previous for next comparison"""
    with open(Path("data") / "previous_results.json", 'w') as f:
        json.dump(results, f, indent=2)

def get_new_failures(current, previous):
    """Identify URLs that newly broke"""
    if not previous:
        return []
    
    current_broken = {
        f"{site['site_id']}:{r['url']}"
        for site in current.get('sites', [])
        for r in site.get('results', [])
        if r['status'] == 'BROKEN'
    }
    
    previous_broken = {
        f"{site['site_id']}:{r['url']}"
        for site in previous.get('sites', [])
        for r in site.get('results', [])
        if r['status'] == 'BROKEN'
    }
    
    return list(current_broken - previous_broken)

def get_recovered_urls(current, previous):
    """Identify URLs that recovered"""
    if not previous:
        return []
    
    current_broken = {
        f"{site['site_id']}:{r['url']}"
        for site in current.get('sites', [])
        for r in site.get('results', [])
        if r['status'] == 'BROKEN'
    }
    
    previous_broken = {
        f"{site['site_id']}:{r['url']}"
        for site in previous.get('sites', [])
        for r in site.get('results', [])
        if r['status'] == 'BROKEN'
    }
    
    return list(previous_broken - current_broken)

def detect_anomalies(current, previous):
    """Detect performance anomalies"""
    anomalies = []
    
    if not previous:
        return anomalies
    
    for site in current.get('sites', []):
        prev_site = next((s for s in previous.get('sites', []) if s['site_id'] == site['site_id']), None)
        if not prev_site:
            continue
        
        # Latency spike detection
        current_p95 = site.get('p95_response_time_ms', 0)
        prev_p95 = prev_site.get('p95_response_time_ms', 0)
        
        if prev_p95 > 0 and current_p95 > prev_p95 * 1.5:
            anomalies.append({
                'type': 'latency_spike',
                'site': site['site_name'],
                'prev_p95': round(prev_p95, 2),
                'current_p95': round(current_p95, 2),
                'increase_percent': round((current_p95 - prev_p95) / prev_p95 * 100, 1)
            })
        
        # Success rate drop
        current_success = site.get('success_rate', 100)
        prev_success = prev_site.get('success_rate', 100)
        
        if prev_success > 95 and current_success < prev_success - 5:
            anomalies.append({
                'type': 'success_rate_drop',
                'site': site['site_name'],
                'prev_success': round(prev_success, 2),
                'current_success': round(current_success, 2)
            })
    
    return anomalies

def send_slack_alert(webhook_url, message_blocks):
    """Send alert to Slack"""
    try:
        payload = {
            "blocks": message_blocks
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Slack alert failed: {e}")
        return False

def send_discord_alert(webhook_url, embeds):
    """Send alert to Discord"""
    try:
        payload = {
            "embeds": embeds
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Discord alert failed: {e}")
        return False

def send_email_alert(smtp_config, to_email, subject, html_content):
    """Send alert via email"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_config['from_email']
        msg['To'] = to_email
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            if smtp_config.get('use_tls'):
                server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"❌ Email alert failed: {e}")
        return False

def format_slack_alert(current, previous):
    """Format alert for Slack"""
    new_failures = get_new_failures(current, previous)
    recovered = get_recovered_urls(current, previous)
    anomalies = detect_anomalies(current, previous)
    
    if not new_failures and not recovered and not anomalies:
        return None
    
    blocks = []
    
    # Header
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🚨 WebMonitor Alert"
        }
    })
    
    # New failures
    if new_failures:
        failure_text = "\n".join([f"  • {url}" for url in new_failures[:10]])
        if len(new_failures) > 10:
            failure_text += f"\n  ... and {len(new_failures) - 10} more"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔴 New Failures ({len(new_failures)})*\n{failure_text}"
            }
        })
    
    # Recovered
    if recovered:
        recovered_text = "\n".join([f"  • {url}" for url in recovered[:10]])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*✅ Recovered ({len(recovered)})*\n{recovered_text}"
            }
        })
    
    # Anomalies
    for anomaly in anomalies:
        if anomaly['type'] == 'latency_spike':
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚡ Latency Spike* - {anomaly['site']}\nP95: {anomaly['prev_p95']}ms → {anomaly['current_p95']}ms (+{anomaly['increase_percent']}%)"
                }
            })
        elif anomaly['type'] == 'success_rate_drop':
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📉 Success Rate Down* - {anomaly['site']}\n{anomaly['prev_success']}% → {anomaly['current_success']}%"
                }
            })
    
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }]
    })
    
    return blocks

def format_discord_alert(current, previous):
    """Format alert for Discord"""
    new_failures = get_new_failures(current, previous)
    recovered = get_recovered_urls(current, previous)
    anomalies = detect_anomalies(current, previous)
    
    if not new_failures and not recovered and not anomalies:
        return None
    
    embeds = []
    
    # Main embed
    embed = {
        "title": "🚨 WebMonitor Alert",
        "color": 15105570,  # Red
        "timestamp": datetime.now().isoformat(),
        "fields": []
    }
    
    if new_failures:
        failure_list = "\n".join([f"• {url[:60]}" for url in new_failures[:8]])
        embed['fields'].append({
            "name": f"🔴 New Failures ({len(new_failures)})",
            "value": failure_list,
            "inline": False
        })
    
    if recovered:
        recovered_list = "\n".join([f"• {url[:60]}" for url in recovered[:8]])
        embed['fields'].append({
            "name": f"✅ Recovered ({len(recovered)})",
            "value": recovered_list,
            "inline": False
        })
    
    for anomaly in anomalies[:3]:
        if anomaly['type'] == 'latency_spike':
            embed['fields'].append({
                "name": f"⚡ Latency Spike - {anomaly['site']}",
                "value": f"P95: {anomaly['prev_p95']}ms → {anomaly['current_p95']}ms (+{anomaly['increase_percent']}%)",
                "inline": False
            })
        elif anomaly['type'] == 'success_rate_drop':
            embed['fields'].append({
                "name": f"📉 Success Rate - {anomaly['site']}",
                "value": f"{anomaly['prev_success']}% → {anomaly['current_success']}%",
                "inline": False
            })
    
    embeds.append(embed)
    return embeds

def process_alerts():
    """Load results and send alerts"""
    if not RESULTS_FILE.exists():
        print("⚠️  No results file found")
        return
    
    with open(RESULTS_FILE) as f:
        current = json.load(f)
    
    previous = load_previous_results()
    
    # Slack
    slack_webhook = os.getenv("SLACK_WEBHOOK")
    if slack_webhook:
        blocks = format_slack_alert(current, previous)
        if blocks:
            if send_slack_alert(slack_webhook, blocks):
                print("✅ Slack alert sent")
            else:
                print("❌ Slack alert failed")
    
    # Discord
    discord_webhook = os.getenv("DISCORD_WEBHOOK")
    if discord_webhook:
        embeds = format_discord_alert(current, previous)
        if embeds:
            if send_discord_alert(discord_webhook, embeds):
                print("✅ Discord alert sent")
            else:
                print("❌ Discord alert failed")
    
    # Save current results for next comparison
    save_current_results(current)

if __name__ == "__main__":
    process_alerts()
