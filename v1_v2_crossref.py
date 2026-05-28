# SYSTEMATIC V.1 vs V.2 FUNCTION CROSS-REFERENCE
# Phase 1: Extract ALL callback_query handler functions from V.1 monolithic handlers.py
# These are the functions triggered when buttons are pressed

import sys
sys.path.insert(0, '/root')
import importlib.util
import re

# V.1 monolithic handlers.py
v1_path = '/root/Sales-Tele-Bot/main.py.bak.phase4'
with open(v1_path) as f:
    v1_lines = f.readlines()
v1_text = ''.join(v1_lines)

# V.2 handler files
import os
v2_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'

# Extract ALL ConversationHandler state callbacks from V.1
# Pattern: ConversationHandler(..., states={
#    STATE_NAME: [CallbackQueryHandler(function_name), ...],
# }, ...)

# Find CallbackQueryHandler patterns in V.1
v1_callbacks = set()
for line in v1_lines:
    # CallbackQueryHandler(cmd_staff_book_hub, pattern='^(BTN_STAFF_BOOK|BTN_MEMBER_MGMT)')
    matches = re.findall(r'CallbackQueryHandler\(\s*(\w+)\s*,', line)
    for m in matches:
        v1_callbacks.add(m)
    # Also find in actual function calls
    matches2 = re.findall(r'(?<!def )(\w+)_callback\b', line)
    for m in matches2:
        if m.endswith('_callback'):
            v1_callbacks.add(m)

# Find ALL function definitions in V.1  
v1_functions = {}
for line in v1_lines:
    m = re.match(r'^def (\w+)\(', line.strip())
    if m:
        v1_functions[m.group(1)] = line.strip()

print('=== V.1 CALLBACK HANDLERS REGISTERED ===')
for cb in sorted(v1_callbacks):
    print(f'  {cb}')
print(f'Total: {len(v1_callbacks)} callbacks')
print()
print('=== V.1 FUNCTIONS DEFINED ===')
for fn in sorted(v1_functions.keys()):
    print(f'  def {fn}')
print(f'Total: {len(v1_functions)} functions')
