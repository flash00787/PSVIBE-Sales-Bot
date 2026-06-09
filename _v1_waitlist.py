    # Save receipt JSON (local disk — instant)
    save_receipt_json(v_no, {
        "type":           "sale",
        "voucher_id":     v_no,
        "date":           today,
        "member_id":      m_id,
        "console_id":     c_id,
        "play_mins":      play_mins,
        "game_amt":       game_amt,
        "food_items":     food_sold,
        "food_total":     food_total,
        "net_total":      net_total,
        "kpay":           kpay,
        "cash":           cash,
        "multiplier":     mult,
        "is_guest":       is_guest,
        "prev_balance":   wallet_before,
        "balance_change": -wallet_deduct if not is_guest else None,
        "balance_after":  remaining_mins,
    })
    context.user_data.clear()

    # ── RECEIPT — sent BEFORE sheet writes ────────────────────────
    await update.message.reply_text(
        f"✅ *{v_no} သိမ်းဆည်းပြီးပါပြီ!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{member_ln}{staff_line}\n"
        f"🕹️ Console: *{c_id}*  |  {game_ln}\n"
        f"🍔 Food & Drink:\n{food_sec_receipt}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🧾 Game: *{game_amt:,} Ks*  |  Food: *{food_total:,} Ks*\n"
        f"💰 Grand Total: *{net_total:,} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💳 Kpay: *{kpay:,} Ks*  |  💵 Cash: *{cash:,} Ks*"
        f"{wallet_bal_line}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    if receipt_kb:
        await update.message.reply_text("🖨️ Receipt ပုံနှိပ်ရန် -", reply_markup=receipt_kb)

    # ── SHEET WRITES — background (user already has receipt) ──────
    _disc = discount if discount else ""
    async def _sale_bg():
        def _do():
            sales_sh.batch_update(
                [{"range": f"A{s_row}:K{s_row}",
                  "values": [[today, v_no, m_id, c_id, play_mins,
                              game_amt, food_total, _disc, net_total, kpay, cash]]},
                 {"range": f"O{s_row}", "values": [[staff_name]]}],
                value_input_option="USER_ENTERED",
            )
            for item in food_sold:
                cp = food_costs.get(item["name"], 0)
                stock_sh.append_row(
                    [today, v_no, item["name"], item["qty"],
                     item.get("unit_price", 0), item.get("subtotal", 0), cp, cp * item["qty"]],
                    value_input_option="USER_ENTERED",
                )
            if food_sold:
                _update_inv_total_k1()
                _replit_get("sheets/inventory?nocache=1")
        try:
            await asyncio.to_thread(_do)
        except Exception as _e:
            logging.error("sale_bg_write: %s", _e)
    asyncio.create_task(_sale_bg())

    # ── Waitlist notify (non-blocking) ───────────────────────────────────────
    _wl_cid = d.get("c_id", "")
    if _wl_cid and _wl_cid not in ("-", ""):
        async def _wl_notify():
            try:
                resp = await asyncio.to_thread(
                    _replit_post, "waitlist/notify", {"console_id": _wl_cid}
                )
                if resp and resp.get("notified"):
                    logging.info("Waitlist notified: %s for console %s",
                                 resp.get("entry", {}).get("customer_name", "?"), _wl_cid)
            except Exception as _e:
                logging.warning("waitlist notify error: %s", _e)
        asyncio.create_task(_wl_notify())

    # ── Low balance alert (non-blocking, member only) ────────────────────────
    if not is_guest:
        asyncio.create_task(_check_low_balance_alert(m_id, c_id))

    return await show_main_menu(update, context)


# ═════════════════════════════════════════
#  PAYROLL CALCULATION
# ═════════════════════════════════════════

def calc_monthly_payroll(month_str: str | None = None) -> list[dict]:
    """
    Calculate monthly payroll for all staff.
    month_str format: 'YYYY-MM' (default = current month).
    Rules:
      - New Member card: 1,500 Ks per card registered
      - Game play bonus (BUSINESS-WIDE total mins):
          ≥ 90,000 mins (1,500 hrs) → 50,000 Ks each
          ≥ 120,000 mins (2,000 hrs) → 100,000 Ks each
      - Food & Drink: daily TOTAL ≥ 50,000 Ks
          → 5% of amount EXCEEDING 50,000 each day
    """
    if month_str is None:
        month_str = now_mmt().strftime("%Y-%m")
    year_i, mon_i = int(month_str[:4]), int(month_str[5:7])

    staff_list = fetch_staff()
    if not staff_list:
        return []

    # daily_food_total: date_key → total F&D sales for that day (ALL staff combined)
    daily_food_total: dict[str, int] = {}
    total_play_mins = 0   # BUSINESS-WIDE sum — col O may be empty for older sessions

    def _parse_date(val: str):
        for fmt in ("%m/%d/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(val.strip(), fmt)
            except ValueError:
                pass
        # fallback: try splitting manually for M/D/YYYY
        try:
            parts = val.strip().split("/")
            if len(parts) == 3:
                return datetime(int(parts[2]), int(parts[0]), int(parts[1]))
        except Exception:
            pass
        return None

    # ── Sales_Daily: col E=PlayMins (idx4), G=FoodTotal (idx6) ──
    try:
        sales_rows = sales_sh.get_all_values()
        for row in sales_rows[1:]:
            if len(row) < 7:
                continue
            d = _parse_date(row[0])
            if not d or d.year != year_i or d.month != mon_i:
                continue
            day_key = d.strftime("%Y-%m-%d")

            # Sum ALL play_mins for the month (regardless of staff field)
            total_play_mins += _int(row[4])

            # Food — accumulate daily TOTAL regardless of staff
            daily_food_total[day_key] = daily_food_total.get(day_key, 0) + _int(row[6])
    except Exception as e:
        logging.warning("calc_monthly_payroll sales read: %s", e)

    # ── TopUp_Log: count total new member registrations for the month ──
    total_nm_count = 0
    try:
        topup_rows = topup_sh.get_all_values()
        for row in topup_rows[1:]:
            if len(row) < 9:
                continue
            if row[8].strip() != "First Purchase":
                continue
            d = _parse_date(row[0].strip())
            if not d or d.year != year_i or d.month != mon_i:
                continue
            total_nm_count += 1
    except Exception as e:
        logging.warning("calc_monthly_payroll topup read: %s", e)

    # ── Shared commissions (same for ALL staff) ──
    # New Member: total cards × 1,500 each
    shared_nm_comm = total_nm_count * 1500

    # Food & Drink: days where cafe total ≥ 50,000 → 5% on amount ABOVE 50,000
    # e.g. 60,000 → (60,000-50,000)*5% = 500; 120,000 → 70,000*5% = 3,500
    food_days_qualified = 0
    shared_food_comm    = 0
    for daily_total in daily_food_total.values():
        if daily_total >= 50000:
            shared_food_comm += int((daily_total - 50000) * 0.05)
            food_days_qualified += 1

    base_salaries = fetch_base_salaries()
    attendance    = fetch_attendance(month_str)

    # Business-wide play bonus (same for all staff — total mins not per-staff)
    play_hrs_total = round(total_play_mins / 60, 1)
    game_bonus_shared = (
        100000 if total_play_mins >= 120000 else
        (50000 if total_play_mins >= 90000 else 0)
    )

    payroll = []
    for s in staff_list:
        commission = game_bonus_shared + shared_nm_comm + shared_food_comm
        base_sal   = base_salaries.get(s, 0)

        att = attendance.get(s, {})
        leave_days      = att.get("leave_days", 0)
        late_count      = att.get("late_count", 0)
        deduct_per_late = att.get("deduct_per_late", 500)
        leave_deduct    = int((base_sal / 26) * leave_days) if base_sal > 0 and leave_days > 0 else 0
