#!/usr/bin/env python3
"""Extract and split handlers.py into domain modules.
Reads handlers.py.full, outputs to handlers/ directory.
"""
import re, os

HANDLERS_PATH = "/home/node/.openclaw/workspace/refactor_staging/handlers.py.full"
OUT_DIR = "/home/node/.openclaw/workspace/refactor_staging/handlers"

with open(HANDLERS_PATH, "r", encoding="utf-8") as f:
    content = f.read()
lines = content.split("\n")

# Domain boundaries (line numbers, 1-indexed)
# Based on grep output analysis
DOMAINS = {
    "_common":     (1, 103),      # Imports, helpers: show_main_menu, step_main_menu, staff whitelist, text kb rendering
    "main_menu":   (7, 102),      # show_main_menu, step_main_menu
    "members":     (103, 1276),   # Staff select, MM menu, New Member, Top Up
    "sales":       (1277, 2376),  # Daily Sales flow (prompts and steps)
    "payroll":     (2377, 2597),  # calc_monthly_payroll, cmd_payroll, cmd_staff_kpi
    "discount":    (2598, 3054),  # Discount/Promotions
    "commands":    (3055, 3133),  # Command shortcuts
    "finance":     (3134, 5050),  # Finance (OPEX, Assets, Prepaid, Transfer, Payables, Receivables, Settle, Advance Pay)
    "salary_adv":  (5050, 6166),  # Salary Advance
    "admin":       (6167, 6568),  # Admin Panel, Monthly P&L, Cashflow, Liability
    "booking":     (6569, 7150),  # Staff Booking / Console Booking
    "notify":      (7151, 7219),  # Customer notification helpers
    "waitlist":    (7220, 7490),  # Waitlist Management
    "admin_bookings": (7490, 7720), # Admin Booking Management
    "attendance":  (7721, 7858),  # Attendance wizard
    "reports":     (7859, 8310),  # Inventory, StockToday, Promo Reports, Today's Report, Financial Report
    "broadcast":   (8311, 8940),  # Broadcast, KPI, Console Status
    "booking_flow": (8940, 9754), # Session Timer, Booking Cancel/Extend, Booking flow
    "console":     (9755, 10200), # Console Menu, Game Change, End Session, Session→Sales Bridge
    "games":       (10201, 10611),# Game Library (add/del/edit)
    "ginst":       (10612, 10850),# Console-Game Install flows
    "ssd_disc":    (10852, 11325),# SSD Management, Discs Record
    "console_mgmt":(11326, 11468),# Console CRUD
    "help":        (11469, 11533),# Help, Version, Error handler
    "stock":       (11534, 11728),# Stock Out (PIN, menu, items)
    "stock_in":    (11729, 12016),# Stock In
    "referral":    (12017, 12142),# Referral Code
}

# ============================================================
# Part A: Create the merged __init__.py
# ============================================================
# The bot/__init__.py (local) is newer (177 states) vs outer (174 states).
# Outer is missing: BOOK_LINK, WL_MENU, ADJUST_TIME states and some buttons.
# We use bot/__init__.py as canonical merged version.

import shutil
shutil.copy("/home/node/.openclaw/workspace/refactor_staging/__init__.py",
            "/home/node/.openclaw/workspace/refactor_staging/__init___merged.py")
print("Created __init___merged.py (canonical version from bot/__init__.py)")

# Also create the minimal outer __init__.py
outer_init = '''"""PS VIBE Sales Bot — Package init (outer level).
The real package code is in bot/__init__.py.
This file exists for Python package resolution only.
"""
# Re-export everything from the bot package
from bot.__init__ import *  # noqa: F401,F403
'''
with open("/home/node/.openclaw/workspace/refactor_staging/__init___outer_minimal.py", "w") as f:
    f.write(outer_init)
print("Created __init___outer_minimal.py (lightweight outer __init__)")

# ============================================================
# Part B: Extract each domain's functions from handlers.py
# ============================================================
# We need to parse the actual function groupings
# Strategy: extract chunks between section separators

# First, let's just extract the content for each domain

domain_content = {}
for name, (start, end) in DOMAINS.items():
    # Convert 1-indexed to 0-indexed
    chunk = "\n".join(lines[start-1:end])
    domain_content[name] = chunk

# Write each domain file
for name, chunk in domain_content.items():
    filepath = os.path.join(OUT_DIR, f"{name}.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(chunk)
    print(f"Wrote handlers/{name}.py ({len(chunk.split(chr(10)))} lines)")

# Create the __init__.py for handlers package
handlers_init = '''"""PS VIBE Bot — Handlers package.
Domain-split modules re-exported for backward compatibility.
"""
# Shared helpers (imported by all modules)
from ._common import *  # noqa: F401,F403

# Domain handlers
from .main_menu import *  # noqa: F401,F403
from .sales import *  # noqa: F401,F403
from .members import *  # noqa: F401,F403
from .stock import *  # noqa: F401,F403
from .stock_in import *  # noqa: F401,F403
from .booking import *  # noqa: F401,F403
from .waitlist import *  # noqa: F401,F403
from .games import *  # noqa: F401,F403
from .console import *  # noqa: F401,F403
from .console_mgmt import *  # noqa: F401,F403
from .ginst import *  # noqa: F401,F403
from .ssd_disc import *  # noqa: F401,F403
from .finance import *  # noqa: F401,F403
from .admin import *  # noqa: F401,F403
from .admin_bookings import *  # noqa: F401,F403
from .attendance import *  # noqa: F401,F403
from .payroll import *  # noqa: F401,F403
from .discount import *  # noqa: F401,F403
from .reports import *  # noqa: F401,F403
from .broadcast import *  # noqa: F401,F403
from .referral import *  # noqa: F401,F403
from .help import *  # noqa: F401,F403
from .commands import *  # noqa: F401,F403
from .salary_adv import *  # noqa: F401,F403
from .booking_flow import *  # noqa: F401,F403
from .notify import *  # noqa: F401,F403
'''

with open(os.path.join(OUT_DIR, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(handlers_init)
print("Created handlers/__init__.py")

print("\nDone! All domain files extracted.")
