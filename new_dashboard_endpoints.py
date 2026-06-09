
# ═══════════════════════════════════════
#  MEMBERS — DELETE
# ═══════════════════════════════════════
@router.delete("/members/{member_id}")
async def dashboard_delete_member(member_id: str, user: dict = Depends(get_current_user)):
    """Delete a member."""
    try:
        existing = _mysql_query_one("SELECT * FROM member_wallets WHERE member_id = %s", (member_id,))
        if not existing:
            return {"success": False, "error": "Member not found"}

        _mysql_execute("DELETE FROM member_wallets WHERE member_id = %s", (member_id,))
        _mysql_execute("DELETE FROM topup_log WHERE member_id = %s", (member_id,))
        _mysql_execute("DELETE FROM members WHERE member_id = %s", (member_id,))
        return {"success": True, "data": {"deleted": member_id}}
    except Exception as e:
        logger.error(f"DELETE /members/{member_id} error: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════
#  STOCK IN — List & Delete
# ═══════════════════════════════════════
@router.get("/stock-in")
async def dashboard_get_stock_in(
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """List stock-in records."""
    try:
        where = ["1=1"]
        params = []
        if search:
            where.append("(item_name LIKE %s OR batch_id LIKE %s OR source LIKE %s OR staff_name LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like, like])

        sql = f"""
            SELECT id, batch_id, item_name, quantity, unit_cost, source,
                   receipt_no, payment_method, paid_by, staff_name, created_at
            FROM stock_in
            WHERE {' AND '.join(where)}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        rows = _mysql_query(sql, tuple(params))

        count_row = _mysql_query_one(
            f"SELECT COUNT(*) as total FROM stock_in WHERE {' AND '.join(where)}",
            tuple(params[:-2])
        )
        total = count_row["total"] if count_row else 0

        entries = []
        for r in rows:
            entries.append({
                "id": r["id"],
                "batch_id": r.get("batch_id"),
                "item_name": r.get("item_name"),
                "quantity": r.get("quantity"),
                "unit_cost": float(r.get("unit_cost") or 0),
                "source": r.get("source"),
                "receipt_no": r.get("receipt_no"),
                "payment_method": r.get("payment_method"),
                "paid_by": r.get("paid_by"),
                "staff_name": r.get("staff_name"),
                "created_at": str(r["created_at"]) if r.get("created_at") else None,
            })
        return {"success": True, "data": entries, "total": total}
    except Exception as e:
        logger.error(f"GET /stock-in error: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/stock-in/{entry_id}")
async def dashboard_delete_stock_in(entry_id: int, user: dict = Depends(get_current_user)):
    """Delete a stock-in record and reverse inventory quantity."""
    try:
        existing = _mysql_query_one("SELECT * FROM stock_in WHERE id = %s", (entry_id,))
        if not existing:
            return {"success": False, "error": "Stock-in record not found"}

        # Reverse inventory: find item by name and subtract quantity
        item = _mysql_query_one("SELECT * FROM inventory WHERE item_name = %s", (existing["item_name"],))
        if item:
            new_qty = max(0, int(item["quantity"] or 0) - int(existing["quantity"] or 0))
            _mysql_execute(
                "UPDATE inventory SET quantity = %s, last_updated = NOW() WHERE id = %s",
                (new_qty, item["id"])
            )

        _mysql_execute("DELETE FROM stock_in WHERE id = %s", (entry_id,))
        return {"success": True, "data": {"deleted": entry_id}}
    except Exception as e:
        logger.error(f"DELETE /stock-in/{entry_id} error: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════
#  STOCK OUT — List & Delete
# ═══════════════════════════════════════
@router.get("/stock-out")
async def dashboard_get_stock_out(
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """List stock-out records."""
    try:
        where = ["1=1"]
        params = []
        if search:
            where.append("(item_name LIKE %s OR staff_name LIKE %s OR notes LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like])

        sql = f"""
            SELECT id, item_name, quantity, unit_price, total, sale_date,
                   staff_name, notes, created_at
            FROM stock_out
            WHERE {' AND '.join(where)}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        rows = _mysql_query(sql, tuple(params))

        count_row = _mysql_query_one(
            f"SELECT COUNT(*) as total FROM stock_out WHERE {' AND '.join(where)}",
            tuple(params[:-2])
        )
        total = count_row["total"] if count_row else 0

        entries = []
        for r in rows:
            entries.append({
                "id": r["id"],
                "item_name": r.get("item_name"),
                "quantity": r.get("quantity"),
                "unit_price": float(r.get("unit_price") or 0),
                "total": float(r.get("total") or 0),
                "sale_date": str(r["sale_date"]) if r.get("sale_date") else None,
                "staff_name": r.get("staff_name"),
                "notes": r.get("notes"),
                "created_at": str(r["created_at"]) if r.get("created_at") else None,
            })
        return {"success": True, "data": entries, "total": total}
    except Exception as e:
        logger.error(f"GET /stock-out error: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/stock-out/{entry_id}")
async def dashboard_delete_stock_out(entry_id: int, user: dict = Depends(get_current_user)):
    """Delete a stock-out record and restore inventory quantity."""
    try:
        existing = _mysql_query_one("SELECT * FROM stock_out WHERE id = %s", (entry_id,))
        if not existing:
            return {"success": False, "error": "Stock-out record not found"}

        # Restore inventory: find item by name and add quantity back
        item = _mysql_query_one("SELECT * FROM inventory WHERE item_name = %s", (existing["item_name"],))
        if item:
            new_qty = int(item["quantity"] or 0) + int(existing["quantity"] or 0)
            _mysql_execute(
                "UPDATE inventory SET quantity = %s, last_updated = NOW() WHERE id = %s",
                (new_qty, item["id"])
            )

        _mysql_execute("DELETE FROM stock_out WHERE id = %s", (entry_id,))
        return {"success": True, "data": {"deleted": entry_id}}
    except Exception as e:
        logger.error(f"DELETE /stock-out/{entry_id} error: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════
#  SALES DAILY — List
# ═══════════════════════════════════════
@router.get("/sales-daily")
async def dashboard_get_sales_daily(
    date: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """List sales daily records."""
    try:
        where = ["1=1"]
        params = []
        if date:
            where.append("sale_date = %s")
            params.append(date)
        if search:
            where.append("(voucher_no LIKE %s OR member_id LIKE %s OR staff_name LIKE %s OR notes LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like, like])

        sql = f"""
            SELECT id, voucher_no, sale_date, console_id, member_id,
                   amount, gross, discount, net, staff_name,
                   payment_method, notes, created_at
            FROM sales_daily
            WHERE {' AND '.join(where)}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        rows = _mysql_query(sql, tuple(params))

        count_row = _mysql_query_one(
            f"SELECT COUNT(*) as total FROM sales_daily WHERE {' AND '.join(where)}",
            tuple(params[:-2])
        )
        total = count_row["total"] if count_row else 0

        summary = _mysql_query_one(
            f"SELECT COALESCE(SUM(amount), 0) as total_amount, COALESCE(SUM(gross), 0) as total_gross, COALESCE(SUM(discount), 0) as total_discount, COALESCE(SUM(net), 0) as total_net FROM sales_daily WHERE {' AND '.join(where)}",
            tuple(params[:-2])
        )

        entries = []
        for r in rows:
            entries.append({
                "id": r["id"],
                "voucher_no": r.get("voucher_no"),
                "sale_date": str(r["sale_date"]) if r.get("sale_date") else None,
                "console_id": r.get("console_id"),
                "member_id": r.get("member_id"),
                "amount": float(r.get("amount") or 0),
                "gross": float(r.get("gross") or 0),
                "discount": float(r.get("discount") or 0),
                "net": float(r.get("net") or 0),
                "staff_name": r.get("staff_name"),
                "payment_method": r.get("payment_method"),
                "notes": r.get("notes"),
                "created_at": str(r["created_at"]) if r.get("created_at") else None,
            })
        return {
            "success": True,
            "data": entries,
            "total": total,
            "summary": {
                "total_amount": float(summary["total_amount"] or 0),
                "total_gross": float(summary["total_gross"] or 0),
                "total_discount": float(summary["total_discount"] or 0),
                "total_net": float(summary["total_net"] or 0),
            } if summary else None
        }
    except Exception as e:
        logger.error(f"GET /sales-daily error: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════
#  FINANCIAL REPORT
# ═══════════════════════════════════════
@router.get("/financial-report")
async def dashboard_financial_report(user: dict = Depends(get_current_user)):
    """Get financial summary including assets, payables, receivables, advances."""
    try:
        assets = _mysql_query("SELECT id, name, purchase_date, amount, notes, created_at FROM finance_assets ORDER BY purchase_date DESC")
        assets_total = sum(float(a["amount"] or 0) for a in assets)

        payables = _mysql_query("SELECT id, payee, amount, due_date, status, created_at FROM finance_payables ORDER BY due_date ASC")
        payables_total = sum(float(p["amount"] or 0) for p in payables)
        payables_pending = sum(float(p["amount"] or 0) for p in payables if p.get("status") == "pending")

        receivables = _mysql_query("SELECT id, payer, amount, due_date, status, created_at FROM finance_receivables ORDER BY due_date ASC")
        receivables_total = sum(float(r["amount"] or 0) for r in receivables)
        receivables_pending = sum(float(r["amount"] or 0) for r in receivables if r.get("status") == "pending")

        advances = _mysql_query("SELECT id, member_id, amount, advance_date, settle_date, status, notes, created_at FROM finance_advances ORDER BY advance_date DESC")
        advances_total = sum(float(a["amount"] or 0) for a in advances)
        advances_pending = sum(float(a["amount"] or 0) for a in advances if a.get("status") == "pending")

        prepaid = _mysql_query("SELECT id, description, amount, settle_date, status, created_at FROM finance_prepaid ORDER BY settle_date ASC")
        prepaid_total = sum(float(p["amount"] or 0) for p in prepaid)

        opex_rows = _mysql_query("SELECT COALESCE(SUM(amount), 0) as total FROM finance_opex_log WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
        opex_30d = float(opex_rows[0]["total"] or 0) if opex_rows else 0

        return {
            "success": True,
            "data": {
                "assets": [{
                    "id": a["id"],
                    "name": a.get("name"),
                    "purchase_date": str(a["purchase_date"]) if a.get("purchase_date") else None,
                    "amount": float(a["amount"] or 0),
                    "notes": a.get("notes"),
                } for a in assets],
                "assets_total": assets_total,
                "payables": [{
                    "id": p["id"],
                    "payee": p.get("payee"),
                    "amount": float(p["amount"] or 0),
                    "due_date": str(p["due_date"]) if p.get("due_date") else None,
                    "status": p.get("status"),
                } for p in payables],
                "payables_total": payables_total,
                "payables_pending": payables_pending,
                "receivables": [{
                    "id": r["id"],
                    "payer": r.get("payer"),
                    "amount": float(r["amount"] or 0),
                    "due_date": str(r["due_date"]) if r.get("due_date") else None,
                    "status": r.get("status"),
                } for r in receivables],
                "receivables_total": receivables_total,
                "receivables_pending": receivables_pending,
                "advances": [{
                    "id": a["id"],
                    "member_id": a.get("member_id"),
                    "amount": float(a["amount"] or 0),
                    "advance_date": str(a["advance_date"]) if a.get("advance_date") else None,
                    "settle_date": str(a["settle_date"]) if a.get("settle_date") else None,
                    "status": a.get("status"),
                    "notes": a.get("notes"),
                } for a in advances],
                "advances_total": advances_total,
                "advances_pending": advances_pending,
                "prepaid": [{
                    "id": p["id"],
                    "description": p.get("description"),
                    "amount": float(p["amount"] or 0),
                    "settle_date": str(p["settle_date"]) if p.get("settle_date") else None,
                    "status": p.get("status"),
                } for p in prepaid],
                "prepaid_total": prepaid_total,
                "opex_30d": opex_30d,
            }
        }
    except Exception as e:
        logger.error(f"GET /financial-report error: {e}")
        return {"success": False, "error": str(e)}
