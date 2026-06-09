#!/usr/bin/env python3
"""Fix remaining gspread fallbacks in set_game_disc_count."""
FILE = "/root/psvibe-sales-bot/bot/__init__.py"
with open(FILE) as f:
    code = f.read()

# Fix set_game_disc_count gspread fallback
old = (
    '        logging.warning("API call failed")\n'
    '    try:\n'
    '        sh = get_game_lib_sh()\n'
    '        # GSheet fallback: find row by game title\n'
    '        rows_b = sh.get("B:B")'
)
new = (
    '        logging.warning("API call failed")\n'
    '    return False\n'
    '    try:\n'
    '        sh = []\n'
    '        rows_b = sh'
)
if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    import py_compile
    py_compile.compile(FILE, doraise=True)
    print("OK")
else:
    print("NOT FOUND")
