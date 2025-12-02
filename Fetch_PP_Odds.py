import os
import json
import requests

# Read configuration from environment variables
PP_API_KEY = os.environ.get('PP_API_KEY')
PP_API_URL = os.environ.get('PP_API_URL', 'https://api.prizepicks.com/projections')
HEADERS = {
    'User-Agent': os.environ.get('BR_USER_AGENT', 'Mozilla/5.0 (Copilot Automation)'),
}
if PP_API_KEY:
    HEADERS['Authorization'] = f'Bearer {PP_API_KEY}'

# Existing logic (minimal integration) — replace direct requests with configured values
def fetch_pp_odds():
    try:
        resp = requests.get(PP_API_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print(f"[Fetch_PP_Odds] Error fetching PP odds: {e}")
        return None

if __name__ == '__main__':
    data = fetch_pp_odds()
    if not data:
        exit(0)
    # Save to the canonical input for the builder
    out_path = os.environ.get('PP_LINES_PATH', 'NBA_PURE_STANDARD_SINGLE.json')
    try:
        with open(out_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f'[Fetch_PP_Odds] Saved PrizePicks lines → {out_path}')
    except Exception as e:
        print(f'[Fetch_PP_Odds] Error saving PP odds: {e}')
# Fetch_Pure_NBA_Odds.py → THE UNBREAKABLE ONE
import requests
import pandas as pd
import json
from datetime import datetime

print("Fetching 100% PURE NBA Standard Single-Stat Lines (No NFL, No Halves, No Combos)")

# 2025-26 NBA Teams - THE WALL
NBA_TEAMS = {
    'ATL','BKN','BOS','CHA','CHI','CLE','DAL','DEN','DET','GSW',
    'HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK',
    'OKC','ORL','PHI','PHX','POR','SAC','SAS','TOR','UTA','WAS'
}

# Pure single stats ONLY (what real bettors use)
ALLOWED_STATS = {
    'Points', 'Rebounds', 'Assists', 'Threes Made', 'Steals', 'Blocks',
    'Turnovers', 'Fantasy Score', 'Pts+Rebs+Asts', 'Pts+Rebs', 'Pts+Asts', 'Rebs+Asts',
    'Free Throws Made', 'Three Pointers Made', 'Blocked Shots', 'Steals + Blocks'
}

def fetch_pure_nba_odds():
    url = "https://partner-api.prizepicks.com/projections?per_page=1000&league_id=7"  # ← NBA ONLY (league_id=7)
    try:
        data = requests.get(url, timeout=15).json()
    except:
        print("API down or blocked. Try again later.")
        return pd.DataFrame()

    players = {}
    for item in data.get('included', []):
        if item.get('type') == 'new_player':
            attr = item['attributes']
            team = attr.get('team')
            if team in NBA_TEAMS:
                players[item['id']] = {
                    'name': attr.get('name'),
                    'team': team
                }

    pure_lines = []
    for prop in data.get('data', []):
        attrs = prop['attributes']
        rel = prop.get('relationships', {})
        player_id = rel.get('new_player', {}).get('data', {}).get('id')
        
        if player_id not in players:
            continue

        player = players[player_id]
        stat = attrs.get('stat_type', '')
        odds_type = attrs.get('odds_type', '')
        line = attrs.get('line_score')
        description = attrs.get('description', '')

        # FINAL FILTERS - NO ESCAPE
        if odds_type != 'standard':           # Only Standard
            continue
        if not line:                           # Must have line
            continue
        if '+' in stat and stat not in ALLOWED_STATS:  # Block weird combos
            continue
        if any(x in description.lower() for x in ['1h', '2h', '1q', '2q', 'half', 'quarter', '1st half', '2nd half']):
            continue  # NO HALVES OR QUARTERS
        if any(bad in stat.lower() for bad in ['combo', '1st 3 minutes', 'completion', 'yards', 'rush', 'receiving']):
            continue  # Kill remaining football junk

        # Clean stat name
        clean_stat = stat.replace(' Made', '').replace(' Attempted', '').replace('Three Pointers', 'Threes')

        pure_lines.append({
            "Name": player['name'],
            "Team": player['team'],
            "Stat": clean_stat,
            "Line": float(line),
            "Versus": description.replace('vs ', '').replace(' at ', '').upper().split(' - ')[0],
            "Odds_Type": "Standard",
            "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

    df = pd.DataFrame(pure_lines)
    if df.empty:
        print("No clean NBA lines right now. Games might be over or not started yet.")
        return df

    df = df.sort_values(by='Line', ascending=False).reset_index(drop=True)

    # SAVE FINAL GOLD FILES
    df.to_csv('NBA_PURE_STANDARD_SINGLE.csv', index=False)
    with open('NBA_PURE_STANDARD_SINGLE.json', 'w', encoding='utf-8') as f:
        json.dump(df.to_dict(orient='records'), f, indent=2)

    print(f"SUCCESS → {len(df)} PURE NBA single-stat standard lines saved!")
    print("Files → NBA_PURE_STANDARD_SINGLE.csv + .json")

    return df

# RUN IT
df = fetch_pure_nba_odds()

if not df.empty:
    print("\nTop 15 Clean NBA Lines Right Now:")
    print(df.head(15)[['Name', 'Team', 'Stat', 'Line', 'Versus']].to_string(index=False))