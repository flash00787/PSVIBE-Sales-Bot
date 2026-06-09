import re

with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    content = f.read()

# 1. Add _THREAD_CACHE_LOCK after _CACHE_LOCK
content = content.replace(
    '_CACHE_LOCK = asyncio.Lock()',
    '_CACHE_LOCK = asyncio.Lock()  # async lock for background tasks\n_THREAD_CACHE_LOCK = _threading.Lock()  # thread-safe lock for sync cache fns'
)

# 2. Wrap fetch_promotions_cached cache read/write
old_promo = "    global _PROMO_CACHE, _PROMO_TS\n    if _PROMO_CACHE and (time.time() - _PROMO_TS) < _PROMO_TTL:\n        return _PROMO_CACHE\n    data = _replit_get(" + '"' + "sheets/promotions" + '"' + ")\n    promos = (data or {}).get(" + '"' + "promotions" + '"' + ", [])\n    _PROMO_CACHE = promos\n    _PROMO_TS    = time.time()\n    return promos"

new_promo = "    global _PROMO_CACHE, _PROMO_TS\n    with _THREAD_CACHE_LOCK:\n        if _PROMO_CACHE and (time.time() - _PROMO_TS) < _PROMO_TTL:\n            return _PROMO_CACHE\n    data = _replit_get(" + '"' + "sheets/promotions" + '"' + ")\n    promos = (data or {}).get(" + '"' + "promotions" + '"' + ", [])\n    with _THREAD_CACHE_LOCK:\n        _PROMO_CACHE = promos\n        _PROMO_TS    = time.time()\n    return promos"

if old_promo in content:
    content = content.replace(old_promo, new_promo)
    print('Patched fetch_promotions_cached')
else:
    print('WARNING: fetch_promotions_cached pattern not found!')

# 3. Wrap _load_cfg cache write
old_cfg = 'def _load_cfg() -> None:\n    global _CFG, _CFG_TS\n    data = _replit_get("sheets/config")\n    if data and "base_rate" in data:\n        _CFG    = data\n        _CFG_TS = time.time()\n        logging.info("Config cache refreshed (base_rate=%s)", data.get("base_rate"))'

new_cfg = 'def _load_cfg() -> None:\n    global _CFG, _CFG_TS\n    data = _replit_get("sheets/config")\n    if data and "base_rate" in data:\n        with _THREAD_CACHE_LOCK:\n            _CFG    = data\n            _CFG_TS = time.time()\n        logging.info("Config cache refreshed (base_rate=%s)", data.get("base_rate"))'

if old_cfg in content:
    content = content.replace(old_cfg, new_cfg)
    print('Patched _load_cfg')
else:
    print('WARNING: _load_cfg pattern not found!')

# 4. Wrap _cfg_fresh cache read
old_fresh = 'def _cfg_fresh() -> bool:\n    return bool(_CFG) and (time.time() - _CFG_TS) < _CFG_TTL'

new_fresh = 'def _cfg_fresh() -> bool:\n    with _THREAD_CACHE_LOCK:\n        return bool(_CFG) and (time.time() - _CFG_TS) < _CFG_TTL'

if old_fresh in content:
    content = content.replace(old_fresh, new_fresh)
    print('Patched _cfg_fresh')
else:
    print('WARNING: _cfg_fresh pattern not found!')

# 5. Wrap _mbr_fresh cache read (also module-level cache)
old_mbr = 'def _mbr_fresh() -> bool:\n    return bool(_MBR_ROWS) and (time.time() - _MBR_TS) < _MBR_TTL'

new_mbr = 'def _mbr_fresh() -> bool:\n    with _THREAD_CACHE_LOCK:\n        return bool(_MBR_ROWS) and (time.time() - _MBR_TS) < _MBR_TTL'

if old_mbr in content:
    content = content.replace(old_mbr, new_mbr)
    print('Patched _mbr_fresh')
else:
    print('WARNING: _mbr_fresh pattern not found!')

# 6. Wrap _load_members cache write
old_load_members = 'def _load_members() -> None:\n    global _MBR_ROWS, _MBR_TS\n    try:\n        _MBR_ROWS = member_sh.get("A:Q")  # OPT: range-restricted read (A=row_no through Q=referral_code)\n        _MBR_TS   = time.time()'

new_load_members = 'def _load_members() -> None:\n    global _MBR_ROWS, _MBR_TS\n    try:\n        _MBR_ROWS = member_sh.get("A:Q")  # OPT: range-restricted read (A=row_no through Q=referral_code)\n        with _THREAD_CACHE_LOCK:\n            _MBR_TS   = time.time()'

if old_load_members in content:
    content = content.replace(old_load_members, new_load_members)
    print('Patched _load_members')
else:
    print('WARNING: _load_members pattern not found!')

# Write back
with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.write(content)

print('All done. File written.')
