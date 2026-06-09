#!/usr/bin/env python3
"""Fix 6 & 8: Games - add empty name guard, show game list directly with edit options."""
path = '/root/psvibe-sales-bot/bot/handlers/games.py'
content = open(path).read()

# Fix 6: Add empty name guard in _build_game_kb (consistent with _build_game_list_text)
old_kb = '''    for i, g in enumerate(page_games, start=start + 1):
        name = g.get("title", "").strip()
        genre = g.get("genre", "").strip()
        sm = g.get("solo_multi", "").strip()
        sm_icon = "🧑" if sm == "Solo" else ("👥" if sm == "Multiplayer" else ("🧑👥" if sm else ""))
        label = f"{i}. {name}"
        if genre:
            label += f" · {genre}"
        kb.append([label])'''

new_kb = '''    for i, g in enumerate(page_games, start=start + 1):
        name = g.get("title", "").strip()
        if not name:
            continue
        genre = g.get("genre", "").strip()
        sm = g.get("solo_multi", "").strip()
        sm_icon = "🧑" if sm == "Solo" else ("👥" if sm == "Multiplayer" else ("🧑👥" if sm else ""))
        label = f"{i}. {name}"
        if genre:
            label += f" · {genre}"
        kb.append([label])'''

if old_kb in content:
    content = content.replace(old_kb, new_kb)
    print('FIX 6a DONE: Added empty name guard in _build_game_kb')
else:
    print('FIX 6a: Old _build_game_kb pattern not found')

# Fix 6b & 8: Modify show_game_menu to show game list directly with edit/delete options
old_menu = '''async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [BTN_VIEW_GAMES],
        [BTN_EDIT_GAME],
        [BTN_BACK_MAIN],
    ]
    games = await fetch_games_async()
    count = len(games)
    await update.message.reply_text(
        f"🎮 *Game Library* ({count} ဂိမ်း)\\n"
        "━━━━━━━━━━━━━━━━━━\\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    # Clear any lingering game view state
    context.user_data.pop("game_list", None)
    context.user_data.pop("game_page", None)
    context.user_data.pop("game_query", None)
    return GAME_MENU'''

new_menu = '''async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show game library directly with paginated view and edit/delete options."""
    games = await fetch_games_async()
    count = len(games)
    # Clear any lingering game view state
    context.user_data.pop("game_list", None)
    context.user_data.pop("game_page", None)
    context.user_data.pop("game_query", None)
    context.user_data.pop("game_searching", None)

    if not games:
        await update.message.reply_text(
            "ℹ️ Game Library ဗလာ ဖြစ်နေသည်\\nဂိမ်းထည့်ပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return GAME_MENU

    context.user_data["game_list"] = games
    context.user_data["game_page"] = 0
    context.user_data["game_query"] = ""
    total_pages = max(1, (len(games) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
    text = _build_game_list_text(games, 0, total_pages)
    kb = _build_game_kb(games, 0, total_pages)
    # Add edit option at bottom
    kb.append([BTN_EDIT_GAME])
    kb.append([BTN_BACK_MAIN])

    await update.message.reply_text(text, parse_mode="HTML",
                                     reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return GAME_MENU'''

if old_menu in content:
    content = content.replace(old_menu, new_menu)
    print('FIX 6b/8 DONE: show_game_menu now shows game list directly with edit options')
else:
    print('FIX 6b/8: Old show_game_menu pattern not found')
    # Try to find it
    idx = content.find('async def show_game_menu')
    if idx >= 0:
        end = min(len(content), idx + 800)
        print(f'  Found at position {idx}:')
        print(content[idx:end])

open(path, 'w').write(content)
print('games.py saved')
