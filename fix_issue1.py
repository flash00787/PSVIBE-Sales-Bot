#!/usr/bin/env python3
"""Fix Issue 1: Filter inactive/expired promotions in fetch_promotions_cached()"""
import re

with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    content = f.read()

# Helper function to add (deduplicated)
def apply_filter_block(old_block, new_block):
    if old_block in content:
        return content.replace(old_block, new_block)
    return None

# ---- Fix 1: API path - filter after normalization ----
old_api = '            return normalized\n        logging.warning("API api_fetch_promotions_cached() failed, falling back to gspread")'

new_api = '''            # Filter: only show active promos (status=active, not expired)
            from datetime import datetime as _fdt
            active_promos = []
            for p in normalized:
                if not isinstance(p, dict):
                    active_promos.append(p)
                    continue
                pstatus = str(p.get("status", "")).strip().lower()
                if pstatus in ("inactive", "expired", "deleted"):
                    continue
                end_d = p.get("end_date", "")
                if end_d:
                    try:
                        ed = str(end_d).strip()
                        m = re.match(r'(\\d{4})-(\\d{2})-(\\d{2})', ed)
                        if m and _fdt(int(m.group(1)), int(m.group(2)), int(m.group(3))) < _fdt.now():
                            continue
                    except Exception:
                        pass
                active_promos.append(p)
            return active_promos
        logging.warning("API api_fetch_promotions_cached() failed, falling back to gspread")'''

result = apply_filter_block(old_api, new_api)
if result:
    content = result
    print('[OK] Issue 1 API path: FILTER ADDED')
else:
    print('[FAIL] Issue 1 API path: pattern not found')
    idx = content.find('return normalized')
    if idx > 0:
        print(f'Context: ...{content[idx-50:idx+80]}...')

# ---- Fix 1b: gspread fallback path - filter promos ----
# Need to find exact pattern
idx2 = content.find('_replit_get("sheets/promotions")')
if idx2 > 0:
    # Read surrounding context
    fallback_section = content[idx2:idx2+400]
    print(f'Fallback section: ...{fallback_section[:400]}...')

# The pattern uses both a local _dt that needs datetime import
# Let's find the exact block and replace
old_fb = '    data = _replit_get("sheets/promotions")\n    promos = (data or {}).get("promotions", [])\n    with _THREAD_CACHE_LOCK:\n        _PROMO_CACHE = promos\n        _PROMO_TS    = time.time()\n    return promos'

new_fb = '''    data = _replit_get("sheets/promotions")
    promos = (data or {}).get("promotions", [])
    # Filter: only show active promos
    from datetime import datetime as _fdt2
    active_promos = []
    for p in promos:
        if not isinstance(p, dict):
            active_promos.append(p)
            continue
        pstatus = str(p.get("status", "")).strip().lower()
        if pstatus in ("inactive", "expired", "deleted"):
            continue
        end_d = p.get("end_date", "")
        if end_d:
            try:
                ed = str(end_d).strip()
                m = re.match(r'(\d{4})-(\d{2})-(\d{2})', ed)
                if m and _fdt2(int(m.group(1)), int(m.group(2)), int(m.group(3))) < _fdt2.now():
                    continue
            except Exception:
                pass
        active_promos.append(p)
    promos = active_promos
    with _THREAD_CACHE_LOCK:
        _PROMO_CACHE = promos
        _PROMO_TS    = time.time()
    return promos'''

result2 = apply_filter_block(old_fb, new_fb)
if result2:
    content = result2
    print('[OK] Issue 1 gspread path: FILTER ADDED')
else:
    print('[FAIL] Issue 1 gspread path: pattern not found')
    # Try to find the exact location
    idx3 = content.find('_replit_get("sheets/promotions")')
    if idx3 > 0:
        print(f'Context around gspread path: ...{content[idx3:idx3+400]}...')

with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.write(content)
print('[DONE] fix_issue1.py completed')
