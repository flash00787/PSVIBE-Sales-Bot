#!/usr/bin/env python3
"""Add shareholder API endpoints + update BS icap."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# ── 1. Add shareholder endpoints at the end of the file ──
# Find the last endpoint (before file end) and add before
end_marker = '# ═══════════════════════════════════════\n#  MUTATION — send_booking_reminders'
shareholder_endpoints = '''

# ── Shareholders ──
@router.get("/shareholders")
async def get_shareholders(user: dict = Depends(get_current_user)):
    """List all shareholders."""
    from mysql_db import query as _mq
    rows = _mq("SELECT * FROM shareholders ORDER BY capital_contribution DESC")
    return {"success": True, "data": rows}

@router.post("/shareholders")
async def add_shareholder(req: dict, user: dict = Depends(get_current_user)):
    """Add a new shareholder."""
    from mysql_db import execute as _me
    name = req.get("name", "").strip()
    if not name:
        return {"success": False, "error": "Name is required"}
    role = req.get("role", "Shareholder")
    cap = float(req.get("capital_contribution", 0) or 0)
    pct = float(req.get("ownership_pct", 0) or 0)
    notes = req.get("notes", "")
    _me("INSERT INTO shareholders (name,role,capital_contribution,ownership_pct,notes) VALUES (%s,%s,%s,%s,%s)",
        (name, role, cap, pct, notes))
    return {"success": True, "message": f"Shareholder {name} added"}

@router.put("/shareholders/{sid}")
async def update_shareholder(sid: int, req: dict, user: dict = Depends(get_current_user)):
    """Update a shareholder."""
    from mysql_db import execute as _me
    fields = []
    params = []
    for k in ("name","role","capital_contribution","ownership_pct","notes"):
        if k in req:
            fields.append(f"{k}=%s")
            params.append(req[k])
    if not fields:
        return {"success": False, "error": "No fields to update"}
    params.append(sid)
    _me(f"UPDATE shareholders SET {','.join(fields)} WHERE id=%s", params)
    return {"success": True, "message": "Updated"}

@router.delete("/shareholders/{sid}")
async def delete_shareholder(sid: int, user: dict = Depends(get_current_user)):
    """Delete a shareholder."""
    from mysql_db import execute as _me
    _me("DELETE FROM shareholders WHERE id=%s", (sid,))
    return {"success": True, "message": "Deleted"}

# ── Update cash_withdrawal endpoint ──
@router.get("/endpoints/capital")
async def get_capital_summary(user: dict = Depends(get_current_user)):
    """Get capital summary for Balance Sheet."""
    from mysql_db import query as _mq
    rows = _mq("SELECT SUM(capital_contribution) as total_cap, SUM(ownership_pct) as total_pct FROM shareholders")
    total_cap = float(rows[0]["total_cap"] or 0) if rows else 0
    return {"success": True, "data": {"total_capital": total_cap}}
'''

# Find insertion point and add
idx = src.find(end_marker)
if idx >= 0:
    src = src[:idx] + shareholder_endpoints + src[idx:]
    print('Shareholder endpoints added')

# ── 2. Update BS to use shareholders table instead of hardcoded icap ──
old_icap = 'icap = 300000000.0'
new_icap = '''_sh = _mq("SELECT SUM(capital_contribution) as tc FROM shareholders")
        icap = float(_sh[0]["tc"] or 0) if _sh else 0'''
src = src.replace(old_icap, new_icap, 1)
print('icap updated to read from shareholders table')

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print('Syntax OK ✅')
except SyntaxError as e:
    print(f'Syntax Error line {e.lineno}: {e.msg}')
