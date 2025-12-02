import os
import json
import requests

DVP_API_URL = os.environ.get('DVP_API_URL', 'https://draftedge.com/draftedge-data/nba_dvp.json')
BR_USER_AGENT = os.environ.get('BR_USER_AGENT', 'Mozilla/5.0 (Copilot Automation)')
HEADERS = {'User-Agent': BR_USER_AGENT}

def fetch_dvp():
    try:
        resp = requests.get(DVP_API_URL, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[dvp_parser] Error fetching DVP: {e}")
        return None

def save_team_rankings(payload):
    if not payload:
        return False
    data = payload.get('dvp') or payload.get('data') or payload
    team_rankings = data.get('team_dvp_rankings') if isinstance(data, dict) else None
    if not team_rankings:
        print('[dvp_parser] No team_dvp_rankings found')
        return False
    out = {
        'generated_at': payload.get('generated_at'),
        'source': DVP_API_URL,
        'summary': {
            'team_position_rankings': len(team_rankings),
            'player_game_logs': 0
        },
        'data': {'team_dvp_rankings': team_rankings}
    }
    with open('nba_dvp_latest.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"[dvp_parser] Saved {len(team_rankings)} team rankings → nba_dvp_latest.json")
    return True

if __name__ == '__main__':
    payload = fetch_dvp()
    save_team_rankings(payload)
# File: scrape_nba_dvp.py
import requests
import json
from datetime import datetime

# Step 1: Scrape the data
url = "https://draftedge.com/draftedge-data/nba_dvp.json"
print("Fetching latest NBA DVP data from DraftEdge...")

raw = requests.get(url).json()        # Auto-parses JSON

# Normalize payload: recent responses have top-level keys like {'dvp': [...], 'top_players': [...]}
if isinstance(raw, dict):
    data = raw.get("dvp") or raw.get("data") or raw.get("rows") or []
else:
    data = raw

# Step 2: Smartly separate the two data types
# Identify team position rankings vs player logs by key presence
# DraftEdge team rows typically have keys like 'team', 'position', 'dvp'
# Player logs may have 'player'/'player_name', 'team', 'opponent', etc.
team_rankings = [item for item in data if isinstance(item, dict) and ("position" in item or ("player" not in item and "player_name" not in item))]
player_logs   = [item for item in data if isinstance(item, dict) and ("player" in item or "player_name" in item)]

# Step 3: Build a pro-level structured JSON
final_json = {
    "generated_at": datetime.now().isoformat(),
    "source": url,
    "summary": {
        "team_position_rankings": len(team_rankings),
        "player_game_logs": len(player_logs)
    },
    "data": {
        "team_dvp_rankings": team_rankings,    # ~150 rows (30 teams × 5 positions) when available
        "player_game_logs": player_logs        # Individual performances if present
    }
}

# Step 4: Save as clean, readable JSON file
with open("nba_dvp_latest.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=2, ensure_ascii=False)

print(f"Success! Saved {len(team_rankings)} rankings + {len(player_logs)} games → nba_dvp_latest.json")