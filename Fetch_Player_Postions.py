# nba_2025_26_positions_scraper.py
# Run with: python nba_2025_26_positions_scraper.py

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import re

# List of all 30 NBA team abbreviations (common form)
teams = [
    'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW',
    'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK',
    'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS'
]

# Basketball-Reference uses different codes for a few teams
BBR_TEAM_CODE = {
    'BKN': 'BRK',  # Brooklyn Nets
    'CHA': 'CHO',  # Charlotte Hornets
    'PHX': 'PHO',  # Phoenix Suns
}

base_url = "https://www.basketball-reference.com/teams/"
year = "2026"  # 2025-26 season page on B-R

# Store results: { "Player Name": "Position" }
players_dict = {}

# Polite header so we don't get blocked
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
}

print("Starting NBA 2025-26 player position scraper...\n")

for team in teams:
    team_code = BBR_TEAM_CODE.get(team, team)
    url = urljoin(base_url, f"{team_code}/{year}.html")
    print(f"Fetching {team} roster...", end=" ")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed ({response.status_code})")
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"id": "roster"})

        if not table:
            print("No roster table found")
            continue

        tbody = table.find("tbody")
        if not tbody:
            print("No tbody in roster table")
            continue
        rows = tbody.find_all("tr")

        for row in rows:
            player_td = row.find("td", {"data-stat": "player"})
            pos_td = row.find("td", {"data-stat": "pos"})
            if not player_td or not pos_td:
                continue

            player_name = player_td.get_text(strip=True)
            position = pos_td.get_text(strip=True)

            # Skip headers, inactive, or two-way players (marked with *), and empty rows
            if (not player_name or not position or 
                player_name.startswith("Team") or 
                "*" in player_name):
                continue

            # Clean name: remove backslashes and trailing parentheticals like (TW)
            clean_name = re.sub(r"\s*\(.*?\)\s*$", "", player_name.replace("\\", "")).strip()

            # Use the most recent position if player appears on multiple teams
            players_dict[clean_name] = position

        print(f"Done ({len(rows)} rows processed)")
        time.sleep(1.2)  # Be nice to the server

    except Exception as e:
        print(f"Error: {e}")

# Final count
print(f"\nFinished! Collected {len(players_dict)} unique active players.")

# Save to JSON
output_file = "/Users/kahlilhodge/NBA-UI-Props/nba_players_2025_26_positions.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(players_dict, f, indent=4, ensure_ascii=False)

print(f"JSON file saved as → {output_file}")
print("\nPreview (first 10 players):")
for i, (name, pos) in enumerate(list(players_dict.items())[:10]):
    print(f"   {name}: {pos}")

print("\nReady for your fantasy app, dashboard, or model! Go build something awesome!")