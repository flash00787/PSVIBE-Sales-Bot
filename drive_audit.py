#!/usr/bin/env python3
"""Audit 'Data For Game Menu' folder and all game subfolders."""
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "/home/node/.openclaw/workspace/service-account.json"
DATA_FOR_GAME_MENU_ID = "16lP68VxXGNqP6NPDfG0QlXxemlAhJzBL"

# The 37 games list
ALL_GAMES = [
    "GTA 5", "Tekken 8", "Devil May Cry 5", "Mortal Kombat", "Elden Ring",
    "Horizon Forbidden West", "Red Dead Redemption 2", "God of War Ragnarok",
    "Witcher 3", "Batman Arkham Knight", "Hades", "Hitman", "Injustice 2",
    "It Takes Two", "BlackMyth Wukong", "Dragon Ball Sparking Zero",
    "Ghost of Tsushima", "CRIMSON DESERT", "WWE 2025", "Spider-Man 2",
    "Ghost of Yotei", "Resident Evil 9", "Assassin's Creed Shadows",
    "Last of Us Part 2", "Minecraft", "SUICIDE SQUAD", "Spiderman",
    "UFC 5", "Rise of Ronnin", "Sprit Fiction", "Naruto x Boruto",
    "LEGO:StarWars", "Gran Turismo 7", "Reanimal", "Silent Hill",
    "Astro Bot", "INVINCIBLE VS"
]

# Map folder names to canonical names (folders use slightly different names)
FOLDER_TO_CANONICAL = {
    "GTA 5": "GTA 5",
    "Tekken 8": "Tekken 8",
    "Devil May Cry 5": "Devil May Cry 5",
    "Mortal Kombat": "Mortal Kombat",
    "Elder Ring": "Elden Ring",
    "Horizontal Forbidden West": "Horizon Forbidden West",
    "Red Dead Redemption 2": "Red Dead Redemption 2",
    "God Of War Ragnarok": "God of War Ragnarok",
    "Witcher 3": "Witcher 3",
    "Batman Arkham Knight": "Batman Arkham Knight",
    "Hades": "Hades",
    "Hitman": "Hitman",
    "Injustice 2": "Injustice 2",
    "It Takes two": "It Takes Two",
    "BlackMyth Wukong": "BlackMyth Wukong",
    "Dragon Ball Sparking Zero": "Dragon Ball Sparking Zero",
    "Ghost of Tsushima": "Ghost of Tsushima",
    "CRIMSON DESERT": "CRIMSON DESERT",
    "WWE 2025": "WWE 2025",
    "Spider Man - 2": "Spider-Man 2",
    "Ghost of Yotei": "Ghost of Yotei",
    "Resident Evil 9": "Resident Evil 9",
    "Assassian Creeds Shadow": "Assassin's Creed Shadows",
    "Last of Us part 2 Remastered": "Last of Us Part 2",
    "Minecraft": "Minecraft",
    "SUICIDE SQUAD": "SUICIDE SQUAD",
    "Spiderman": "Spiderman",
    "UFC 5": "UFC 5",
    "Rise of Ronnin": "Rise of Ronnin",
    "Sprit Fiction": "Sprit Fiction",
    "Naruto x Boruto ultimate": "Naruto x Boruto",
    "LEGO-StarWars": "LEGO:StarWars",
    "Gran Turismo 7": "Gran Turismo 7",
    "Reanimal": "Reanimal",
    "Sillent Hill": "Silent Hill",
    "Astro Bot": "Astro Bot",
    "INVINCIBLE VS": "INVINCIBLE VS",
    # Unreleased
    "Basketball 2026": "Basketball 2026 (unreleased)",
    "Expedition 33": "Expedition 33 (unreleased)",
    "Fifa 2026": "FIFA 2026 (unreleased)",
    "Little Nightmare 3": "Little Nightmare 3 (unreleased)",
}

def get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def list_folder_contents(service, folder_id, folder_name="root"):
    """List all files in a folder."""
    files = []
    page_token = None
    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        files.extend(results.get('files', []))
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return files

def main():
    service = get_service()
    
    # 1. Check Data For Game Menu folder
    print("=" * 80)
    print("Data For Game Menu folder contents:")
    print("=" * 80)
    menu_files = list_folder_contents(service, DATA_FOR_GAME_MENU_ID, "Data For Game Menu")
    print(f"Total files: {len(menu_files)}")
    for f in sorted(menu_files, key=lambda x: x['name']):
        size_kb = int(f.get('size', 0)) / 1024
        print(f"  {f['name']} ({size_kb:.1f} KB)")
    
    if not menu_files:
        print("  (EMPTY - all files were deleted!)")
    
    # 2. Check all game folders
    print("\n" + "=" * 80)
    print("Per-game folder audit:")
    print("=" * 80)
    
    game_status = {}
    
    for folder_name, canonical_name in sorted(FOLDER_TO_CANONICAL.items()):
        # Find folder by name
        results = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            pageSize=5
        ).execute()
        folders = results.get('files', [])
        
        if not folders:
            game_status[canonical_name] = {'folder_exists': False, 'files': []}
            continue
        
        fid = folders[0]['id']
        files = list_folder_contents(service, fid, folder_name)
        game_status[canonical_name] = {
            'folder_exists': True,
            'folder_id': fid,
            'files': files
        }
    
    # Print summary
    print(f"\n{'Game':<35} {'Folder':<8} {'Poster':<8} {'Gameplay':<10} {'Total'}")
    print("-" * 75)
    
    missing_games = []
    incomplete_games = []
    
    for canonical_name in ALL_GAMES:
        # Find matching folder
        matched = None
        matched_key = None
        for folder_name, cn in FOLDER_TO_CANONICAL.items():
            if cn == canonical_name:
                matched = game_status.get(cn)
                matched_key = cn
                break
        
        if matched is None or not matched.get('folder_exists'):
            print(f"{canonical_name:<35} {'NO':<8} {'-':<8} {'-':<10} -")
            missing_games.append(canonical_name)
            continue
        
        files = matched['files']
        has_poster = any('Poster' in f['name'] or 'poster' in f['name'].lower() for f in files)
        gameplay_count = sum(1 for f in files if 'Gameplay' in f['name'] or 'gameplay' in f['name'].lower())
        total = len(files)
        
        status = "✓"
        if not has_poster:
            status = "NO POSTER"
            incomplete_games.append(canonical_name)
        if gameplay_count < 5:
            status = f"{gameplay_count}/5 GP"
            incomplete_games.append(canonical_name)
        
        print(f"{canonical_name:<35} {'YES':<8} {'YES' if has_poster else 'NO':<8} {gameplay_count:<10} {total}  {status}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Missing entirely (no folder): {len(missing_games)}")
    for g in missing_games:
        print(f"    - {g}")
    print(f"  Incomplete (missing poster or <5 gameplay): {len(incomplete_games)}")
    for g in incomplete_games:
        print(f"    - {g}")
    
    # Save to JSON
    report = {
        'data_for_game_menu_files': [{'name': f['name'], 'id': f['id'], 'size': f.get('size')} for f in menu_files],
        'game_status': {k: {'folder_exists': v.get('folder_exists', False), 'file_count': len(v.get('files', []))} for k, v in game_status.items()},
        'missing_games': missing_games,
        'incomplete_games': incomplete_games
    }
    
    with open('/home/node/.openclaw/workspace/audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved detailed report to audit_report.json")

if __name__ == '__main__':
    main()
