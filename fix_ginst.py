#!/usr/bin/env python3
"""Fix get_consoles_from_setting to use API instead of gspread."""
FILE = "/root/psvibe-sales-bot/bot/__init__.py"
with open(FILE) as f:
    code = f.read()

old = '''def get_consoles_from_setting() -> list[dict]:
    """Return all consoles from Setting!H:J as list of dicts."""
    try:
        names = setting_sh.col_values(8)[1:]
        types = setting_sh.col_values(9)[1:]
        mults = setting_sh.col_values(10)[1:]
        result = []
        for i, name in enumerate(names):
            if not name.strip():
                continue
            result.append({
                "id":   name.strip(),
                "type": types[i].strip() if i < len(types) else "",
                "mult": mults[i].strip() if i < len(mults) else "1",
            })
        return result
    except Exception:
        return []'''

new = '''def get_consoles_from_setting() -> list[dict]:
    """Return all consoles from API (MySQL) as list of dicts."""
    if _HAS_API:
        result = api_fetch_console_status()
        if result is not None:
            cons = result.get("consoles", [])
            return [{
                "id":   c.get("console_id", ""),
                "type": c.get("console_type", ""),
                "mult": "1",
            } for c in cons]
        logging.warning("API fetch_console_status failed, no fallback")
    return []'''

if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    import py_compile
    py_compile.compile(FILE, doraise=True)
    print("OK")
else:
    print("NOT FOUND")
    idx = code.find("def get_consoles_from_setting")
    if idx >= 0:
        print("Found at", idx)
        print(repr(code[idx-10:idx+50]))
