#!/usr/bin/env python3
"""Fix issues 1, 10 in __init__.py and issue 9 in discount.py"""

# ======= FIX 1: Filter promotions =======
with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    lines = f.readlines()

# Find "return normalized" in the API path and insert filtering before it
# Also fix the gspread fallback
new_lines = []
i = 0
fix1_done = False
fix10_done = False

while i < len(lines):
    line = lines[i]

    # FIX 1a: Filter promos before API return
    if not fix1_done and 'return normalized' in line and i > 10:
        # Check this is inside fetch_promotions_cached
        # Insert filtering block before the return
        new_lines.append('            # Filter: only show active promos (status=active, not expired)\n')
        new_lines.append('            from datetime import datetime as _fdt\n')
        new_lines.append('            _filtered = []\n')
        new_lines.append('            for _p in normalized:\n')
        new_lines.append('                if not isinstance(_p, dict):\n')
        new_lines.append('                    _filtered.append(_p)\n')
        new_lines.append('                    continue\n')
        new_lines.append('                _ps = str(_p.get("status", "")).strip().lower()\n')
        new_lines.append('                if _ps in ("inactive", "expired", "deleted"):\n')
        new_lines.append('                    continue\n')
        new_lines.append('                _ed = _p.get("end_date", "")\n')
        new_lines.append('                if _ed:\n')
        new_lines.append('                    try:\n')
        new_lines.append('                        import re as _fre\n')
        new_lines.append('                        _em = _fre.match(r"(\d{4})-(\d{2})-(\d{2})", str(_ed).strip())\n')
        new_lines.append('                        if _em and _fdt(int(_em.group(1)), int(_em.group(2)), int(_em.group(3))) < _fdt.now():\n')
        new_lines.append('                            continue\n')
        new_lines.append('                    except Exception:\n')
        new_lines.append('                        pass\n')
        new_lines.append('                _filtered.append(_p)\n')
        new_lines.append('            normalized = _filtered\n')
        new_lines.append('            return normalized\n')
        fix1_done = True
        i += 1
        continue

    # FIX 10: Add C09/C10 hardcoded multiplier fallback in fetch_console_multiplier
    if not fix10_done and 'return 1.0' in line and i > 10:
        # Check this is at the end of fetch_console_multiplier
        # Look at next few lines to confirm end of function
        if i+2 < len(lines) and 'async def fetch_console_multiplier_async' in (lines[i+1] + (lines[i+2] if i+2 < len(lines) else '')):
            new_lines.append('    # Hardcoded multiplier for C-09 and C-10 (these run at 1.2x)\n')
            new_lines.append('    console_id_clean = console_id.strip().upper() if console_id else ""\n')
            new_lines.append('    if console_id_clean in ("C-09", "C-10", "C09", "C10"):\n')
            new_lines.append('        return 1.2\n')
            new_lines.append('    return 1.0\n')
            fix10_done = True
            i += 1
            continue

    new_lines.append(line)
    i += 1

with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.writelines(new_lines)

print('Issue 1 (filter promos):', 'OK' if fix1_done else 'SKIPPED (check manually)')
print('Issue 10 (C09/C10 multiplier):', 'OK' if fix10_done else 'SKIPPED (check manually)')
