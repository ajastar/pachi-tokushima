import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import datetime

def fetch_minrepo_data(days_back=30):
    # Correct URL for Tokushima Prefecture category
    base_url = "https://min-repo.com/category/%E5%BE%B3%E5%B3%B6%E7%9C%8C/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    all_data = []
    page = 1
    cutoff_date = datetime.date.today() - datetime.timedelta(days=days_back)
    current_year = datetime.date.today().year
    
    while True:
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}page/{page}/"
            
        print(f"Fetching Min-Repo Page {page}...")
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                print("End of pages reached.")
                break
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching Min-Repo page {page}: {e}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        entries = soup.select("div.ichiran_post")
        
        if not entries:
            print("No entries found on this page. Stopping.")
            break
            
        page_has_new_data = False
        
        for entry in entries:
            try:
                title_div = entry.find("div", class_="ichiran_title")
                if not title_div: continue
                title_link = title_div.find("a")
                if not title_link: continue
                
                full_title = title_link.get_text(strip=True)
                link_url = title_link["href"]
                
                match = re.match(r"(\d+)/(\d+)\([^\)]+\)\s*(.+)", full_title)
                if match:
                    month = int(match.group(1))
                    day = int(match.group(2))
                    store_name = match.group(3)
                    
                    # Estimate year (Handle Dec->Jan transition)
                    # If current is Jan and data is Dec, it's last year.
                    # Simple heuristic: If data date > current date + 30 days, it's likely last year (unlikely future).
                    # Actually, simple is best: If month > current_month + 6, it's last year.
                    # Or just rely on "days_back".
                    
                    # Assume report year is current year, fallback to last year if needed
                    entry_date = datetime.date(current_year, month, day)
                    if entry_date > datetime.date.today() + datetime.timedelta(days=2): # Future? likely last year err? No, maybe just scraping older.
                        # If we are in Jan 2026, and see Dec 25, it parses as Dec 25 2026 (Future).
                        # So it must be 2025.
                        entry_date = datetime.date(current_year - 1, month, day)
                    
                    if entry_date < cutoff_date:
                        continue # Skip old, but don't break yet, page might have mixed? Usually sorted.
                    
                    page_has_new_data = True
                    
                    date_str = f"{month}/{day}" # Keep original format for string
                    
                else:
                    date_str = "Unknown"
                    store_name = full_title
                    entry_date = datetime.date.today() # Fallback

                result_div = entry.find("div", class_="ichiran_result")
                result_text = result_div.get_text(strip=True) if result_div else ""
                
                total_diff = 0
                avg_diff = 0
                rotation_count = 0 # Default
                
                total_match = re.search(r"総差枚\s*[:：]?\s*([+-]?[\d,]+)", result_text)
                avg_match = re.search(r"平均差枚\s*[:：]?\s*([+-]?[\d,]+)", result_text)
                
                if total_match:
                    total_diff = int(total_match.group(1).replace(",", ""))
                if avg_match:
                    avg_diff = int(avg_match.group(1).replace(",", ""))

                result2_div = entry.find("div", class_="ichiran_result2")
                hot_models = result2_div.get_text(separator=" ", strip=True) if result2_div else ""

                all_data.append({
                    "store_name": store_name,
                    "date": date_str,
                    "datetime": entry_date, # Internal use
                    "total_diff": total_diff,
                    "avg_diff": avg_diff,
                    "rotation_count": rotation_count, # Placeholder
                    "hot_models": hot_models,
                    "url": link_url,
                    "source": "minrepo"
                })
                
            except Exception as e:
                # print(f"Error parsing entry: {e}")
                continue
        
        if not page_has_new_data and entries:
            # If a whole page was completely skipped due to being too old, we can stop.
            # Check if the FIRST entry of the page is too old.
            # (Loop logic above might continue if mixed, but usually minrepo is desc sorted)
            
            # Let's check the last processed date on this page
            # If the loop finished and we didn't add anything, and we saw entries, likely all old.
            print("Reached date cutoff. Stopping.")
            break
            
        page += 1
        if page > 10: # Safety break
            break

    return all_data

if __name__ == "__main__":
    results = fetch_minrepo_data()
    print(f"Found {len(results)} reports")
    for r in results:
        print(f"[{r['date']}] {r['store_name']}: Total {r['total_diff']}, Avg {r['avg_diff']}")
