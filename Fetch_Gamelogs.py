import os
import requests

BR_USER_AGENT = os.environ.get('BR_USER_AGENT', 'Mozilla/5.0 (Copilot Automation)')
HEADERS = {'User-Agent': BR_USER_AGENT}

# Optionally allow a source URL via env
GAMELOGS_URL = os.environ.get('GAMELOGS_URL')

def fetch_gamelogs():
    if not GAMELOGS_URL:
        print('[Fetch_Gamelogs] No GAMELOGS_URL provided; using existing local/legacy logic')
        return None
    try:
        resp = requests.get(GAMELOGS_URL, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[Fetch_Gamelogs] Error: {e}")
        return None

if __name__ == '__main__':
    content = fetch_gamelogs()
    if content:
        out_path = os.environ.get('GAMELOGS_PATH', 'Full_Gamelogs25.csv')
        with open(out_path, 'w') as f:
            f.write(content)
        print(f'[Fetch_Gamelogs] Saved gamelogs → {out_path}')
# Player_Gamelogs.py
import pandas as pd
import json

# Step 1: Read the full season CSV we made earlier
print("Loading Full_Gamelogs25.csv...")
df = pd.read_csv('Full_Gamelogs25.csv')

# Step 2: Clean "-" values (NBA site uses - when attempts = 0)
df = df.replace('-', None)

# Step 3: Convert percentage columns to float (they come as object because of "-")
percent_cols = ['FG%', '3P%', 'FT%']
df[percent_cols] = df[percent_cols].astype(float)

# Step 4: Convert to JSON (list of player-game objects)
print("Converting to JSON...")
player_logs = df.to_dict(orient='records')

# Step 5: Save the final JSON file
with open('Player_Gamelogs25.json', 'w', encoding='utf-8') as f:
    json.dump(player_logs, f, indent=2)

# Step 6: Success message
print(f"Done! {len(player_logs):,} player-game logs saved → Player_Gamelogs25.json")

# Bonus: Show first game as proof
print("\nFirst game in dataset:")
print(player_logs[0])