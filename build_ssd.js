// Build ssd_disc.py with move functionality
const fs = require('fs');
const { Client } = require('ssh2');

const orig = fs.readFileSync('/tmp/ssd_orig_local.py', 'utf8');

// 1. Fix imports - add new constants
let content = orig;
content = content.replace(
  'BTN_SSD_ADD, BTN_SSD_BLUE, BTN_SSD_GREY,',
  'BTN_SSD_ADD, BTN_SSD_BLUE, BTN_SSD_GREY,\n    BTN_SSD_MOVE_TO_CONSOLE, BTN_SSD_MOVE_TO_SSD,'
);
content = content.replace(
  'SSD_XFER_SSD, SSD_BTN_TO_ID, SSD_NAMES,',
  'SSD_XFER_SSD, SSD_BTN_TO_ID, SSD_NAMES,\n    SSD_MOVE_SSD, SSD_MOVE_GAME, SSD_MOVE_CONS,\n    SSD_MOVE_FROM_CONS, SSD_MOVE_FROM_GAME, SSD_MOVE_TO_SSD,'
);

// 2. Add move_console_game_async import
content = content.replace(
  'import asyncio\nlogger = logging.getLogger(__name__)',
  'import asyncio\nfrom bot.api_client import move_console_game_async\nlogger = logging.getLogger(__name__)'
);

// 3. Add move buttons to SSD menu kb
content = content.replace(
  '[BTN_SSD_TRANSFER, BTN_SSD_RETURN],\n        [BTN_BACK],',
  '[BTN_SSD_TRANSFER, BTN_SSD_RETURN],\n        [BTN_SSD_MOVE_TO_CONSOLE, BTN_SSD_MOVE_TO_SSD],\n        [BTN_BACK],'
);

// 4. Add move handlers in step_ssd_menu (before BTN_SSD_RETURN)
const returnBlock = '    if text == BTN_SSD_RETURN:';
const moveHandlers = [
  '    if text == BTN_SSD_MOVE_TO_CONSOLE:',
  '        await update.message.reply_text(',
  '            "\\U0001f504 *SSD\\u2192Console Move*\\n\\nSSD \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",',
  '            parse_mode="Markdown",',
  '            reply_markup=_ssd_kb(),',
  '        )',
  '        return SSD_MOVE_SSD',
  '    if text == BTN_SSD_MOVE_TO_SSD:',
  '        await update.message.reply_text(',
  '            "\\U0001f504 *Console\\u2192SSD Move*\\n\\nConsole \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",',
  '            parse_mode="Markdown",',
  '            reply_markup=ReplyKeyboardMarkup(',
  '                [[c["id"]] for c in get_consoles_from_setting()] + [[BTN_BACK]],',
  '                resize_keyboard=True,',
  '            ),',
  '        )',
  '        return SSD_MOVE_FROM_CONS',
  '',
];
content = content.replace(returnBlock, moveHandlers.join('\n') + '\n' + returnBlock);

// 5. Add move handler functions
const newFunctions = `

async def step_ssd_move_ssd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose SSD to move from (SSD->Console flow)."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("\\u26a0\\ufe0f \\u1019\\u103e\\u1014\\u103a\\u101e\\u1031\\u102c SSD \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:", reply_markup=_ssd_kb())
        return SSD_MOVE_SSD
    rows = [r for r in await fetch_console_games_async() if r["console_id"] == ssd_id]
    if not rows:
        await update.message.reply_text(
            f"\\U0001f4c0 <b>{SSD_NAMES[ssd_id]}</b> \\u2014 \\u1002\\u102d\\u1019\\u103a\\u1038 \\u1019\\u101b\\u103e\\u102d\\u101e\\u1031\\u1038\\u1015\\u102b",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)
    context.user_data["ssd_move_src"] = ssd_id
    titles = [r["game_title"] for r in rows]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"\\U0001f504 <b>{SSD_NAMES[ssd_id]}</b> \\u1019\\u103e Move \\u1019\\u100a\\u1037\\u103a \\u1002\\u102d\\u1019\\u103a\\u1038 \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_MOVE_GAME

async def step_ssd_move_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose game to move from SSD -> pick destination console."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    context.user_data["ssd_move_game"] = text
    consoles = get_consoles_from_setting()
    kb_rows = [[c["id"]] for c in consoles] + [[BTN_BACK]]
    await update.message.reply_text(
        f'\\U0001f504 <b>"{text}"</b> \\u1000\\u102d\\u102f \\u1018\\u101a\\u103a Console \\u1011\\u1032 \\u1011\\u100a\\u1037\\u103a\\u1019\\u100a\\u103a\\u1014\\u100a\\u103a\\u1038?',
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_MOVE_CONS

async def step_ssd_move_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute SSD->Console move."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = context.user_data.get("ssd_move_src", "")
    game = context.user_data.get("ssd_move_game", "")
    to_console = text
    ok = await move_console_game_async(ssd_id, game, to_console)
    if ok:
        await update.message.reply_text(
            f'\\u2705 <b>"{game}"</b>\\n\\U0001f4c0 {SSD_NAMES.get(ssd_id, ssd_id)} \\u2192 \\U0001f579\\ufe0f <b>{to_console}</b>\\nMove \\u1015\\u103c\\u102e\\u1038\\u1015\\u102b\\u1015\\u103c\\u102e',
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("\\u274c Move \\u1019\\u101b\\u1015\\u102b \\u2014 \\u1011\\u1015\\u103a\\u1000\\u103c\\u102d\\u102f\\u1038\\u1005\\u102c\\u1038\\u1015\\u102b")
    return await show_ssd_menu(update, context)

async def step_ssd_move_from_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose source console for Console->SSD move."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    cid = text
    rows = [r for r in await fetch_console_games_async()
            if r["console_id"].upper() == cid.upper()
            and r.get("status", "") == "Installed"]
    if not rows:
        await update.message.reply_text(
            f"\\U0001f579\\ufe0f <b>{cid}</b> \\u2014 Installed \\u1002\\u102d\\u1019\\u103a\\u1038 \\u1019\\u101b\\u103e\\u102d\\u1015\\u102b",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)
    context.user_data["ssd_move_from_cons"] = cid
    titles = [r["game_title"] for r in rows]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"\\U0001f504 <b>{cid}</b> \\u1019\\u103e Move \\u1019\\u100a\\u1037\\u103a \\u1002\\u102d\\u1019\\u103a\\u1038 \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_MOVE_FROM_GAME

async def step_ssd_move_from_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose game to move from console -> pick destination SSD."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    context.user_data["ssd_move_from_game"] = text
    await update.message.reply_text(
        f'\\U0001f504 <b>"{text}"</b> \\u1000\\u102d\\u102f \\u1018\\u101a\\u103a SSD \\u1011\\u1032 \\u1011\\u100a\\u1037\\u103a\\u1019\\u100a\\u103a\\u1014\\u100a\\u103a\\u1038?',
        parse_mode="HTML",
        reply_markup=_ssd_kb(),
    )
    return SSD_MOVE_TO_SSD

async def step_ssd_move_to_ssd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute Console->SSD move."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("\\u26a0\\ufe0f \\u1019\\u103e\\u1014\\u103a\\u101e\\u1031\\u102c SSD \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:", reply_markup=_ssd_kb())
        return SSD_MOVE_TO_SSD
    from_cons = context.user_data.get("ssd_move_from_cons", "")
    game = context.user_data.get("ssd_move_from_game", "")
    ok = await move_console_game_async(from_cons, game, ssd_id)
    if ok:
        await update.message.reply_text(
            f'\\u2705 <b>"{game}"</b>\\n\\U0001f579\\ufe0f <b>{from_cons}</b> \\u2192 \\U0001f4c0 {SSD_NAMES.get(ssd_id, ssd_id)}\\nMove \\u1015\\u103c\\u102e\\u1038\\u1015\\u102b\\u1015\\u103c\\u102e',
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("\\u274c Move \\u1019\\u101b\\u1015\\u102b \\u2014 \\u1011\\u1015\\u103a\\u1000\\u103c\\u102d\\u102f\\u1038\\u1005\\u102c\\u1038\\u1015\\u102b")
    return await show_ssd_menu(update, context)
`;

content += newFunctions;

// Upload via SFTP
const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err); conn.end(); return; }
    const w = sftp.createWriteStream('/root/psvibe-sales-bot/bot/handlers/ssd_disc.py');
    w.on('close', () => {
      console.log('Uploaded. Compiling...');
      conn.exec('cd /root/psvibe-sales-bot && python3 -c "import py_compile; py_compile.compile(\'bot/handlers/ssd_disc.py\', doraise=True); print(\'ssd_disc.py: OK\')"', (e2, stream) => {
        if (e2) { console.error(e2); conn.end(); return; }
        stream.on('data', d => process.stdout.write(d.toString()));
        stream.stderr.on('data', d => process.stderr.write(d.toString()));
        stream.on('close', () => conn.end());
      });
    });
    w.end(content);
  });
});
conn.connect({host:'5.223.81.16', username:'root', privateKey:fs.readFileSync(process.env.HOME + '/.openclaw/workspace/.ssh/id_rsa')});
