# UI_DATA_BUILDER_PERFECT.py → THE ONE YOU'LL USE FOREVER
import os
import pandas as pd
import json
from datetime import datetime

print("Building PERFECT Player Cards → Last 5, 10, 20 + Full Season %")

# Load data (env-overridable paths for automation)
PP_LINES_PATH = os.environ.get('PP_LINES_PATH', 'NBA_PURE_STANDARD_SINGLE.json')
GAMELOGS_PATH = os.environ.get('GAMELOGS_PATH', 'Full_Gamelogs25.csv')
OUTPUT_PATH = os.environ.get('OUTPUT_PATH', 'PLAYER_UI_CARDS_PERFECT.json')

with open(PP_LINES_PATH, 'r') as f:
    pp_lines = json.load(f)

df_logs = pd.read_csv(GAMELOGS_PATH)
df_logs['GAME DATE'] = pd.to_datetime(df_logs['GAME DATE'])

"""Stat mapping: each key maps to list of columns to sum per game.
Single-column props use a single-item list. Combos sum all listed columns.
"""
STAT_MAP = {
    'Points': ['PTS'],
    'Rebounds': ['REB'],
    'Assists': ['AST'],
    'Threes': ['3PM'],
    'Steals': ['STL'],
    'Blocks': ['BLK'],
    'Turnovers': ['TOV'],
    'Fantasy Score': ['FP'],
    'Threes Made': ['3PM'],
    'Three Pointers Made': ['3PM'],
    'Blocked Shots': ['BLK'],
    'Steals + Blocks': ['STL','BLK'],
    # Combo props (support both legacy and PrizePicks naming)
    'PRA': ['PTS','REB','AST'],              # legacy key
    'Pts+Rebs+Asts': ['PTS','REB','AST'],    # PrizePicks displayed key
    'Pts+Rebs': ['PTS','REB'],
    'Pts+Asts': ['PTS','AST'],
    'Rebs+Asts': ['REB','AST']
}

ui_cards = []
base_projections = {}

for prop in pp_lines:
    name = prop['Name']
    team = prop['Team']
    stat = prop['Stat']
    line = prop['Line']
    opponent = prop.get('Versus', '???')

    # Skip if stat not supported
    if stat not in STAT_MAP:
        continue
    cols = STAT_MAP[stat]

    # Get player's full season games
    player_df = df_logs[df_logs['PLAYER'] == name].copy()
    if player_df.empty or len(player_df) < 5:
        continue

    player_df = player_df.sort_values('GAME DATE', ascending=False)
    # Build per-game values (sum for combos)
    if len(cols) == 1:
        values = player_df[cols[0]].astype(float).tolist()
    else:
        values = (player_df[cols].astype(float).sum(axis=1)).tolist()

    # Calculate hits
    def hit_rate(n):
        if len(values) < n:
            hits = sum(1 for v in values[:n] if v > line)
            return hits, len(values[:n])
        else:
            hits = sum(1 for v in values[:n] if v > line)
            return hits, n

    l5_hits, l5_games = hit_rate(5)
    l10_hits, l10_games = hit_rate(10)
    l20_hits, l20_games = hit_rate(20)
    season_hits = sum(1 for v in values if v > line)
    season_games = len(values)

    # Last 10 raw sequence (chronological oldest → newest) for charts
    last_10_values = (values[:10][::-1]) if values else []

    # Window averages for projection formula
    def window_avg(vals, n):
        if not vals:
            return 0.0
        return sum(vals[:n]) / min(n, len(vals))

    l5_avg = window_avg(values, 5)
    l10_avg = window_avg(values, 10)
    l20_avg = window_avg(values, 20)
    season_avg = sum(values)/len(values) if values else 0.0

    # Weighted projection: (L5*.30) + (L10*.40) + (L20*.20) + (Full*.10)
    weighted_projection = round(
        l5_avg * 0.30 +
        l10_avg * 0.40 +
        l20_avg * 0.20 +
        season_avg * 0.10, 2
    )

    # Cache base projections for single stats to support combo sums
    if stat in ['Points','Rebounds','Assists']:
        base_projections[(name, stat)] = weighted_projection

    # Final card
    # Display name adjustments (rename PRA to explicit combo wording)
    # Normalize display: if PRA legacy key encountered, show modern label
    if stat == 'PRA':
        display_stat = 'Pts+Rebs+Asts'
    else:
        display_stat = stat

    # If combo, sum component projections when available
    combo_projection = None
    if display_stat in ['Pts+Rebs','Pts+Asts','Rebs+Asts','Pts+Rebs+Asts']:
        parts = []
        if display_stat == 'Pts+Rebs':
            parts = ['Points','Rebounds']
        elif display_stat == 'Pts+Asts':
            parts = ['Points','Assists']
        elif display_stat == 'Rebs+Asts':
            parts = ['Rebounds','Assists']
        elif display_stat == 'Pts+Rebs+Asts':
            parts = ['Points','Rebounds','Assists']
        s = 0.0
        have_any = False
        for p in parts:
            bp = base_projections.get((name, p))
            if bp is not None:
                s += bp
                have_any = True
        if have_any:
            combo_projection = round(s, 2)

    card = {
        "name": name,
        "team": team,
        "opponent": opponent,
        "prop": display_stat,
        "line": line,
        "last_5": f"{l5_hits}/{l5_games}",
        "last_5_pct": round(l5_hits / l5_games * 100, 1),
        "last_10": f"{l10_hits}/{l10_games}",
        "last_10_pct": round(l10_hits / l10_games * 100, 1),
        "last_20": f"{l20_hits}/{l20_games}",
        "last_20_pct": round(l20_hits / l20_games * 100, 1),
        "season": f"{season_hits}/{season_games}",
        "season_pct": round(season_hits / season_games * 100, 1),
        "avg": round(sum(values)/len(values), 1),
        "games": season_games,
        "last_10_values": last_10_values,
        "projection": combo_projection if combo_projection is not None else weighted_projection
    }
    ui_cards.append(card)

# Sort by Last 10 hit rate (your money metric)
ui_cards = sorted(ui_cards, key=lambda x: x['last_10_pct'], reverse=True)

# SAVE THE GOLD
with open(OUTPUT_PATH, 'w') as f:
    json.dump(ui_cards, f, indent=2)

print(f"\nMASTERPIECE COMPLETE → {len(ui_cards)} elite player cards built!")
print(f"File: {OUTPUT_PATH}")

# Write a simple metadata file with generation timestamp
meta = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "cards": len(ui_cards),
    "output": OUTPUT_PATH
}
with open('PLAYER_UI_CARDS_PERFECT.meta.json', 'w') as mf:
    json.dump(meta, mf, indent=2)
print("\nTop 5 Hitters (Last 10 Games):")
for card in ui_cards[:5]:
    print(f"{card['name']:25} {card['prop']:12} {card['line']:>5} → {card['last_10']:>6} ({card['last_10_pct']:>5}%) vs {card['opponent']}")