
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import datetime

def fetch_pworld_events():
    url = "https://www.p-world.co.jp/tokushima/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching P-World: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser", from_encoding=response.encoding)
    data = []
    
    # 1. New Machine Replacements (X-Dai Irekae)
    # IDs: today (Today), tom (Tomorrow)
    target_ids = {"today": "新台入替(今日)", "tom": "新台入替(明日)"}
    
    for div_id, label in target_ids.items():
        div = soup.find("div", id=div_id)
        if not div:
            continue
            
        rows = div.find_all("tr")
        current_hall = None
        current_url = None
        
        for row in rows:
            # Check for hall name link
            hall_link = row.find("a", href=True)
            if hall_link and "/tokushima/" in hall_link['href']:
                current_hall = hall_link.get_text(strip=True)
                current_url = "https://www.p-world.co.jp" + hall_link['href']
                
                data.append({
                    "store_name": current_hall,
                    "event_text": label,
                    "url": current_url,
                    "source": "p-world"
                })

    # 2. Hall Ads (Pickups / Events)
    ads = soup.find_all("div", class_="hallAds")
    for ad in ads:
        try:
            name_tag = ad.find("p", class_="hallAds-hallName")
            if not name_tag:
                continue
            
            # Name often contains " - CityName", strip it.
            raw_name = name_tag.get_text(strip=True)
            store_name = raw_name.split("-")[0].strip()
            
            title_tag = ad.find("p", class_="hallAds-title")
            text_tag = ad.find("p", class_="hallAds-text")
            
            event_text = ""
            if title_tag:
                event_text += title_tag.get_text(strip=True) + " "
            if text_tag:
                event_text += text_tag.get_text(strip=True)
                
            link_tag = ad.find("a", class_="hallAds-detail")
            url = ""
            if link_tag:
                url = "https://www.p-world.co.jp" + link_tag['href']
                
            data.append({
                "store_name": store_name,
                "event_text": event_text.strip(),
                "url": url,
                "source": "p-world_ad"
            })
            
        except Exception:
            continue

    return data

if __name__ == "__main__":
    results = fetch_pworld_events()
    print(f"Found {len(results)} events")
    for r in results:
        print(f"[{r['store_name']}] {r['event_text'][:50]}...")
