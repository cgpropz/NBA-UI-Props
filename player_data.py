import json
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats

# -------------------------------------------------
# Pull players who played in 2025-26 Regular Season
# -------------------------------------------------
stats = leaguedashplayerstats.LeagueDashPlayerStats(
    season="2025-26",
    season_type_all_star="Regular Season",
).get_data_frames()[0]

# -------------------------------------------------
# Extract unique player info
# -------------------------------------------------
players_df = stats[['PLAYER_ID', 'PLAYER_NAME']].drop_duplicates()

# Split first/last names
players_df['FIRST_NAME'] = players_df['PLAYER_NAME'].apply(lambda x: x.split(" ")[0])
players_df['LAST_NAME'] = players_df['PLAYER_NAME'].apply(lambda x: " ".join(x.split(" ")[1:]))

# -------------------------------------------------
# Build JSON structure
# -------------------------------------------------
players_list = [
    {
        "id": int(row.PLAYER_ID),
        "full_name": row.PLAYER_NAME,
        "first_name": row.FIRST_NAME,
        "last_name": row.LAST_NAME,
        "is_active": True   # everyone in this endpoint played in 2025-26
    }
    for _, row in players_df.iterrows()
]

# -------------------------------------------------
# Save to players.json
# -------------------------------------------------
with open("players.json", "w") as f:
    json.dump(players_list, f, indent=4)

# Preview
players_df.head()

