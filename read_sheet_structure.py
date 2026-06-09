import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, json

# Use the same service account as V2
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name("/root/Sales-Tele-Bot_refactored/service_account.json", scope)
gc = gspread.authorize(creds)

sheet_id = os.environ.get("SHEET_ID", "1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA")
wb = gc.open_by_key(sheet_id)

print("=" * 60)
print("GOOGLE SHEET STRUCTURE")
print("Sheet ID:", sheet_id)
print("=" * 60)

worksheets = wb.worksheets()
print(f"\n📊 Total worksheets: {len(worksheets)}")
print("-" * 40)

for ws in worksheets:
    title = ws.title
    try:
        # Get first 3 rows to understand columns
        sample = ws.get_all_values(max_rows=3)
        if sample and len(sample) > 0:
            header = sample[0]
            col_count = len(header)
            row_count = len(ws.get_all_values())
            print(f"\n📋 {title}")
            print(f"   Rows: {row_count} | Columns: {col_count}")
            print(f"   Headers: {header[:20]}{'...' if col_count > 20 else ''}")
            if len(sample) > 1:
                print(f"   Row 1: {sample[1][:10]}{'...' if len(sample[1]) > 10 else ''}")
                print(f"   Row 2: {sample[2][:10]}{'...' if len(sample[2]) > 10 else ''}")
    except Exception as e:
        print(f"\n📋 {title}")
        print(f"   ❌ Error reading: {str(e)[:100]}")
