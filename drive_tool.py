#!/usr/bin/env python3
"""
drive_tool.py — Full Google Drive Integration (OAuth-based)

Usage:
  python3 drive_tool.py upload <local_path> [--folder-id <id>] [--name <filename>]
  python3 drive_tool.py list [--folder-id <id>] [--recursive]
  python3 drive_tool.py mkdir <folder_name> [--parent-id <id>]
  python3 drive_tool.py share <file_id> [--role reader|writer]
  python3 drive_tool.py delete <file_id>
  python3 drive_tool.py search <query>

Uses token.json OAuth (drive.file scope) — works with My Drive.
"""
import json, os, sys, mimetypes, io, time, argparse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.json")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_creds():
    """Get OAuth credentials from token.json (auto-refresh)."""
    if not os.path.exists(TOKEN_PATH):
        print(f"❌ token.json not found at {TOKEN_PATH}")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save refreshed token
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    elif not creds or not creds.valid:
        print("❌ Token expired and cannot refresh")
        sys.exit(1)
    return creds


def get_service():
    return build("drive", "v3", credentials=get_creds())


def upload_file(local_path, folder_id=None, filename=None):
    """Upload a file to Drive. Returns file ID and web link."""
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        return None

    service = get_service()
    filename = filename or os.path.basename(local_path)
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Detect file type for folder routing
    ext = os.path.splitext(filename)[1].lower()
    name_lower = filename.lower()

    # If no folder specified, auto-route based on file type
    if not folder_id:
        if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            folder_id = "16lP68VxXGNqP6NPDfG0QlXxemlAhJzBL"  # Data For Game Menu
            print(f"📂 Auto-routed image → Data For Game Menu folder")
        elif "receipt" in name_lower or ext == ".pdf":
            print(f"📂 No auto-folder for receipt/PDF — upload to root")
        else:
            print(f"📂 No folder specified, uploading to root")

    file_metadata = {"name": filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name, size, webViewLink")
        .execute()
    )

    print(f"✅ Uploaded: {file['name']}")
    print(f"   ID: {file['id']}")
    print(f"   Size: {int(file.get('size', 0)) / 1024:.1f} KB")
    print(f"   Link: {file.get('webViewLink', 'N/A')}")
    return file["id"]


def list_files(folder_id="root", recursive=False):
    """List files in a folder."""
    service = get_service()
    page_token = None
    total = 0

    while True:
        query = f"'{folder_id}' in parents and trashed=false"
        results = (
            service.files()
            .list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, webViewLink)",
                pageSize=200,
                pageToken=page_token,
            )
            .execute()
        )
        files = results.get("files", [])
        for f in files:
            total += 1
            is_folder = f["mimeType"] == "application/vnd.google-apps.folder"
            size_str = ""
            if not is_folder and "size" in f:
                size_kb = int(f["size"]) / 1024
                size_str = f" ({size_kb:.1f} KB)" if size_kb < 1024 else f" ({size_kb/1024:.1f} MB)"
            prefix = "📁 " if is_folder else "📄 "
            print(f"  {prefix}{f['name']}{size_str}")
            print(f"     ID: {f['id']}")

            # Recursive listing for folders
            if recursive and is_folder:
                print(f"     ──── Inside {f['name']} ────")
                list_files(f["id"], recursive=False)
                print(f"     ──── End of {f['name']} ────")

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    print(f"\n📊 Total: {total} files")
    return total


def create_folder(name, parent_id=None):
    """Create a new folder in Drive."""
    service = get_service()
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = (
        service.files()
        .create(body=metadata, fields="id, name, webViewLink")
        .execute()
    )
    print(f"📁 Created folder: {folder['name']}")
    print(f"   ID: {folder['id']}")
    print(f"   Link: {folder.get('webViewLink', 'N/A')}")
    return folder["id"]


def share_file(file_id, role="reader"):
    """Create a shareable link for a file."""
    service = get_service()
    permission = {
        "type": "anyone",
        "role": role,
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

    # Get file metadata
    file = (
        service.files()
        .get(fileId=file_id, fields="id, name, webViewLink")
        .execute()
    )
    print(f"🔗 Shared: {file['name']}")
    print(f"   Role: {role}")
    print(f"   Link: {file.get('webViewLink', 'N/A')}")
    return file.get("webViewLink")


def delete_file(file_id):
    """Delete a file (move to trash)."""
    service = get_service()
    service.files().delete(fileId=file_id).execute()
    print(f"🗑️ Deleted file: {file_id}")


def search_files(query):
    """Search files by name or content."""
    service = get_service()
    results = (
        service.files()
        .list(
            q=f"name contains '{query}' and trashed=false",
            fields="files(id, name, mimeType, size, createdTime)",
            pageSize=50,
        )
        .execute()
    )
    files = results.get("files", [])
    if not files:
        print(f"🔍 No files found for '{query}'")
        return

    print(f"🔍 Search results for '{query}':")
    for f in files:
        is_folder = f["mimeType"] == "application/vnd.google-apps.folder"
        prefix = "📁 " if is_folder else "📄 "
        print(f"  {prefix}{f['name']} (ID: {f['id']})")


def main():
    parser = argparse.ArgumentParser(description="Google Drive Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Upload
    up = subparsers.add_parser("upload", help="Upload file to Drive")
    up.add_argument("path", help="Local file path")
    up.add_argument("--folder-id", help="Destination folder ID")
    up.add_argument("--name", help="Custom filename on Drive")

    # List
    ls = subparsers.add_parser("list", help="List files in folder")
    ls.add_argument("--folder-id", default="root", help="Folder ID (default: root)")
    ls.add_argument("--recursive", action="store_true", help="List subfolders")

    # Mkdir
    mk = subparsers.add_parser("mkdir", help="Create folder")
    mk.add_argument("name", help="Folder name")
    mk.add_argument("--parent-id", help="Parent folder ID")

    # Share
    sh = subparsers.add_parser("share", help="Create shareable link")
    sh.add_argument("file_id", help="File ID")
    sh.add_argument("--role", default="reader", choices=["reader", "writer"])

    # Delete
    dl = subparsers.add_parser("delete", help="Delete file")
    dl.add_argument("file_id", help="File ID")

    # Search
    sr = subparsers.add_parser("search", help="Search files")
    sr.add_argument("query", help="Search query")

    args = parser.parse_args()

    if args.command == "upload":
        upload_file(args.path, args.folder_id, args.name)
    elif args.command == "list":
        list_files(args.folder_id, args.recursive)
    elif args.command == "mkdir":
        create_folder(args.name, args.parent_id)
    elif args.command == "share":
        share_file(args.file_id, args.role)
    elif args.command == "delete":
        delete_file(args.file_id)
    elif args.command == "search":
        search_files(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
