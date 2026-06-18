#!/usr/bin/env python3
"""Apply Fixes 2.7, 2.4a, 2.4b, 2.3 to app.py"""
import re, sys

with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

original = content

# ============================================================
# FIX 2.7: Add MAX_SESSION_MINS validation at top of api_bookings_create
# ============================================================
old_27 = 'async def api_bookings_create(req: dict, auth=Depends(verify_api_key)):\n    """Create a booking - supports both customer bot and staff formats."""\n    try:\n        now = now_mmt()\n        logging.warning("api_bookings_create: req keys=%s", list(req.keys()))'

new_27 = '''async def api_bookings_create(req: dict, auth=Depends(verify_api_key)):
    """Create a booking — customer bot format ONLY (staff use POST /api/sessions/start)."""
    try:
        now = now_mmt()
        # FIX 2.7: Server-side MAX_SESSION_MINS validation
        MAX_SESSION_MINS = 1440  # 24 hours
        duration_mins_raw = req.get("durationMins", req.get("duration_mins", 0))
        try:
            duration_mins_raw = int(duration_mins_raw) if duration_mins_raw else 0
        except (ValueError, TypeError):
            duration_mins_raw = 0
        if not duration_mins_raw or duration_mins_raw <= 0 or duration_mins_raw > MAX_SESSION_MINS:
            return JSONResponse(content={"success": False, "message": f"duration_mins must be 1-{MAX_SESSION_MINS}"}, status_code=400)
        logging.warning("api_bookings_create: req keys=%s", list(req.keys()))'''

if old_27 not in content:
    print("ERROR: FIX 2.7 old text not found!")
    sys.exit(1)
content = content.replace(old_27, new_27, 1)
print("FIX 2.7 applied OK")

# ============================================================
# FIX 2.4a: Remove staff format else-branch from api_bookings_create
# ============================================================
# The staff format starts after the customer branch returns ok
# Pattern: return ok({"id": bk_id, "message": "Booking created"})
#          else: ... (staff format)
# We want to remove everything from "else:" to the closing except
old_staff_start = '''            return ok({"id": bk_id, "message": "Booking created"})
        else:
            # Staff format (existing) — CI-3: wrap in transaction'''

if old_staff_start not in content:
    print("ERROR: FIX 2.4a staff start not found!")
    # Try to find it
    idx = content.find('return ok({"id": bk_id, "message": "Booking created"})')
    print(f"  Found return ok at index {idx}")
    snippet = content[idx:idx+200]
    print(f"  Snippet: {repr(snippet[:200])}")
    sys.exit(1)

idx_start = content.index(old_staff_start)
# Find the closing except that catches the outer exception
# After the staff else block, the next line should be:
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
search_from = idx_start + len(old_staff_start)
except_marker = '\n    except Exception as e:\n        raise HTTPException(status_code=500, detail=str(e))'
idx_except = content.index(except_marker, search_from)
staff_block = content[idx_start:idx_except]

new_block = '''            return ok({"id": bk_id, "message": "Booking created"})'''

content = content.replace(staff_block, new_block, 1)
print(f"FIX 2.4a applied OK (removed {len(staff_block)} bytes of staff format)")

# ============================================================
# FIX 2.4b: Add POST /api/sessions/start endpoint
# ============================================================
# Insert before the api_bookings_create function
# Find the location just before the current api_bookings_create
marker_24b = '@app.post("/api/bookings", response_model=GenericResponse, tags=["Bookings"], summary="Create booking from customer bot payload [MySQL]")'
if marker_24b not in content:
    print("ERROR: FIX 2.4b marker not found!")
    sys.exit(1)

new_endpoint = '''# ═══════════════════════════════════════
# FIX 2.4: POST /api/sessions/start — Dedicated staff walk-in session start
# Replaces the legacy staff format that was in POST /api/bookings
@app.post("/api/sessions/start", response_model=GenericResponse, tags=["Sessions"], summary="Start a walk-in session (staff only) [MySQL]")
async def api_sessions_start(req: dict, auth=Depends(verify_api_key)):
    """Start a walk-in session on a console. Staff-only endpoint.
    
    Accepts: {console_id, member_id, member_name, duration_mins, booking_date?}
    - console_status check (already Active?)
    - Conflict check (any overlapping Active booking on same console)
    - Create booking row + sync console_status
    - ALL inside a transaction with FOR UPDATE
    """
    try:
        console_id = (req.get("console_id") or "").strip()
        member_id = req.get("member_id") or req.get("memberId") or "Guest"
        member_name = req.get("member_name") or req.get("memberName") or member_id
        game_name = req.get("game_name") or req.get("gameName") or ""
        duration_mins = req.get("duration_mins")
        if duration_mins is None:
            duration_mins = req.get("durationMins", 60)
        try:
            duration_mins = int(duration_mins)
        except (ValueError, TypeError):
            return JSONResponse(content={"success": False, "error": "duration_mins must be a number"}, status_code=400)
        
        MAX_SESSION_MINS = 1440
        if duration_mins < 1 or duration_mins > MAX_SESSION_MINS:
            return JSONResponse(content={"success": False, "error": f"duration_mins must be 1-{MAX_SESSION_MINS}"}, status_code=400)
        
        if not console_id:
            return JSONResponse(content={"success": False, "error": "console_id required"}, status_code=400)
        
        booking_date = req.get("booking_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Check if console already Active
        cs = _mysql_query_one("SELECT status FROM console_status WHERE console_id=%s", (console_id,))
        if cs and cs["status"] == "Active":
            return JSONResponse(content={"success": False, "error": f"Console {console_id} is already Active"}, status_code=409)
        
        _now_ref = now_mmt()
        
        # CI-3: ALL inside transaction with FOR UPDATE
        conn = _mc.connect(**_MYSQL_CFG)
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)
        try:
            # FOR UPDATE: lock the console_status row to prevent race conditions
            cur.execute("SELECT status FROM console_status WHERE console_id=%s FOR UPDATE", (console_id,))
            cs_locked = cur.fetchone()
            if cs_locked and cs_locked["status"] == "Active":
                conn.rollback()
                conn.close()
                return JSONResponse(content={"success": False, "error": f"Console {console_id} is already Active"}, status_code=409)
            
            # Conflict check: any overlapping Active booking
            cur.execute(
                "SELECT id FROM console_booking WHERE console_id=%s AND status='Active' LIMIT 1 FOR UPDATE",
                (console_id,)
            )
            active_conflict = cur.fetchone()
            if active_conflict:
                conn.rollback()
                conn.close()
                return JSONResponse(content={"success": False, "error": f"Console {console_id} already has active session (BK#{active_conflict['id']})"}, status_code=409)
            
            # Create booking
            cur.execute(
                "INSERT INTO console_booking (console_id, member_id, status, booking_date, start_time, duration_mins, game_name) VALUES (%s, %s, 'Active', %s, %s, %s, %s)",
                (console_id, member_id, booking_date, _now_ref, duration_mins, game_name)
            )
            booking_id = cur.lastrowid
            
            # Sync console_status
            cur.execute(
                "UPDATE console_status SET status='Active', current_member=%s, current_game=%s, start_time=%s WHERE console_id=%s",
                (member_id, game_name, _now_ref, console_id)
            )
            
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except:
                pass
        
        return ok({
            "booking_id": booking_id,
            "console_id": console_id,
            "member_id": member_id,
            "member_name": member_name,
            "status": "Active",
            "duration_mins": duration_mins,
        })
    except Exception as e:
        logger.exception(f"sessions/start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

'''

content = content.replace(marker_24b, new_endpoint + marker_24b, 1)
print("FIX 2.4b applied OK (new POST /api/sessions/start added)")

# ============================================================
# FIX 2.3: Update /api/available-slots endpoint
# ============================================================
# Find the current endpoint
old_23_start = '@app.get("/api/available-slots", response_model=GenericResponse, tags=["Bookings"], summary="Get available time slots for a date (with conflict detection) [MySQL]")'
if old_23_start not in content:
    print("ERROR: FIX 2.3 start not found!")
    sys.exit(1)

# Find the end of the function
idx_23_start = content.index(old_23_start)
# Find the next @app decorator or def after this endpoint
next_route = content.find('\n@app.', idx_23_start + 100)
if next_route < 0:
    next_route = content.find('\n# ═══', idx_23_start + 100)
old_23_func = content[idx_23_start:next_route]

new_23_func = '''@app.get("/api/available-slots", response_model=GenericResponse, tags=["Bookings"], summary="Get available time slots for a date (with console count) [MySQL]")
async def api_available_slots(
    date: str = "",
    console_type: str = "",
    branch_id: str = "",
    auth=Depends(verify_api_key)
):
    """Return available time slots with free/total console counts.
    
    Query params:
    - date: YYYY-MM-DD (defaults to today MMT)
    - console_type: Filter by console type (PS5 / PS5 Pro)
    - branch_id: Filter by branch (optional)
    
    Returns: {slots: [{time: "10:00", free: 3, total: 5}, ...]}
    """
    try:
        if not date:
            date = now_mmt().strftime("%Y-%m-%d")
        
        # Get all consoles of matching type at matching branch
        where_clauses = []
        params = []
        if console_type:
            where_clauses.append("console_type=%s")
            params.append(console_type)
        if branch_id:
            where_clauses.append("branch_id=%s")
            params.append(branch_id)
        
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        cs_rows = _mysql_query(f"SELECT console_id, console_type FROM console_status{where_sql} ORDER BY console_id", tuple(params))
        all_consoles = [r["console_id"] for r in cs_rows]
        total_consoles = len(all_consoles)
        
        if total_consoles == 0:
            return ok({"date": date, "slots": [], "total_consoles": 0})
        
        # Get active bookings for this date
        bookings = _mysql_query(
            "SELECT console_id, start_time, end_time, duration_mins, status FROM console_booking "
            "WHERE booking_date=%s AND status NOT IN ('cancelled', 'done', 'rejected') "
            "ORDER BY start_time",
            (date,)
        )
        
        # Build 30-min slots from 10:00 to 22:00
        OPEN_HOUR, CLOSE_HOUR = 10, 22
        SLOT_MINUTES = 30
        
        slots = []
        for h in range(OPEN_HOUR, CLOSE_HOUR):
            for m in (0, 30):
                if h == CLOSE_HOUR and m > 0:
                    break
                time_str = f"{h:02d}:{m:02d}"
                try:
                    slot_start = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
                    slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)
                except ValueError:
                    continue
                
                # Count busy consoles at this slot
                busy_consoles = set()
                for b in bookings:
                    b_console = b.get("console_id", "")
                    if b_console not in all_consoles:
                        continue
                    b_start = b.get("start_time")
                    b_end = b.get("end_time")
                    if not b_start:
                        continue
                    if isinstance(b_start, str):
                        try:
                            b_start = datetime.fromisoformat(b_start)
                        except ValueError:
                            continue
                    if not b_end:
                        b_dur = b.get("duration_mins")
                        if b_dur:
                            b_end = b_start + timedelta(minutes=int(b_dur))
                    if not b_end:
                        continue
                    if isinstance(b_end, str):
                        try:
                            b_end = datetime.fromisoformat(b_end)
                        except ValueError:
                            continue
                    
                    # Overlap check: slot overlaps with booking
                    if slot_start < b_end and slot_end > b_start:
                        busy_consoles.add(b_console)
                
                free = total_consoles - len(busy_consoles)
                slots.append({
                    "time": time_str,
                    "free": max(0, free),
                    "total": total_consoles,
                })
        
        return ok({
            "date": date,
            "slots": slots,
            "total_consoles": total_consoles,
        })
    except Exception as e:
        logger.error("api_available_slots: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
'''

content = content.replace(old_23_func, new_23_func, 1)
print("FIX 2.3 applied OK (updated /api/available-slots)")

# Write back
with open("/root/psvibe_api_server/app.py", "w") as f:
    f.write(content)

print("\nAll fixes applied successfully!")
print(f"File size: {len(content)} bytes (was {len(original)} bytes)")
PYEOF
