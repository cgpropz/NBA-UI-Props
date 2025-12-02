# download_player_images.py → DOWNLOADS EVERY SINGLE PLAYER FROM YOUR JSON
import json
import requests
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

print("Loading players from NBA_PURE_STANDARD_SINGLE.json...")
print("Downloading headshots from Basketball-Reference...")

# LOAD ALL PLAYERS FROM YOUR JSON (100% AUTOMATIC)
try:
    with open('NBA_PURE_STANDARD_SINGLE.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    player_names = list(set(p['Name'] for p in data))
    print(f"Found {len(player_names)} unique players in JSON")
except FileNotFoundError:
    print("NBA_PURE_STANDARD_SINGLE.json not found!")
    exit()
except Exception as e:
    print(f"Error reading JSON: {e}")
    exit()

os.makedirs('player_images', exist_ok=True)

# Basketball-Reference headshot base
BASE_URL = "https://www.basketball-reference.com/req/202106291/images/headshots/"

def download_headshot(name):
    # Clean filename
    clean_name = re.sub(r"[.'\s]+", "", name.lower())
    filename = f"player_images/{clean_name}.jpg"
    
    if os.path.exists(filename):
        return f"Exists → {name}"

    # Try common B-R naming patterns
    parts = name.split()
    if len(parts) < 2:
        return f"Skip (bad name) → {name}"
    
    last = parts[-1].lower()[:5]
    first = parts[0].lower()[:2]
    codes = [
        f"{last}{first}01",
        f"{last}{first}02",
        f"{last[:5]}{first[:2]}01",
        f"{last[:5]}{first[:2]}02"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for code in codes:
        url = f"{BASE_URL}{code}.jpg"
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200 and len(r.content) > 8000:  # valid image
                with open(filename, 'wb') as f:
                    f.write(r.content)
                return f"DOWNLOADED → {name} ({code})"
        except:
            pass
        time.sleep(0.05)
    
    return f"MISSING → {name}"

# DOWNLOAD ALL — FAST & RESPECTFUL
print("Starting download (15 at a time)...\n")
with ThreadPoolExecutor(max_workers=15) as executor:
    results = list(executor.map(download_headshot, player_names))

# Summary
downloaded = sum(1 for r in results if "DOWNLOADED" in r)
exists = sum(1 for r in results if "Exists" in r)
missing = len(results) - downloaded - exists

print("\n" + "="*60)
print(f"HEADSHOT DOWNLOAD COMPLETE")
print(f"Total players: {len(player_names)}")
print(f"Downloaded: {downloaded}")
print(f"Already existed: {exists}")
print(f"Missing: {missing}")
print("="*60)
print("All images saved to: /player_images/")
print("Now run: python generate_players.py")

# Create default fallback
default_path = "player_images/default.jpg"
if not os.path.exists(default_path):
    print("Creating default player silhouette...")
    default_url = "https://i.imgur.com/0VGBj.jpg"  # clean NBA silhouette
    try:
        img = requests.get(default_url)
        with open(default_path, 'wb') as f:
            f.write(img.content)
        print("Default image created")
    except:
        print("Could not download default")