with open("/root/psvibe-sales-bot/bot/handlers/games.py") as f:
    content = f.read()

old = '                            if status == "Installed":\n                                cons_list.append(cid)\n                            elif status == "SSD Copy":\n                                ssd_list.append(f"{cid} ({status})")\n                            elif status == "Session":\n                                ssd_list.append(f"{cid} (Session)")\n                            # Skip entries with status "false" (not installed)'
new = '                            if status == "Installed":\n                                cons_list.append(cid)\n                            elif status in ("SSD Copy", "Moved"):\n                                ssd_list.append(f"{cid} ({status})")\n                            elif status == "Session":\n                                ssd_list.append(f"{cid} (Session)")\n                            # Skip entries with status "Not Installed"'

if old in content:
    content = content.replace(old, new)
    print("games.py: second instance fixed")
else:
    print("games.py: second instance NOT FOUND")

with open("/root/psvibe-sales-bot/bot/handlers/games.py", "w") as f:
    f.write(content)
