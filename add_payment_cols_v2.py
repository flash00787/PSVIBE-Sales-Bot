import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "/root/Aung Chan Myint/Sales-Tele-Bot/service_account.json", scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key("1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA")

# 1. Sales_Daily — Add Wave (P), CB Pay (Q), AYA Pay (R)
sd = wb.worksheet("Sales_Daily")
hdr = sd.row_values(1)
print("Sales_Daily cols:", len(hdr))

# Insert new columns after Staff (col O = index 15)
# Using insert_cols approach - add columns at the end and rename headers
current_max = sd.col_count
print(f"Current max col: {current_max}")

# Add headers for new payment columns
if current_max < 16:
    sd.update_cell(1, 16, "Wave Money")
    print("Added: Wave Money (P)")
if current_max < 17:
    sd.update_cell(1, 17, "CB Pay")
    print("Added: CB Pay (Q)")
if current_max < 18:
    sd.update_cell(1, 18, "AYA Pay")
    print("Added: AYA Pay (R)")

# Fill existing rows with 0
all_rows = sd.get_all_values()
count = 0
for i, row in enumerate(all_rows[1:], start=2):
    row_len = len(row)
    if row_len < 16 or row[15].strip() == "":
        sd.update_cell(i, 16, "0")
        count += 1
    if row_len < 17 or row[16].strip() == "":
        sd.update_cell(i, 17, "0")
        count += 1
    if row_len < 18 or row[17].strip() == "":
        sd.update_cell(i, 18, "0")
        count += 1
print(f"Sales_Daily: filled {count} cells")

# 2. TopUp_Log — Add Wave (K), CB Pay (L), AYA Pay (M)
tl = wb.worksheet("TopUp_Log")
hdr2 = tl.row_values(1)
print("TopUp_Log cols:", len(hdr2))

current_max2 = tl.col_count
if current_max2 < 11:
    tl.update_cell(1, 11, "Wave Money")
    print("Added: Wave Money (K)")
if current_max2 < 12:
    tl.update_cell(1, 12, "CB Pay")
    print("Added: CB Pay (L)")
if current_max2 < 13:
    tl.update_cell(1, 13, "AYA Pay")
    print("Added: AYA Pay (M)")

all_rows2 = tl.get_all_values()
count2 = 0
for i, row in enumerate(all_rows2[1:], start=2):
    row_len = len(row)
    if row_len < 11 or row[10].strip() == "":
        tl.update_cell(i, 11, "0")
        count2 += 1
    if row_len < 12 or row[11].strip() == "":
        tl.update_cell(i, 12, "0")
        count2 += 1
    if row_len < 13 or row[12].strip() == "":
        tl.update_cell(i, 13, "0")
        count2 += 1
print(f"TopUp_Log: filled {count2} cells")

print("SHEETS DONE")
