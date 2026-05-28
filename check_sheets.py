import sys; sys.path.insert(0,'/root/psvibe_api_server')
from sheets_client import get_worksheet
from config import SHEET_SALES_DAILY, SHEET_TOPUP_LOG
ws = get_worksheet(SHEET_SALES_DAILY)
rows = ws.get_all_values()
print('=== Sales_Daily ===')
print(f'Rows: {len(rows)}')
if rows:
    print(f'Header: {rows[0][:25]}')
    for i in range(1, min(5, len(rows))):
        print(f'Row {i}: {rows[i][:25]}')
ws2 = get_worksheet(SHEET_TOPUP_LOG)
rows2 = ws2.get_all_values()
print('=== TopUp_Log ===')
print(f'Rows: {len(rows2)}')
if rows2:
    print(f'Header: {rows2[0][:15]}')
    for i in range(1, min(5, len(rows2))):
        print(f'Row {i}: {rows2[i][:15]}')
