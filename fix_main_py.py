import re

with open("/root/Aung Chan Myint/Sales-Tele-Bot/main.py", "r") as f:
    content = f.read()

# Fix tab characters in topup reads
content = content.replace('res[\topup_wave]', 'res["topup_wave"]')
content = content.replace('res[\topup_cb]', 'res["topup_cb"]')
content = content.replace('res[\topup_aya]', 'res["topup_aya"]')

# Check if sales_wave/cb/aya reads were added, if not add them
if 'sales_wave' not in content:
    # Add after the sales_cash += cash line
    content = content.replace(
        'res["sales_cash"] += cash',
        'res["sales_cash"] += cash\n            wave = _int(row[15]) if len(row) > 15 else 0\n            cb   = _int(row[16]) if len(row) > 16 else 0\n            aya  = _int(row[17]) if len(row) > 17 else 0\n            res["sales_wave"] += wave\n            res["sales_cb"]   += cb\n            res["sales_aya"]  += aya'
    )

with open("/root/Aung Chan Myint/Sales-Tele-Bot/main.py", "w") as f:
    f.write(content)

print("MAIN_FIX_DONE")
