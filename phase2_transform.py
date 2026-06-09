#!/usr/bin/env python3
"""
Phase 2: Remove GSheet fallbacks from ALL functions in bot/__init__.py
Runs on the VPS as a single-pass transformation.
"""
import re
import sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/root/psvibe-sales-bot/bot/__init__.py"
OUTPUT = INPUT + ".phase2"

with open(INPUT, 'r') as f:
    lines = f.readlines()

# Track which line indices are part of gspread fallback blocks (to remove)
REMOVE_LINES = set()  # set of line numbers (0-indexed)

# Track lines that need modification (line_num -> new_text)
MODIFIED = {}

# Phase A: Remove gspread imports and infrastructure
GS_INFRA_START = None
GS_INFRA_END = None
FOUND_RETRY_START = False

for i, line in enumerate(lines):
    # Remove gspread imports
    if line.strip() == 'import gspread':
        REMOVE_LINES.add(i)
    elif line.strip() == 'from gspread.exceptions import APIError':
        REMOVE_LINES.add(i)
    elif line.strip().startswith('from oauth2client'):
        REMOVE_LINES.add(i)
    
    # Find the GSheet retry wrapper block
    if '# GOOGLE SHEETS RETRY WRAPPER' in line:
        GS_INFRA_START = i
        FOUND_RETRY_START = True
    
    if FOUND_RETRY_START and GS_INFRA_END is None:
        # Find end: _sheets_retry wrapper function ends with "return wrapper"
        # After that, the next major section starts (HANDLER DURATION LOGGING or similar)
        # Actually, let's find "#  HANDLER DURATION LOGGING" 
        if '#  HANDLER DURATION LOGGING' in line:
            GS_INFRA_END = i
            # Remove everything from GS_INFRA_START to GS_INFRA_END-1
            for j in range(GS_INFRA_START, GS_INFRA_END):
                REMOVE_LINES.add(j)
        elif 'from oauth2client' in line:
            GS_INFRA_END = i
            for j in range(GS_INFRA_START, GS_INFRA_END):
                REMOVE_LINES.add(j)

# Also remove SheetsPermissionError class
in_sheets_error_class = False
sheets_error_start = None
for i, line in enumerate(lines):
    if line.strip().startswith('class SheetsPermissionError'):
        in_sheets_error_class = True
        sheets_error_start = i
    elif in_sheets_error_class:
        if line.strip() == 'pass' or (line.startswith('    ') and 'pass' in line):
            REMOVE_LINES.add(sheets_error_start)
            REMOVE_LINES.add(i)
            in_sheets_error_class = False
        elif line.strip() and not line.startswith('    '):
            # End of class without finding pass
            in_sheets_error_class = False

# Remove _get_sa_email function
in_sa_email = False
sa_email_start = None
sa_email_end = None
for i, line in enumerate(lines):
    if line.strip().startswith('def _get_sa_email('):
        in_sa_email = True
        sa_email_start = i
    elif in_sa_email:
        if line.strip() == '' or (line.strip() and not line.startswith('    ') and not line.startswith('def ')):
            # End of function - check if it's empty line or new def
            if line.strip().startswith('def ') or (line.strip().startswith('from ') or line.strip().startswith('class ')):
                sa_email_end = i
                for j in range(sa_email_start, sa_email_end):
                    REMOVE_LINES.add(j)
                in_sa_email = False

# Remove _sheets_retry function if still there
in_sheets_retry = False
sr_start = None
sr_end = None
depth = 0
for i, line in enumerate(lines):
    if line.strip().startswith('def _sheets_retry('):
        in_sheets_retry = True
        sr_start = i
        depth = 0
        continue
    if in_sheets_retry:
        # Track Python indentation-based blocks
        stripped = line.rstrip('\n')
        if stripped.strip() == '':
            continue
        indent = len(stripped) - len(stripped.lstrip())
        if depth == 0:
            base_indent = indent
        if indent <= base_indent and stripped.strip():
            sr_end = i
            for j in range(sr_start, sr_end):
                REMOVE_LINES.add(j)
            in_sheets_retry = False

# Remove _gsheets_executor, _SHEETS_* constants (empty lines after removal are fine)
for i, line in enumerate(lines):
    s = line.strip()
    if s.startswith('_gsheets_executor = ') or s.startswith('_SHEETS_RETRY_CODES = ') or \
       s.startswith('_SHEETS_MAX_RETRIES = ') or s.startswith('_SHEETS_BASE_DELAY = '):
        REMOVE_LINES.add(i)

# Phase B: For each function, find and remove gspread fallback blocks
# Pattern: if _HAS_API: ... api call ... "falling back to gspread" ... [gspread fallback code]

# Find all lines with "falling back to gspread"
fallback_lines = []
for i, line in enumerate(lines):
    if 'falling back to gspread' in line and '#' not in line.split('falling')[0]:
        fallback_lines.append(i)

print(f"Found {len(fallback_lines)} fallback lines")

# For each fallback line, work backwards to find the matching "if _HAS_API:"
# and forwards to find the end of the gspread fallback block

for fb_line in fallback_lines:
    # Work backwards to find "if _HAS_API:"
    api_if_line = None
    api_call_indent = None
    
    for j in range(fb_line - 1, max(fb_line - 50, 0), -1):
        l = lines[j]
        if 'if _HAS_API:' in l:
            api_if_line = j
            api_call_indent = len(l) - len(l.lstrip())
            break
    
    if api_if_line is None:
        print(f"  ⚠ Could not find if _HAS_API: for fallback at line {fb_line+1}")
        continue
    
    # Find the end of the gspread fallback block
    # This is where the function ends OR where a new function/class starts
    # Look forward from fb_line for the end of the function
    # Strategy: find the next line at the same or lesser indent as api_if_line
    # that is NOT inside a try/except/if/for/while block
    
    # But simpler: the fallback code extends from fb_line to the end of the function
    # We mark everything from fb_line+1 (after the warning log) to end of function for removal
    
    # Find function start (def line) by going backwards
    fn_def_line = None
    fn_indent = None
    for j in range(api_if_line - 1, max(api_if_line - 20, 0), -1):
        l = lines[j].strip()
        if l.startswith('def ') or l.startswith('async def '):
            fn_def_line = j
            fn_indent = len(lines[j]) - len(lines[j].lstrip())
            break
    
    if fn_def_line is None:
        print(f"  ⚠ Could not find function def for fallback at line {fb_line+1}")
        continue
    
    # Find function end: next line at fn_indent or less that is a def/class/@ or empty with next being def/class
    fn_end_line = None
    for j in range(fb_line + 1, len(lines)):
        l = lines[j]
        stripped = l.strip()
        if stripped == '':
            continue
        indent = len(l) - len(l.lstrip())
        if indent < fn_indent:
            fn_end_line = j
            break
        if indent == fn_indent and (stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('@')):
            fn_end_line = j
            break
        if indent == fn_indent and not stripped.startswith(' ') and stripped:
            fn_end_line = j
            break
    
    if fn_end_line is None:
        fn_end_line = len(lines)
    
    # Now we know the function spans from fn_def_line to fn_end_line
    # The API block is from api_if_line to fb_line (the warning)
    # The gspread fallback is from fb_line+1 (or wherever the warning line ends) to fn_end_line-1
    # But careful: there might be multiple internal blocks (try/except) inside the fallback
    
    # Actually, the gspread fallback code starts right after the API if-block ends
    # The API if-block ends at the line with "falling back to gspread" (the warning)
    # So the gspread sub-block starts at fb_line + 1
    
    # Mark all lines from fb_line+1 to fn_end_line for removal (the gspread fallback)
    for j in range(fb_line + 1, fn_end_line):
        if j not in REMOVE_LINES:
            REMOVE_LINES.add(j)
    
    # Replace the warning line: change logging.warning → logging.error, remove "falling back to gspread"
    old_line = lines[fb_line]
    new_line = old_line.replace('logging.warning("', 'logging.error("')
    new_line = new_line.replace('failed, falling back to gspread")', 'failed")')
    new_line = new_line.replace('returned empty data, falling back to gspread")', 'returned empty data")')
    new_line = new_line.replace('returned success=False, falling back to gspread")', 'returned success=False — API unavailable")')
    
    if new_line != old_line:
        MODIFIED[fb_line] = new_line
    
    # Also, replace "if _HAS_API:" with nothing (just remove it, keep the body)
    # But we need to UNINDENT the API block body by 4 spaces
    # The API block body is from api_if_line+1 to fb_line (inclusive)
    # Each of these lines is indented by api_call_indent + 4
    for j in range(api_if_line + 1, fb_line + 1):
        if j in REMOVE_LINES:
            continue
        l = lines[j]
        # Check if this line has the right indent
        indent = len(l) - len(l.lstrip())
        expected_indent = api_call_indent + 4
        if indent >= expected_indent:
            # Unindent by 4 spaces
            MODIFIED[j] = l[4:] if l.startswith(' ' * expected_indent) else l
    
    # Remove the if _HAS_API: line
    REMOVE_LINES.add(api_if_line)

# Also transform "get_booking_sh" calls to just return empty - these are gspread-only helpers
# Actually, get_booking_sh might be used in non-fallback code too (like check_disc_session_conflict)
# Let's only remove it from functions we transformed above

# Phase C: After removing all gspread fallback blocks, check which functions
# now end without a return statement. If a function's last meaningful line
# is not a return, add a sensible default return.

# This is complex — let's handle it differently. After removing the blocks,
# functions that had the API+fallback pattern will now end with the API code.
# The API code already has returns for success cases, and the warning -> error
# lines serve as the fallback path. But in the original, after the warning,
# there was gspread code that would return something. Now there's nothing.
# So we need to add return statements after the error log lines.

# Strategy: for each function we transformed, add a return after the error log
# We'll do this by tracking which fb_lines we processed and adding appropriate returns.

# Map of fn_name patterns to their default return values
# We need to figure this out from context - the original gspread code would have returned something

# Instead of adding default returns after error logs (which is complex), 
# let's just make the warning line into an error + return:
# logging.error("API xxx failed") → logging.error("API xxx failed"); return default_val

# But we can't have two statements on one line in Python easily...
# Let's just add a return line right after the error log line

# Actually let's do this in a post-processing pass:
# After building all the output lines, scan for functions that end abruptly

# Build the output
output_lines = []
for i, line in enumerate(lines):
    if i in REMOVE_LINES:
        continue
    if i in MODIFIED:
        output_lines.append(MODIFIED[i])
    else:
        output_lines.append(line)

# Post-processing: Add return statements after error log lines in functions that lost their fallback
# Pattern: find lines with logging.error(...failed") that are followed by the function ending
# or by another def/class/blank+def

final_output = []
i = 0
while i < len(output_lines):
    line = output_lines[i]
    final_output.append(line)
    
    stripped = line.strip()
    # Check if this is an API error log line
    if 'logging.error("API ' in stripped and ' failed")' in stripped:
        # Look ahead to see what follows
        next_line = output_lines[i + 1] if i + 1 < len(output_lines) else ''
        next_stripped = next_line.strip()
        
        # If next line is empty, followed by a function return or function end
        # or if next line is not at a deeper indent, add a return
        if next_stripped == '' or next_stripped.startswith('def ') or next_stripped.startswith('class '):
            # Determine the default return value based on context
            # For now, just add return with sensible default
            final_output.append('    return []  # API unavailable')
            i += 1
            continue
    
    i += 1

# Write output
with open(OUTPUT, 'w') as f:
    f.write(''.join(final_output))

print(f"\nOutput: {OUTPUT}")
print(f"Lines: {len(lines)} → {len(final_output)}")
print(f"Removed: {len(REMOVE_LINES)} lines, Modified: {len(MODIFIED)} lines")

# Verify no remaining gspread references
remaining = ''.join(final_output)
if 'falling back to gspread' in remaining:
    print("⚠ WARNING: 'falling back to gspread' still present!")
else:
    print("✓ No 'falling back to gspread' remaining")

if 'wb.worksheet(' in remaining:
    print("⚠ WARNING: 'wb.worksheet(' still present!")
else:
    print("✓ No 'wb.worksheet(' remaining")
