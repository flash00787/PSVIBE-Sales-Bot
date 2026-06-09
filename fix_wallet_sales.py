with open('/root/psvibe-sales-bot/bot/handlers/sales.py', 'r') as f:
    content = f.read()

# The code to find and replace: after the GSheet wallet update, add MySQL update
old = '''                            _current_j = int(str(_wr[9]).replace(',', '').strip() or 0)
                            member_sh.update_cell(_wi + 1, 10, _current_j + _w_deduct)
                            logging.info("wallet_deduct: %s -%d mins → %d", _m_id, _w_deduct, _new_bal)
                            break'''

new = '''                            _current_j = int(str(_wr[9]).replace(',', '').strip() or 0)
                            member_sh.update_cell(_wi + 1, 10, _current_j + _w_deduct)
                            logging.info("wallet_deduct: %s -%d mins → %d", _m_id, _w_deduct, _new_bal)
                            # ── MySQL wallet deduction ────────
                            try:
                                _replit_post("wallet/deduct", {
                                    "member_id": _m_id,
                                    "deduct_mins": _w_deduct,
                                    "total_mins": play_mins,
                                })
                            except Exception as _we:
                                logging.warning("MySQL wallet_deduct failed (GSheet OK): %s", _we)
                            break'''

count = content.count(old)
if count != 1:
    print(f"ERROR: old text found {count} times (expected 1)")
else:
    content = content.replace(old, new)
    with open('/root/psvibe-sales-bot/bot/handlers/sales.py', 'w') as f:
        f.write(content)
    print('BUG 3b: MySQL wallet deduction added to sales.py')
