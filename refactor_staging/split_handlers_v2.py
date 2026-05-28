#!/usr/bin/env python3
"""
Phase 6 Refactor: Split handlers.py into domain modules.
Each module gets proper imports and only its own functions.
"""
import os, re

BASE = "/home/node/.openclaw/workspace/refactor_staging"
HANDLERS = f"{BASE}/handlers.py.full"
OUT = f"{BASE}/handlers"

os.makedirs(OUT, exist_ok=True)

with open(HANDLERS, "r", encoding="utf-8") as f:
    full_text = f.read()
lines = full_text.split("\n")

# ── Extract all function names and line ranges ───────────────────────────
# Pattern: async def funcname(...  OR  def funcname(...
func_pattern = re.compile(r'^(async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
funcs = []
for i, line in enumerate(lines):
    m = func_pattern.match(line.strip())
    if m:
        funcs.append((i + 1, m.group(2)))

# ── Domain assignments based on function name prefixes ───────────────────
DOMAIN_RULES = {
    "main_menu":    ["show_main_menu", "step_main_menu"],
    "members":      ["prompt_nm", "step_nm", "prompt_mm", "step_mm",
                     "prompt_tu", "step_tu", "show_mm", "step_mm",
                     "show_rank", "prompt_staff_select", "step_staff_select",
                     "_PLACEHOLDER_prompt_discount",  # lives in members context
                     ],
    "sales":        ["prompt_member", "prompt_console", "prompt_mins",
                     "prompt_adjust", "step_adjust", "prompt_food",
                     "prompt_confirm", "prompt_kpay", "prompt_discount",
                     "prompt_promo", "step_promo", "step_bundle",
                     "step_member", "step_console", "step_mins",
                     "step_food_menu", "step_food_qty", "step_confirm",
                     "step_kpay", "step_sale_confirm",
                     "step_discount", "step_ds_",
                     "_check_member_in_session", "_check_console_in_session",
                     "_end_single_session",
                     "cmd_sales_direct",
                     "launch_session_sale", "prompt_session_shortfall",
                     "step_session_shortfall",
                     ],
    "stock":        ["step_stock_pin", "show_stock_menu", "step_stock_menu",
                     "show_stock_out", "step_stock_item", "step_stock_qty",
                     "cmd_stock_menu", "cmd_stockin_direct", "cmd_stockout_direct",
                     "cmd_inventory", "cmd_stocktoday",
                     ],
    "stock_in":     ["show_si_items", "step_si_item", "step_si_qty",
                     "step_si_cost", "show_si_cart", "step_si_cart",
                     "_show_si_review", "step_si_pay", "step_si_pay_split",
                     "step_si_confirm",
                     "_replit_get", "_replit_patch", "_replit_post",
                     "_update_inv_total_k1",
                     ],
    "booking":      ["cmd_staff_book_hub", "cmd_confirmed_bookings",
                     "cmd_staff_booking",
                     "step_sbk_console", "step_sbk_cust_name",
                     "step_sbk_date", "step_sbk_time", "step_sbk_dur",
                     "step_sbk_game", "step_sbk_confirm",
                     "_sbk_console_kb", "_sbk_parse_console_label",
                     "prompt_book_console", "prompt_book_link",
                     "_show_console_select", "step_book_link",
                     "step_book_console", "step_book_member",
                     "prompt_book_game", "step_book_game",
                     "prompt_book_mins", "step_book_mins",
                     "_do_create_booking", "step_book_dup_warn",
                     ],
    "waitlist":     ["cmd_waitlist_mgmt", "_show_wl_menu", "step_wl_menu",
                     "cb_wl_action",
                     "_wl_console_availability", "_fmt_mmt_dt",
                     "_wl_status_label", "_wl_pref_label",
                     ],
    "admin_bookings": ["cmd_admin_bookings", "cmd_approve_booking",
                       "cmd_reject_booking", "cb_booking_mgmt",
                       "_do_booking_action",
                       ],
    "games":        ["show_game_menu", "step_game_menu",
                     "step_game_add_title", "step_game_add_platform",
                     "step_game_add_genre", "step_game_add_status",
                     "step_game_edit_select", "step_game_edit_field",
                     "step_game_edit_value", "step_game_del_select",
                     ],
    "console":      ["show_console_menu", "step_console_menu",
                     "prompt_game_change_cons", "step_game_change_cons",
                     "step_game_change_game",
                     "prompt_end_session", "step_end_session",
                     "cmd_console_status",
                     ],
    "console_mgmt": ["show_con_mgmt_menu", "step_con_mgmt_menu",
                     "step_con_add_id", "step_con_add_type",
                     "step_con_add_mult", "step_con_del_select",
                     ],
    "ginst":        ["show_ginst_menu", "step_ginst_menu",
                     "step_ginst_view_cons",
                     "step_ginst_add_cons", "step_ginst_add_game",
                     "step_ginst_add_type",
                     "step_ginst_del_cons", "step_ginst_del_game",
                     "_ginst_pick_console",
                     ],
    "ssd_disc":     ["show_ssd_menu", "step_ssd_menu",
                     "step_ssd_view", "step_ssd_add_ssd",
                     "step_ssd_add_game", "step_ssd_add_type",
                     "step_ssd_del_ssd", "step_ssd_del_game",
                     "step_ssd_xfer_ssd", "step_ssd_xfer_game",
                     "step_ssd_xfer_cons",
                     "step_ssd_ret_cons", "step_ssd_ret_game",
                     "step_disc_select", "step_disc_set_qty",
                     "_ssd_kb",
                     ],
    "finance":      ["show_finance_menu", "step_finance_menu",
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
                     ],
    "admin":        ["cmd_admin_pnl", "cmd_admin_cashflow",
                     "cmd_admin_liability",
                     "_parse_date_mmt", "fetch_alltime_effective_rate",
                     "calc_monthly_pnl",
                     "show_admin_menu", "step_admin_menu",
                     "cmd_admin",
                     ],
    "attendance":   ["cmd_setattend", "step_attend_staff", "step_attend_leave",
                     "step_attend_late", "step_attend_deduct",
                     "_attend_save_and_next", "_attend_finish",
                     ],
    "payroll":      ["calc_monthly_payroll", "cmd_payroll"],
    "discount":     [],  # discount functions live in sales.py since they're part of sales flow
    "commands":     ["cmd_topup", "cmd_member_mgmt", "cmd_check_member",
                     "cmd_newmember", "cmd_ranks",
                     "cmd_sales_direct",  # already in sales
                     ],
    "broadcast":    ["cmd_broadcast", "cmd_staff_kpi",
                     "cmd_financial_report", "cmd_today_report",
                     "cmd_promo_reports",
                     ],
    "booking_flow": ["_extend_timer_kb", "_remind_key", "_cancel_remind",
                     "_is_session_active", "_remind_loop",
                     "_send_session_reminder",
                     "_post_n8n_session_reminder", "_post_n8n_booking_reminder",
                     "cmd_cancel_booking", "cb_cancel_booking",
                     "cb_cancel_with_reason", "_do_cancel_booking",
                     "handle_cancel_note_input",
                     "_do_extend", "cb_extend_timer", "cb_booking_arrive",
                     "handle_custom_extend_reply",
                     ],
    "notify":       ["_notify_customer", "get_customer_chat_id",
                     "_check_low_balance_alert",
                     ],
    "help":         ["cmd_version", "cmd_help", "error_handler"],
    "referral":     ["prompt_referral_code", "step_referral_code"],
    "salary_adv":   ["step_sal_adv_staff", "step_sal_adv_amt",
                     "step_sal_adv_pay", "step_sal_adv_confirm",
                     ],
}

# Also handle the step_admin_pin and step_admin_menu
DOMAIN_RULES["admin"].extend(["step_admin_pin", "step_admin_menu"])

# Build reverse mapping: func_name -> domain
func_to_domain = {}
for domain, names in DOMAIN_RULES.items():
    for name in names:
        func_to_domain[name] = domain

# Map every function to a domain
domain_funcs = {d: [] for d in DOMAIN_RULES}
unmapped = []
for lineno, fname in funcs:
    domain = func_to_domain.get(fname)
    if domain:
        domain_funcs[domain].append((lineno, fname))
    else:
        unmapped.append((lineno, fname))

if unmapped:
    print(f"UNMAPPED functions ({len(unmapped)}):")
    for ln, fn in unmapped:
        print(f"  Line {ln}: {fn}")

# ── Function extraction: find start/end lines for each function ──────────
def find_func_end(start_line):
    """Find the end line of a function (1-indexed). Returns end line (inclusive)."""
    # Simple heuristic: find next function def or section separator at same indent
    i = start_line - 1  # 0-indexed
    # Count indent of function def
    indent = len(lines[i]) - len(lines[i].lstrip())
    depth = 0
    started = False
    for j in range(i, len(lines)):
        stripped = lines[j].strip()
        if j == i:
            started = True
            continue
        # Skip empty lines
        if not stripped:
            continue
        # Check if we hit a new top-level definition
        line_indent = len(lines[j]) - len(lines[j].lstrip())
        if line_indent <= indent and stripped:
            # Check if it's a decorator or continuation
            if stripped.startswith("@") or stripped.startswith(")") or stripped.startswith("]") or stripped.startswith("}"):
                continue
            # Check if it's a new def/class at same level
            if re.match(r'^(async\s+)?def\s+|^class\s+|^#\s+[═╤╧╔╗╚╝║]', stripped):
                return j  # 0-indexed, line before this
            # Could be a continuation line
            if stripped.startswith("#") and "═" not in stripped:
                continue
            return j  # end on this line
    return len(lines)

# Extract each function's code as (start_line, end_line, name, code)
func_blocks = {}
for lineno, fname in funcs:
    end = find_func_end(lineno)
    code_lines = lines[lineno-1:end]
    # Trim trailing blank lines
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()
    func_blocks[fname] = "\n".join(code_lines)

# ── Import header for each domain file ────────────────────────────────
IMPORT_HEADER = '''"""PS VIBE Bot — {domain_title} handlers.
Auto-refactored from monolithic handlers.py (Phase 6).
"""
# ═══════ Imports from bot package ═══════
from bot import *  # noqa: F401,F403
'''
# Note: We keep `from bot import *` for now since the star import accesses 
# everything via the bot package namespace. In a follow-up step, we can
# replace with explicit imports.

# ── Write domain files ────────────────────────────────────────────────
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
    "commands": "Command Shortcuts",
    "broadcast": "Broadcast & Financial Reports",
    "booking_flow": "Booking Timer & Cancel/Extend",
    "notify": "Customer Notifications",
    "help": "Help, Version & Error Handler",
    "referral": "Referral Code Assignment",
    "salary_adv": "Salary Advance",
}

written_files = []
for domain in sorted(domain_funcs.keys()):
    funcs_list = domain_funcs[domain]
    if not funcs_list:
        continue
    
    title = DOMAIN_TITLES.get(domain, domain.replace("_", " ").title())
    header = IMPORT_HEADER.format(domain_title=title)
    body_parts = [header]
    
    for lineno, fname in funcs_list:
        if fname in func_blocks:
            body_parts.append(func_blocks[fname])
            body_parts.append("")  # blank line between functions
    
    if len(body_parts) <= 1:
        continue  # no actual functions found
    
    filepath = os.path.join(OUT, f"{domain}.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(body_parts))
    written_files.append(domain)
    print(f"  handlers/{domain}.py — {len(funcs_list)} functions ({title})")

# ── Create handlers/__init__.py ────────────────────────────────────────
init_lines = ['"""PS VIBE Bot — Handlers package (Phase 6 refactor).',
              'Domain-split modules for maintainability.',
              '"""',
              '# ═══════ Domain handler modules ═══════',
              '']
for domain in written_files:
    init_lines.append(f'from .{domain} import *  # noqa: F401,F403')
init_lines.append('')

with open(os.path.join(OUT, "__init__.py"), "w", encoding="utf-8") as f:
    f.write("\n".join(init_lines))

print(f"\n✅ Created {len(written_files)} domain modules in handlers/")
print(f"✅ Created handlers/__init__.py with {len(written_files)} imports")
