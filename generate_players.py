# generate_players.py → FINAL: REAL DATA + PLAYER HEADSHOTS
import json
import os
import re
import unicodedata
import pandas as pd

print("Generating ELITE player pages with HEADSHOTS...")

# Load data
with open('NBA_PURE_STANDARD_SINGLE.json') as f:
    pp_lines = json.load(f)

df_logs = pd.read_csv('Full_Gamelogs25.csv')
df_logs['GAME DATE'] = pd.to_datetime(df_logs['GAME DATE'])

STAT_MAP = {
    'Points': ['PTS'],
    'Rebounds': ['REB'],
    'Assists': ['AST'],
    'Threes': ['3PM'],
    'Steals': ['STL'],
    'Blocks': ['BLK'],
    'Turnovers': ['TOV'],
    'Fantasy Score': ['FP'],
    # Combo props (support both legacy and PrizePicks naming)
    'PRA': ['PTS','REB','AST'],
    'Pts+Rebs+Asts': ['PTS','REB','AST'],
    'Pts+Rebs': ['PTS','REB'],
    'Pts+Asts': ['PTS','AST'],
    'Rebs+Asts': ['REB','AST']
}

with open('player-template-new.html') as f:
    template = f.read()

os.makedirs('players', exist_ok=True)
count = 0

def normalize_name(n: str) -> str:
    nf = unicodedata.normalize('NFKD', n)
    return ''.join(c for c in nf if not unicodedata.combining(c))

def make_slug(name: str):
    base = normalize_name(name.lower())
    return re.sub(r'[^a-z0-9]+', '-', base).strip('-')

for prop in pp_lines:
    name = prop['Name']
    team = prop['Team']
    stat = prop['Stat']
    line = prop['Line']
    opponent = prop.get('Versus', 'N/A')

    if stat not in STAT_MAP:
        continue
    cols = STAT_MAP[stat]

    player_games = df_logs[df_logs['PLAYER'] == name]
    if player_games.empty:
        continue

    player_games = player_games.sort_values('GAME DATE', ascending=False)
    if len(cols) == 1:
        values = player_games[cols[0]].astype(float)
    else:
        values = player_games[cols].astype(float).sum(axis=1)

    # Last 10 values (chronological: oldest → newest)
    last10_raw = values.head(10).tolist()
    last10_values = last10_raw[::-1]

    # Last 10 game dates aligned with last10_values (oldest → newest)
    last10_dates_series = player_games['GAME DATE'].head(10)
    # Format as MM/DD and reverse to match chronological ordering
    last10_dates = [d.strftime('%m/%d') for d in last10_dates_series.iloc[::-1]]

    # Hit rates
    hits_l5 = sum(v > line for v in values.head(5))
    hits_l10 = sum(v > line for v in values.head(10))
    hits_l20 = sum(v > line for v in values.head(20))
    hits_season = sum(v > line for v in values)

    l5 = f"{hits_l5}/5"
    l10 = f"{hits_l10}/10"
    l20 = f"{hits_l20}/20" if len(values) >= 20 else f"{hits_l20}/{min(20, len(values))}"
    season = f"{hits_season}/{len(values)}"

    # SLUG + IMAGE PATH
    slug = make_slug(name)
    clean_name = re.sub(r'[^a-z0-9]', '', normalize_name(name).lower())
    image_filename = f"{clean_name}.jpg"
    image_path = f"../player_images/{image_filename}"

    # Prefer remote Basketball-Reference headshots unless a non-empty local override exists
    def make_bbref_slug(full_name: str) -> str:
        nm = normalize_name(full_name.lower())
        parts = [re.sub(r'[^a-z]', '', p) for p in nm.split() if p]
        if len(parts) < 2:
            return ''
        first, last = parts[0], parts[-1]
        # basketball-reference: last 5 + first 2 + 01
        return f"{last[:5]}{first[:2]}01"

    local_path = f"player_images/{image_filename}"
    use_local = False  # Prefer remote headshots for consistency
    bb_slug = make_bbref_slug(name)
    image_path = (
        f"https://www.basketball-reference.com/req/202106291/images/players/{bb_slug}.jpg"
        if bb_slug else "../player_images/default.jpg"
    )

    filename = f"players/{slug}.html"

    # Generate page
    if stat == 'PRA':
        display_stat = 'Pts+Rebs+Asts'
    else:
        display_stat = stat
    # Weighted projection (L5*.30 + L10*.40 + L20*.20 + Season*.10)
    def avg(series, n=None):
        s = series.head(n) if n else series
        arr = s.astype(float).tolist()
        return sum(arr)/len(arr) if arr else 0.0

    avg5 = avg(values, 5)
    avg10 = avg(values, 10)
    avg20 = avg(values, 20)
    avg_season = avg(values, None)
    projection = 0.30*avg5 + 0.40*avg10 + 0.20*avg20 + 0.10*avg_season

    html = template \
        .replace('{{NAME}}', name) \
        .replace('{{TEAM}}', team) \
        .replace('{{OPPONENT}}', opponent) \
        .replace('{{PROP}}', display_stat) \
        .replace('{{LINE}}', str(line)) \
        .replace('{{PROJECTION}}', f"{projection:.1f}") \
        .replace('{{LAST10_DATA}}', json.dumps(last10_values)) \
        .replace('{{LAST10_DATES}}', json.dumps(last10_dates)) \
        .replace('{{HITRATE_L5}}', l5) \
        .replace('{{HITRATE_L10}}', l10) \
        .replace('{{HITRATE_L20}}', l20) \
        .replace('{{SEASON}}', season) \
        .replace('{{PLAYER_IMAGE}}', image_path)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)

    count += 1
    # Status indicator for console output
    status = ("BBREF" if image_path.startswith("https://www.basketball-reference.com") else "DEFAULT")
    print(f"Generated → {filename} | {l10} | {status}")

print(f"\nEMPIRE COMPLETE: {count} player pages with HEADSHOTS!")
print("Open any file in /players/ — they’re alive.")