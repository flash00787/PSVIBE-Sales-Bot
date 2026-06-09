#!/usr/bin/env python3
"""
Phase 2 v3: Remove GSheet fallbacks. Process from BOTTOM to TOP.
"""
import sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/root/psvibe-sales-bot/bot/__init__.py"
OUTPUT = INPUT + ".phase2"

with open(INPUT, 'r') as f:
    lines = f.readlines()

# Step 1: Find ALL fallback blocks (if _HAS_API: ... falling back to gspread)
# Store as: (api_if_line, fb_warn_line, fn_def_line)
blocks = []

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == 'if _HAS_API:':
        # Check if this block has "falling back to gspread" within next 80 lines
        has_fb = False
        fb_line = None
        for j in range(i + 1, min(i + 80, len(lines))):
            if 'falling back to gspread' in lines[j]:
                has_fb = True
                fb_line = j
                break
        
        if has_fb:
            # Find the function this block belongs to
            fn_def = None
            for j in range(i - 1, max(i - 30, 0), -1):
                ls = lines[j].strip()
                if ls.startswith('def ') or ls.startswith('async def '):
                    fn_def = j
                    break
            
            if fn_def is not None:
                blocks.append((i, fb_line, fn_def))

# Process from bottom to top to avoid line number shifts
blocks.sort(key=lambda x: x[2], reverse=True)  # Sort by fn_def_line descending

print(f"Found {len(blocks)} fallback blocks")

# Remove specific lines
REMOVE = set()
MODIFY = {}  # line_num -> new_text

for api_if_line, fb_line, fn_def_line in blocks:
    fn_def_indent = len(lines[fn_def_line]) - len(lines[fn_def_line].lstrip())
    api_if_indent = len(lines[api_if_line]) - len(lines[api_if_line].lstrip())
    
    # Find function end: next line at fn_def_indent that starts a new def/class
    fn_end = len(lines)
    for j in range(fn_def_line + 1, len(lines)):
        ls = lines[j].strip()
        if ls == '':
            continue
        j_indent = len(lines[j]) - len(lines[j].lstrip())
        if j_indent == fn_def_indent and (ls.startswith('def ') or ls.startswith('class ') or ls.startswith('@')):
            fn_end = j
            break
        if j_indent < fn_def_indent:
            fn_end = j
            break
    
    # Mark the if _HAS_API: line for removal
    REMOVE.add(api_if_line)
    
    # Unindent API block body (from api_if_line+1 to fb_line) by 4 spaces
    for j in range(api_if_line + 1, fb_line + 1):
        if j >= len(lines):
            break
        l = lines[j]
        j_indent = len(l) - len(l.lstrip())
        if j_indent >= api_if_indent + 4 and j not in REMOVE:
            MODIFY[j] = l[4:]  # remove 4 spaces
    
    # Modify the warning line: logging.warning → logging.error
    l = lines[fb_line]
    new_l = l.replace('logging.warning("', 'logging.error("')
    new_l = new_l.replace('failed, falling back to gspread")', 'failed")')
    new_l = new_l.replace('returned empty data, falling back to gspread")', 'returned empty data")')
    new_l = new_l.replace('returned success=False, falling back to gspread")', 'returned success=False")')
    if new_l != l:
        MODIFY[fb_line] = new_l
    
    # Mark gspread fallback code for removal (from fb_line+1 to fn_end-1)
    for j in range(fb_line + 1, fn_end):
        REMOVE.add(j)

# Step 2: Remove gspread infrastructure
for i, line in enumerate(lines):
    s = line.strip()
    if s in ('import gspread', 'from gspread.exceptions import APIError') or \
       s.startswith('from oauth2client') or \
       s.startswith('_gsheets_executor = ') or \
       s.startswith('_SHEETS_RETRY_CODES = ') or \
       s.startswith('_SHEETS_MAX_RETRIES = ') or \
       s.startswith('_SHEETS_BASE_DELAY = '):
        REMOVE.add(i)
    
    # Remove GSheet retry wrapper block
    if '# GOOGLE SHEETS RETRY WRAPPER' in s:
        # Find the end of this block (before HANDLER DURATION LOGGING)
        for j in range(i, len(lines)):
            if '#  HANDLER DURATION LOGGING' in lines[j]:
                for k in range(i, j):
                    REMOVE.add(k)
                break

# Remove SheetsPermissionError class
for i, line in enumerate(lines):
    if line.strip().startswith('class SheetsPermissionError'):
        for j in range(i, len(lines)):
            REMOVE.add(j)
            if lines[j].strip() == 'pass':
                break
        break

# Remove _get_sa_email function
for i, line in enumerate(lines):
    if line.strip().startswith('def _get_sa_email('):
        # Find end of function
        j = i + 1
        while j < len(lines) and (lines[j].strip() == '' or lines[j].startswith('    ') or lines[j].startswith('\t')):
            REMOVE.add(j)
            j += 1
        REMOVE.add(i)
        break

# Remove _sheets_retry decorator
for i, line in enumerate(lines):
    if line.strip().startswith('def _sheets_retry('):
        indent = len(line) - len(line.lstrip())
        j = i + 1
        while j < len(lines):
            REMOVE.add(j)
            ls = lines[j].strip()
            if ls and len(lines[j]) - len(lines[j].lstrip()) <= indent:
                break
            j += 1
        REMOVE.add(i)
        break

# Build output
out = []
for i, line in enumerate(lines):
    if i in REMOVE:
        continue
    if i in MODIFY:
        out.append(MODIFY[i])
    else:
        out.append(line)

# Write
with open(OUTPUT, 'w') as f:
    f.write(''.join(out))

print(f"Lines: {len(lines)} → {len(out)}")
print(f"Removed: {len(REMOVE)} lines")
print(f"Modified: {len(MODIFY)} lines")

content = ''.join(out)
remaining_fb = content.count('falling back to gspread')
remaining_api = content.count('if _HAS_API:')
print(f"Remaining 'falling back to gspread': {remaining_fb}")
print(f"Remaining 'if _HAS_API:': {remaining_api}")

# Check for duplicate function definitions  
import re
fns = re.findall(r'^(?:async )?def (\w+)\(', content, re.MULTILINE)
from collections import Counter
dupes = {k: v for k, v in Counter(fns).items() if v > 1}
if dupes:
    print(f"\n⚠ Duplicate function definitions: {dupes}")
else:
    print("\n✓ No duplicate function definitions")
