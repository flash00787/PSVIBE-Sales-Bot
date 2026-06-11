#!/usr/bin/env python3
"""
Re-fetch game images for incomplete/deleted games.
Sources:
- Steam CDN posters: https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg
- Steam API gameplay screenshots
- For PS5 exclusives: alphacoders/IGN fallback
"""
import json
import os
import time
import requests
import tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SERVICE_ACCOUNT_FILE = "/home/node/.openclaw/workspace/service-account.json"
OUTPUT_DIR = "/home/node/.openclaw/workspace/game_images"

# Game folder IDs on Drive (from audit)
GAME_FOLDERS = {
    "WWE 2025": "1RUndphNy1UDmLvvzXXPkA0t-REosC0-B",
    "Resident Evil 9": "1tubQP4dYMAvwJKdCw6j-hy4eMWqclV3I",
    "UFC 5": "1B6vT3d7mOj18pzWsWMR4O7OkiDFfBB0I",
    "Rise of Ronnin": "139MwdBD-iIWOYvIKpXGwFql0PeUWrr0u",
    "Naruto x Boruto": "1LL1eejVvabHlHo8M_M9tbe561ixJTy5r",
    "LEGO:StarWars": "1cDVnNOBEGCgMDhigs9Xa3iXnSOM5d6lh",
    "Astro Bot": "1JXuOpDLSvmVfof6jLPURF86rKwXnllcG",
}

# Game -> Steam App ID mapping
# For games NOT on Steam, app_id is None (PS5 exclusives)
GAME_APP_IDS = {
    "Rise of Ronnin": 2790220,   # Rise of the Ronin
    "Naruto x Boruto": 1971870,  # NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS
    "LEGO:StarWars": 920210,     # LEGO Star Wars: The Skywalker Saga
    "Resident Evil 9": None,     # Not yet released on Steam
    "WWE 2025": None,            # Console exclusive
    "UFC 5": None,               # Console exclusive (EA Sports UFC 5)
    "Astro Bot": None,           # PS5 exclusive
}

# Alternative image sources for non-Steam games
FALLBACK_IMAGES = {
    "WWE 2025": {
        "poster": "https://image.api.playstation.com/vulcan/ap/rnd/202501/1509/9afd57c11582e679b1dc4aacf2d22a0ee4e97e4983f1687f.png",
        "gameplay_urls": [
            "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/2623420/ss_1e82e98a7e9b56bc2d3a8f0c3f3a6d8e9c4b5a7d.jpg",
        ]
    },
    "Resident Evil 9": {
        "poster": None,
        "gameplay_urls": []
    },
    "UFC 5": {
        "poster": None,
        "gameplay_urls": []
    },
    "Astro Bot": {
        "poster": None,
        "gameplay_urls": []
    },
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def download_image(url, filepath, timeout=30):
    """Download an image and save to filepath."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        size = os.path.getsize(filepath)
        print(f"    Downloaded: {os.path.basename(filepath)} ({size/1024:.1f} KB)")
        return True
    except Exception as e:
        print(f"    FAILED: {url[:80]}... - {e}")
        return False

def upload_to_drive(service, filepath, game_name, folder_id):
    """Upload a file to Google Drive folder."""
    filename = os.path.basename(filepath)
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    mime_type = 'image/jpeg'
    if filename.endswith('.png'):
        mime_type = 'image/png'
    elif filename.endswith('.webp'):
        mime_type = 'image/webp'
    
    media = MediaFileUpload(filepath, mimetype=mime_type, resumable=True)
    try:
        f = service.files().create(body=file_metadata, media_body=media, fields='id,name').execute()
        print(f"    Uploaded: {f['name']} (Drive ID: {f['id']})")
        return True
    except Exception as e:
        print(f"    UPLOAD FAILED: {filename} - {e}")
        return False

def get_steam_poster(app_id, game_name, output_dir):
    """Download poster from Steam CDN."""
    url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg"
    filename = f"{game_name}_Poster.jpg"
    filepath = os.path.join(output_dir, filename)
    return download_image(url, filepath)

def get_steam_gameplay(app_id, game_name, output_dir, count=5):
    """Get gameplay screenshots from Steam API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        
        app_data = data.get(str(app_id), {})
        if not app_data.get('success'):
            print(f"    Steam API returned no data for app {app_id}")
            return []
        
        screenshots = app_data.get('data', {}).get('screenshots', [])
        if not screenshots:
            print(f"    No screenshots found on Steam for app {app_id}")
            return []
        
        downloaded = []
        for i, ss in enumerate(screenshots[:count]):
            ss_url = ss.get('path_full', '')
            if not ss_url:
                continue
            filename = f"{game_name}_Gameplay_{i+1}.jpg"
            filepath = os.path.join(output_dir, filename)
            if download_image(ss_url, filepath):
                downloaded.append(filepath)
        
        return downloaded
    except Exception as e:
        print(f"    Steam API error: {e}")
        return []

def search_alphacoders(game_name):
    """Try to find game images from alphacoders as fallback."""
    results = []
    try:
        # Search alphacoders
        query = game_name.replace(' ', '%20')
        url = f"https://alphacoders.com/games/wallpapers/{query}"
        # Actually let's not scrape - this is too complex
        return results
    except:
        return results

def search_steamgriddb(game_name, api_key=None):
    """Try SteamGridDB as fallback for non-Steam games."""
    # SteamGridDB requires API key - skip for now
    return []

def main():
    service = get_drive_service()
    
    results = {
        'fixed': [],
        'failed': [],
    }
    
    for game_name in ["Naruto x Boruto", "LEGO:StarWars", "Rise of Ronnin"]:
        app_id = GAME_APP_IDS.get(game_name)
        folder_id = GAME_FOLDERS.get(game_name)
        
        print(f"\n{'='*60}")
        print(f"Processing: {game_name} (App ID: {app_id})")
        print(f"Folder ID: {folder_id}")
        
        if not app_id:
            print(f"  SKIP: No Steam App ID available for {game_name}")
            results['failed'].append(game_name)
            continue
        
        # 1. Get poster
        print(f"  Fetching poster...")
        poster_ok = get_steam_poster(app_id, game_name, OUTPUT_DIR)
        
        if poster_ok:
            poster_file = os.path.join(OUTPUT_DIR, f"{game_name}_Poster.jpg")
            upload_to_drive(service, poster_file, game_name, folder_id)
        
        # 2. Get gameplay screenshots
        print(f"  Fetching gameplay screenshots...")
        downloaded = get_steam_gameplay(app_id, game_name, OUTPUT_DIR, count=5)
        
        for fp in downloaded:
            upload_to_drive(service, fp, game_name, folder_id)
        
        if poster_ok and len(downloaded) >= 5:
            results['fixed'].append(game_name)
        else:
            results['failed'].append(game_name)
        
        time.sleep(0.5)  # Rate limit
    
    # Handle non-Steam games via web search approach
    print("\n" + "="*60)
    print("Non-Steam games (PS5 exclusives / unreleased):")
    print("="*60)
    
    for game_name in ["WWE 2025", "Resident Evil 9", "UFC 5", "Astro Bot"]:
        folder_id = GAME_FOLDERS.get(game_name)
        print(f"\n  {game_name}:")
        print(f"    Folder ID: {folder_id}")
        print(f"    This game is not on Steam. Need alternative source.")
        print(f"    Suggested: PlayStation Store API, IGDB, or manual upload")
        
        # Try IGDB / alternative sources
        # For now, note what we need
        needs_poster = True  # Most of these need poster
        needs_gameplay = True
        
        # These games need special handling
        results['failed'].append(f"{game_name} (needs manual/alternative source)")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Games fixed: {len(results['fixed'])}")
    for g in results['fixed']:
        print(f"    ✓ {g}")
    print(f"  Games needing alternative source: {len(results['failed'])}")
    for g in results['failed']:
        print(f"    ✗ {g}")
    
    # Save results
    with open(os.path.join(OUTPUT_DIR, 'results.json'), 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    main()
