#!/usr/bin/env python3
"""Test Google Sheets access from the service accounts."""
import os
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

def test_sa(sa_path, sheet_id, label):
    print(f"\n=== Testing {label} ===")
    print(f"  SA: {sa_path}")
    print(f"  Sheet ID: {sheet_id}")
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(sa_path, scope)
        gc = gspread.authorize(creds)
        wb = gc.open_by_key(sheet_id)
        print(f"  ✅ Connected: {wb.title}")
        # Try reading Card_Wallet
        try:
            ws = wb.worksheet("Card_Wallet")
            rows = ws.get_all_values()
            print(f"  ✅ Card_Wallet: {len(rows)} rows")
        except Exception as e:
            print(f"  ⚠️  Card_Wallet: {e}")
        # Try reading Setting
        try:
            ws = wb.worksheet("Setting")
            rows = ws.get_all_values()
            print(f"  ✅ Setting: {len(rows)} rows")
        except Exception as e:
            print(f"  ⚠️  Setting: {e}")
        return True
    except gspread.exceptions.APIError as e:
        code = e.response.status_code if hasattr(e, 'response') else '?'
        print(f"  ❌ API Error {code}: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

# Test 1: Sales Bot SA
sheet_id = os.environ.get("SHEET_ID", "1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA")

sa1 = "/root/psvibe_sales_bot/service_account.json"
sa2 = "/root/psvibe_api_server/service_account.json"

ok1 = test_sa(sa1, sheet_id, "Sales Bot SA → Main Staff Sheet")
ok2 = test_sa(sa2, sheet_id, "API Server SA → Main Staff Sheet")

# Test with additional Google Drive SA
sa3 = "/root/Sales-Tele-Bot/kora_drive_sa.json"
if os.path.exists(sa3):
    ps_vibe_drive_root = "1V6ctTJpXaoRIDnrfxwhVO72I7jfD5GsS"
    ok3 = test_sa(sa3, sheet_id, "Kora Drive SA → Main Staff Sheet")
else:
    print(f"\n  ⏭️  Kora Drive SA not found at {sa3}")

print("\n=== Summary ===")
if ok1 and ok2:
    print("✅ All service accounts can access the sheet!")
    sys.exit(0)
else:
    print("❌ Some tests failed!")
    sys.exit(1)
