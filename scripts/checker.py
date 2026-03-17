import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from pathlib import Path
from collections import defaultdict
import statistics

# Config - Multi-site support
SITES_CONFIG_FILE = Path("data") / "sites_config.json"
DATA_DIR = Path("data")
RESULTS_FILE = DATA_DIR / "results.json"
BROKEN_FILE = DATA_DIR / "broken_urls.json"
HISTORY_DIR = DATA_DIR / "history"

# Create directories
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Default sites config
DEFAULT_SITES = [
    {
        "id": "primary",
        "name": "Primary Site",
        "url": os.getenv("BASE_URL", "https://example.com"),
        "enabled": True,
        "retry_count": 3,
        "timeout": 10,
        "exclude_patterns": []
    }
]

def load_sites_config():
    """Load or create sites configuration"""
    if SITES_CONFIG_FILE.exists():
        try:
            with open(SITES_CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_SITES

def save_sites_config(sites):
    """Save sites configuration"""
    with open(SITES_CONFIG_FILE, 'w') as f:
        json.dump(sites, f, indent=2)

SITES = load_sites_config()


async def fetch_page(session, url, timeout=10):
    """Fetch webpage with proper headers and timing"""
    try:
        start = time.time()
        async with session.get(url, timeout=timeout, allow_redirects=True, ssl=False) as resp:
            elapsed = (time.time() - start) * 1000
            if resp.status == 200:
                return await resp.text(), elapsed
            else:
                return None, elapsed
    except asyncio.TimeoutError:
        return None, timeout * 1000
    except Exception as e:
        return None, 0


async def extract_links(session, page_html):
    """Extract all links from HTML"""
    soup = BeautifulSoup(page_html, 'html.parser')
    links = set()
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if href.startswith('http'):
            links.add(href)
    
    return list(links)


def classify_error(status_code, error_type):
    """Classify error type for better reporting"""
    if error_type == "TIMEOUT":
        return "Connection Timeout"
    elif error_type == "DNS_ERROR":
        return "DNS Resolution Failed"
    elif status_code is None:
        return "Connection Error"
    elif 400 <= status_code < 500:
        if status_code == 404:
            return "Not Found (404)"
        elif status_code == 403:
            return "Forbidden (403)"
        else:
            return f"Client Error ({status_code})"
    elif 500 <= status_code < 600:
        if status_code == 503:
            return "Service Unavailable (503)"
        elif status_code == 502:
            return "Bad Gateway (502)"
        else:
            return f"Server Error ({status_code})"
    else:
        return "Unknown Error"


async def check_url(session, url, retries=3, timeout=5):
    """Check if URL is valid with retry logic"""
    for attempt in range(retries):
        try:
            start = time.time()
            async with session.head(url, timeout=timeout, allow_redirects=True, ssl=False) as resp:
                response_time = (time.time() - start) * 1000
                status = resp.status
                
                if status < 400:
                    return {
                        "url": url,
                        "status": "OK",
                        "code": status,
                        "response_time_ms": round(response_time, 2),
                        "error_type": None
                    }
                else:
                    error_type = classify_error(status, None)
                    return {
                        "url": url,
                        "status": "BROKEN",
                        "code": status,
                        "response_time_ms": round(response_time, 2),
                        "error_type": error_type
                    }
        except asyncio.TimeoutError:
            response_time = timeout * 1000
            if attempt == retries - 1:
                return {
                    "url": url,
                    "status": "TIMEOUT",
                    "code": None,
                    "response_time_ms": round(response_time, 2),
                    "error_type": "Connection Timeout"
                }
        except Exception as e:
            if attempt == retries - 1:
                return {
                    "url": url,
                    "status": "ERROR",
                    "code": None,
                    "response_time_ms": 0,
                    "error_type": "DNS Resolution Failed" if "getaddrinfo" in str(e) else "Connection Error"
                }
    
    return {
        "url": url,
        "status": "ERROR",
        "code": None,
        "response_time_ms": 0,
        "error_type": "Unknown Error"
    }


async def check_site(site, session):
    """Check all URLs for a single site"""
    print(f"\n🔗 Checking: {site['name']} ({site['url']})")
    
    page_html, fetch_time = await fetch_page(session, site['url'], timeout=site['timeout'])
    
    if not page_html:
        print(f"❌ Failed to fetch {site['url']}")
        return None
    
    print("🔍 Extracting links...")
    all_links = await extract_links(session, page_html)
    
    # Filter excluded patterns
    filtered_links = all_links
    for pattern in site.get('exclude_patterns', []):
        filtered_links = [l for l in filtered_links if pattern not in l]
    
    print(f"Found {len(filtered_links)} links")
    
    print("✔️ Checking links...")
    results = []
    batch_size = 20
    
    for i in range(0, len(filtered_links), batch_size):
        batch = filtered_links[i:i+batch_size]
        batch_results = await asyncio.gather(*[
            check_url(session, url, retries=site['retry_count'], timeout=site['timeout'])
            for url in batch
        ])
        results.extend(batch_results)
        progress = min(i + batch_size, len(filtered_links))
        print(f"  Progress: {progress}/{len(filtered_links)}")
    
    # Calculate metrics
    broken = [r for r in results if r["status"] == "BROKEN"]
    timeouts = [r for r in results if r["status"] == "TIMEOUT"]
    errors = [r for r in results if r["status"] == "ERROR"]
    ok = [r for r in results if r["status"] == "OK"]
    
    success_rate = (len(ok) / len(results) * 100) if results else 0
    
    # Response time percentiles (from successful requests)
    response_times = [r["response_time_ms"] for r in ok if r["response_time_ms"] > 0]
    avg_response_time = statistics.mean(response_times) if response_times else 0
    
    if len(response_times) >= 3:
        p50 = statistics.median(response_times)
        p95 =_percentile(response_times, 0.95)
        p99 = _percentile(response_times, 0.99)
    else:
        p50 = p95 = p99 = avg_response_time
    
    output = {
        "site_id": site['id'],
        "site_name": site['name'],
        "base_url": site['url'],
        "last_check": datetime.now().isoformat(),
        "total_urls": len(results),
        "broken_count": len(broken),
        "timeout_count": len(timeouts),
        "error_count": len(errors),
        "success_rate": round(success_rate, 2),
        "avg_response_time_ms": round(avg_response_time, 2),
        "p50_response_time_ms": round(p50, 2),
        "p95_response_time_ms": round(p95, 2),
        "p99_response_time_ms": round(p99, 2),
        "results": results
    }
    
    return output


def _percentile(data, percentile):
    """Calculate percentile"""
    if not data:
        return 0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * percentile)
    return sorted_data[min(index, len(sorted_data) - 1)]


def save_results(all_results):
    """Save results for all sites"""
    combined_results = {
        "timestamp": datetime.now().isoformat(),
        "sites": all_results
    }
    
    # Save combined results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(combined_results, f, indent=2)
    
    # Save broken URLs (for quick reference)
    all_broken = []
    for site_result in all_results:
        if site_result:
            broken = [r for r in site_result['results'] if r['status'] == 'BROKEN']
            for b in broken:
                b['site_id'] = site_result['site_id']
                b['site_name'] = site_result['site_name']
            all_broken.extend(broken)
    
    with open(BROKEN_FILE, 'w') as f:
        json.dump(all_broken, f, indent=2)
    
    # Save to daily history
    today = datetime.now().strftime("%Y-%m-%d")
    history_file = HISTORY_DIR / f"{today}.json"
    with open(history_file, 'w') as f:
        json.dump(combined_results, f, indent=2)


async def main():
    """Main checker logic - multi-site support"""
    sites = load_sites_config()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    all_results = []
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for site in sites:
            if site.get('enabled', True):
                result = await check_site(site, session)
                if result:
                    all_results.append(result)
    
    # Save all results
    save_results(all_results)
    
    # Print summary
    print("\n" + "="*60)
    for result in all_results:
        print(f"\n📊 {result['site_name']}")
        print(f"  Total URLs: {result['total_urls']}")
        print(f"  Broken: {result['broken_count']}")
        print(f"  Timeouts: {result['timeout_count']}")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
        print(f"  Avg Response Time: {result['avg_response_time_ms']:.0f}ms")
        print(f"  P95 Response Time: {result['p95_response_time_ms']:.0f}ms")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
