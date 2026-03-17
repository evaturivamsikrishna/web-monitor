# 🏗️ System Design & Architecture

**WebMonitor Pro** — Technical Architecture Specification

---

## 🧩 System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│                  ┌─────────────────┐                    │
│                  │  Streamlit UI   │                    │
│                  │  Dashboard      │                    │
│                  └────────┬────────┘                    │
└─────────────────────────┬─────────────────────────────┘
                          │
┌─────────────────────────┴─────────────────────────────┐
│                  Application Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Monitoring  │  │    Alert     │  │   AI       │  │
│  │  Engine      │  │    Engine    │  │   Insights │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬───────┘  │
└─────────┼──────────────────┼────────────────┼─────────┘
          │                  │                │
┌─────────┴──────────────────┼────────────────┴─────────┐
│          Data Persistence Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Database │  │  Cache   │  │  Object Storage  │   │
│  │ (SQL)    │  │ (Redis)  │  │  (CSV/JSON)      │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────┘
          │
┌─────────┴──────────────────────────────────────────────┐
│           External Integrations Layer                   │
│  ┌──────┐  ┌──────┐  ┌────────┐  ┌──────────────┐   │
│  │Email │  │Slack │  │Discord │  │OpenAI/LLM    │   │
│  └──────┘  └──────┘  └────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 🔧 Component Architecture

### 1️⃣ Monitoring Engine

**Responsibility:** Crawl websites and validate links/APIs

**Technology Stack:**
- Language: Python 3.11
- HTTP Client: `aiohttp` (async)
- HTML Parser: `BeautifulSoup4`
- Scheduler: GitHub Actions (Phase 1) → Celery (Phase 2)

**Core Modules:**

```python
monitoring/
├── crawler.py          # Web crawling logic
├── checker.py          # Link validation
├── performance.py      # Latency tracking
└── classifier.py       # Failure classification
```

**Data Flow:**

```
1. Load site config
   ↓
2. Fetch base URL + parse HTML
   ↓
3. Extract all links (internal + external)
   ↓
4. Classify links (crawlable vs external)
   ↓
5. Check each link concurrently (batch size: 20)
   ↓
6. Classify failures (DNS, timeout, 4xx, 5xx, etc.)
   ↓
7. Store results
```

**Key Features:**
- Async/await for concurrent checks
- Configurable timeouts
- User-Agent rotation
- Retry logic (3 retries with exponential backoff)
- Response time tracking (ms precision)

**Concurrency Model:**
- Batch size: 20 URLs
- Max workers: 10
- Timeout per URL: 5 seconds
- Connection pool: 20

---

### 2️⃣ Scheduler / Orchestration

**Current Implementation (Phase 1)**
```yaml
# .github/workflows/check_links.yml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:       # Manual trigger

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - Checkout repo
      - Setup Python
      - Install dependencies
      - Run checker.py
      - Commit + push results
```

**Advantages (Phase 1):**
- ✅ Free
- ✅ Reliable
- ✅ No infrastructure
- ✅ Version controlled

**Limitations:**
- ❌ Fixed schedule only (can't trigger on demand at scale)
- ❌ ~6 minute cold start
- ❌ Max 1000 URLs per run

**Phase 2: Celery + Redis**
```python
# Asynchronous task queue
from celery import Celery

app = Celery('webmonitor')

@app.task(bind=True)
def check_site(self, site_id):
    """Queue-based monitoring job"""
    site = get_site(site_id)
    results = run_checks(site)
    store_results(site_id, results)
    trigger_alerts(site_id, results)
```

**Benefits:**
- Parallel site checking
- Real-time triggering
- Retry mechanisms
- Scaling to 10,000+ URLs

---

### 3️⃣ Alert Engine

**Trigger Logic:**

```python
def should_alert(site_id, current_results, previous_results):
    """Determine if alert should be sent"""
    
    # Get threshold config
    config = get_alert_config(site_id)
    
    # New failures (weren't failing before)
    new_failures = get_new_failures(current_results, previous_results)
    if new_failures:
        return True
    
    # Duration threshold
    failure_duration = get_consecutive_failure_duration(site_id)
    if failure_duration >= config.min_duration:
        return True
    
    # Latency spikes
    avg_latency = calculate_avg_latency(current_results)
    baseline = calculate_baseline(site_id)
    if avg_latency > baseline * config.latency_multiplier:
        return True
    
    return False
```

**Alert Channels:**

| Channel | Config | Latency |
|---------|--------|---------|
| Email | SMTP credentials | 1-3 sec |
| Slack | Webhook URL | <500ms |
| Discord | Webhook URL | <500ms |
| PagerDuty | API key (Phase 3) | <1 sec |

**Alert Template:**

```
Subject: 🚨 WebMonitor Alert: {site_name}

{site_name} experienced {failure_count} failures

🔴 Failures:
- {url_1}: {status_code} ({count} occurrences)
- {url_2}: {error_type} (timeout)

⏱️ Duration: {duration} minutes
📊 Success Rate: {success_rate}%

🔍 Details: {dashboard_link}
```

---

### 4️⃣ Database Layer

**Phase 1: CSV/JSON (Current)**

```
data/
├── results.json              # Latest check results
├── broken_urls.json          # Current broken links
└── history/
    ├── 2026-03-18.json       # Daily snapshot
    └── 2026-03-17.json
```

**Schema: results.json**
```json
{
  "last_check": "2026-03-18T15:30:00",
  "base_url": "https://example.com",
  "total_urls": 247,
  "broken_count": 3,
  "timeout_count": 1,
  "success_rate": 98.3,
  "results": [
    {
      "url": "https://example.com/about",
      "status": "OK",
      "code": 200,
      "response_time_ms": 234
    }
  ]
}
```

**Phase 2: PostgreSQL Schema**

```sql
-- Organizations (multi-tenant)
CREATE TABLE orgs (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  created_at TIMESTAMP
);

-- Sites to monitor
CREATE TABLE sites (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES orgs,
  name VARCHAR(255),
  base_url VARCHAR(2048),
  check_frequency_minutes INT DEFAULT 360,
  created_at TIMESTAMP
);

-- Checks (job runs)
CREATE TABLE checks (
  id UUID PRIMARY KEY,
  site_id UUID REFERENCES sites,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status VARCHAR(20),  -- 'success', 'partial', 'failed'
  total_urls INT,
  url_results JSONB
);

-- Results (individual URLs)
CREATE TABLE check_results (
  id UUID PRIMARY KEY,
  check_id UUID REFERENCES checks,
  url VARCHAR(2048),
  status_code INT,
  response_time_ms INT,
  error_type VARCHAR(50),  -- 'DNS_ERROR', 'TIMEOUT', 'HTTP_4xx', etc.
  created_at TIMESTAMP,
  INDEX (check_id, created_at),
  INDEX (url, created_at)
);

-- Alert configurations
CREATE TABLE alert_configs (
  id UUID PRIMARY KEY,
  site_id UUID REFERENCES sites,
  alert_channel VARCHAR(20),  -- 'email', 'slack', 'discord'
  webhook_url VARCHAR(2048),
  min_failure_duration_minutes INT DEFAULT 5,
  created_at TIMESTAMP
);

-- Alert history
CREATE TABLE alerts_sent (
  id UUID PRIMARY KEY,
  check_id UUID REFERENCES checks,
  channel VARCHAR(20),
  triggered_reason VARCHAR(255),
  message TEXT,
  status VARCHAR(20),  -- 'sent', 'failed'
  sent_at TIMESTAMP
);
```

**Indices:** For query optimization
- `checks(site_id, created_at DESC)` — Latest checks per site
- `check_results(check_id)` — All URLs in a check
- `check_results(url, created_at DESC)` — History of single URL
- `alert_configs(site_id)` — Config per site

---

### 5️⃣ Dashboard (Streamlit)

**Architecture:**

```python
streamlit_app.py
├── Page Config + Styling CSS
├── Data Loading (with caching)
├── Layout Components
│   ├── Header
│   ├── KPI Metrics
│   ├── Status Cards
│   └── Tabs
│       ├── Overview (pie charts, gauges)
│       ├── Broken Links (dataframe)
│       ├── Trends (line/bar charts)
│       └── Details (info boxes)
└── Export & Interactions
```

**Data Flow:**

```
Cache miss
    ↓
load_results() from results.json
    ↓
Parse + transform
    ↓
@st.cache_data(ttl=300)
    ↓
Return to UI
    ↓
Render charts (Plotly)
```

**Performance:**
- Cache TTL: 5 minutes
- Page load: < 2 seconds
- Chart render: < 500ms

---

### 6️⃣ AI Insights Module (Phase 2)

**Architecture:**

```python
ai_insights/
├── summarizer.py      # LLM prompting
├── detector.py        # Anomaly detection
└── recommender.py     # Fix suggestions
```

**Data Input:**

```python
context = {
    "last_24h_results": results,
    "baseline_latency": calculate_baseline("2026-03-10"),
    "failure_patterns": detect_patterns(),
    "recent_deployments": get_deployments(),
}
```

**LLM Prompt:**

```
You are a site reliability expert. Analyze this monitoring data:

Site: example.com
Period: Last 24 hours
Results: {context}

Provide concise analysis answering:
1. What failed?
2. Why might it have failed?
3. What should they do about it?

Be specific. Suggest fixes based on patterns.
```

**Output:**

```json
{
  "summary": "3 API endpoints returned 503 for 8 minutes",
  "root_cause": "Coincides with deployment. Health check timeouts suggest scaling issue.",
  "recommendations": [
    "Add 30s delay before marking deployment as complete",
    "Monitor memory usage during peak traffic",
    "Consider adding auto-scaling rules"
  ],
  "confidence": 0.87
}
```

---

## 📊 Data Models

### Check Result Record

```python
@dataclass
class CheckResult:
    url: str
    status: Literal["OK", "BROKEN", "TIMEOUT", "ERROR"]
    status_code: Optional[int]
    response_time_ms: float
    error_type: Optional[str]  # "DNS_ERROR", "CONNECTION_TIMEOUT", etc.
    timestamp: datetime
```

### Site Configuration

```python
@dataclass
class SiteConfig:
    id: str
    name: str
    base_url: str
    check_frequency_minutes: int = 360
    timeout_seconds: int = 10
    max_depth: int = 3
    exclude_patterns: List[str] = []
    auth: Optional[AuthConfig] = None
    alerts: List[AlertConfig] = []
```

### Alert Configuration

```python
@dataclass
class AlertConfig:
    channel: Literal["email", "slack", "discord", "pagerduty"]
    webhook_url: str
    min_failure_duration_minutes: int = 5
    failure_threshold: int = 1  # Alert after X failures
    latency_multiplier: float = 2.0  # Alert if latency > baseline * 2
```

---

## 🔄 Request/Response Flow

### Monitoring Check Flow

```
1. Request: Scheduled job triggers
   Input: { site_id: "prod" }

2. Fetch configuration
   Output: SiteConfig(...)

3. Fetch homepage
   GET https://example.com
   Response: 200 OK (HTML)

4. Parse + Extract links
   Input: HTML
   Output: List[str] (50 URLs)

5. Concurrent checking (batch size 20)
   Parallel requests to all 50 URLs
   Output: List[CheckResult]

6. Store results
   Input: List[CheckResult]
   Output: Write to results.json

7. Trigger alerts
   Input: results, previous_results
   Output: Send to Slack/Email

8. Update dashboard cache
   Input: results.json
   Output: Streamlit refreshes (TTL: 5 min)
```

---

## 🔐 Security Architecture

### Secrets Management

**Phase 1: Environment Variables**
```bash
# .env (local) / GitHub Secrets (CI)
BASE_URL=https://example.com
SLACK_WEBHOOK=https://hooks.slack.com/...
SMTP_PASSWORD=***
```

**Phase 2: Encrypted Vault**
```python
# Use: AWS Secrets Manager or Hashicorp Vault
secret = vault.get_secret("slack_webhook")
```

### API Rate Limiting

```python
async def check_url(session, url):
    """Rate limiting to avoid being blocked"""
    await asyncio.sleep(random.uniform(0.5, 1.5))  # Random delay
    
    headers = {
        "User-Agent": "Mozilla/5.0 (WebMonitor/1.0)"
    }
    
    async with session.get(url, headers=headers, timeout=10):
        ...
```

### Data Privacy

- ✅ No PII collection
- ✅ Logs deleted after 30 days
- ✅ GDPR-compliant (Phase 3)
- ✅ Client-side data processing (Streamlit)

---

## 📈 Scalability Plan

### Phase 1 (Now) → Phase 2 (Q2)

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| URLs per check | 500 | 5,000 | 50,000 |
| Check parallelism | 10 workers | 50 workers | 500 workers |
| Frequency | 6 hourly | 5 minute | 1 minute |
| Storage | CSV | PostgreSQL | TimescaleDB |
| Peak RPS | 2 | 20 | 200 |

### Bottlenecks & Solutions

| Bottleneck | Phase 2 Solution |
|-----------|-----------------|
| Crawler speed | Increase worker pool to 50 |
| Database write | Batch inserts (1000 at a time) |
| Memory usage | Stream results instead of buffering |
| Network I/O | Connection pool per domain |

### Horizontal Scaling (Phase 3)

```
Load Balancer
├── Crawler Worker 1
├── Crawler Worker 2
└── Crawler Worker N

Redis Queue
├── Job 1: Check prod.com
├── Job 2: Check api.com
└── Job N: Check cdn.com

PostgreSQL (read replicas)
├── Primary (writes)
├── Replica 1 (analytics reads)
└── Replica 2 (dashboard reads)
```

---

## 🧪 Testing Strategy

| Test Type | Coverage | Tool |
|-----------|----------|------|
| Unit | Crawler, Parser | pytest |
| Integration | E2E check flow | pytest + fixtures |
| Load | 1000 concurrent URLs | Apache JMeter |
| Monitoring | Uptime, alert latency | New Relic |

---

## 📝 API Contracts (Phase 2)

### POST /api/sites/{site_id}/check

**Request:**
```json
{
  "force": true
}
```

**Response:**
```json
{
  "check_id": "uuid",
  "status": "running",
  "total_urls": 247
}
```

### GET /api/sites/{site_id}/results

**Query Params:**
- `limit=100`
- `offset=0`
- `filter=broken`

**Response:**
```json
{
  "results": [...],
  "total": 247,
  "broken_count": 3
}
```

---

## 🚀 Deployment Strategy

**Phase 1 (Current):**
- GitHub Actions (workflow)
- Streamlit Cloud (dashboard)
- GitHub Commits (data storage)

**Phase 2:**
- AWS EC2 + RDS
- OR Heroku + PostgreSQL
- OR Railway + PostgreSQL

**Phase 3:**
- Kubernetes (GKE/EKS)
- Managed PostgreSQL
- CloudFlare Workers (edge crawling)

---

**Last Updated:** March 18, 2026  
**Owner:** Engineering Team
