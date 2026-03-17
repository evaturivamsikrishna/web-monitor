# ⚡ Quick Start: Advanced Features

Get up and running with WebMonitor Pro's powerful features in minutes.

---

## 🚀 1-Minute Setup Checklist

### Minimum Setup (Just Works)
```bash
# Set BASE_URL in GitHub Secrets
BASE_URL=https://example.com

# Push code
git push

# Run workflow
gh workflow run check_links.yml
```

### Enhanced Setup (30 minutes)
```bash
# Step 1: Add Slack Alerts
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Step 2: Add Discord Alerts (optional)
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR/WEBHOOK

# Step 3: Add AI Insights (optional)
OPENAI_API_KEY=sk-...

# Step 4: Configure multi-site
# Edit data/sites_config.json (see FEATURES.md)

# Step 5: Run workflow
gh workflow run check_links.yml
```

---

## 🎯 Feature Activation Guide

### ✅ Alerts (Slack/Discord)

**Required:** GitHub Secrets setup

**Steps:**
1. Set `SLACK_WEBHOOK` or `DISCORD_WEBHOOK` secret
2. Workflow automatically sends alerts
3. Alerts fire when:
   - New failures detected
   - Links recovered
   - Latency spikes detected
   - Success rate drops

**Test Alert:**
```bash
python scripts/alerts.py
```

### ✅ AI Insights

**Required:** OpenAI API key + Internet

**Steps:**
1. Sign up at OpenAI (gets free $5 credit)
2. Create API key
3. Set `OPENAI_API_KEY` secret
4. AI tab appears in dashboard

**Features:**
- Recommends which links to fix
- Detects failure patterns
- Analyzes latency trends
- Written like an SRE report

**Test Insight:**
```bash
python scripts/ai_insights.py
```

### ✅ Health Scoring

**Built-in** - No setup required

**What it does:**
- Calculates 0-100 health score
- Shows color-coded status
- Factors: success rate, latency, errors

**Dashboard:**
- Prominent display at top
- Updates with every check
- Trending indicator

### ✅ Multi-Site Monitoring

**Setup:**
```bash
# Create data/sites_config.json
[
  {
    "id": "prod",
    "name": "Production",
    "url": "https://example.com",
    "enabled": true,
    "retry_count": 3,
    "timeout": 10
  },
  {
    "id": "staging",
    "name": "Staging",
    "url": "https://staging.example.com",
    "enabled": true
  }
]
```

**Dashboard:**
- Site selector in sidebar
- Independent health scores per site
- Compare across sites

### ✅ Advanced Filtering

**Built-in** - No setup required

**Broken Links Tab:**
- Filter by status (Broken, Timeout, Error)
- Filter by error type (404, Timeout, DNS, etc.)
- Search by URL

**Performance Tab:**
- View percentiles (P50, P95, P99)
- Response time histogram
- Error type breakdown

---

## 📊 Dashboard Overview

### 6-Tab Interface

**1. Overview** 📊
- Status pie chart
- Success rate gauge
- High-level metrics

**2. Broken Links** 🔗
- Filterable list of broken URLs
- Error type classification
- CSV export

**3. Trends** 📈
- 7-day success rate
- URLs checked vs broken
- Historical comparison

**4. Performance** ⚡
- P50/P95/P99 latencies
- Response time distribution
- Error type breakdown

**5. AI Insights** 🤖
- AI-generated recommendations
- Pattern detection
- Actionable suggestions

**6. Details** ℹ️
- Full configuration
- Timing info
- Site IDs

---

## 🔔 Alert Examples

### Slack Alert
```
🚨 WebMonitor Alert

🔴 New Failures (2)
  • https://api.example.com/v1/users
  • https://cdn.example.com/main.js

⚡ Latency Spike - Production
P95: 234ms → 1,823ms (+678%)
```

### Discord Alert
```
🚨 WebMonitor Alert
────────────────────
🔴 New Failures (2)
• https://api.example.com/v1/users

✅ Recovered (1)
• https://example.com/admin

📉 Success Rate Down
92% → 87%
```

---

## 💡 AI Insights Example

```
Recommendation: Fix 3 consistently broken links
- /api/v1/users (503)
- /contact (404)
- /assets/style.js (404)

Recommendation: Investigate latency increase
- P95 response time: 234ms → 1,823ms
- Suggests: Check server load, auto-scaling rules

Recommendation: Monitor external services
- cdn.cloudflare.com: 5 broken links
- Suggest: Set up separate healthcheck
```

---

## 🛠️ Configuration Files

### sites_config.json
```json
[
  {
    "id": "prod",
    "name": "Production",
    "url": "https://example.com",
    "enabled": true,
    "retry_count": 3,
    "timeout": 10,
    "exclude_patterns": ["/admin", "/internal"]
  }
]
```

### .env (Local Development)
```bash
BASE_URL=https://example.com
SLACK_WEBHOOK=
DISCORD_WEBHOOK=
OPENAI_API_KEY=
```

### GitHub Secrets (Production)
```
BASE_URL                 # Required
SLACK_WEBHOOK            # Optional
DISCORD_WEBHOOK          # Optional
OPENAI_API_KEY           # Optional
```

---

## 📈 Performance Expectations

| Metric | Expected | Target |
|--------|----------|--------|
| Dashboard load | <2 sec | <3 sec |
| Check time (250 URLs) | 30-60 sec | <120 sec |
| Latency (avg) | 100-500ms | <1000ms |
| Latency (P95) | 200-1000ms | <2000ms |
| Alert latency | <5 sec | <10 sec |

---

## 🐛 Troubleshooting

### No results showing?
```bash
# Check BASE_URL is set
echo $BASE_URL

# Test manually
python scripts/checker.py

# Check results file
cat data/results.json
```

### Alerts not working?
```bash
# Check secrets are set
gh secret list

# Test alert manually
python scripts/alerts.py

# Check for errors
python scripts/alerts.py 2>&1 | head -20
```

### AI insights missing?
```bash
# Add OPENAI_API_KEY secret
# Test manually
python scripts/ai_insights.py
```

### Dashboard not updating?
```bash
# Clear cache
streamlit cache clear

# Restart app
streamlit run streamlit_app.py
```

---

## 📚 Full Documentation

For more details, see:
- [FEATURES.md](FEATURES.md) — Complete feature docs
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md) — Product roadmap
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — Technical architecture
- [DEPLOYMENT.md](DEPLOYMENT.md) — Deployment guide

---

## 🎓 Common Workflows

### Workflow 1: Find and Fix Broken Links

1. Go to "Broken Links" tab
2. Filter by Status = BROKEN
3. Sort by error type
4. Download CSV
5. Fix each URL
6. Re-run check

### Workflow 2: Monitor Performance

1. Go to "Performance" tab
2. Check P95 latency
3. Review distribution chart
4. Click "Details" for full debug

### Workflow 3: Multi-Site Comparison

1. Go to sidebar
2. Switch between sites
3. Compare health scores
4. Identify underperforming site
5. Debug that specific site

### Workflow 4: Setup Alerts for Team

1. Create Slack/Discord webhook
2. Add to GitHub Secrets
3. Verify in first check
4. Share channel with team
5. Adjust alert sensitivity as needed

---

**Status:** All features production-ready ✅  
**Version:** 1.0.0
