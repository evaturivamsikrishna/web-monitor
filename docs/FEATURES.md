# 🚀 Advanced Features Guide

**WebMonitor Pro** — Complete Feature Documentation

---

## 📋 Table of Contents

1. [Multi-Site Support](#multi-site-support)
2. [Health Scoring](#health-scoring)
3. [Alert Engine](#alert-engine)
4. [AI Insights](#ai-insights)
5. [Performance Analysis](#performance-analysis)
6. [Anomaly Detection](#anomaly-detection)
7. [Advanced Filtering](#advanced-filtering)

---

## 🌍 Multi-Site Support

### Overview
Monitor multiple websites from a single dashboard with independent configuration per site.

### Configuration

Edit `data/sites_config.json`:

```json
[
  {
    "id": "prod",
    "name": "Production Website",
    "url": "https://example.com",
    "enabled": true,
    "retry_count": 3,
    "timeout": 10,
    "exclude_patterns": ["/admin", "/internal"]
  },
  {
    "id": "staging",
    "name": "Staging Website",
    "url": "https://staging.example.com",
    "enabled": true,
    "retry_count": 2,
    "timeout": 8,
    "exclude_patterns": []
  }
]
```

### Per-Site Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `id` | Required | Unique identifier for site |
| `name` | Required | Display name in dashboard |
| `url` | Required | Base URL to monitor |
| `enabled` | true | Enable/disable from checks |
| `retry_count` | 3 | Retries on failure |
| `timeout` | 10 | Timeout per URL (seconds) |
| `exclude_patterns` | [] | URL patterns to skip |

### Dashboard Selection

Use the site selector in the left sidebar to toggle between monitored sites.

---

## 💪 Health Scoring

### Algorithm

Health Score = 0-100 calculated from:

```
Success Rate: 40%
- Score = success_rate * 0.4
- Example: 95% success = 38 points

Response Time: 30%
- <500ms: +30 points
- <1000ms: +20 points
- <2000ms: +10 points
- >2000ms: +0 points

Error Rate: 20%
- Score = (1 - error_rate) * 20
- Lower errors = higher score

Bonus: 10%
- +10 if zero errors AND zero timeouts

Maximum: 100 points
```

### Score Interpretation

| Score | Status | Action |
|-------|--------|--------|
| 90-100 | ✅ Excellent | No action needed |
| 70-89 | ⚠️ Good | Monitor trends |
| 50-69 | 🟡 Fair | Investigate issues |
| <50 | 🔴 Critical | Immediate action required |

### Color Coding

- **Green (#00ff88):** Score ≥ 90
- **Cyan (#00ffff):** Score 70-89
- **Orange (#ffaa00):** Score 50-69
- **Red (#ff0055):** Score < 50

---

## 🔔 Alert Engine

### Supported Channels

#### Slack

**Setup:**

1. Create Incoming Webhook at [api.slack.com/apps](https://api.slack.com/apps)
2. Add secret to GitHub: `SLACK_WEBHOOK`
3. Alerts automatically sent to configured channel

**Alert Format:**

```
🚨 WebMonitor Alert

🔴 New Failures (3)
  • https://example.com/missing
  • https://api.example.com/v1/users
  • https://cdn.example.com/file.js

✅ Recovered (1)
  • https://example.com/admin

⚡ Latency Spike - Production
P95: 234ms → 1823ms (+678%)
```

#### Discord

**Setup:**

1. Create Webhook in Discord server settings
2. Add secret to GitHub: `DISCORD_WEBHOOK`
3. Formatted as embeds

**Alert Format:**

```
🚨 WebMonitor Alert
────────────────────
🔴 New Failures (3)
• https://example.com/missing
• https://api.example.com/v1/users

✅ Recovered (1)
• https://example.com/admin

📉 Success Rate - Production
92% → 87%
```

#### Email

**Setup (future):**

```json
{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USERNAME": "your-email@gmail.com",
  "SMTP_PASSWORD": "your-app-password",
  "FROM_EMAIL": "monitoring@example.com"
}
```

### Alert Triggers

Alerts fire when:

1. **New Failures** — URLs that just started failing
2. **Recovered URLs** — URLs that recovered after being broken
3. **Latency Spike** — P95 response time >50% above baseline
4. **Success Rate Drop** — Drop >5% from previous check
5. **High Error Rate** — >10% of URLs broken
6. **High Timeout Rate** — >5% of URLs timing out

### Alert Frequency

- Alerts deduplicated (same issue won't alert twice)
- Intelligent grouping of related failures
- Maximum 1 alert per URL type per hour

---

## 🤖 AI Insights

### Requirements

1. Add `OPENAI_API_KEY` secret to GitHub
2. Requires OpenAI account with API access

### Enabled Detection

#### Pattern Detection

- **Consistently Broken URLs** → URLs failing >70% of checks
- **Intermittent Failures** → URLs failing 10-70% of checks
- **Latency Trend** → Increasing/decreasing/stable
- **Affected Domains** → External services causing issues

#### Recommendations

AI generates 3-5 actionable recommendations:

```
1. High Priority: Fix 3 consistently broken links
   - /contact (404)
   - /api/v1/users (503)
   - /assets/style.css (404)

2. Medium Priority: Investigate latency increase
   - P95 response time: 234ms → 1823ms
   - Suggests: Check server load, database queries

3. Medium Priority: Monitor external service health
   - cdn.cloudflare.com: 5 broken links
   - Suggest: Set up separate CDN monitoring
```

### AI Summary

Natural language analysis of top 3 issues:

```
"Production website experienced 3 new API failures 
coinciding with the 3pm deployment. Health check timeouts 
suggest your scaling group hit resource limits. Recommend: 
(1) Add 30s delay before marking deployment complete, 
(2) Monitor memory usage during peak traffic, 
(3) Consider auto-scaling rules"
```

### Dashboard Integration

AI Insights tab displays:
- Top recommendations (priority-ordered)
- AI-generated summary
- Detected patterns with counts
- Pattern severity indicators

---

## ⚡ Performance Analysis

### Metrics Tracked

**Per-URL:**
- Response time (ms)
- Status code
- Error type (if applicable)

**Aggregated:**
- Average response time
- P50 (median)
- P95 (95th percentile)
- P99 (99th percentile)

### Analysis Capabilities

#### Response Time Distribution

Histogram showing spread of latencies across all URLs checked.

```
Frequency
    │     ╔═══╗
    │   ╔═╗║ ║ ╔═╗
    │ ╔═╗║ ║║ ║ ║ ║
    └─┴─┴─┴─┴─┴─┴─┴─── Response Time (ms)
    0 100 200 300 400 500
```

#### Error Type Breakdown

Bar chart showing distribution of failure types:
- 404 Not Found: 45
- Connection Timeout: 12
- DNS Resolution Failed: 8
- Forbidden (403): 5

#### Performance Trends

Line chart tracking P95 latency over 7 days:

```
P95 Response Time (ms)
400├─ ╭─╮
   │ ╭─┘ ╰─╮
300├─    ╭─╰─╮
   │   ╭─
200└─╭─╯────────
    Mon Tue Wed Thu Fri Sat Sun
```

---

## 🚨 Anomaly Detection

### Automatic Detection

System continuously monitors for:

#### 1. High Latency Anomalies

- **Trigger:** P95 > 5000ms
- **Alert:** 🔴 if P95 > 10000ms
- **Message:** "ClickFuture{}"

```
⚠️ Detected: High Latency - Production
P95 Response Time: 8,234ms (CRITICAL)
```

#### 2. High Error Rate

- **Trigger:** >10% URLs broken
- **Alert:** 🔴 if >20% broken
- **Impact:** Major service degradation

```
⚠️ Detected: High Error Rate - Production
20.5% broken (critical)
```

#### 3. High Timeout Rate

- **Trigger:** >5% URLs timing out
- **Insight:** Network or endpoint issues

```
⚠️ Detected: High Timeout Rate - Production
8.3% timeouts (medium severity)
```

### Dashboard Display

**Anomalies Section** shows all detected issues:

```
⚠️ Detected Anomalies

🔴 High Latency - Production
    P95: 1,234ms

🟡 High Timeout Rate - Production
    8.3% timeouts
```

### Alert Integration

Anomalies automatically trigger Slack/Discord alerts.

---

## 🔍 Advanced Filtering

### Broken Links Tab

#### Filters

**Status Filter:**
- BROKEN (4xx/5xx errors)
- TIMEOUT (connection timeouts)
- ERROR (DNS, connection errors)

**Error Type Filter:**
- "Not Found (404)"
- "Connection Timeout"
- "DNS Resolution Failed"
- "Forbidden (403)"
- "Service Unavailable (503)"
- etc.

**URL Search:**
- Search by domain
- Partial text matching
- Case-insensitive

### Example Workflows

**Find all 404s:**
1. Filter Status → BROKEN
2. Filter Error Type → "Not Found (404)"
3. Shows all missing pages

**Find timeout issues:**
1. Filter Status → TIMEOUT
2. Sorted by frequency
3. Investigate slow endpoints

**Domain-specific checking:**
1. Search: "cdn.example.com"
2. Shows CDN-only failures
3. Download as CSV for debugging

---

## 📊 Data Storage

### File Structure

```
data/
├── results.json              # Latest check results (all sites)
├── broken_urls.json          # Current broken links
├── previous_results.json     # Last check (for alerts)
├── sites_config.json         # Site configuration
└── history/
    ├── 2026-03-18.json       # Daily snapshot
    ├── 2026-03-17.json
    └── ...
```

### Results Schema

```json
{
  "timestamp": "2026-03-18T15:30:00Z",
  "sites": [
    {
      "site_id": "prod",
      "site_name": "Production",
      "base_url": "https://example.com",
      "total_urls": 247,
      "broken_count": 3,
      "timeout_count": 1,
      "error_count": 0,
      "success_rate": 98.3,
      "avg_response_time_ms": 234.5,
      "p50_response_time_ms": 210,
      "p95_response_time_ms": 650,
      "p99_response_time_ms": 1200,
      "results": [
        {
          "url": "https://example.com/api/v1/users",
          "status": "OK",
          "code": 200,
          "response_time_ms": 234.2,
          "error_type": null
        }
      ]
    }
  ]
}
```

---

## 🔧 Configuration Examples

### Basic Multi-Site Setup

```json
[
  {
    "id": "main",
    "name": "Main Website",
    "url": "https://example.com",
    "enabled": true,
    "retry_count": 3,
    "timeout": 10,
    "exclude_patterns": []
  }
]
```

### Production + Staging

```json
[
  {
    "id": "prod",
    "name": "Production",
    "url": "https://example.com",
    "enabled": true,
    "retry_count": 3,
    "timeout": 10,
    "exclude_patterns": ["/admin", "/internal", "/debug"]
  },
  {
    "id": "staging",
    "name": "Staging",
    "url": "https://staging.example.com",
    "enabled": true,
    "retry_count": 2,
    "timeout": 8,
    "exclude_patterns": []
  }
]
```

### API + Website

```json
[
  {
    "id": "api",
    "name": "API Server",
    "url": "https://api.example.com",
    "enabled": true,
    "retry_count": 5,
    "timeout": 15,
    "exclude_patterns": ["/internal"]
  },
  {
    "id": "web",
    "name": "Website",
    "url": "https://example.com",
    "enabled": true,
    "retry_count": 3,
    "timeout": 10,
    "exclude_patterns": []
  }
]
```

---

## 🎯 Best Practices

### 1. Health Score Optimization

- Target: Health Score > 85
- Monitor trends weekly
- Investigate drops > 10 points

### 2. Alert Configuration

- Enable Slack for critical issues
- Filter to avoid alert fatigue
- Use Discord for detailed logs

### 3. Performance Tuning

- P95 should be <500ms for web
- P95 should be <100ms for APIs
- Investigate outliers in distribution

### 4. Multi-Site Strategy

- Prod/Staging/Dev site setup
- 1-min checks for prod, 6-hour for dev
- Different retry counts per env

---

**Version:** 1.0.0  
**Last Updated:** March 18, 2026
