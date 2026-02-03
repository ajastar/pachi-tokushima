# Tokushima Pachinko/Slot Data Collector Implementation Plan

## Goal
Build an automated tool to collect Pachinko/Slot data for Tokushima City/Prefecture to help the user decide where to play.
- **Level A (Store Info)**: Events, New Machines (Source: P-World / DMM)
- **Level B (Performance)**: Total Difference, Average Difference, "Hot" Stores (Source: Min-Repo)
- **Level C (Deep Dive)**: Direct links to Anaslo for machine-specific data (Anti-scraping workaround).
- **Level D (Long-term Trends)**: Scrape past 3 months of Min-Repo to find strong dates and machine preferences.

## Architecture

### 1. Data Collection (`/src/scrapers`)
- **`minrepo.py`**: Scrapes `https://min-repo.com/area/tokushima/`
  - Extracts: Store Name, Date, Total Diff, Avg Diff, Number of data points.
  - Frequency: Daily (Reflects yesterday's results).
- **`historical_minrepo.py` [NEW]**:
  - Scrapes `https://min-repo.com/category/徳島県/page/X/` (Pages 1-20).
  - Collects ~3 months of performance data to build a local database (`history.csv`).
  - Frequency: On-demand or Weekly.
- **`pworld.py`**: Scrapes `https://www.p-world.co.jp/tokushima/` and specific store pages if needed.
  - Extracts: "New Machine Replacement" (新台入替), "Opening Time" (12時開店 means strong event usually).
- **`anaslo_linker.py` (Planned)**:
  - Validates and generates direct links to `ana-slo.com` for specific stores.
  - No scraping due to Cloudflare protection; relies on URL pattern matching.

### 2. Data Processing (`/src/analysis`)
- **`aggregator.py`**: Combines data.
- **`cleaner.py`**: Normalizes store names to match between sources (e.g., "MIRAION Tokushima" vs "Million Tokushima").

### 3. Reporting (`/src/reporting`)
- **`dashboard.py`**: Generates a local HTML file (`report_YYYYMMDD.html`).
- **Features**: 
  - Top 10 "Hot" Stores from yesterday (High Total Diff).
  - Stores with "New Machines" or "Special Opening Times" today.
  - Stores with "New Machines" or "Special Opening Times" today.
  - **[NEW]** Direct "Anaslo" buttons for checking detailed machine data (BB/RB/Games).
  - Links to specific store pages for detailed verification.
- **`trend_analyzer.py` [NEW]**:
  - Analyzes `history.csv` to find:
    - **Strong Dates**: Which days (e.g., 7th, 11th) have high Avg Diff for each store.
    - **Machine Trends**: Which models appear most often in "Hot Models" text over time.

## Tech Stack
- **Language**: Python 3.10+
- **Libraries**:
  - `requests`: HTTP fetching (Lightweight).
  - `beautifulsoup4`: HTML Parsing.
  - `pandas`: Data manipulation.
  - `jinja2`: HTML Template engine.

## Verification
- Run scripts against live URLs.
- Check parsing accuracy (Total Diff numbers must match website).
- Ensure HTML report renders correctly in browser.

## User Action Required
- Install Python dependencies: `pip install requests beautifulsoup4 pandas jinja2`
- Run the script daily (can be automated via Task Scheduler).
