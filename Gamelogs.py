# Gamelogs.py — FINAL VERSION (player names included + perfect matching)
from nba_api.stats.endpoints import playergamelog, leaguegamefinder
from nba_api.stats.static import players
import pandas as pd

def scrape_gamelogs(season: str = "2025-26"):
    print("Fetching ALL player gamelogs for season", season)
    
    # Get every active + some historical players (covers everyone who played this season)
    all_players = players.get_players()  # ~5000 players, includes inactive/retired
    print(f"Total players in database: {len(all_players)}")
    
    all_gamelogs = []
    
    for player in all_players:
        player_id = player['id']
        full_name = player['full_name']
        
        try:
            # Pull this player's gamelog for the season
            gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season, timeout=30)
            df = gamelog.get_data_frames()[0]
            
            if df.empty:
                continue
                
            # CRITICAL: Add the clean player name so you can match perfectly later
            df['PLAYER_NAME'] = full_name
            df['PLAYER_ID']   = player_id
            
            all_gamelogs.append(df)
            print(f"✓ {full_name:30} → {len(df)} games")
            
        except Exception as e:
            # Skip players who have no games or hit rate limit (very rare)
            continue
    
    if not all_gamelogs:
        raise ValueError("No gamelog data found — check season format")
    
    # Combine everything
    final_df = pd.concat(all_gamelogs, ignore_index=True)
    
    # Reorder columns so name is first (easy matching)
    cols = ['PLAYER_NAME', 'PLAYER_ID'] + [c for c in final_df.columns if c not in ['PLAYER_NAME', 'PLAYER_ID']]
    final_df = final_df[cols]
    
    # Save
    final_df.to_csv = 'Full_Gamelogs25.csv'
    final_df.to_csv(final_df_csv, index=False)
    print(f"\nSUCCESS → {final_df_csv}")
    print(f"Total rows: {len(final_df)} | Unique players: {final_df['PLAYER_NAME'].nunique()}")
    print("\nFirst few rows:")
    print(final_df[['PLAYER_NAME', 'GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST']].head(10))

# Run it
if __name__ == "__main__":
    scrape_gamelogs("2024-25")