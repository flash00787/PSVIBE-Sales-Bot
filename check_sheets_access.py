#!/usr/bin/env python3
"""
PS VIBE Sales Bot — Google Sheets Access Diagnostic

Tests the service account can access the configured Google Sheet,
lists all worksheets, and checks read access on each.

Usage:  python3 check_sheets_access.py

Exit codes:
  0 — All ok
  1 — Config / auth error
  2 — Permission denied (403)
  3 — Partial failure (some sheets inaccessible)
"""

import os
import sys
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("sheets_check")

# ────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────

def get_sa_email(sa_file: str = "service_account.json") -> str:
    """Extract the service account client_email."""
    try:
        with open(sa_file, "r") as f:
            data = json.load(f)
        return data.get("client_email", "unknown")
    except Exception as e:
        return f"ERROR reading {sa_file}: {e}"


def print_header(text: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}")


def print_ok(text: str) -> None:
    print(f"  ✅ {text}")


def print_warn(text: str) -> None:
    print(f"  ⚠️  {text}")


def print_err(text: str) -> None:
    print(f"  🔴 {text}")


# ────────────────────────────────────────
#  Main
# ────────────────────────────────────────

def main() -> int:
    print_header("PS VIBE — Google Sheets Access Diagnostic")

    # 1. Check environment
    print_header("1. Environment")
    sheet_id = os.environ.get("SHEET_ID", "")
    if not sheet_id:
        print_err("SHEET_ID env variable is NOT set!")
        return 1
    print_ok(f"SHEET_ID = {sheet_id}")

    # 2. Check service account file
    print_header("2. Service Account")
    sa_file = "service_account.json"
    if not os.path.exists(sa_file):
        print_err(f"service_account.json NOT FOUND at {os.getcwd()}/{sa_file}")
        return 1
    print_ok(f"Found: {sa_file}")

    sa_email = get_sa_email(sa_file)
    print(f"     Email: {sa_email}")

    # 3. Auth
    print_header("3. Google Auth")
    try:
        from oauth2client.service_account import ServiceAccountCredentials
        import gspread

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(sa_file, scope)
        gc = gspread.authorize(creds)
        print_ok("Authorized successfully")
    except Exception as e:
        print_err(f"Auth failed: {e}")
        return 1

    # 4. Open workbook
    print_header("4. Open Workbook")
    try:
        wb = gc.open_by_key(sheet_id)
        print_ok(f"Opened: {wb.title}")
    except Exception as e:
        status = getattr(e, 'response', None)
        code = status.status_code if status else 0
        if code == 403:
            msg = getattr(e, 'args', [''])[0] if hasattr(e, 'args') else str(e)
            print_err("403 FORBIDDEN — Permission Denied!")
            print()
            print(f"  The service account ({sa_email}) does NOT have access to this sheet.")
            print(f"  Sheet ID: {sheet_id}")
            print()
            print("  🔧 HOW TO FIX:")
            print(f"     1. Open the sheet in Google Sheets")
            print(f"     2. Click 'Share' (top-right)")
            print(f"     3. Add: {sa_email}")
            print(f"     4. Give 'Editor' access")
            print(f"     5. Click 'Send' / 'Done'")
            print()
            return 2
        print_err(f"Failed to open workbook: {e}")
        return 1

    # 5. List worksheets
    print_header("5. Worksheets")
    try:
        worksheets = wb.worksheets()
        print(f"     Found {len(worksheets)} worksheet(s):")
        for ws in worksheets:
            print(f"       · {ws.title} ({ws.row_count} rows × {ws.col_count} cols)")
        print_ok("Worksheets listed successfully")
    except Exception as e:
        print_err(f"Failed to list worksheets: {e}")
        return 3

    # 6. Read test each worksheet
    print_header("6. Read Access Check")
    all_ok = True
    for ws in worksheets:
        try:
            vals = ws.get_all_values()
            rows = len(vals)
            cols = max((len(r) for r in vals), default=0)
            print_ok(f"{ws.title}: {rows} rows × {cols} cols — READ OK")
        except Exception as e:
            print_err(f"{ws.title}: READ FAILED — {e}")
            all_ok = False

    # 7. Summary
    print_header("7. Summary")
    if all_ok:
        print_ok("ALL CHECKS PASSED — Sheets access is working correctly!")
        print(f"\n     Sheet:   {wb.title}")
        print(f"     SA:      {sa_email}")
        print(f"     Sheets:  {len(worksheets)} worksheets, all readable")
        return 0
    else:
        print_err("SOME CHECKS FAILED — See details above.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
