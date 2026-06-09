#!/usr/bin/env python3
"""Fix ginst.py back button: console menu not game library."""
FILE = "/root/psvibe-sales-bot/bot/handlers/ginst.py"
with open(FILE) as f:
    code = f.read()

# Add show_console_menu to imports
code = code.replace(
    "show_game_menu, update_game_library_install_async,",
    "show_game_menu, show_console_menu, update_game_library_install_async,",
)

# Change Back in step_ginst_menu from show_game_menu to show_console_menu
code = code.replace(
    "        return await show_game_menu(update, context)\n    if text == BTN_GINST_VIEW:",
    "        return await show_console_menu(update, context)\n    if text == BTN_GINST_VIEW:",
)

# Remove the redundant local import  
code = code.replace(
    "    from bot.handlers.games import show_game_menu\n    text = update.message.text.strip()",
    "    text = update.message.text.strip()",
)

with open(FILE, "w") as f:
    f.write(code)
import py_compile
py_compile.compile(FILE, doraise=True)
print("OK")
