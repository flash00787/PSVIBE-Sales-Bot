import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "/root/Aung Chan Myint/Sales-Tele-Bot/service_account.json", scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key("1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA")

# 1. Sales_Daily — Headers at P(16), Q(17), R(18)
sd = wb.worksheet("Sales_Daily")
hdr = sd.row_values(1)
print("SD headers:", len(hdr))

# Force-write headers
sd.update_cell(1, 16, "Wave Money")
print("SD P16: Wave Money")
sd.update_cell(1, 17, "CB Pay")
print("SD Q17: CB Pay")
sd.update_cell(1, 18, "AYA Pay")
print("SD R18: AYA Pay")

# Fill existing rows
all_rows = sd.get_all_values()
count = 0
for i, row in enumerate(all_rows[1:], start=2):
    row_len = len(row)
    if row_len < 16 or not str(row[15]).strip():
        sd.update_cell(i, 16, "0")
        count += 1
    if row_len < 17 or not str(row[16]).strip():
        sd.update_cell(i, 17, "0")
        count += 1
    if row_len < 18 or not str(row[17]).strip():
        sd.update_cell(i, 18, "0")
        count += 1
print(f"SD filled {count} cells")

# 2. TopUp_Log — Headers at K(11), L(12), M(13)
tl = wb.worksheet("TopUp_Log")
hdr2 = tl.row_values(1)
print("TL headers:", len(hdr2))

tl.update_cell(1, 11, "Wave Money")
print("TL K11: Wave Money")
tl.update_cell(1, 12, "CB Pay")
print("TL L12: CB Pay")
tl.update_cell(1, 13, "AYA Pay")
print("TL M13: AYA Pay")

all_rows2 = tl.get_all_values()
count2 = 0
for i, row in enumerate(all_rows2[1:], start=2):
    row_len = len(row)
    if row_len < 11 or not str(row[10]).strip():
        tl.update_cell(i, 11, "0")
        count2 += 1
    if row_len < 12 or not str(row[11]).strip():
        tl.update_cell(i, 12, "0")
        count2 += 1
    if row_len < 13 or not str(row[12]).strip():
        tl.update_cell(i, 13, "0")
        count2 += 1
print(f"TL filled {count2} cells")

print("SHEETS DONE")
