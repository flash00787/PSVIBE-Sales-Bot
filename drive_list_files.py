#!/usr/bin/env python3
"""List all files in 'Data For Game Menu' Google Drive folder using service account."""
import json
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "/tmp/service_account.json"
FOLDER_NAME = "Data For Game Menu"

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def find_folder(service, name):
    """Find folder by name."""
    results = service.files().list(
        q=f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)",
        pageSize=10
    ).execute()
    folders = results.get('files', [])
    return folders[0] if folders else None

def list_all_files(service, folder_id):
    """List all files in a folder recursively."""
    files = []
    page_token = None
    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, size, createdTime)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        files.extend(results.get('files', []))
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return files

def main():
    service = get_drive_service()
    
    # Find the folder
    folder = find_folder(service, FOLDER_NAME)
    if not folder:
        print(f"ERROR: Folder '{FOLDER_NAME}' not found!")
        # Try listing all root-level folders
        print("\nTop-level folders:")
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            pageSize=50
        ).execute()
        for f in results.get('files', []):
            print(f"  - {f['name']} (id: {f['id']})")
        return
    
    print(f"Found folder: '{folder['name']}' (id: {folder['id']})")
    folder_id = folder['id']
    
    # List all files
    files = list_all_files(service, folder_id)
    print(f"\nTotal files in folder: {len(files)}")
    
    # Categorize files
    games_map = {}  # game_name -> {poster: [files], gameplay: [files]}
    
    for f in files:
        name = f['name']
        # Try to extract game name from filename
        # Expected formats: "Game Name - Poster.jpg", "Game Name - Gameplay 1.jpg", etc.
        parts = name.rsplit('.', 1)
        stem = parts[0] if len(parts) > 1 else name
        
        if ' - Poster' in stem or ' - poster' in stem.lower():
            game = stem.split(' - Poster')[0].strip()
            games_map.setdefault(game, {'poster': [], 'gameplay': []})
            games_map[game]['poster'].append(f)
        elif ' - Gameplay' in stem or ' - gameplay' in stem.lower() or ' - screenshot' in stem.lower():
            # Extract game name before " - Gameplay"
            for sep in [' - Gameplay', ' - gameplay', ' - screenshot', ' - Screenshot']:
                if sep in stem:
                    game = stem.split(sep)[0].strip()
                    break
            else:
                game = stem
            games_map.setdefault(game, {'poster': [], 'gameplay': []})
            games_map[game]['gameplay'].append(f)
        else:
            print(f"  UNKNOWN format: {name}")
    
    print(f"\nGames with files in Drive:")
    print(f"{'Game':<35} {'Poster':<8} {'Gameplay':<10} {'Total'}")
    print("-" * 65)
    for game in sorted(games_map.keys()):
        g = games_map[game]
        print(f"{game:<35} {'YES' if g['poster'] else 'NO':<8} {len(g['gameplay']):<10} {len(g['poster'])+len(g['gameplay'])}")
    
    # Save to JSON for later use
    output = {
        'folder_id': folder_id,
        'folder_name': folder['name'],
        'total_files': len(files),
        'games': {}
    }
    for game, data in games_map.items():
        output['games'][game] = {
            'has_poster': bool(data['poster']),
            'gameplay_count': len(data['gameplay']),
            'poster_files': [f['name'] for f in data['poster']],
            'gameplay_files': [f['name'] for f in data['gameplay']],
            'poster_ids': [f['id'] for f in data['poster']],
            'gameplay_ids': [f['id'] for f in data['gameplay']]
        }
    
    with open('/home/node/.openclaw/workspace/drive_contents.json', 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved detailed report to drive_contents.json")
    
    # Also save all files raw
    all_files_data = []
    for f in files:
        all_files_data.append({
            'id': f['id'],
            'name': f['name'],
            'mime_type': f.get('mimeType', ''),
            'size': f.get('size', '0'),
            'created': f.get('createdTime', '')
        })
    
    with open('/home/node/.openclaw/workspace/drive_all_files.json', 'w') as f:
        json.dump(all_files_data, f, indent=2)

if __name__ == '__main__':
    main()
