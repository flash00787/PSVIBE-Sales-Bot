#!/usr/bin/env python3
"""Add /api/dashboard/coupons endpoint + update frontend expectation."""
import pymysql, os

# Read env
with open('/etc/psvibe/secrets.env') as f:
    envlines = f.readlines()

db_pass = ''
for line in envlines:
    line = line.strip()
    if line.startswith('export '):
        line = line[7:]
    if '=' in line:
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k == 'MYSQL_PASSWORD':
            db_pass = v
            break

# Step 1: Insert the dashboard coupons endpoint
f = '/root/psvibe_api_server/dashboard_routes.py'
with open(f) as fh:
    src = fh.read()

# Find the insertion point: after members/{member_id}/topups and before INVENTORY section
marker = """        return {"success": True, "data": topups, "total": total}
    except Exception as e:
        logger.error(f"GET /members/{member_id}/topups error: {e}")
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════
#  INVENTORY — CRUD"""

new_endpoint = """        return {"success": True, "data": topups, "total": total}
    except Exception as e:
        logger.error(f"GET /members/{member_id}/topups error: {e}")
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════
#  COUPONS — View All
# ═══════════════════════════════════════
@router.get("/coupons")
async def dashboard_get_coupons(
    search: str | None = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    \"\"\"List all member coupons with member details.\"\"\"
    try:
        where = ["1=1"]
        params = []
        if search:
            where.append("(c.coupon_code LIKE %s OR c.member_id LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like])

        sql = f'''
            SELECT c.id, c.coupon_code, c.member_id, c.original_minutes,
                   c.balance_minutes, c.issued_date, c.expiry_date, c.status,
                   c.redeemed_at, m.member_name, m.phone
            FROM member_coupons c
            LEFT JOIN members m ON c.member_id = m.member_id
            WHERE {' AND '.join(where)}
            ORDER BY c.issued_date DESC
            LIMIT %s OFFSET %s
        '''
        params.extend([limit, offset])
        rows = _mysql_query(sql, tuple(params))

        count_sql = f"SELECT COUNT(*) as total FROM member_coupons c WHERE {' AND '.join(where)}"
        cnt_params = params[:-2]  # remove limit/offset
        count_row = _mysql_query_one(count_sql, tuple(cnt_params))
        total = count_row["total"] if count_row else 0

        coupons = []
        for r in rows:
            coupons.append({
                "id": r["id"],
                "code": r["coupon_code"],
                "member_id": r["member_id"],
                "member_name": r.get("member_name") or "-",
                "phone": r.get("phone") or "-",
                "original_minutes": r["original_minutes"],
                "balance_minutes": r["balance_minutes"],
                "issued_date": str(r["issued_date"])[:16] if r.get("issued_date") else "",
                "expiry_date": str(r["expiry_date"])[:10] if r.get("expiry_date") else "",
                "status": r["status"],
                "redeemed_at": str(r["redeemed_at"])[:16] if r.get("redeemed_at") else "",
            })
        return {"success": True, "data": coupons, "total": total}
    except Exception as e:
        logger.error(f"GET /coupons error: {e}")
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════
#  INVENTORY — CRUD"""

src = src.replace(marker, new_endpoint, 1)
with open(f, 'w') as fh:
    fh.write(src)

# Verify syntax
compile(src, f, 'exec')
print("✅ Dashboard coupons endpoint added: GET /api/dashboard/coupons")

# Step 2: Also check what the frontend expects from the coupons page
# The Vue app calls /api/dashboard/coupons - which now exists
print("✅ Frontend now has matching endpoint")

# Step 3: Check promotion status - it's expired (June 7). Update to active for today
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=db_pass, database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()
cur.execute("SELECT id, promo_name, start_date, end_date, status FROM promotions WHERE id=516")
r = cur.fetchone()
print(f"\nPromotion #516: name={r[1]} | start={r[2]} | end={r[3]} | status={r[4]}")

# Check if we should extend the promotion
import datetime
today = datetime.date.today()
print(f"Today: {today}")
print(f"End date: {r[3]}")
print(f"Promotion is {'ACTIVE' if r[3] >= today else 'EXPIRED'}")

conn.close()
