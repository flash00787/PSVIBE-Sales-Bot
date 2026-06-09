#!/usr/bin/env python3
"""Fix 5: GINST add flow - make it go through type selection instead of hardcoding HDD."""
import re

path = '/root/psvibe-sales-bot/bot/handlers/ginst.py'
content = open(path).read()

# The fix: modify step_ginst_add_game to save game title and show type selection
# Find the pattern and replace it

old_pattern = (
    '    cid   = context.user_data.get("ginst_console_id", "")\n'
    '    title = text\n'
    '    install_type = "HDD"\n'
)

new_pattern = (
    '    cid   = context.user_data.get("ginst_console_id", "")\n'
    '    title = text\n'
    '    # Save game title for next step (type selection)\n'
    '    context.user_data["ginst_game_title"] = title\n'
)

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern, 1)
    
    # Also remove the gather/save section and replace with type selection prompt
    # Find: "    ok, gl_ok = await asyncio.gather(..."
    # Replace from that line to "return await show_ginst_menu(update, context)"
    # with type selection
    gather_start = content.find('\n    # ── Duplicate check')
    if gather_start > 0:
        # Find the section after duplicate check that saves directly
        after_dup = content.find('\n    ok, gl_ok = await asyncio.gather(', gather_start)
        if after_dup < 0:
            after_dup = content.find('\n    ok', gather_start + 100)
        
        end_section = content.find('\n    return await show_ginst_menu(update, context)', after_dup)
        if end_section > 0:
            # Replace the save section with type selection
            save_block = content[after_dup:end_section + len('\n    return await show_ginst_menu(update, context)')]
            new_block = '''
    # Show install type selection
    await update.message.reply_text(
        f"🖥️ <b>{cid}</b> — 🎮 <b>{title}</b>\\n\\nInstall Type ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_GINST_HDD, BTN_GINST_DISC], [BTN_GINST_SSD], [BTN_BACK]],
            resize_keyboard=True,
        ),
    )
    return GINST_ADD_TYPE'''
            content = content.replace(save_block, new_block)
            open(path, 'w').write(content)
            print('FIX 5 DONE: GINST add flow now includes type selection')
        else:
            print('FIX 5: Could not find end of save section')
    else:
        print('FIX 5: Could not find duplicate check section')
else:
    # Try easier approach: just check
    print('FIX 5: Old pattern not found exactly')
    if 'install_type = "HDD"' in content:
        print('  Found install_type line')
        idx = content.find('install_type = "HDD"')
        print(f'  At position {idx}')
        start = max(0, idx-200)
        end = min(len(content), idx+500)
        print('  Context:')
        print(content[start:end])
