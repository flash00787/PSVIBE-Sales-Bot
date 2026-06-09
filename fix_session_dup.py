#!/usr/bin/env python3
"""Fix _show_game_detail: Session entries shown as duplicates in SSD list."""
FILE = "/root/psvibe-sales-bot/bot/handlers/games.py"
with open(FILE) as f:
    code = f.read()

old = """    cons_list = []
    ssd_list = []
    for r in cgames:"""

new = """    cons_list = []
    ssd_list = []
    session_list = []
    for r in cgames:"""

code = code.replace(old, new, 1)

old = """                elif status == "Session":
                    ssd_list.append(f"{SSD_NAMES.get(cid, cid)} (Session)")
                # Skip entries with status "Not Installed\""""

new = """                elif status == "Session":
                    session_list.append(f"{cid}")
                # Skip entries with status "Not Installed\""""

code = code.replace(old, new, 1)

old = """    if ssd_list:
        unique_ssd = sorted(set(ssd_list))
        info_lines.append(f"💾 <b>SSD တွင်ရှိသည်:</b> {', '.join(unique_ssd)}")
    else:
        info_lines.append("💾 <b>SSD:</b> <i>မရှိပါ</i>")"""

new = """    if ssd_list:
        unique_ssd = sorted(set(ssd_list))
        info_lines.append(f"💾 <b>SSD တွင်ရှိသည်:</b> {', '.join(unique_ssd)}")
    else:
        info_lines.append("💾 <b>SSD:</b> <i>မရှိပါ</i>")

    if session_list:
        unique_sessions = sorted(set(session_list))
        info_lines.append(f"⏱️ <b>Session ကစားဖူးသည်:</b> {', '.join(unique_sessions)}")"""

code = code.replace(old, new, 1)

with open(FILE, "w") as f:
    f.write(code)
import py_compile
py_compile.compile(FILE, doraise=True)
print("OK")
