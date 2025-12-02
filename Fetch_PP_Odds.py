import os
import json
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Read configuration from environment variables
PP_API_KEY = os.environ.get('PP_API_KEY')
PP_API_URL = os.environ.get('PP_API_URL', 'https://api.prizepicks.com/projections')
PP_LEAGUE_ID = os.environ.get('PP_LEAGUE_ID', '7')  # 7 = NBA

HEADERS = {
    'User-Agent': os.environ.get('BR_USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'),
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://app.prizepicks.com',
    'Referer': 'https://app.prizepicks.com/',
}
if PP_API_KEY:
    HEADERS['Authorization'] = f'Bearer {PP_API_KEY}'

PARAMS = {
    'league_id': PP_LEAGUE_ID,
    'per_page': os.environ.get('PP_PER_PAGE', '500'),
    'page': os.environ.get('PP_PAGE', '1'),
    'single_stat': os.environ.get('PP_SINGLE_STAT', 'true')
}

def build_session():
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1.2, status_forcelist=[429, 500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if proxy:
        s.proxies.update({'http': proxy, 'https': proxy})
    return s

# Existing logic (minimal integration) — replace direct requests with configured values
def fetch_pp_odds():
    try:
        session = build_session()
        resp = session.get(PP_API_URL, headers=HEADERS, params=PARAMS, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[Fetch_PP_Odds] Error fetching PP odds: {e}")
        return None

def looks_like_canonical(items):
    # Expect list of dicts with keys like Name/Stat/Line/Team/Versus
    if not isinstance(items, list) or not items:
        return False
    sample = items[0]
    return isinstance(sample, dict) and any(k in sample for k in ('Name','Stat','Line'))

if __name__ == '__main__':
    # Only attempt direct PrizePicks API when a key is provided or explicitly allowed
    if PP_API_KEY or os.environ.get('ALLOW_UNAUTH_PP', '').lower() == 'true':
        data = fetch_pp_odds()
        if data:
            # Always keep a raw snapshot for debugging
            os.makedirs('downloaded_files', exist_ok=True)
            raw_path = os.path.join('downloaded_files', 'pp_odds.raw.json')
            try:
                with open(raw_path, 'w') as rf:
                    json.dump(data, rf, indent=2)
                print(f'[Fetch_PP_Odds] Saved raw response → {raw_path}')
            except Exception as e:
                print(f'[Fetch_PP_Odds] Warning: could not save raw odds: {e}')

            # Only overwrite canonical file if structure already matches expected format
            out_path = os.environ.get('PP_LINES_PATH', 'NBA_PURE_STANDARD_SINGLE.json')
            if looks_like_canonical(data):
                try:
                    with open(out_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f'[Fetch_PP_Odds] Saved canonical lines → {out_path}')
                except Exception as e:
                    print(f'[Fetch_PP_Odds] Error saving canonical lines: {e}')
            else:
                print('[Fetch_PP_Odds] Raw response did not match canonical schema; skipped overwriting NBA_PURE_STANDARD_SINGLE.json')
        else:
            print('[Fetch_PP_Odds] No data from direct API.')
    else:
        print('[Fetch_PP_Odds] Skipping direct PP fetch (no PP_API_KEY). Using partner endpoint instead.')
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
    url = os.environ.get('PP_PARTNER_URL', "https://partner-api.prizepicks.com/projections?per_page=1000&league_id=7")  # NBA ONLY
    try:
        session = build_session()
        # Reuse browser-like headers to improve reliability
        partner_headers = dict(HEADERS)
        partner_headers.setdefault('Origin', 'https://www.prizepicks.com')
        partner_headers.setdefault('Referer', 'https://www.prizepicks.com/')
        resp = session.get(url, headers=partner_headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Partner API down or blocked: {e}. Try again later.")
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