from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime

# Automatically determine NBA season string for today (ex: '2025-26')
def current_nba_season_str(today=None):
    if today is None:
        today = datetime.now()
    year = today.year
    if today.month >= 10:
        # October–December is start of new season
        start_year = year
        end_year = year + 1
    else:
        # Jan–Sep is still in previous season's end
        start_year = year - 1
        end_year = year
    return f"{start_year}-{str(end_year)[-2:]}"

nba_season = current_nba_season_str()
today = datetime.now().strftime("%m/%d/%Y")
nba_url = f"https://www.nba.com/stats/players/boxscores/?Season={nba_season}&SeasonType=Regular%20Season"

def get_boxscores_table(page, timeout=60):
    """
    Wait for the player stats table and return its HTML.
    """
    selector = 'table[class^="Crom_table"]'
    page.wait_for_selector(selector, timeout=timeout * 1000)
    table = page.query_selector(selector)
    if not table:
        return None
    return table.evaluate('node => node.outerHTML')

def main():
    print(f"Detected NBA season: {nba_season} • Scraping up to {today}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        print(f"Loading {nba_url} ...")
        page.goto(nba_url, timeout=90000)
        page.wait_for_timeout(8000)

        # Handle cookie/privacy modal if present
        for btn_word in ["accept", "agree", "consent"]:
            try:
                button = page.query_selector(f'button:has-text("{btn_word}")')
                if button:
                    button.click()
                    print(f"Clicked '{btn_word}' button.")
                    page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        page.wait_for_timeout(4000)
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')

        try:
            table_html = get_boxscores_table(page)
            if not table_html:
                print("ERROR: Could not find NBA boxscores table.")
                browser.close()
                exit(2)
            df = pd.read_html(table_html)[0]
        except Exception as e:
            print("ERROR locating/parsing the NBA boxscores table.")
            print(e)
            browser.close()
            exit(2)

        csv_file = "Full_Gamelogs25.csv"
        json_file = "Player_Gamelogs25.json"
        try:
            df.to_csv(csv_file, index=False)
            df.to_json(json_file, orient="records")
            print(f"Saved {len(df)} player-game logs to {csv_file} and {json_file}")
            if len(df) > 0:
                print("First game in dataset:")
                print(df.head(1).to_dict(orient="records")[0])
            else:
                print("No player-game logs found!")
        except Exception as e:
            print("ERROR writing output file.")
            print(e)
            browser.close()
            exit(2)
        browser.close()

if __name__ == "__main__":
    main()
