# 🚀 Deployment Guide

**WebMonitor Pro** — Production Deployment & Operations

---

## 📋 Quick Start

### Prerequisites

```bash
# System requirements
- Python 3.11+
- Git
- Docker (optional, for containerization)
- PostgreSQL 14+ (Phase 2+)
```

### Clone & Setup (5 minutes)

```bash
# Clone repository
git clone https://github.com/yourname/web-monitor.git
cd web-monitor

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your BASE_URL and secrets
```

---

## 🏠 Phase 1: Local Development

### Running Locally

```bash
# Start Streamlit dashboard
streamlit run streamlit_app.py

# In another terminal, run manual check
python scripts/checker.py

# View results
cat data/results.json | jq .
```

### Environment Setup

**.env** (local development)
```
BASE_URL=https://example.com
SLACK_WEBHOOK=
DISCORD_WEBHOOK=
SMTP_SERVER=
SMTP_PASSWORD=
```

**.env.example** (commit to repo)
```
BASE_URL=
SLACK_WEBHOOK=
DISCORD_WEBHOOK=
SMTP_SERVER=
SMTP_PASSWORD=
```

**Never commit `.env` with real secrets!**

---

## 🌐 Phase 1: Streamlit Cloud Deployment

### Deploy Dashboard

1. **Create GitHub repo**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourname/web-monitor.git
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [streamlit.io/cloud](https://share.streamlit.io)
   - Click "New app" → "Deploy from GitHub"
   - Select repo: `yourname/web-monitor`
   - Main file path: `streamlit_app.py`
   - Python version: `3.11`

3. **Add GitHub Secrets** in Streamlit Cloud settings:
   - `BASE_URL` = https://example.com

### Deployed URL
```
https://[your-username]-web-monitor.streamlit.app
```

---

## 🤖 Phase 1: GitHub Actions Setup

### Configure Secrets

In GitHub repo: **Settings → Secrets and variables → Actions**

| Secret | Value | Example |
|--------|-------|---------|
| `BASE_URL` | Website to monitor | `https://example.com` |
| `SLACK_WEBHOOK` | (Optional) | `https://hooks.slack.com/...` |
| `DISCORD_WEBHOOK` | (Optional) | `https://discord.com/...` |

### Workflow Status

The workflow `.github/workflows/check_links.yml` runs:
- **Every 6 hours** (automatic)
- **Manually** via GitHub UI (workflow_dispatch)

**View runs:** Go to **Actions** tab → **check_links** workflow → Latest run

### Manual Trigger

```bash
# Via GitHub CLI
gh workflow run check_links.yml

# Via GitHub UI
1. Go to Actions
2. Select "check_links"
3. Click "Run workflow" → "Run workflow"
```

---

## ☁️ Phase 2: Self-Hosted Deployment (AWS EC2)

### Infrastructure Setup

#### 1. Launch EC2 Instance

```bash
# AWS CLI quick launch
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name my-key \
  --security-groups ssh-http-https
```

**Instance Specs:**
- Type: `t2.medium` (2 vCPU, 4GB RAM)
- Storage: 30GB SSD
- OS: Ubuntu 22.04
- Region: Closest to target sites

#### 2. Configure Security Groups

```
Inbound:
- SSH (22): Your IP only
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0

Outbound:
- All traffic
```

#### 3. Install Dependencies

```bash
# SSH into instance
ssh -i my-key.pem ubuntu@ec2-xxx.amazonaws.com

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python + PostgreSQL
sudo apt install python3.11 python3.11-venv \
  postgresql postgresql-contrib \
  nginx supervisor git -y

# Clone repo
git clone https://github.com/yourname/web-monitor.git
cd web-monitor

# Setup Python env
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

#### 4. Setup PostgreSQL

```bash
# Log in to PostgreSQL
sudo sudo -u postgres psql

# Create database
CREATE DATABASE webmonitor;
CREATE USER monitor_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE webmonitor TO monitor_user;
\q
```

#### 5. Deploy Application

**Create systemd service** (`/etc/systemd/system/webmonitor.service`):

```ini
[Unit]
Description=WebMonitor Gunicorn Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/web-monitor
ExecStart=/home/ubuntu/web-monitor/venv/bin/gunicorn \
  --workers 4 \
  --bind 127.0.0.1:8000 \
  --timeout 60 \
  streamlit_app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable & start:**

```bash
sudo systemctl enable webmonitor
sudo systemctl start webmonitor
sudo systemctl status webmonitor
```

#### 6. Setup Nginx Reverse Proxy

**File:** `/etc/nginx/sites-available/webmonitor`

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL (use Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

**Enable & test:**

```bash
sudo ln -s /etc/nginx/sites-available/webmonitor \
  /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl restart nginx
```

#### 7. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y

sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

#### 8. Setup Monitoring Scheduler (Celery)

**Install Redis:**

```bash
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**Create celery app** (`celery_worker.py`):

```python
from celery import Celery
from celery.schedules import crontab
import os
from scripts.checker import check_site

app = Celery('webmonitor')
app.conf.broker_url = 'redis://localhost:6379'
app.conf.result_backend = 'redis://localhost:6379'

app.conf.beat_schedule = {
    'check-every-6-hours': {
        'task': 'check_website',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}

@app.task(name='check_website')
def check_website():
    base_url = os.getenv('BASE_URL')
    check_site(base_url)
    return "Check completed"
```

**Start Celery worker:**

```bash
celery -A celery_worker worker --loglevel=info
```

**Start Celery beat** (in another terminal):

```bash
celery -A celery_worker beat --loglevel=info
```

---

## 🐳 Phase 2: Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/_stcore/health')"

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8000", \
     "--server.address=0.0.0.0"]
```

### Docker Compose

```yaml
version: '3.9'

services:
  # Dashboard
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      BASE_URL: ${BASE_URL}
      SLACK_WEBHOOK: ${SLACK_WEBHOOK}
    volumes:
      - ./data:/app/data
    depends_on:
      - db

  # Database
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: webmonitor
      POSTGRES_USER: monitor_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis (for Celery queue)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Celery Worker
  celery_worker:
    build: .
    command: celery -A celery_worker worker --loglevel=info
    environment:
      BASE_URL: ${BASE_URL}
      CELERY_BROKER_URL: redis://redis:6379
    depends_on:
      - redis

volumes:
  pgdata:
```

**Deploy:**

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app
```

---

## 📊 Phase 3: Kubernetes Deployment

### Helm Chart Structure

```
web-monitor-helm/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    └── secret.yaml
```

### Deploy to GKE

```bash
# Create GKE cluster
gcloud container clusters create webmonitor \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --region us-central1

# Install Helm chart
helm repo add web-monitor https://helm.example.com
helm install webmonitor web-monitor/web-monitor \
  -f values-prod.yaml \
  --namespace production

# Verify
kubectl get pods -n production
```

---

## 🔍 Monitoring & Observability

### Logging

**Send logs to:**
- [DataDog](https://dashboard.datadoghq.com) (recommended)
- [Papertrail](https://papertrailapp.com)
- [Loki](https://grafana.com/oss/loki/)

```python
# In checker.py
import logging
from datadog import initialize, api

logger = logging.getLogger(__name__)

# Log to stdout (Datadog collects from container)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
```

### Metrics

**Track:**
- Crawl duration (ms)
- URLs checked per run
- Success rate (%)
- Alert latency (ms)

```python
from prometheus_client import Counter, Histogram

crawl_duration = Histogram('crawl_duration_seconds', 'Time spent crawling')
urls_checked = Counter('urls_checked_total', 'Total URLs checked')
```

### Uptime Monitoring

- [Better Stack](https://betterstack.com) — Ping endpoint every minute
- [Pingdom](https://www.pingdom.com) — DNS + HTTP checks
- [New Relic](https://newrelic.com) — Full APM

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Heroku
        run: |
          git remote add heroku https://git.heroku.com/web-monitor.git
          git push heroku main
```

---

## 🛑 Troubleshooting

### App won't start

```bash
# Check logs
docker compose logs app

# Verify environment
python -c "import streamlit; print(streamlit.__version__)"

# Test database connection
psql -h localhost -U monitor_user -d webmonitor -c "SELECT 1"
```

### Workflow fails

1. **Check GitHub Actions logs**
   - Go to repo → Actions → Latest run
   
2. **Verify secrets**
   ```bash
   # These should NOT be empty
   echo $BASE_URL
   echo $SLACK_WEBHOOK
   ```

3. **Test locally**
   ```bash
   # Run checker manually
   python scripts/checker.py
   ```

### Slow dashboard

```bash
# Clear cache
rm -rf ~/.streamlit/

# Check data file size
ls -lh data/results.json

# Profile execution
python -m cProfile -s cumtime streamlit_app.py
```

---

## 📋 Pre-Launch Checklist

- [ ] Environment variables set (BASE_URL, secrets)
- [ ] Database created and migrations applied
- [ ] SSL certificate installed
- [ ] Monitoring configured (logs, metrics)
- [ ] Backup strategy in place (daily DB exports)
- [ ] Alert channels tested (Slack/Discord)
- [ ] Load testing completed (1000 URLs)
- [ ] Disaster recovery plan documented
- [ ] Documentation updated
- [ ] Team trained on operations

---

## 🚀 Launch Steps

```bash
# 1. Final pre-flight checks
pytest tests/
python scripts/checker.py  # Manual run

# 2. Deploy to staging
git tag v1.0.0
git push --tags

# 3. Monitor staging for 24 hours
# Check: uptime, alert latency, error rate

# 4. Promote to production
docker tag web-monitor:staging web-monitor:latest
docker push web-monitor:latest

# 5. Post-launch monitoring (first week)
# - Daily check of dashboard
# - Verify all alerts firing correctly
# - Monitor server logs for errors
```

---

## 📞 Support & Escalation

| Issue | Escalation Path |
|-------|-----------------|
| Dashboard down | Check EC2/Streamlit status → View logs → Restart service |
| Checker not running | Check GitHub Actions → Verify secrets → Manual trigger |
| High latency | Check database connections → Review server load → Scale workers |
| Data loss | Use daily backups → Restore to point-in-time → Replay checks |

---

**Last Updated:** March 18, 2026  
**Deployment Channels:** Streamlit Cloud, EC2, Docker, Kubernetes
