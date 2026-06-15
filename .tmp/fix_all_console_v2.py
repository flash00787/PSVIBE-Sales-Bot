with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    lines = f.readlines()

changes = []

# First pass: find all the key lines and their indices
end_booking_idx = -1
ssd_check_idx = -1
voucher_msg_start = -1
voucher_msg_end = -1
delete_game_idx = -1
bookings_fetch_idx = -1
launch_sale_idx = -1
step_end_def_idx = -1

for i, line in enumerate(lines):
    if 'def step_end_session' in line:
        step_end_def_idx = i
    if 'await end_booking_async(bk_id)' in line:
        end_booking_idx = i
    if 'SSD ပြန်ရွေ့ပါ' in line:
        ssd_check_idx = i
    if '"📝 Sales Voucher ဖွင့်နေသည်..."' in line:
        voucher_msg_start = i
    if '_delete_session_game(cid)' in line:
        delete_game_idx = i
    if 'bookings?memberId=' in line:
        bookings_fetch_idx = i
    if 'from bot.handlers.sales import launch_session_sale' in line:
        launch_sale_idx = i

print(f'step_end_def={step_end_def_idx}')
print(f'end_booking={end_booking_idx}')
print(f'voucher_msg={voucher_msg_start}')
print(f'delete_game={delete_game_idx}')
print(f'bookings_fetch={bookings_fetch_idx}')
print(f'launch_sale={launch_sale_idx}')

# Step 1: Add _t0 and time import
for i in range(step_end_def_idx, min(step_end_def_idx + 10, len(lines))):
    if 'text = update.message.text.strip()' in lines[i] and '"""' not in lines[i]:
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        lines.insert(i, f'{indent}_t0 = time.monotonic()\n')
        print(f'Inserted _t0 at {i}')
        # Adjust indices after insert
        if end_booking_idx >= i: end_booking_idx += 1
        if voucher_msg_start >= i: voucher_msg_start += 1
        if delete_game_idx >= i: delete_game_idx += 1
        if bookings_fetch_idx >= i: bookings_fetch_idx += 1
        if launch_sale_idx >= i: launch_sale_idx += 1
        break

# Add time import
for i, line in enumerate(lines):
    if 'import asyncio, logging, re, json' in line:
        lines[i] = line.replace('import asyncio, logging, re, json', 'import asyncio, logging, re, json, time')
        print(f'Added time import at {i}')
        break

# Step 2: Add timing after end_booking
if end_booking_idx > 0:
    indent = lines[end_booking_idx][:len(lines[end_booking_idx]) - len(lines[end_booking_idx].lstrip())]
    lines.insert(end_booking_idx + 1, f'{indent}logger.warning("step_t end_booking: %dms from_start=%dms", (time.monotonic() - _t0) * 1000, (time.monotonic() - _t0) * 1000)\n')
    # Adjust indices
    if voucher_msg_start >= end_booking_idx + 1: voucher_msg_start += 1
    if delete_game_idx >= end_booking_idx + 1: delete_game_idx += 1
    if bookings_fetch_idx >= end_booking_idx + 1: bookings_fetch_idx += 1
    if launch_sale_idx >= end_booking_idx + 1: launch_sale_idx += 1
    print(f'Added timing after end_booking at {end_booking_idx + 1}')

# Step 3: Add timing after voucher message
if voucher_msg_start > 0:
    indent = lines[voucher_msg_start][:len(lines[voucher_msg_start]) - len(lines[voucher_msg_start].lstrip())]
    # Find the reply_text closing line (next line with same indent)
    for j in range(voucher_msg_start, voucher_msg_start + 10):
        if lines[j].strip().startswith(')') or 'reply_markup' in lines[j] or 'parse_mode' in lines[j]:
            pass
        if j > voucher_msg_start and lines[j].strip().startswith(')'):
            lines.insert(j + 1, f'{indent}logger.warning("step_t voucher_msg_sent: %dms from_start=%dms", (time.monotonic() - _t0) * 1000, (time.monotonic() - _t0) * 1000)\n')
            print(f'Added timing after voucher msg at {j + 1}')
            # Adjust indices
            if delete_game_idx >= j + 1: delete_game_idx += 1
            if bookings_fetch_idx >= j + 1: bookings_fetch_idx += 1
            if launch_sale_idx >= j + 1: launch_sale_idx += 1
            break

# Step 4: Add timing after delete_session_game
if delete_game_idx > 0:
    indent = lines[delete_game_idx][:len(lines[delete_game_idx]) - len(lines[delete_game_idx].lstrip())]
    lines.insert(delete_game_idx + 1, f'{indent}logger.warning("step_t delete_game: %dms from_start=%dms", (time.monotonic() - _t0) * 1000, (time.monotonic() - _t0) * 1000)\n')
    if bookings_fetch_idx >= delete_game_idx + 1: bookings_fetch_idx += 1
    if launch_sale_idx >= delete_game_idx + 1: launch_sale_idx += 1
    print(f'Added timing after delete_game at {delete_game_idx + 1}')

# Step 5: Add timing after bookings fetch
if bookings_fetch_idx > 0:
    # Lines after: the bookings fetch block goes from bookings_fetch_idx until the except/coupon block
    # Look for next line that starts like: except Exception:
    target_j = -1
    for j in range(bookings_fetch_idx, min(bookings_fetch_idx + 15, len(lines))):
        stripped = lines[j].strip()
        if stripped.startswith('#') and 'CashBack' in stripped:
            # This is the coupon section - add timing BEFORE this
            target_j = j - 1
            break
    if target_j > 0:
        indent = lines[bookings_fetch_idx][:len(lines[bookings_fetch_idx]) - len(lines[bookings_fetch_idx].lstrip())]
        lines.insert(target_j + 1, f'{indent}logger.warning("step_t bookings_fetch: %dms from_start=%dms", (time.monotonic() - _t0) * 1000, (time.monotonic() - _t0) * 1000)\n')
        if launch_sale_idx >= target_j + 1: launch_sale_idx += 1
        print(f'Added timing after bookings fetch at {target_j + 1}')

# Step 6: Replace the return at launch_sale with timing version
if launch_sale_idx > 0:
    launch_return_idx = -1
    for j in range(launch_sale_idx, min(launch_sale_idx + 5, len(lines))):
        if 'return await launch_session_sale' in lines[j]:
            launch_return_idx = j
            break
    if launch_return_idx > 0:
        indent = lines[launch_return_idx][:len(lines[launch_return_idx]) - len(lines[launch_return_idx].lstrip())]
        old_line = lines[launch_return_idx]
        lines[launch_return_idx] = f'{indent}from bot.handlers.sales import launch_session_sale\n'
        lines.insert(launch_return_idx + 1, f'{indent}_t5 = time.monotonic()\n')
        lines.insert(launch_return_idx + 2, f'{indent}_pre_ms = (_t5 - _t0) * 1000\n')
        lines.insert(launch_return_idx + 3, f'{indent}_ls_result = await launch_session_sale(update, context, cid, mbr, total_mins, session_staff, booking_id=_linked_bk_id)\n')
        lines.insert(launch_return_idx + 4, f'{indent}_total_ms = (time.monotonic() - _t0) * 1000\n')
        lines.insert(launch_return_idx + 5, f'{indent}logger.warning("CONSOLE_TIME step_end_session: pre_sale=%dms sale=%dms total=%dms", _pre_ms, _total_ms - _pre_ms, _total_ms)\n')
        lines.insert(launch_return_idx + 6, f'{indent}return _ls_result\n')
        print(f'Replaced launch return at {launch_return_idx}')

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.writelines(lines)

print('DONE')
