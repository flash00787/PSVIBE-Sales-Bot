const { Client } = require('ssh2');
const fs = require('fs');

function run(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let out = '', err = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err2, stream) => {
        if (err2) { conn.end(); return reject(err2); }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => err += d.toString());
        stream.on('close', code => {
          conn.end();
          if (code !== 0 && err) reject(new Error(err));
          else resolve({out, err, code});
        });
      });
    });
    conn.connect({
      host: '5.223.81.16', port: 22, username: 'root',
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
    });
  });
}

async function main() {
  // === 1. Fix sales.py - add missing imports ===
  // Replace the comment about update_inv_total_k1 with actual lazy imports
  const salesPath = '/root/psvibe-sales-bot/bot/handlers/sales.py';
  
  // Use Python to do the precise edit
  const editScript = `
import re

# --- Edit 1: sales.py - replace comment with actual lazy imports ---
with open('/root/psvibe-sales-bot/bot/handlers/sales.py', 'r') as f:
    content = f.read()

old_comment = "# Explicit import for helper from stock module\\n# update_inv_total_k1 imported lazily inside functions to avoid circular deps"
new_imports = "# Lazy imports to avoid circular deps\\nfrom bot.handlers.notify import _check_low_balance_alert, get_customer_chat_id\\nfrom bot.handlers.booking_flow import _cancel_remind\\n\\ndef _lazy_update_inv_total_k1():\\n    from bot.handlers.stock import update_inv_total_k1 as _f\\n    return _f()"

content = content.replace(old_comment, new_imports)

# Also replace update_inv_total_k1() call with _lazy_update_inv_total_k1()
content = content.replace('update_inv_total_k1()', '_lazy_update_inv_total_k1()')

with open('/root/psvibe-sales-bot/bot/handlers/sales.py', 'w') as f:
    f.write(content)
print("sales.py fixed")

# --- Edit 2: console.py - restructure console menu ---
with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    content = f.read()

# Remove BTN_CHANGE_GAME and BTN_SSD_MANAGE imports from top
content = content.replace(
    '    BTN_END_SESSION, BTN_GAME_LIB_MENU, BTN_SKIP_GAME, BTN_SSD_MANAGE,\\n    BTN_SSD_TRANSFER, BTN_START_SESSION, BTN_STATUS_BOARD, CONSOLE_MENU,\\n    END_SESSION_SELECT, GAME_CHANGE_CONS, GAME_CHANGE_GAME, MMT,\\n    SSD_XFER_SSD, _delete_session_game, _replit_get, _replit_get_async, add_console_game,',
    '    BTN_CONSOLE_INSTALL, BTN_END_SESSION, BTN_GAME_LIB_MENU, BTN_START_SESSION,\\n    BTN_STATUS_BOARD, CONSOLE_MENU, END_SESSION_SELECT, _delete_session_game,\\n    _replit_get, _replit_get_async, add_console_game,'
)

# Also fix the _replit_post_async in imports if missing
content = content.replace(
    '    calc_duration, cmd_cancel, end_booking, end_booking_async, fetch_console_games,\\n    fetch_console_status, get_games_on_console, get_games_on_console_async, now_mmt,\\n    show_console_menu, show_game_menu, show_main_menu,\\n    prompt_book_console,',
    '    calc_duration, cmd_cancel, end_booking, end_booking_async, fetch_console_games,\\n    fetch_console_status, get_games_on_console, get_games_on_console_async, now_mmt,\\n    show_console_menu, show_game_menu, show_main_menu,\\n    prompt_book_console, _replit_post_async,'
)

# Remove the _show_ssd_menu lazy import
content = content.replace(
    '# Lazy import for show_ssd_menu\\ndef _show_ssd_menu(update, context):\\n    from bot.handlers.ssd_disc import show_ssd_menu as _f\\n    return _f(update, context)\\n\\n\\n',
    ''
)

# Now restructure the show_console_menu function
old_menu = '''async def show_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Console Management submenu — accessible from Main Menu and Admin Panel."""
    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_STATUS_BOARD,   BTN_GAME_LIB_MENU],
        [BTN_CHANGE_GAME,    BTN_SSD_MANAGE],
        [BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "🕹️ *Console Management*\\n"
        "━━━━━━━━━━━━━━━━━━\\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return CONSOLE_MENU'''

new_menu = '''async def show_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Console Management submenu — accessible from Main Menu and Admin Panel."""
    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_STATUS_BOARD,   BTN_GAME_LIB_MENU],
        [BTN_CONSOLE_INSTALL],
        [BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "🕹️ *Console Management*\\n"
        "━━━━━━━━━━━━━━━━━━\\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return CONSOLE_MENU'''

content = content.replace(old_menu, new_menu)

# Now restructure step_console_menu
old_step = '''async def step_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.main_menu import show_main_menu
    from bot.handlers.games import show_game_menu
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_START_SESSION:
        return await prompt_book_console(update, context)
    if choice == BTN_END_SESSION:
        return await prompt_end_session(update, context)
    if choice == BTN_STATUS_BOARD:
        await cmd_console_status(update, context)
        return await show_console_menu(update, context)
    if choice == BTN_GAME_LIB_MENU:
        return await show_game_menu(update, context)
    if choice == BTN_SSD_MANAGE:
        return await _show_ssd_menu(update, context)
    if choice == BTN_CHANGE_GAME:
        return await prompt_game_change_cons(update, context)
    return await show_console_menu(update, context)'''

new_step = '''async def step_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.main_menu import show_main_menu
    from bot.handlers.games import show_game_menu
    from bot.handlers.ginst import show_ginst_menu
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_START_SESSION:
        return await prompt_book_console(update, context)
    if choice == BTN_END_SESSION:
        return await prompt_end_session(update, context)
    if choice == BTN_STATUS_BOARD:
        await cmd_console_status(update, context)
        return await show_console_menu(update, context)
    if choice == BTN_GAME_LIB_MENU:
        return await show_game_menu(update, context)
    if choice == BTN_CONSOLE_INSTALL:
        return await show_ginst_menu(update, context)
    return await show_console_menu(update, context)'''

content = content.replace(old_step, new_step)

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.write(content)
print("console.py fixed")

# --- Edit 3: games.py - clean up game library menu ---
with open('/root/psvibe-sales-bot/bot/handlers/games.py', 'r') as f:
    content = f.read()

# Remove BTN_ADD_GAME, BTN_CONSOLE_INSTALL, BTN_DEL_GAME, BTN_SSD_MANAGE, BTN_DISC_RECORD from show_game_menu
old_game_menu = '''async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [BTN_VIEW_GAMES,      BTN_ADD_GAME],
        [BTN_CONSOLE_INSTALL, BTN_DEL_GAME],
        [BTN_EDIT_GAME,       BTN_DISC_RECORD],
        [BTN_SSD_MANAGE],
        [BTN_BACK_MAIN],
    ]'''

new_game_menu = '''async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [BTN_VIEW_GAMES],
        [BTN_EDIT_GAME],
        [BTN_BACK_MAIN],
    ]'''

content = content.replace(old_game_menu, new_game_menu)

# Remove the lazy import helpers for ginst and ssd
content = content.replace(
    '''# ── Lazy imports (break circular deps) ──
def _show_ginst_menu(update, context):
    from bot.handlers.ginst import show_ginst_menu as _f
    return _f(update, context)

def _show_ssd_menu(update, context):
    from bot.handlers.ssd_disc import show_ssd_menu as _f
    return _f(update, context)
''',
    ''
)

# Now fix step_game_menu - remove handlers for removed buttons
# Remove BTN_ADD_GAME handler
content = content.replace(
    '''    # ── Add Game ──
    if choice == BTN_ADD_GAME:
        context.user_data.pop("new_game", None)
        context.user_data["new_game"] = {}
        await update.message.reply_text(
            "➕ *ဂိမ်းအသစ် ထည့်*\\n━━━━━━━━━━━━━━━━━━\\n"
            "🎮 ဂိမ်းနာမည် ရိုက်ပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[BTN_CANCEL]], resize_keyboard=True),
        )
        return GAME_ADD_TITLE''',
    ''
)

# Remove BTN_CONSOLE_INSTALL handler
content = content.replace(
    '''    # ── Console Install ──
    if choice == BTN_CONSOLE_INSTALL:
        return await _show_ginst_menu(update, context)''',
    ''
)

# Remove BTN_SSD_MANAGE handler
content = content.replace(
    '''    # ── SSD Manage ──
    if choice == BTN_SSD_MANAGE:
        return await _show_ssd_menu(update, context)''',
    ''
)

# Remove BTN_DISC_RECORD handler
content = content.replace(
    '''    # ── Disc Record ──
    if choice == BTN_DISC_RECORD:
        games = await fetch_games_async()
        if not games:
            await update.message.reply_text("ℹ️ Game Library ဗလာ ဖြစ်နေသည်")
            return await show_game_menu(update, context)
        context.user_data["disc_games"] = games
        disc_map = {}
        kb_rows = []
        for g in games:
            d = g.get("discs", "").strip()
            lbl = f"{g['title']}  💿{d}pc" if d and d != "0" else f"{g['title']}  💿--"
            disc_map[lbl] = g
            disc_map[g["title"]] = g
            kb_rows.append([lbl])
        kb_rows.append([BTN_BACK])
        context.user_data["disc_map"] = disc_map
        await update.message.reply_text(
            "💿 <b>Game Discs Record</b>\\n"
            "━━━━━━━━━━━━━━━━━━\\n"
            "ပြင်မည့် ဂိမ်း ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
        )
        return DISC_SELECT''',
    ''
)

# Remove BTN_DEL_GAME handler
content = content.replace(
    '''    # ── Delete Game ──
    if choice == BTN_DEL_GAME:
        games = await fetch_games_async()
        if not games:
            await update.message.reply_text("ℹ️ ဖျက်ရန် ဂိမ်းမရှိပါ")
            return await show_game_menu(update, context)
        kb = [[f"{i}. {g['title']}"] for i, g in enumerate(games, 1)]
        kb.append([BTN_BACK])
        context.user_data["del_games"] = games
        await update.message.reply_text(
            "🗑️ *ဂိမ်းဖျက်မည်*\\n━━━━━━━━━━━━━━━━━━\\n"
            "ဖျက်မည့် ဂိမ်းကို ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return GAME_DEL_SELECT''',
    ''
)

# Remove the unused BTN_ADD_GAME, BTN_DEL_GAME, BTN_CONSOLE_INSTALL, BTN_DISC_RECORD, BTN_SSD_MANAGE from import
content = content.replace(
    'from bot import (\\n    BTN_ADD_GAME, BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL,\\n    BTN_CONSOLE_INSTALL, BTN_DEL_GAME, BTN_DISC_RECORD, BTN_EDIT_GAME,\\n    BTN_SSD_MANAGE, BTN_VIEW_GAMES, DISC_SELECT, GAME_ADD_GENRE,',
    'from bot import (\\n    BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL,\\n    BTN_EDIT_GAME,\\n    BTN_VIEW_GAMES, GAME_ADD_GENRE,'
)

# Also clean up imports that aren't needed anymore
content = content.replace(
    '    fetch_console_games, fetch_console_games_async, fetch_games, fetch_games_async, get_game_lib_sh, show_game_menu,',
    '    fetch_console_games, fetch_console_games_async, fetch_games, fetch_games_async, get_game_lib_sh, show_game_menu,'
)

with open('/root/psvibe-sales-bot/bot/handlers/games.py', 'w') as f:
    f.write(content)
print("games.py fixed")
'''

  // Write the edit script to remote and execute
  await run(`cat > /tmp/fix_bot.py << 'PYEOF'
${editScript}
PYEOF
python3 /tmp/fix_bot.py`);

  console.log('All edits applied');
}

main().catch(e => { console.error(e); process.exit(1); });
