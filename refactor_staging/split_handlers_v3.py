#!/usr/bin/env python3
"""
Phase 6 Refactor v3: Accurate function-to-domain mapping.
Uses exact function name matching for reliability.
"""
import os, re

BASE = "/home/node/.openclaw/workspace/refactor_staging"
HANDLERS = f"{BASE}/handlers.py.full"
OUT = f"{BASE}/handlers"

os.makedirs(OUT, exist_ok=True)

with open(HANDLERS, "r", encoding="utf-8") as f:
    full_text = f.read()
lines = full_text.split("\n")

# ── Complete function-to-domain mapping (every single function) ────────
func_to_domain = {}

# Main Menu
for fn in ["show_main_menu", "step_main_menu"]:
    func_to_domain[fn] = "main_menu"

# Member Management
for fn in ["show_mm_menu", "show_rank_info", "step_mm_menu",
           "prompt_mm_lookup", "step_mm_lookup",
           "prompt_nm_staff", "step_nm_staff",
           "prompt_nm_name", "step_nm_name",
           "prompt_nm_phone", "step_nm_phone",
           "prompt_nm_email", "step_nm_email",
           "prompt_nm_id", "step_nm_id",
           "prompt_nm_amt", "step_nm_amt",
           "step_nm_gift_pin",
           "prompt_nm_kpay", "step_nm_kpay",
           "prompt_nm_referral", "step_nm_referral",
           "_show_nm_confirm", "step_nm_confirm",
           "prompt_tu_member", "step_tu_member",
           "prompt_tu_amt", "step_tu_amt",
           "prompt_tu_kpay", "step_tu_kpay",
           "step_tu_confirm",
           "prompt_staff_select", "step_staff_select",
           ]:
    func_to_domain[fn] = "members"

# Daily Sales
for fn in ["prompt_member", "prompt_console", "prompt_mins",
           "prompt_adjust_time", "step_adjust_time",
           "prompt_food_menu", "prompt_confirm", "prompt_kpay",
           "step_member", "step_console", "step_mins",
           "step_food_menu", "step_food_qty", "step_confirm",
           "step_kpay", "step_sale_confirm",
           "_check_member_in_session", "_check_console_in_session",
           "_end_single_session_and_launch",
           "step_ds_member_in_session", "step_ds_console_in_session",
           "cmd_sales_direct",
           "launch_session_sale", "prompt_session_shortfall",
           "step_session_shortfall",
           ]:
    func_to_domain[fn] = "sales"

# Discount/Promotions (extracted from sales range but separate module)
for fn in ["prompt_discount", "step_discount",
           "prompt_promo_select", "step_promo_select",
           "step_bundle_foc"]:
    func_to_domain[fn] = "discount"

# Stock Out
for fn in ["step_stock_pin", "show_stock_menu", "step_stock_menu",
           "show_stock_out_items", "step_stock_item", "step_stock_qty",
           "cmd_stock_menu", "cmd_stockin_direct", "cmd_stockout_direct"]:
    func_to_domain[fn] = "stock"

# Stock In
for fn in ["show_si_items", "step_si_item", "step_si_qty",
           "step_si_cost", "show_si_cart", "step_si_cart",
           "_show_si_review", "step_si_pay", "step_si_pay_split",
           "step_si_confirm"]:
    func_to_domain[fn] = "stock_in"

# Reports (Inventory, StockToday, Today's Report)
for fn in ["cmd_inventory", "cmd_stocktoday",
           "cmd_today_report", "cmd_promo_reports",
           "cmd_financial_report"]:
    func_to_domain[fn] = "reports"

# Console Booking / Staff Advance Booking
for fn in ["cmd_staff_book_hub", "cmd_confirmed_bookings",
           "cmd_staff_booking",
           "step_sbk_console", "step_sbk_cust_name",
           "step_sbk_date", "step_sbk_time", "step_sbk_dur",
           "step_sbk_game", "step_sbk_confirm",
           "_sbk_console_kb", "_sbk_parse_console_label",
           ]:
    func_to_domain[fn] = "booking"

# Console Booking Flow (book_link, book_console, etc)
for fn in ["prompt_book_console", "prompt_book_link",
           "_show_console_select", "step_book_link",
           "step_book_console", "step_book_member",
           "prompt_book_game", "step_book_game",
           "prompt_book_mins", "step_book_mins",
           "_do_create_booking", "step_book_dup_warn",
           ]:
    func_to_domain[fn] = "booking"

# Waitlist
for fn in ["cmd_waitlist_mgmt", "_show_wl_menu", "step_wl_menu",
           "cb_wl_action",
           "_wl_console_availability", "_fmt_mmt_dt",
           "_wl_status_label", "_wl_pref_label",
           ]:
    func_to_domain[fn] = "waitlist"

# Admin Bookings
for fn in ["cmd_admin_bookings", "cmd_approve_booking",
           "cmd_reject_booking", "cb_booking_mgmt",
           "_do_booking_action"]:
    func_to_domain[fn] = "admin_bookings"

# Game Library
for fn in ["show_game_menu", "step_game_menu",
           "step_game_add_title", "step_game_add_platform",
           "step_game_add_genre", "step_game_add_status",
           "step_game_edit_select", "step_game_edit_field",
           "step_game_edit_value", "step_game_del_select"]:
    func_to_domain[fn] = "games"

# Console Management & Session
for fn in ["show_console_menu", "step_console_menu",
           "prompt_game_change_cons", "step_game_change_cons",
           "step_game_change_game",
           "prompt_end_session", "step_end_session",
           "cmd_console_status"]:
    func_to_domain[fn] = "console"

# Console CRUD
for fn in ["show_con_mgmt_menu", "step_con_mgmt_menu",
           "step_con_add_id", "step_con_add_type",
           "step_con_add_mult", "step_con_del_select"]:
    func_to_domain[fn] = "console_mgmt"

# Console-Game Install
for fn in ["show_ginst_menu", "step_ginst_menu",
           "step_ginst_view_cons",
           "step_ginst_add_cons", "step_ginst_add_game",
           "step_ginst_add_type",
           "step_ginst_del_cons", "step_ginst_del_game",
           "_ginst_pick_console"]:
    func_to_domain[fn] = "ginst"

# SSD & Discs
for fn in ["show_ssd_menu", "step_ssd_menu",
           "step_ssd_view", "step_ssd_add_ssd",
           "step_ssd_add_game", "step_ssd_add_type",
           "step_ssd_del_ssd", "step_ssd_del_game",
           "step_ssd_xfer_ssd", "step_ssd_xfer_game",
           "step_ssd_xfer_cons",
           "step_ssd_ret_cons", "step_ssd_ret_game",
           "step_disc_select", "step_disc_set_qty",
           "_ssd_kb"]:
    func_to_domain[fn] = "ssd_disc"

# Finance
for fn in ["show_finance_menu", "step_finance_menu",
           "get_opex_sh", "get_assets_sh", "get_prepaid_fin_sh",
           "get_acct_trf_sh", "get_payables_sh", "get_receivables_sh",
           "get_advpay_sh",
           "prompt_opex_cat", "step_opex_cat", "step_opex_desc",
           "step_opex_amt", "step_opex_acct", "step_opex_pay",
           "step_opex_confirm",
           "prompt_asset_name", "step_asset_name", "step_asset_cat",
           "step_asset_date", "step_asset_cost", "step_asset_qty",
           "step_asset_life", "step_asset_salvage", "step_asset_pay",
           "step_asset_confirm",
           "_calc_nbv_per_unit",
           "prompt_asset_dispose_sel", "step_asset_dispose_sel",
           "step_asset_dispose_date", "step_asset_dispose_qty",
           "step_asset_dispose_proceeds", "step_asset_dispose_confirm",
           "prompt_prepaid_desc", "step_prepaid_desc",
           "step_prepaid_cat", "step_prepaid_amt", "step_prepaid_acct",
           "_prepaid_add_months", "step_prepaid_start",
           "step_prepaid_end", "step_prepaid_confirm",
           "prompt_acct_trf_from", "step_acct_trf_from",
           "step_acct_trf_to", "step_acct_trf_amt",
           "step_acct_trf_note", "step_acct_trf_confirm",
           "prompt_pay_vendor", "step_pay_vendor", "step_pay_desc",
           "step_pay_amt", "step_pay_due", "step_pay_acct",
           "step_pay_confirm",
           "prompt_rec_cust", "step_rec_cust", "step_rec_desc",
           "step_rec_amt", "step_rec_due", "step_rec_acct",
           "step_rec_confirm",
           "show_settle_list", "_handle_settle_list",
           "_show_settle_confirm", "_handle_settle_acct",
           "prompt_advpay_party", "step_advpay_party",
           "step_advpay_desc", "step_advpay_amt", "step_advpay_acct",
           "step_advpay_due", "step_advpay_note",
           "step_advpay_confirm", "show_advpay_settle",
           "step_advpay_list", "step_advpay_settle_confirm",
           "step_pay_settle_list", "step_rec_settle_list",
           "step_pay_settle_acct", "step_rec_settle_acct",
           "_handle_settle_confirm",
           "step_pay_settle_confirm", "step_rec_settle_confirm",
           "show_fin_report_menu", "step_fin_report_menu",
           "cmd_fin_pnl", "cmd_fin_bs", "cmd_fin_accts",
           "cmd_fin_depr", "cmd_fin_profit_share",
           "cmd_finance_setup", "cmd_finance",
           "get_capital_sh", "show_shareholder_menu",
           "step_shareholder_menu",
           "prompt_share_name", "step_share_name",
           "step_share_role", "step_share_cap",
           "step_share_own", "step_share_confirm",
           "prompt_cap_acct", "step_cap_acct",
           "step_cap_amt", "step_cap_confirm",
           ]:
    func_to_domain[fn] = "finance"

# Admin Panel
for fn in ["cmd_admin_pnl", "cmd_admin_cashflow",
           "cmd_admin_liability",
           "fetch_salary_advances", "cmd_admin_sal_adv",
           "_parse_date_mmt", "fetch_alltime_effective_rate",
           "calc_monthly_pnl",
           "show_admin_menu", "step_admin_menu",
           "step_admin_pin", "step_admin_menu",
           "cmd_admin",
           "_pin_then",
           ]:
    func_to_domain[fn] = "admin"

# Attendance
for fn in ["cmd_setattend", "step_attend_staff", "step_attend_leave",
           "step_attend_late", "step_attend_deduct",
           "_attend_save_and_next", "_attend_finish",
           "cmd_setattend_cmd"]:
    func_to_domain[fn] = "attendance"

# Payroll & KPI
for fn in ["calc_monthly_payroll", "cmd_payroll",
           "cmd_payroll_cmd", "cmd_kpi_cmd"]:
    func_to_domain[fn] = "payroll"

# Salary Advance
for fn in ["step_sal_adv_staff", "step_sal_adv_amt",
           "step_sal_adv_pay", "step_sal_adv_confirm"]:
    func_to_domain[fn] = "salary_adv"

# Broadcast & KPI display
for fn in ["cmd_broadcast", "cmd_staff_kpi"]:
    func_to_domain[fn] = "broadcast"

# Booking Timer/Extend/Cancel
for fn in ["_extend_timer_kb", "_remind_key", "_cancel_remind",
           "_is_session_active", "_remind_loop",
           "_send_session_reminder",
           "_post_n8n_session_reminder", "_post_n8n_booking_reminder",
           "cmd_cancel_booking", "cb_cancel_booking",
           "cb_cancel_with_reason", "_do_cancel_booking",
           "handle_cancel_note_input",
           "_do_extend", "cb_extend_timer", "cb_booking_arrive",
           "handle_custom_extend_reply"]:
    func_to_domain[fn] = "booking_flow"

# Notifications
for fn in ["_notify_customer", "get_customer_chat_id",
           "_check_low_balance_alert"]:
    func_to_domain[fn] = "notify"

# Help/Version/Error
for fn in ["cmd_version", "cmd_help", "error_handler"]:
    func_to_domain[fn] = "help"

# Referral Code
for fn in ["prompt_referral_code", "step_referral_code"]:
    func_to_domain[fn] = "referral"

# Command shortcuts
for fn in ["cmd_topup", "cmd_member_mgmt", "cmd_check_member",
           "cmd_newmember", "cmd_ranks", "cmd_cancel"]:
    func_to_domain[fn] = "commands"

# ── Now scan the file for ALL functions and assign domains ─────────────
func_pattern = re.compile(r'^(async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
all_funcs = []
for i, line in enumerate(lines):
    m = func_pattern.match(line.strip())
    if m:
        all_funcs.append((i + 1, m.group(2)))

domain_funcs = {}
unmapped = []
for lineno, fname in all_funcs:
    domain = func_to_domain.get(fname)
    if domain:
        domain_funcs.setdefault(domain, []).append((lineno, fname))
    else:
        # Skip inner functions and helper lambdas
        if not fname.startswith("_"):
            unmapped.append((lineno, fname))

if unmapped:
    print(f"⚠️  {len(unmapped)} unmapped non-private functions (may be inner helpers):")
    for ln, fn in unmapped:
        print(f"  Line {ln}: {fn}")

# ── Function extraction ────────────────────────────────────────────────
def find_func_end(start_line):
    """Find the end line of a top-level function."""
    i = start_line - 1
    indent = len(lines[i]) - len(lines[i].lstrip())
    for j in range(i + 1, len(lines)):
        stripped = lines[j].strip()
        if not stripped:
            continue
        line_indent = len(lines[j]) - len(lines[j].lstrip())
        if line_indent <= indent:
            if stripped.startswith("@"):
                continue
            if re.match(r'^(async\s+)?def\s+|^class\s+|^#\s+[═╤╧╔╗╚╝║]', stripped):
                return j
            # Check if it's really a new definition or just continuation
            if re.match(r'^(async\s+)?def\s+', stripped):
                return j
            if '═' in stripped and stripped.startswith('#'):
                return j
            # Might be continuation; check if previous line ended properly
            prev = lines[j-1].strip() if j > 0 else ""
            if prev.endswith("\\") or prev.endswith(",") or prev.endswith("("):
                continue
            return j
    return len(lines)

func_blocks = {}
for lineno, fname in all_funcs:
    end = find_func_end(lineno)
    code_lines = lines[lineno-1:end]
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()
    func_blocks[fname] = "\n".join(code_lines)

# ── Import header ──────────────────────────────────────────────────────
IMPORT_HEADER = '''"""PS VIBE Bot — {domain_title} handlers.
Auto-refactored from monolithic handlers.py (Phase 6).
"""
# ═══════ Imports from bot package ═══════
import bot as _bot_module  # for globals that need mutation  # noqa: F401
from bot import *  # noqa: F401,F403
'''

DOMAIN_TITLES = {
    "main_menu": "Main Menu",
    "members": "Member Management (NM/TU/MM)",
    "sales": "Daily Sales Flow",
    "stock": "Stock Out / Inventory",
    "stock_in": "Stock In (Restock)",
    "booking": "Console / Staff Booking",
    "waitlist": "Waitlist Management",
    "admin_bookings": "Admin Booking Management",
    "games": "Game Library",
    "console": "Console Management & Session Control",
    "console_mgmt": "Console CRUD",
    "ginst": "Console-Game Installation Tracking",
    "ssd_disc": "SSD Management & Game Discs",
    "finance": "Finance (OPEX, Assets, Payables, Receivables)",
    "admin": "Admin Panel & Reports",
    "attendance": "Attendance (Leave/Late)",
    "payroll": "Payroll & KPI",
    "discount": "Discount & Promotions",
    "commands": "Command Shortcuts",
    "broadcast": "Broadcast & KPI Display",
    "booking_flow": "Booking Timer & Cancel/Extend",
    "notify": "Customer Notifications",
    "help": "Help, Version & Error Handler",
    "referral": "Referral Code Assignment",
    "salary_adv": "Salary Advance",
    "reports": "Reports (Inventory, Stock, Daily)",
}

# ── Write domain files ─────────────────────────────────────────────────
written_files = []
for domain in sorted(domain_funcs.keys()):
    funcs_list = domain_funcs[domain]
    if not funcs_list:
        continue
    
    title = DOMAIN_TITLES.get(domain, domain.replace("_", " ").title())
    header = IMPORT_HEADER.format(domain_title=title)
    body_parts = [header, ""]
    
    for lineno, fname in funcs_list:
        if fname in func_blocks:
            body_parts.append(func_blocks[fname])
            body_parts.append("")  # blank separator
    
    if len(body_parts) <= 2:
        continue
    
    filepath = os.path.join(OUT, f"{domain}.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(body_parts))
    written_files.append(domain)
    print(f"  handlers/{domain}.py — {len(funcs_list)} functions ({title})")

# ── Create handlers/__init__.py ────────────────────────────────────────
init_lines = [
    '"""PS VIBE Bot — Handlers package (Phase 6 refactor).',
    'Domain-split modules for maintainability.',
    '',
    'All handler functions are re-exported for backward compatibility.',
    '"""',
    '# ═══════ Domain handler modules ═══════',
    '',
]
for domain in written_files:
    init_lines.append(f'from .{domain} import *  # noqa: F401,F403')
init_lines.append('')

with open(os.path.join(OUT, "__init__.py"), "w", encoding="utf-8") as f:
    f.write("\n".join(init_lines))

print(f"\n✅ Created {len(written_files)} domain modules in handlers/")
print(f"✅ Created handlers/__init__.py with {len(written_files)} imports")
print(f"\nTotal functions mapped: {sum(len(v) for v in domain_funcs.values())}")
