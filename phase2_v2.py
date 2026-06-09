#!/usr/bin/env python3
"""
Phase 2 single-pass transformer for bot/__init__.py
Reads line by line, removes gspread fallback blocks.
"""
import sys, re

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/root/psvibe-sales-bot/bot/__init__.py"
OUTPUT = INPUT + ".phase2"

with open(INPUT, 'r') as f:
    lines = f.readlines()

out = []
i = 0
removed_count = 0
transformed_fns = []

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Skip gspread import lines
    if stripped == 'import gspread':
        i += 1
        removed_count += 1
        continue
    if stripped == 'from gspread.exceptions import APIError':
        i += 1
        removed_count += 1
        continue
    if stripped.startswith('from oauth2client'):
        i += 1
        removed_count += 1
        continue
    
    # Skip gspread infrastructure variables
    if stripped.startswith('_gsheets_executor = ') or \
       stripped.startswith('_SHEETS_RETRY_CODES = ') or \
       stripped.startswith('_SHEETS_MAX_RETRIES = ') or \
       stripped.startswith('_SHEETS_BASE_DELAY = '):
        i += 1
        removed_count += 1
        continue
    
    # Track function context: are we in a function that has API+fallback?
    # Check if this line starts a function definition
    # Also check if approximately within a function that has API+fallback
    
    # First, check for the gspread retry wrapper block
    if '# GOOGLE SHEETS RETRY WRAPPER' in stripped:
        # Skip the entire block until HANDLER DURATION LOGGING
        while i < len(lines) and '#  HANDLER DURATION LOGGING' not in lines[i]:
            i += 1
            removed_count += 1
        continue
    
    # Skip SheetsPermissionError class
    if stripped.startswith('class SheetsPermissionError'):
        while i < len(lines):
            i += 1
            removed_count += 1
            if lines[i].strip() == 'pass' or (lines[i].strip() and not lines[i].startswith('    ')):
                break
        continue
    
    # Skip _get_sa_email function
    if stripped.startswith('def _get_sa_email('):
        while i < len(lines):
            i += 1
            removed_count += 1
            if lines[i].strip() == '' or (lines[i].strip() and not lines[i].startswith('    ')):
                break
        continue
    
    # Skip _sheets_retry decorator function
    if stripped.startswith('def _sheets_retry('):
        while i < len(lines):
            i += 1
            removed_count += 1
            if lines[i].strip() and not lines[i].startswith('    '):
                break
        continue
    
    # ==========================================
    # MAIN TRANSFORM: API+fallback pattern
    # ==========================================
    # Check if current line is "if _HAS_API:" at function body level
    indent = len(line) - len(line.lstrip())
    is_if_has_api = stripped == 'if _HAS_API:'
    
    if is_if_has_api:
        # Look ahead to see if this block contains "falling back to gspread"
        has_fallback = False
        fb_line_idx = None
        for j in range(i + 1, min(i + 80, len(lines))):
            if 'falling back to gspread' in lines[j]:
                has_fallback = True
                fb_line_idx = j
                break
        
        if has_fallback:
            # Find the function this belongs to (search backwards for def)
            fn_def_idx = None
            fn_def_indent = None
            for j in range(i - 1, max(i - 30, 0), -1):
                ls = lines[j].strip()
                if ls.startswith('def ') or ls.startswith('async def '):
                    fn_def_idx = j
                    fn_def_indent = len(lines[j]) - len(lines[j].lstrip())
                    break
            
            if fn_def_idx is None:
                out.append(line)
                i += 1
                continue
            
            fn_name = lines[fn_def_idx].strip()
            
            # Find the end of this function (next def/class at same or lesser indent)
            fn_end_idx = len(lines)  # default: end of file
            for j in range(fn_def_idx + 1, len(lines)):
                ls = lines[j].strip()
                if ls == '':
                    continue
                j_indent = len(lines[j]) - len(lines[j].lstrip())
                if j_indent == fn_def_indent and (ls.startswith('def ') or ls.startswith('class ') or ls.startswith('@')):
                    fn_end_idx = j
                    break
                if j_indent < fn_def_indent:
                    fn_end_idx = j
                    break
            
            # Now we need to transform:
            # 1. Output function signature + docstring (everything from fn_def_idx to i-1)
            for j in range(fn_def_idx, i):
                out.append(lines[j])
            
            # 2. Output the API block (from i+1 to fb_line), unindented by 4 spaces
            for j in range(i + 1, fb_line_idx + 1):
                api_line = lines[j]
                api_indent = len(api_line) - len(api_line.lstrip())
                if api_indent >= indent + 4:
                    # Unindent by 4 spaces
                    api_line = api_line[4:]
                out.append(api_line)
            
            # 3. Replace the warning with error
            # (already appended above, but let's modify it)
            # Actually, the warning line was already appended. Replace the last line.
            if out:
                last = out[-1]
                if 'falling back to gspread' in last:
                    last = last.replace('logging.warning("', 'logging.error("')
                    last = last.replace('failed, falling back to gspread")', 'failed")')
                    last = last.replace('returned empty data, falling back to gspread")', 'returned empty data")')
                    last = last.replace('returned success=False, falling back to gspread")', 'returned success=False")')
                    out[-1] = last
            
            # 4. Add a return default after the error log (if not present)
            # Check if the API block already has a return
            api_block_has_return = False
            for j in range(i + 1, fb_line_idx + 1):
                if 'return ' in lines[j]:
                    api_block_has_return = True
                    break
            
            if not api_block_has_return:
                # Add a sensible default return
                # Determine based on function context
                return_val = '[]'
                fn_text = lines[fn_def_idx].lower()
                if 'bool' in lines[fn_def_idx] or 'true' in fn_text or 'false' in fn_text:
                    return_val = 'False'
                elif 'str' in lines[fn_def_idx]:
                    return_val = '""'
                elif 'int' in lines[fn_def_idx]:
                    return_val = '0'
                elif 'dict' in lines[fn_def_idx]:
                    return_val = '{}'
                out.append(f'    return {return_val}  # API unavailable, no GSheet fallback\n')
            
            # 5. Skip the rest of the function (the gspread fallback code)
            skipped = fn_end_idx - fb_line_idx - 1
            removed_count += skipped
            i = fn_end_idx
            transformed_fns.append(fn_name)
            continue
    
    # Normal line - keep it
    out.append(line)
    i += 1

# Post-process: Remove now-unused get_*_sh() helper functions
# These are only used by gspread fallback code that's now removed
# But some might still be needed (like get_booking_sh for check_disc_session_conflict)
# We'll keep them for now but they'll become dead code

# Write output
with open(OUTPUT, 'w') as f:
    f.write(''.join(out))

print(f"Input: {len(lines)} lines")
print(f"Output: {len(out)} lines")
print(f"Removed: {removed_count} lines")
print(f"Transformed functions: {len(transformed_fns)}")
for f in transformed_fns:
    print(f"  {f}")

# Final check
content = ''.join(out)
if 'falling back to gspread' in content:
    print(f"\n⚠ WARNING: {content.count('falling back to gspread')} 'falling back to gspread' remaining!")
else:
    print("\n✓ All 'falling back to gspread' removed!")

if 'import gspread' in content:
    print("⚠ WARNING: 'import gspread' still present!")
else:
    print("✓ 'import gspread' removed!")
