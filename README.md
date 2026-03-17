# 🔗 Web Monitor

Automated link checker with Streamlit dashboard. Free, simple, effective.

## Features

- ✅ Automatic link checking every 6 hours
- ✅ Real-time Streamlit dashboard
- ✅ 7-day trend tracking
- ✅ Broken links CSV export
- ✅ Zero cost (GitHub Actions + Streamlit Cloud)

## Setup

### 1. Clone & Configure

```bash
git clone https://github.com/[username]/web-monitor.git
cd web-monitor
pip install -r requirements.txt
```

### 2. Add Secrets

Create `.env` file:
```bash
cp .env.example .env
```

Or add GitHub Secrets:
- `BASE_URL` - Website to monitor
- `STREAMLIT_URL` - Dashboard URL

### 3. Deploy Dashboard

```bash
streamlit run streamlit_app.py
```

Or deploy to Streamlit Cloud:
1. Go to https://streamlit.io/cloud
2. Connect your repo
3. Select main file: `streamlit_app.py`
4. Deploy

### 4. Trigger First Check

```bash
python scripts/checker.py
```

Or via GitHub Actions (automatic every 6 hours)

## Dashboard

View at: `https://share.streamlit.io/[username]/web-monitor`

## Cost

**$0/month** - Uses free GitHub Actions + Streamlit Cloud

## Files

- `.github/workflows/` - GitHub Actions automation
- `scripts/checker.py` - Link checking logic
- `streamlit_app.py` - Dashboard
- `data/` - Results storage

## License

MIT
