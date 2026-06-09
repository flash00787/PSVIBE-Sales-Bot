import sys

# Step 1: constants.py
with open('/root/psvibe-sales-bot/bot/constants.py') as f:
    c = f.read()
if 'BTN_BALANCE' not in c:
    c = c.replace(
        'BTN_FINANCIAL_REPORT   = "\U0001f4b9 Financial Report"',
        'BTN_FINANCIAL_REPORT   = "\U0001f4b9 Financial Report"\nBTN_BALANCE          = "\U0001f4b0 Account Balance"'
    )
    with open('/root/psvibe-sales-bot/bot/constants.py', 'w') as f:
        f.write(c)
    print('Step1: constants.py OK')
else:
    print('Step1: skip (already has BTN_BALANCE)')

# Step 2: main_menu.py
with open('/root/psvibe-sales-bot/bot/handlers/main_menu.py') as f:
    m = f.read()

if 'BTN_BALANCE' not in m:
    m = m.replace(
        'BTN_FINANCIAL_REPORT, BTN_GAME_LIB_MENU,',
        'BTN_FINANCIAL_REPORT, BTN_BALANCE, BTN_GAME_LIB_MENU,'
    )

if '_replit_get_async' not in m:
    m = m.replace(
        'fetch_allowed_staff_ids_async,',
        'fetch_allowed_staff_ids_async, _replit_get_async,'
    )

if 'async def cmd_balance' not in m:
    bf = """
async def cmd_balance(update, context):
    \"\"\"Show account balances for staff (no PIN needed).\"\"\"
    await update.message.reply_text(
        "\\U0001f4b0 *Account Balance — ရှာဖွေနေပါသည်...*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    data = await _replit_get_async("finance/accounts")
    if not data:
        await update.message.reply_text(
            "\\u274c Account Balances API ချိတ်မရပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return MAIN_MENU
    accounts = data.get("accounts", [])
    total_bal = data.get("total_balance", 0)
    if not accounts:
        await update.message.reply_text(
            "\\u26a0\\ufe0f Account မှတ်တမ်း မရှိသေးပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return MAIN_MENU
    lines = ["\\U0001f4b0 *Account Balances*", "\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501"]
    for a in accounts:
        name = a.get("name", "?")
        bal = a.get("balance", a.get("opening", 0))
        low = name.lower()
        icon = "\\U0001f3e6" if ("bank" in low or "kbz" in low or "aya" in low or "cb" in low) else ("\\U0001f4f1" if ("mmqr" in low or "kpay" in low or "wave" in low) else "\\U0001f4b5")
        lines.append(f"{icon} {name:<16}: {int(bal):>10,} Ks")
    lines += ["\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501", f"\\U0001f4b5 *Total : {int(total_bal):,} Ks*"]
    await update.message.reply_text(
        "\\n".join(lines),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
    )
    return MAIN_MENU

"""
    m = m.replace('async def show_main_menu', bf + 'async def show_main_menu')

# Add button to main menu keyboard
old_kb = '[BTN_CONSOLES,         BTN_TODAY_REPORT],'
new_kb = '[BTN_CONSOLES,         BTN_TODAY_REPORT],\n        [BTN_BALANCE,          BTN_MEMBER_MGMT],'
if old_kb in m:
    m = m.replace(old_kb, new_kb)

# Add routing in step_main_menu
old_route = 'if choice == BTN_FINANCIAL_REPORT:\n        return await cmd_financial_report(update, context)\n\n    if choice == BTN_ADMIN:'
new_route = 'if choice == BTN_FINANCIAL_REPORT:\n        return await cmd_financial_report(update, context)\n\n    if choice == BTN_BALANCE:\n        return await cmd_balance(update, context)\n\n    if choice == BTN_ADMIN:'
if old_route in m:
    m = m.replace(old_route, new_route)

with open('/root/psvibe-sales-bot/bot/handlers/main_menu.py', 'w') as f:
    f.write(m)
print('Step2: main_menu.py OK')

# Step 3: app.py
with open('/root/psvibe-sales-bot/bot/app.py') as f:
    a = f.read()

if 'CommandHandler("balance",' not in a:
    a = a.replace(
        'CommandHandler("console",    cmd_console_status),',
        'CommandHandler("balance",    cmd_balance),\n            CommandHandler("console",    cmd_console_status),'
    )
    a = a.replace(
        'CommandHandler("console",    cmd_console_status),\n        ],',
        'CommandHandler("balance",    cmd_balance),\n            CommandHandler("console",    cmd_console_status),\n        ],'
    )
    a = a.replace(
        '("console",     cmd_console_status),',
        '("balance",     cmd_balance),\n        ("console",     cmd_console_status),'
    )
    a = a.replace(
        'BotCommand("console",    "\\U0001f579\\ufe0f Console live status"),',
        'BotCommand("console",    "\\U0001f579\\ufe0f Console live status"),\n            BotCommand("balance",    "\\U0001f4b0 Account Balance"),'
    )
    with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
        f.write(a)
    print('Step3: app.py OK')
else:
    print('Step3: skip (already has /balance)')

print('\\n=== ALL DONE ===')
