#!/usr/bin/env python3
"""
Get missing posters and handle non-Steam games.
Use alternative image sources.
"""
import os
import time
import requests

OUTPUT_DIR = "/home/node/.openclaw/workspace/game_images"

def download_image(url, filepath, timeout=30):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get('content-type', '')
        if 'image' not in content_type and content_type:
            print(f"    Not an image: {content_type}")
            return False
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        size = os.path.getsize(filepath)
        if size < 1000:
            os.remove(filepath)
            return False
        print(f"    ✓ {os.path.basename(filepath)} ({size/1024:.1f} KB)")
        return True
    except Exception as e:
        print(f"    ✗ {e}")
        return False

def try_steam_poster_variants(app_id, game_name, game_dir):
    """Try multiple Steam CDN URLs for posters."""
    variants = [
        f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg",
        f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900.jpg",
        f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg",
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/library_600x900.jpg",
    ]
    
    poster_path = os.path.join(game_dir, f"{game_name}_Poster.jpg")
    
    for url in variants:
        print(f"    Trying: {url.split('/')[-1]}...")
        if download_image(url, poster_path):
            return True
    
    return False

def search_steamgriddb_poster(game_name, game_dir):
    """Try SteamGridDB for posters (no API key needed for search)."""
    # This is just a search for reference - actual API needs key
    search_term = game_name.replace(' ', '%20').replace(':', '%3A')
    url = f"https://www.steamgriddb.com/search/grids?term={search_term}"
    print(f"    SteamGridDB search: {url}")
    return False  # Would need actual scraping/API

def try_igdb_poster(game_name, game_dir):
    """Try IGDB for images."""
    # IGDB requires Twitch OAuth - skip for now
    return False

# === 1. Missing Steam Posters ===
print("=" * 60)
print("FIXING MISSING POSTERS")
print("=" * 60)

# Rise of Ronnin - Steam App 2790220
print("\nRise of Ronnin (App 2790220):")
game_dir = os.path.join(OUTPUT_DIR, "Rise of Ronnin")
os.makedirs(game_dir, exist_ok=True)
if not try_steam_poster_variants(2790220, "Rise of Ronnin", game_dir):
    # Try searching for "Rise of the Ronin" - it's on Steam as that name
    print("  Trying 'Rise of the Ronin' variants...")
    # Check if there's another app ID for "Rise of the Ronin"
    # Try the Korean/Japanese Steam pages too
    
# WWE 2025 - Try WWE 2K25 Steam App 2623420
print("\nWWE 2025 (WWE 2K25 App 2623420):")
game_dir = os.path.join(OUTPUT_DIR, "WWE 2025")
os.makedirs(game_dir, exist_ok=True)
if not try_steam_poster_variants(2623420, "WWE 2025", game_dir):
    # Try without _2x
    alt_url = "https://cdn.akamai.steamstatic.com/steam/apps/2623420/capsule_616x353.jpg"
    poster_path = os.path.join(game_dir, "WWE 2025_Poster.jpg")
    download_image(alt_url, poster_path)

# === 2. Non-Steam Games ===
print("\n" + "=" * 60)
print("NON-STEAM GAMES - SEARCHING FOR IMAGES")
print("=" * 60)

# Resident Evil 9
print("\nResident Evil 9:")
game_dir = os.path.join(OUTPUT_DIR, "Resident Evil 9")
os.makedirs(game_dir, exist_ok=True)

# Try to find official teaser images
re9_urls = [
    "https://www.residentevil.com/re9/assets/images/ogp.png",
    "https://image.api.playstation.com/vulcan/ap/rnd/202406/1200/resident_evil_9_keyart.jpg",
]
for i, url in enumerate(re9_urls):
    fp = os.path.join(game_dir, f"Resident Evil 9_Poster.jpg")
    if download_image(url, fp):
        break

# Actually, let me search the web for these images
print("  Resident Evil 9: Not yet released. Will note for boss.")

# UFC 5
print("\nUFC 5:")
game_dir = os.path.join(OUTPUT_DIR, "UFC 5")
os.makedirs(game_dir, exist_ok=True)

# EA Sports UFC 5 is on PS5/Xbox
# Try EA website
ufc_urls = [
    "https://media.contentapi.ea.com/content/dam/ea/easports/ufc/ufc-5/common/ufc5-keyart.jpg",
    "https://image.api.playstation.com/vulcan/ap/rnd/202309/1213/ea_sports_ufc_5_keyart.jpg",
]
for url in ufc_urls:
    fp = os.path.join(game_dir, "UFC 5_Poster.jpg")
    if download_image(url, fp):
        break

# Astro Bot
print("\nAstro Bot:")
game_dir = os.path.join(OUTPUT_DIR, "Astro Bot")
os.makedirs(game_dir, exist_ok=True)

astro_urls = [
    "https://image.api.playstation.com/vulcan/ap/rnd/202405/3016/1a8e3e1d5f7b9c0a2e4d6f8a0c2b4d6e8a0c2b4d6e.png",
    "https://image.api.playstation.com/vulcan/ap/rnd/202409/0600/astro_bot_poster_keyart.jpg",
]
for url in astro_urls:
    fp = os.path.join(game_dir, "Astro Bot_Poster.jpg")
    if download_image(url, fp):
        break

# Try to get gameplay for non-Steam games from the web
print("\n" + "=" * 60)
print("SEARCHING WEB FOR NON-STEAM GAMEPLAY IMAGES")
print("=" * 60)

# Use web_fetch to find image URLs for each game
games_to_search = {
    "Resident Evil 9": ["Resident Evil 9 gameplay screenshots PS5", "Resident Evil 9 screenshots"],
    "UFC 5": ["EA Sports UFC 5 gameplay screenshots", "UFC 5 PS5 screenshots"],
    "Astro Bot": ["Astro Bot PS5 gameplay screenshots", "Astro Bot game screenshots 4K"],
}

# For now, try known image hosting sites
for game_name, queries in games_to_search.items():
    print(f"\n{game_name}:")
    game_dir = os.path.join(OUTPUT_DIR, game_name)
    os.makedirs(game_dir, exist_ok=True)
    
    # Check if we already have files
    existing = os.listdir(game_dir) if os.path.isdir(game_dir) else []
    print(f"  Existing files: {len(existing)}")
    for f in existing:
        print(f"    - {f}")

print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)

total_files = 0
for game in sorted(os.listdir(OUTPUT_DIR)):
    game_dir = os.path.join(OUTPUT_DIR, game)
    if os.path.isdir(game_dir):
        files = os.listdir(game_dir)
        total_files += len(files)
        print(f"  {game}: {len(files)} files")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(game_dir, f))
            print(f"    - {f} ({size/1024:.1f} KB)")

print(f"\n  Total: {total_files} files in {OUTPUT_DIR}")
