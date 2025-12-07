import requests
import pandas as pd
from datetime import datetime
import time
import sys

season_start = "10/01/2025"  # Set season start
today = datetime.now().strftime("%m/%d/%Y")  # Always up to latest date

url = "https://stats.nba.com/stats/leaguegamelog"
params = {
    "Counter": "1000",
    "DateFrom": season_start,
    "DateTo": today,
    "Direction": "DESC",
    "ISTRound": "",
    "LeagueID": "00",
    "PlayerOrTeam": "P",
    "Season": "2025-26",
    "SeasonType": "Regular Season",
    "Sorter": "DATE"
}
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com"
}

def fetch_with_retry(url, params, headers, retries=5, timeout=60):
    for attempt in range(1, retries+1):
        try:
            print(f"Attempt {attempt} of {retries}: Fetching NBA player gamelogs ({params['DateFrom']}–{params['DateTo']}) with timeout {timeout}s")
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.ReadTimeout:
            print(f"ReadTimeout on attempt {attempt}. Retrying in {2**attempt} seconds...", file=sys.stderr)
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            print(f"Request error on attempt {attempt}: {e}. Retrying in {2**attempt} seconds...", file=sys.stderr)
            time.sleep(2 ** attempt)
    return None

response = fetch_with_retry(url, params, headers)
if response is None:
    print(f"ERROR: Failed to fetch NBA gamelogs from {season_start} to {today} after max retries.", file=sys.stderr)
    sys.exit(2)

print("Parsing JSON data...")
try:
    data = response.json()
    columns = data['resultSets'][0]['headers']
    rows = data['resultSets'][0]['rowSet']
    df = pd.DataFrame(rows, columns=columns)
except Exception as e:
    print("ERROR: Could not parse NBA stats API response.", file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(2)

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
    print("ERROR: Failed to write output CSV/JSON.", file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(2)
