import asyncio
import aiohttp
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path

# Config
BASE_URL = os.getenv("BASE_URL", "https://example.com")
DATA_DIR = Path("data")
RESULTS_FILE = DATA_DIR / "results.json"
BROKEN_FILE = DATA_DIR / "broken_urls.json"
HISTORY_DIR = DATA_DIR / "history"

# Create directories
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

async def fetch_page(session, url):
    """Fetch webpage"""
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                return await resp.text()
    except:
        pass
    return None

async def extract_links(session, page_html):
    """Extract all links from HTML"""
    soup = BeautifulSoup(page_html, 'html.parser')
    links = set()
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if href.startswith('http'):
            links.add(href)
    
    return list(links)

async def check_url(session, url):
    """Check if URL is valid"""
    try:
        async with session.head(url, timeout=5, allow_redirects=True) as resp:
            status = resp.status
            if status < 400:
                return {"url": url, "status": "OK", "code": status}
            else:
                return {"url": url, "status": "BROKEN", "code": status}
    except asyncio.TimeoutError:
        return {"url": url, "status": "TIMEOUT", "code": None}
    except Exception as e:
        return {"url": url, "status": "ERROR", "code": None}

async def main():
    """Main checker logic"""
    print(f"🔗 Checking links for: {BASE_URL}")
    
    async with aiohttp.ClientSession() as session:
        print("📥 Fetching homepage...")
        page_html = await fetch_page(session, BASE_URL)
        
        if not page_html:
            print("❌ Failed to fetch homepage")
            return
        
        print("🔍 Extracting links...")
        all_links = await extract_links(session, page_html)
        print(f"Found {len(all_links)} links")
        
        print("✔️ Checking links...")
        results = []
        batch_size = 20
        
        for i in range(0, len(all_links), batch_size):
            batch = all_links[i:i+batch_size]
            batch_results = await asyncio.gather(*[
                check_url(session, url) for url in batch
            ])
            results.extend(batch_results)
            print(f"  Progress: {min(i+batch_size, len(all_links))}/{len(all_links)}")
    
    # Analyze results
    broken = [r for r in results if r["status"] == "BROKEN"]
    ok = [r for r in results if r["status"] == "OK"]
    success_rate = (len(ok) / len(results) * 100) if results else 0
    
    # Save results
    output = {
        "last_check": datetime.now().isoformat(),
        "total_urls": len(results),
        "broken_count": len(broken),
        "timeout_count": len([r for r in results if r["status"] == "TIMEOUT"]),
        "success_rate": round(success_rate, 2),
        "results": results,
        "base_url": BASE_URL
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    with open(BROKEN_FILE, 'w') as f:
        json.dump(broken, f, indent=2)
    
    # Save to history
    today = datetime.now().strftime("%Y-%m-%d")
    history_file = HISTORY_DIR / f"{today}.json"
    with open(history_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print("\n" + "="*50)
    print(f"✅ Total URLs: {len(results)}")
    print(f"🔴 Broken: {len(broken)}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
