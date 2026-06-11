#!/usr/bin/env python3
"""
Download ALL missing images for the 7 incomplete games.
Save them locally organized. Try to upload via alternative method.
"""
import json
import os
import time
import requests
import subprocess

OUTPUT_DIR = "/home/node/.openclaw/workspace/game_images"

# Game -> Steam App ID
STEAM_GAMES = {
    "Naruto x Boruto": 1971870,
    "LEGO:StarWars": 920210,
    "Rise of Ronnin": 2790220,
}

NON_STEAM_GAMES = {
    "WWE 2025": {
        "search_terms": ["WWE 2K25", "WWE 2025 game"],
        "ps_store_id": None,
    },
    "Resident Evil 9": {
        "search_terms": ["Resident Evil 9", "Resident Evil IX game"],
        "ps_store_id": None,
    },
    "UFC 5": {
        "search_terms": ["EA Sports UFC 5", "UFC 5 game PS5"],
        "ps_store_id": None,
    },
    "Astro Bot": {
        "search_terms": ["Astro Bot PS5", "Astro Bot game 2024"],
        "ps_store_id": None,
    },
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        if size < 1000:  # Too small
            os.remove(filepath)
            print(f"    Too small ({size} bytes), skipped")
            return False
        
        print(f"    ✓ {os.path.basename(filepath)} ({size/1024:.1f} KB)")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def get_steam_data(app_id):
    """Get game data from Steam API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        app_data = data.get(str(app_id), {})
        if app_data.get('success'):
            return app_data['data']
        return None
    except:
        return None

def download_steam_game(game_name, app_id, game_dir):
    """Download poster + 5 gameplay for a Steam game."""
    print(f"\n{'='*50}")
    print(f"Steam: {game_name} (App ID: {app_id})")
    
    game_dir = os.path.join(OUTPUT_DIR, game_name)
    os.makedirs(game_dir, exist_ok=True)
    
    results = {'poster': False, 'gameplay': 0}
    
    # Poster
    print("  Poster:")
    poster_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg"
    poster_path = os.path.join(game_dir, f"{game_name}_Poster.jpg")
    if download_image(poster_url, poster_path):
        results['poster'] = True
    
    # Gameplay
    print("  Gameplay:")
    game_data = get_steam_data(app_id)
    if game_data:
        screenshots = game_data.get('screenshots', [])
        for i, ss in enumerate(screenshots[:5]):
            ss_url = ss.get('path_full', '')
            if ss_url:
                gp_path = os.path.join(game_dir, f"{game_name}_Gameplay_{i+1}.jpg")
                if download_image(ss_url, gp_path):
                    results['gameplay'] += 1
        
        # If Steam API returned fewer than 5, try alternate posters
        if results['gameplay'] < 5:
            print(f"  Only got {results['gameplay']}/5 from Steam API, checking movie screenshots...")
            movies = game_data.get('movies', [])
            # Can't easily get movie thumbnails via API alone
    else:
        print(f"  Steam API failed for {game_name}")
    
    return results

def download_nonsteam_game(game_name, game_dir):
    """Try various sources for non-Steam games."""
    print(f"\n{'='*50}")
    print(f"Non-Steam: {game_name}")
    
    game_dir = os.path.join(OUTPUT_DIR, game_name)
    os.makedirs(game_dir, exist_ok=True)
    
    results = {'poster': False, 'gameplay': 0}
    
    # Try IGDB / GiantBomb / PlayStation Store
    # For now, use web search to find image URLs
    search_query = game_name.replace(' ', '+') + "+game+wallpaper"
    
    # Try steamgriddb for posters
    # Try IGDB for gameplay
    # These typically need API keys
    
    # Let's try direct known URLs for some games
    if game_name == "WWE 2025":
        # Try WWE 2K25 images
        urls_to_try = [
            "https://cdn.akamai.steamstatic.com/steam/apps/2623420/header.jpg",  # WWE 2K25 header
        ]
        print("  Trying WWE 2K25 Steam images...")
        # WWE 2K25 app ID is 2623420
        wwe_data = get_steam_data(2623420)
        if wwe_data:
            # Poster
            poster_url = f"https://cdn.akamai.steamstatic.com/steam/apps/2623420/library_600x900_2x.jpg"
            poster_path = os.path.join(game_dir, f"{game_name}_Poster.jpg")
            if download_image(poster_url, poster_path):
                results['poster'] = True
            
            # Gameplay
            screenshots = wwe_data.get('screenshots', [])
            for i, ss in enumerate(screenshots[:5]):
                ss_url = ss.get('path_full', '')
                if ss_url:
                    gp_path = os.path.join(game_dir, f"{game_name}_Gameplay_{i+1}.jpg")
                    if download_image(ss_url, gp_path):
                        results['gameplay'] += 1
    
    elif game_name == "UFC 5":
        # EA Sports UFC 5 - not on Steam but maybe we can get images from EA
        print("  Trying to find UFC 5 images...")
        # UFC 5 might not be available
    
    elif game_name == "Astro Bot":
        # Astro Bot - PS5 exclusive
        print("  Trying to find Astro Bot images...")
        # Try PlayStation Blog / Store
        astro_urls = [
            "https://image.api.playstation.com/vulcan/ap/rnd/202405/2816/ea88b7ed20b66a9fa203c0400dca75c78c57abd673efbf9e.png",
        ]
        for i, url in enumerate(astro_urls):
            fp = os.path.join(game_dir, f"{game_name}_Poster.jpg")
            if download_image(url, fp):
                results['poster'] = True
                break
    
    elif game_name == "Resident Evil 9":
        # Not released yet - try to find teaser/trailer images
        print("  Resident Evil 9 is not yet released. Limited images available.")
        # Try RE Village or RE4 remake images as placeholder
        # RE9 might have teaser images
    
    return results

def main():
    all_results = {}
    
    # 1. Steam games
    for game_name, app_id in STEAM_GAMES.items():
        game_dir = os.path.join(OUTPUT_DIR, game_name)
        os.makedirs(game_dir, exist_ok=True)
        result = download_steam_game(game_name, app_id, game_dir)
        all_results[game_name] = result
        time.sleep(0.3)
    
    # 2. Non-Steam games
    for game_name in NON_STEAM_GAMES:
        game_dir = os.path.join(OUTPUT_DIR, game_name)
        os.makedirs(game_dir, exist_ok=True)
        result = download_nonsteam_game(game_name, game_dir)
        all_results[game_name] = result
        time.sleep(0.3)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"DOWNLOAD SUMMARY:")
    print(f"{'='*60}")
    total_posters = 0
    total_gameplay = 0
    
    for game_name, result in all_results.items():
        poster_icon = "✓" if result['poster'] else "✗"
        print(f"  {game_name:<30} Poster: {poster_icon}  Gameplay: {result['gameplay']}/5")
        total_posters += 1 if result['poster'] else 0
        total_gameplay += result['gameplay']
    
    print(f"\n  Total: {total_posters} posters, {total_gameplay} gameplay images")
    
    # Save manifest
    manifest = {
        'output_dir': OUTPUT_DIR,
        'results': all_results,
        'total_posters': total_posters,
        'total_gameplay': total_gameplay,
    }
    
    with open(os.path.join(OUTPUT_DIR, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # List files
    print(f"\nFiles downloaded to: {OUTPUT_DIR}")
    for game in sorted(all_results.keys()):
        game_dir = os.path.join(OUTPUT_DIR, game)
        if os.path.isdir(game_dir):
            files = os.listdir(game_dir)
            print(f"  {game}/: {len(files)} files")
            for f in sorted(files):
                size = os.path.getsize(os.path.join(game_dir, f))
                print(f"    - {f} ({size/1024:.1f} KB)")

if __name__ == '__main__':
    main()
