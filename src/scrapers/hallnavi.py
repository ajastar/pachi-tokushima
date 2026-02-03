
import requests
from bs4 import BeautifulSoup
import datetime
import re

def fetch_hallnavi_events():
    url = "https://hall-navi.com/area/tokushima"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching Hall Navi: {e}")
        # Hall Navi is notoriously strict. If 403, we might return empty or mock data for now.
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    data = []
    
    # Hall Navi structure varies, but often works by looking for lists of events.
    # Look for table rows or lists with store names and event names.
    # We will try a generic approach first.
    
    # Tables often have class "event_table" or similar
    tables = soup.find_all("table")
    
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            text = row.get_text(strip=True)
            if "イベント" in text or "取材" in text:
                # Naive extractions
                cols = row.find_all("td")
                if len(cols) >= 2:
                    hall_link = row.find("a")
                    store_name = hall_link.get_text(strip=True) if hall_link else "Unknown"
                    event_name = cols[-1].get_text(strip=True)
                    
                    data.append({
                        "store_name": store_name,
                        "event_text": event_name,
                        "url": hall_link['href'] if hall_link else "",
                        "source": "hall_navi"
                    })

    return data

if __name__ == "__main__":
    results = fetch_hallnavi_events()
    print(f"Found {len(results)} events")
    for r in results:
        print(r)
