import gspread, os, time
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/root/Aung Chan Myint/Sales-Tele-Bot/service_account.json", scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key("1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA")

# 1. Sales_Daily — Add Wave (L), CB Pay (M), AYA Pay (N)
sd = wb.worksheet("Sales_Daily")
hdr = sd.row_values(1)
print("Sales_Daily cols:", len(hdr), hdr)

if len(hdr) < 12 or not hdr[11]:
    sd.update_cell(1, 12, "Wave Money")
    print("Added: Wave Money (col L)")
if len(hdr) < 13 or not hdr[12]:
    sd.update_cell(1, 13, "CB Pay")
    print("Added: CB Pay (col M)")
if len(hdr) < 14 or not hdr[13]:
    sd.update_cell(1, 14, "AYA Pay")
    print("Added: AYA Pay (col N)")

# Fill existing rows with 0
all_rows = sd.get_all_values()
count = 0
for i, row in enumerate(all_rows[1:], start=2):
    updates = []
    if len(row) < 12 or row[11].strip() == "":
        updates.append((12, "0"))
    if len(row) < 13 or row[12].strip() == "":
        updates.append((13, "0"))
    if len(row) < 14 or row[13].strip() == "":
        updates.append((14, "0"))
    for col, val in updates:
        sd.update_cell(i, col, val)
        count += 1
print(f"Filled {count} cells across {len(all_rows)-1} rows")

# 2. TopUp_Log — Add Wave (H), CB Pay (I), AYA Pay (J)
tl = wb.worksheet("TopUp_Log")
hdr2 = tl.row_values(1)
print("TopUp_Log cols:", len(hdr2), hdr2)

if len(hdr2) < 8 or not hdr2[7]:
    tl.update_cell(1, 8, "Wave Money")
    print("Added: Wave Money (col H)")
if len(hdr2) < 9 or not hdr2[8]:
    tl.update_cell(1, 9, "CB Pay")
    print("Added: CB Pay (col I)")
if len(hdr2) < 10 or not hdr2[9]:
    tl.update_cell(1, 10, "AYA Pay")
    print("Added: AYA Pay (col J)")

# Fill existing TopUp_Log rows
all_rows2 = tl.get_all_values()
count2 = 0
for i, row in enumerate(all_rows2[1:], start=2):
    updates = []
    if len(row) < 8 or row[7].strip() == "":
        updates.append((8, "0"))
    if len(row) < 9 or row[8].strip() == "":
        updates.append((9, "0"))
    if len(row) < 10 or row[9].strip() == "":
        updates.append((10, "0"))
    for col, val in updates:
        tl.update_cell(i, col, val)
        count2 += 1
print(f"Filled {count2} cells across {len(all_rows2)-1} rows")

print("DONE")
