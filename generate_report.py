
import sys
import os
import datetime
import urllib.parse
import re
import json
from collections import Counter
from jinja2 import Environment, FileSystemLoader

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from scrapers.minrepo import fetch_minrepo_data
from scrapers.pworld import fetch_pworld_events

MANUAL_DATA_FILE = "manual_data.json"

def load_manual_data():
    if os.path.exists(MANUAL_DATA_FILE):
        with open(MANUAL_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manual_data(data):
    with open(MANUAL_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def analyze_trends(minrepo_data):
    all_text = ""
    for item in minrepo_data:
        if item.get('hot_models'):
            all_text += " " + item['hot_models']
            
    targets = [
        "北斗", "カバネリ", "ジャグラー", "マイジャグ", "ファンキー", "アイム", "ハナハナ", 
        "沖ドキ", "ヴァルヴレイヴ", "からくり", "モンキー", "戦国乙女", "慶次", "海物語",
        "ユニコーン", "エヴァ", "Re:ゼロ", "番長", "吉宗", "バジリスク", "絆", "天膳"
    ]
    
    counts = Counter()
    normalized_text = all_text.replace("スマスロ", " ").replace("L", " ").replace("パチスロ", " ")
    
    for target in targets:
        count = normalized_text.count(target)
        if count > 0:
            counts[target] = count
            
    return counts.most_common(5)

def get_anaslo_url(store_name):
    """
    Returns the Anaslo direct link if the store is a known supported store.
    """
    # Base URL for Tokushima
    base_url = "https://ana-slo.com/%E3%83%9B%E3%83%BC%E3%83%AB%E3%83%87%E3%83%BC%E3%82%BF/%E5%BE%B3%E5%B3%B6%E7%9C%8C/"
    
    # Mapping of partial name match -> Exact URL suffix
    # The suffix must be URL encoded as per the browser check
    mapping = {
        "ミリオン中吉野": "%E3%83%9F%E3%83%AA%E3%82%AA%E3%83%B3%E4%B8%AD%E5%90%89%E9%87%8E%E5%BA%97-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/",
        "スロット123田宮": "%E3%82%B9%E3%83%AD%E3%83%83%E3%83%88123%E7%94%B0%E5%AE%AE%E5%BA%97-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/",
        "123松茂": "123%E6%9D%BE%E8%8C%82%E5%BA%97-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/",
        "123南昭和": "123%E5%8D%97%E6%98%AD%E5%92%8C%E5%BA%97-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/",
        "123論田": "123%E8%AB%96%E7%94%B0%E5%BA%97-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/"
    }
    
    for key, suffix in mapping.items():
        if key in store_name:
            return base_url + suffix
            
    return None

def enrich_data(data_list, manual_data=None):
    for item in data_list:
        query = f"{item['store_name']} 徳島"
        encoded_query = urllib.parse.quote(query)
        item['x_search_url'] = f"https://twitter.com/search?q={encoded_query}&src=typed_query&f=live"
        item['anaslo_url'] = get_anaslo_url(item['store_name'])
        
        # Apply Manual Data (Rotation Count)
        if manual_data:
            # Key: "StoreName_YYYY/MM/DD" (Simple key)
            key = f"{item['store_name']}_{item.get('date', '')}"
            if key in manual_data:
                item['rotation_count'] = manual_data[key].get('rotation_count', 0)
        
        tags = []
        text = str(item.get('event_text', '')) + " " + str(item.get('hot_models', ''))
        
        if "新台" in text:
            tags.append({"text": "新台", "class": "bg-warning text-dark"})
        if "リニューアル" in text:
            tags.append({"text": "RENEWAL", "class": "bg-danger text-white"})
        if "周年" in text:
            tags.append({"text": "周年", "class": "bg-danger text-white border border-light"})
        if "OPEN" in text or "時" in text:
            tags.append({"text": "時差OPEN", "class": "bg-info text-dark"})
        if "ジャグラー" in text or "ペカ" in text:
            tags.append({"text": "🤡Juggler", "class": "bg-dark text-white"})
        if "北斗" in text:
            tags.append({"text": "👊北斗", "class": "bg-primary text-white"})
            
        item['tags'] = tags
        
    return data_list

def calculate_recommendations(minrepo_data, pworld_data):
    """
    Cross-reference data to find the best candidates.
    """
    scores = {}
    store_info = {}

    # Helper to canonicalize names (Simple partial match)
    def get_id(name):
        return name.replace(" ", "").replace("　", "").replace("店", "")

    # 1. Evaluate Performance (Yesterday)
    for i, item in enumerate(minrepo_data):
        sid = get_id(item['store_name'])
        if sid not in scores: scores[sid] = 0
        if sid not in store_info: 
            store_info[sid] = {
                "name": item['store_name'], 
                "reasons": [], 
                "url": item['url'],
                "anaslo_url": item.get('anaslo_url'),
                "badges": []
            }
        
        # Recency Bonus for MinRepo (Since we now fetch 30 days)
        # Only yesterday's data should count heavily.
        # Check date string "M/D" vs Today/Yesterday
        # Ideally parsing minrepo date properly.
        # For now, we assume the list is sorted desc, so index 0 is latest.
        # But we loop all. Let's just trust "Recent Strong Result".
        
        # We process ALL data, but only give points if it's VERY recent (last 2 days)?
        # For simplicity, if it's in the top 3 OF THE FETCHED LIST, it might be old.
        # We need to filter by date if we want "Yesterday's Recommendation".
        # However, the user wants "Data Accumulation", implies Analysis over time.
        # Recommendation Logic currently targets "Today's Visit".
        # So we should only look at "Latest Available Date" for each store.
        pass

    # Re-logic: Group by Store, find latest report.
    latest_reports = {}
    for item in minrepo_data:
        sid = get_id(item['store_name'])
        if sid not in latest_reports:
            latest_reports[sid] = item
        else:
            # Already have one, assume first encountered is latest due to sort
            pass
            
    for sid, item in latest_reports.items():
        if sid not in scores: scores[sid] = 0
        if sid not in store_info:
            store_info[sid] = {
                "name": item['store_name'], 
                "reasons": [], 
                "url": item['url'],
                "anaslo_url": item.get('anaslo_url'),
                "badges": []
            }

        try:
            avg = int(item['avg_diff'])
            if avg > 200:
                scores[sid] += 10
                store_info[sid]['reasons'].append(f"直近平均+{avg}枚")
                
            # Rotation Count Bonus
            rot = item.get('rotation_count', 0)
            if rot and rot > 5000:
                 scores[sid] += 5
                 store_info[sid]['reasons'].append(f"高稼働({rot}G)")

        except:
            pass

    # 2. Evaluate Events (Today) - MAIN DRIVER
    for item in pworld_data:
        sid = get_id(item['store_name'])
        match_key = None
        for k in scores.keys():
            if k in sid or sid in k:
                match_key = k
                break
        
        if not match_key:
            match_key = sid
            scores[match_key] = 0
            store_info[match_key] = {
                "name": item['store_name'], 
                "reasons": [], 
                "url": item['url'],
                "anaslo_url": item.get('anaslo_url'),
                "badges": []
            }

        text = item['event_text']
        has_strong_event = False
        
        if "リニューアル" in text or "周年" in text:
            scores[match_key] += 50
            store_info[match_key]['reasons'].append("本日イベ: RE/周年")
            store_info[match_key]['badges'].append("◎本命")
            has_strong_event = True
        elif "OPEN" in text or "時" in text:
            scores[match_key] += 40
            store_info[match_key]['reasons'].append("本日イベ: 時差OPEN")
            store_info[match_key]['badges'].append("〇チャンス")
            has_strong_event = True
        elif "新台" in text:
            scores[match_key] += 25
            store_info[match_key]['reasons'].append("本日イベ: 新台")
            has_strong_event = True

        if has_strong_event and scores[match_key] > 20: 
             scores[match_key] += 20
             store_info[match_key]['reasons'].append("★実績+イベ")
             store_info[match_key]['badges'].append("★激熱")


    # Convert to list and sort
    rec_list = []
    for sid, score in scores.items():
        if score > 0:
            rec_list.append({
                "name": store_info[sid]['name'],
                "score": score,
                "reasons": store_info[sid]['reasons'],
                "badges": store_info[sid]['badges'],
                "url": store_info[sid]['url'],
                "anaslo_url": store_info[sid].get('anaslo_url')
            })
            
    rec_list.sort(key=lambda x: x['score'], reverse=True)
    return rec_list[:5] # Return Top 5 candidates


def input_manual_data(minrepo_data):
    """
    Interactive prompt for missing data.
    """
    manual_data = load_manual_data()
    updated = False
    
    # Filter for top performers (avg_diff > 100) that are recent and missing rotation count
    # We don't want to ask for every single store in last 30 days.
    # Logic: Only ask for "Interesting" stores (Avg Diff > 100) from the LATEST dates.
    
    print("\n--- Manual Data Entry Mode ---")
    print("Press Enter to skip, or input value.")
    
    # Sort by date desc
    # minrepo_data is already sorted by something? Re-sort by date if possible, but date is str.
    # Assuming list order is roughly recent->old.
    
    count = 0
    for item in minrepo_data:
        if count > 5: break # Only ask top few to avoid spam
        
        # Skip if weak result
        if item['avg_diff'] < 100: continue
        
        key = f"{item['store_name']}_{item.get('date', '')}"
        
        # Skip if already has data
        if key in manual_data and manual_data[key].get('rotation_count'):
            item['rotation_count'] = manual_data[key]['rotation_count']
            continue
            
        # Prompt
        print(f"\nStore: {item['store_name']} ({item['date']}) | Avg Diff: +{item['avg_diff']}")
        val = input(f"Input Avg Rotation Count (Enter to skip): ")
        
        if val.strip().isdigit():
            rot = int(val.strip())
            if key not in manual_data: manual_data[key] = {}
            manual_data[key]['rotation_count'] = rot
            item['rotation_count'] = rot
            updated = True
            count += 1
        else:
            print("Skipped.")
            
    if updated:
        save_manual_data(manual_data)
        print("Manual data saved.")

def generate_report():
    print("Fetching Min-Repo data (Past 30 days)...")
    minrepo_data = fetch_minrepo_data(days_back=30)
    
    # Sort by total_diff desc for display (or maybe date?)
    # Users usually want to see recent strong results.
    minrepo_data.sort(key=lambda x: x['total_diff'], reverse=True)
    
    # Load manual data first
    manual_data = load_manual_data()
    minrepo_data = enrich_data(minrepo_data, manual_data)
    
    # Interactive Input
    # Check args to see if interactive mode is requested? 
    # Or just always do it if running in terminal?
    if sys.stdout.isatty():
        input_manual_data(minrepo_data)
    
    print("Fetching P-World data...")
    pworld_data = fetch_pworld_events()
    pworld_data = enrich_data(pworld_data, manual_data) # Reuse enrich for consistency if needed
    
    recommendations = calculate_recommendations(minrepo_data, pworld_data)
    trending_machines = analyze_trends(minrepo_data)
    
    external_links = [
        {"name": "ホールナビ", "url": "https://hall-navi.com/area/tokushima", "desc": "取材・旧イベ日程"},
        {"name": "DMMぱちタウン", "url": "https://p-town.dmm.com/regions/tokushima", "desc": "公式取材・動画"},
        {"name": "みんパチ", "url": "https://minpachi.com/pref/tokushima", "desc": "口コミ・換金率"},
        {"name": "サイトセブン", "url": "https://m.site777.jp/f/regions/36", "desc": "リアルタイム詳細"}
    ]
    
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "src", "reporting")))
    template = env.get_template("report_template.html")
    
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Display top 50 performers in table instead of just 5
    html_content = template.render(
        date=current_date,
        top_performers=minrepo_data[:50], 
        today_events=pworld_data,
        minrepo_data=minrepo_data, # Full data for graphing if needed
        pworld_data=pworld_data,
        external_links=external_links,
        trending_machines=trending_machines,
        recommendations=recommendations
    )
    
    output_file = "tokushima_pachi_report.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Report generated: {output_file}")
    
if __name__ == "__main__":
    generate_report()
