#!/usr/bin/env python3
"""
Final attempt to get images for remaining 3 games.
Uses alphacoders image CDN, PlayStation Store, etc.
"""
import os
import requests

OUTPUT_DIR = "/home/node/.openclaw/workspace/game_images"

def download(url, filepath):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=20, stream=True)
        resp.raise_for_status()
        ct = resp.headers.get('content-type', '')
        if 'image' not in ct and ct:
            return False
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        size = os.path.getsize(filepath)
        if size < 2000:
            os.remove(filepath)
            return False
        print(f"    ✓ {os.path.basename(filepath)} ({size/1024:.1f} KB)")
        return True
    except Exception as e:
        print(f"    ✗ {e}")
        return False

def try_alphacoders(game_name, wallpaper_ids, game_dir):
    """Try alphacoders CDN: https://imagesN.alphacoders.com/XXX/XXXXX.jpg"""
    for wid in wallpaper_ids:
        prefix = str(wid)[:3]  # First 3 digits
        for server in range(1, 10):
            for ext in ['.jpg', '.png']:
                url = f"https://images{server}.alphacoders.com/{prefix}/{wid}{ext}"
                fp = os.path.join(game_dir, f"{game_name}_Gameplay_{len(os.listdir(game_dir))+1}.jpg")
                if download(url, fp):
                    return True
    return False

# === ASTRO BOT ===
print("=" * 60)
print("ASTRO BOT - alphacoders")
print("=" * 60)
astro_dir = os.path.join(OUTPUT_DIR, "Astro Bot")
os.makedirs(astro_dir, exist_ok=True)

# Wallpaper IDs for Astro Bot / Astro's Playroom (from alphacoders)
astro_ids = [1082646, 1082649, 1082647, 1082648, 1212258, 1212257, 1408378, 1403604, 953500, 1082639, 1212260]

for wid in astro_ids[:8]:  # Try first 8
    prefix = str(wid)[:3]
    for server in [6, 7, 8, 4, 5, 3, 2, 1]:
        for ext in ['.jpg', '.png', '.webp']:
            url = f"https://images{server}.alphacoders.com/{prefix}/{wid}{ext}"
            idx = len(os.listdir(astro_dir)) + 1
            fp = os.path.join(astro_dir, f"Astro Bot_Gameplay_{idx}.jpg")
            if download(url, fp):
                break
        else:
            continue
        break

# Also try poster from PlayStation Store style URL
ps_poster_urls = [
    "https://image.api.playstation.com/vulcan/ap/rnd/202409/0600/ea88b7ed20b66a9fa203c0400dca75c78c57abd673efbf9e.png",
    "https://image.api.playstation.com/vulcan/ap/rnd/202409/0600/1a8e3e1d5f7b9c0a2e4d6f8a0c2b4d6e8a0c2b4d6e.png",
]
for url in ps_poster_urls:
    fp = os.path.join(astro_dir, "Astro Bot_Poster.png")
    if download(url, fp):
        break

# === RESIDENT EVIL 9 ===
print("\n" + "=" * 60)
print("RESIDENT EVIL 9 - checking Steam/PS Store")
print("=" * 60)
re9_dir = os.path.join(OUTPUT_DIR, "Resident Evil 9")
os.makedirs(re9_dir, exist_ok=True)

# RE9: Requiem - check if it has a Steam page
# Try known RE games' IDs + newer range
for app_id in [2941790, 2941800, 2782190, 2782200, 2782210, 2941780]:
    poster_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg"
    fp = os.path.join(re9_dir, "Resident Evil 9_Poster.jpg")
    if download(poster_url, fp):
        print(f"    Found RE9 Steam App ID: {app_id}")
        # Get gameplay too
        api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        try:
            data = requests.get(api_url, timeout=10).json()
            app_data = data.get(str(app_id), {})
            if app_data.get('success'):
                name = app_data['data'].get('name', '')
                print(f"    Game: {name}")
                for i, ss in enumerate(app_data['data'].get('screenshots', [])[:5]):
                    ss_url = ss.get('path_full', '')
                    gp_fp = os.path.join(re9_dir, f"Resident Evil 9_Gameplay_{i+1}.jpg")
                    if ss_url:
                        download(ss_url, gp_fp)
        except:
            pass
        break

# Try PS Store or IGN
re9_alt_urls = [
    "https://sm.ign.com/ign_ap/news/r/resident-e/resident-evil-9-requiem-officially-revealed-summer-game-fest_bw6e.jpg",
    "https://assets1.ignimgs.com/2025/06/09/resident-evil-9-requiem-blogroll-1749473045830.jpg",
]
for i, url in enumerate(re9_alt_urls):
    fp = os.path.join(re9_dir, f"Resident Evil 9_Poster.jpg" if i == 0 else f"Resident Evil 9_Gameplay_{i}.jpg")
    download(url, fp)

# === UFC 5 ===
print("\n" + "=" * 60)
print("UFC 5 - EA / alphacoders")
print("=" * 60)
ufc_dir = os.path.join(OUTPUT_DIR, "UFC 5")
os.makedirs(ufc_dir, exist_ok=True)

# Try alphacoders UFC wallpaper IDs
ufc_ids = [516940, 1409287, 516941, 516942, 516943]

for wid in ufc_ids:
    prefix = str(wid)[:3]
    for server in [6, 7, 8, 4, 5, 3, 2, 1]:
        for ext in ['.jpg', '.png']:
            url = f"https://images{server}.alphacoders.com/{prefix}/{wid}{ext}"
            idx = len(os.listdir(ufc_dir)) + 1
            fp = os.path.join(ufc_dir, f"UFC 5_Gameplay_{idx}.jpg")
            if download(url, fp):
                break
        else:
            continue
        break

# Try EA website
ea_urls = [
    "https://media.contentapi.ea.com/content/dam/ea/easports/ufc/ufc-5/common/ufc-5-key-art.jpg",
    "https://media.contentapi.ea.com/content/dam/ea/easports/ufc/ufc-5/screenshots/ufc5-ss-1.jpg",
]
for i, url in enumerate(ea_urls):
    fp = os.path.join(ufc_dir, f"UFC 5_Poster.jpg" if i == 0 else f"UFC 5_Gameplay_{i}.jpg")
    download(url, fp)

# === FINAL SUMMARY ===
print("\n" + "=" * 60)
print("FINAL STATE OF ALL GAME IMAGES")
print("=" * 60)

total = 0
for game in sorted(os.listdir(OUTPUT_DIR)):
    game_dir = os.path.join(OUTPUT_DIR, game)
    if os.path.isdir(game_dir):
        files = sorted(os.listdir(game_dir))
        posters = [f for f in files if 'Poster' in f]
        gameplay = [f for f in files if 'Gameplay' in f]
        total += len(files)
        status = "✓" if posters and len(gameplay) >= 5 else "⚠"
        print(f"  {status} {game:<30} Poster: {'✓' if posters else '✗':<3} Gameplay: {len(gameplay):<3} Total: {len(files)}")
        for f in files:
            size = os.path.getsize(os.path.join(game_dir, f))
            print(f"      - {f} ({size/1024:.1f} KB)")

print(f"\n  Total files: {total}")
print(f"  Location: {OUTPUT_DIR}")
