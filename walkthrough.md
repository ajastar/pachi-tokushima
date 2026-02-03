
# Tokushima Pachinko Data Collector Walkthrough

This AI tool collects data from **Min-Repo**, **P-World**, and provides quick links to **DMM** and **Hall Navi** for Tokushima Prefecture. It generates a mobile-friendly HTML dashboard.

## 1. Local Usage (PC Only)

1.  **Open Terminal** in the project directory:
    ```bash
    cd C:\Users\shiny\.gemini\antigravity\brain\c34d34c0-1832-4365-8aab-83f47bcf5c7c
    ```

2.  **Run the script**:
    ```bash
    python generate_report.py
    ```

3.  **View the Report**:
    - Open `tokushima_pachi_report.html` in your web browser.

## 2. Mobile Access Setup (Recommended)

To view this dashboard on your smartphone and update it automatically every morning (8:00 AM), use **GitHub Pages**.

### Prerequisites
- A GitHub Account (Free)

### Steps
1.  **Create a New Repository** on GitHub (e.g., named `tokushima-pachi`).
2.  **Push this code** to the repository:
    ```bash
    # Run these commands in the terminal inside the project folder
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    # Replace <YOUR_USERNAME> with your GitHub username
    git remote add origin https://github.com/<YOUR_USERNAME>/tokushima-pachi.git
    git push -u origin main
    ```
3.  **Enable GitHub Pages**:
    - Go to your Repository Settings > Pages.
    - Under "Build and deployment", source should be "Deploy from a branch".
    - **Important**: The *Action* will create a branch named `gh-pages` automatically after the first run.
    - Wait for the "Actions" tab to show a green checkmark for "Daily Pachinko Scrape".
    - Once the `gh-pages` branch exists (might take a few minutes after the first run), go back to Settings > Pages and set the branch to `gh-pages` / `/(root)`.
    - Click Save.

4.  **Access on Mobile**:
    - Your site will be live at `https://<YOUR_USERNAME>.github.io/tokushima-pachi/`.
    - Bookmark this URL on your phone!

## 3. Data Analysis & Features
- **Trend Analysis**:
  - Aggregates "Hot Models" data from Min-Repo.
  - Generates a "Yesterday's Trends" board to show which machines were popular across multiple stores.
- **Recommendation Engine**:
  - Scores stores based on a mix of **Yesterday's Performance** (Momentum) and **Today's Events** (Motivation).
  - Prioritizes stores with "Strong Events" (Renewal, Opening Time) + "Good Past Performance" (Synergy).
- **Anaslo Integration**:
  - Provides direct "台データ" (Machine Data) buttons for supported stores (Million, 123 Group).
  - Bypasses anti-scraping measures by linking directly to the store's data page on `ana-slo.com`.

## 4. Direct Links (Fallback)
- **Problem**: Some sites (Hall Navi, DMM) have strict anti-scraping protections.
- **Solution**: The dashboard provides a "Quick Access" section with direct links to these sites for manual checking.

## Verification & Screenshots
**Generated Report - Rankings with Anaslo Buttons:**
![Anaslo Buttons](rankings_anaslo_buttons_1769264642452.png)
*Shows the "台データ" button appearing for stores with available data mappings.*

## Troubleshooting

- **403 Errors**: Hall Navi and DMM often block automated scripts. The dashboard includes "Quick Access" buttons to open these sites directly.
- **GitHub Action Failed**: Check the "Actions" tab on GitHub for error logs.
