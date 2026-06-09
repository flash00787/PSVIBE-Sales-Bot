#!/usr/bin/env python3
"""Replace entire cashflow function in dashboard_routes.py."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    lines = f.readlines()

# Find start and end of cashflow function
start = None
end = None
for i, line in enumerate(lines):
    if '# ── Financial Statement: Cash Flow ──' in line:
        start = i
    if start is not None and 'return {"success": False, "error": str(e)}' in line:
        end = i + 1
        break

if start is None or end is None:
    print('Could not find cashflow function bounds')
    exit(1)

print(f'Found cashflow function at lines {start+1}-{end}')

new_function = '''# ── Financial Statement: Cash Flow (Redesigned) ──
@router.get("/financial/cashflow")
async def get_cashflow(year: int = 2026, month: int = 6, user: dict = Depends(get_current_user)):
    """Cash Flow Statement for a given month — redesigned for readability."""
    from mysql_db import query as _mq
    ym = f"{year:04d}-{month:02d}"
    try:
        # ── Operating Activities ──
        sr = _mq("SELECT COALESCE(SUM(net),0) as t FROM sales_daily WHERE DATE_FORMAT(created_at,'%%Y-%%m')=%s AND net>0", (ym,))
        cfc = float(sr[0]["t"] or 0) if sr else 0
        tr = _mq("SELECT COALESCE(SUM(amount),0) as t FROM topup_log WHERE DATE_FORMAT(topup_date,'%%Y-%%m')=%s", (ym,))
        tfc = float(tr[0]["t"] or 0) if tr else 0
        or2 = _mq("SELECT COALESCE(SUM(amount),0) as t FROM opex WHERE DATE_FORMAT(expense_date,'%%Y-%%m')=%s", (ym,))
        ofc = float(or2[0]["t"] or 0) if or2 else 0
        st = _mq("SELECT COALESCE(SUM(total_cost),0) as t FROM stock_in WHERE DATE_FORMAT(created_at,'%%Y-%%m')=%s", (ym,))
        sfc = float(st[0]["t"] or 0) if st else 0
        net_op = cfc + tfc - ofc - sfc

        # ── Investing Activities ──
        ap = _mq("SELECT COALESCE(SUM(per_price*qty),0) as t FROM finance_assets WHERE status='active'", ())
        apc = float(ap[0]["t"] or 0) if ap else 0
        av = _mq("SELECT COALESCE(SUM(amount),0) as t FROM finance_advances", ())
        avc = float(av[0]["t"] or 0) if av else 0
        pp = _mq("SELECT COALESCE(SUM(amount),0) as t FROM finance_prepaid", ())
        ppc = float(pp[0]["t"] or 0) if pp else 0
        dp = _mq("SELECT COALESCE(SUM(disposal_amount),0) as t FROM asset_disposals WHERE DATE_FORMAT(disposal_date,'%%Y-%%m')=%s", (ym,))
        dpc = float(dp[0]["t"] or 0) if dp else 0
        _dp_rows = _mq("SELECT COALESCE(SUM(monthly_dep),0) as t FROM finance_assets WHERE status='active' AND useful_life > 0")
        _dep_amt = float(_dp_rows[0]["t"] or 0) if _dp_rows else 0
        net_inv = dpc - apc - avc - ppc

        # ── Financing Activities ──
        ki = _mq("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account='KBZ Bank' AND movement_type='transfer_in' AND DATE_FORMAT(created_at,'%%Y-%%m')=%s", (ym,))
        cap_in = float(ki[0]["t"] or 0) if ki else 0
        acm_in = _mq("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account='ACM''s Acc' AND movement_type='transfer_in' AND DATE_FORMAT(created_at,'%%Y-%%m')=%s", (ym,))
        acm_out = _mq("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account='ACM''s Acc' AND movement_type='transfer_out' AND DATE_FORMAT(created_at,'%%Y-%%m')=%s", (ym,))
        acm_net = (float(acm_in[0]["t"] or 0) if acm_in else 0) - (float(acm_out[0]["t"] or 0) if acm_out else 0)
        cash_out = _mq("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account='Cash' AND movement_type='transfer_out' AND DATE_FORMAT(created_at,'%%Y-%%m')=%s", (ym,))
        c_out_val = float(cash_out[0]["t"] or 0) if cash_out else 0

        fin_in = cap_in
        fin_out = 0
        if acm_net > 0: fin_in += acm_net
        if acm_net < 0: fin_out += abs(acm_net)
        if c_out_val > 0: fin_out += abs(c_out_val)
        net_fin = fin_in - fin_out

        # ── Opening Balance: cumulative before this period ──
        _bef = ym + "-01"
        _bf_rev = _mq("SELECT COALESCE(SUM(net),0) as t FROM sales_daily WHERE DATE(created_at) < %s AND net>0", (_bef,))
        _bf_tfu = _mq("SELECT COALESCE(SUM(amount),0) as t FROM topup_log WHERE DATE(topup_date) < %s", (_bef,))
        _bf_ope = _mq("SELECT COALESCE(SUM(amount),0) as t FROM opex WHERE DATE(expense_date) < %s", (_bef,))
        _bf_sto = _mq("SELECT COALESCE(SUM(total_cost),0) as t FROM stock_in WHERE DATE(created_at) < %s", (_bef,))
        opener = (float(_bf_rev[0]["t"] or 0) if _bf_rev else 0) + (float(_bf_tfu[0]["t"] or 0) if _bf_tfu else 0) - (float(_bf_ope[0]["t"] or 0) if _bf_ope else 0) - (float(_bf_sto[0]["t"] or 0) if _bf_sto else 0)

        net_chg = net_op + net_inv + net_fin
        closer = opener + net_chg

        # Build structured items
        op_items = [
            {"label": "Game Sales", "emoji": "🎮", "amount": round(cfc,0), "type": "inflow"},
            {"label": "Top-up / Refill", "emoji": "💳", "amount": round(tfc,0), "type": "inflow"},
            {"label": "Operating Expenses", "emoji": "📉", "amount": round(ofc,0), "type": "outflow"},
            {"label": "Stock Purchases", "emoji": "📦", "amount": round(sfc,0), "type": "outflow"},
        ]
        inv_items = [
            {"label": "Equipment / Asset Purchases", "emoji": "🔧", "amount": round(apc,0), "type": "outflow"},
        ]
        if avc: inv_items.append({"label": "Advances Paid", "emoji": "📋", "amount": round(avc,0), "type": "outflow"})
        if ppc: inv_items.append({"label": "Prepaid Expenses", "emoji": "📋", "amount": round(ppc,0), "type": "outflow"})
        if dpc: inv_items.append({"label": "Asset Sale Proceeds", "emoji": "♻️", "amount": round(dpc,0), "type": "inflow"})
        if _dep_amt: inv_items.append({"label": "Depreciation Add-back (non-cash)", "emoji": "↩️", "amount": round(_dep_amt,0), "type": "adjustment"})

        fin_items = []
        if cap_in: fin_items.append({"label": "Capital from KBZ Bank", "emoji": "🏦", "amount": round(cap_in,0), "type": "inflow"})
        if acm_net != 0: fin_items.append({"label": "ACM Account Movement", "emoji": "🏧", "amount": round(abs(acm_net),0), "type": "inflow" if acm_net > 0 else "outflow"})
        if c_out_val: fin_items.append({"label": "Withdrawals / Owner Draw", "emoji": "🏧", "amount": round(abs(c_out_val),0), "type": "outflow"})

        return {"success": True, "data": {
            "period": ym,
            "opening_balance": round(opener,0),
            "sections": {
                "operating": {"title": "Daily Operations", "items": op_items, "subtotal": round(net_op,0)},
                "investing": {"title": "Long-term Investments", "items": inv_items, "subtotal": round(net_inv,0)},
                "financing": {"title": "Financing & Capital", "items": fin_items, "subtotal": round(net_fin,0)}
            },
            "summary": {
                "opening_balance": round(opener,0),
                "total_inflows": round(cfc + tfc + dpc + max(0, cap_in) + max(0, acm_net), 0),
                "total_outflows": round(ofc + sfc + apc + avc + ppc + abs(min(0, acm_net)) + c_out_val, 0),
                "net_change": round(net_chg, 0),
                "closing_balance": round(closer, 0)
            }
        }}
    except Exception as e:
        return {"success": False, "error": str(e)}

'''

# Replace lines
new_lines = lines[:start] + [new_function] + lines[end:]

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.writelines(new_lines)

compile(''.join(new_lines), '/root/psvibe_api_server/dashboard_routes.py', 'exec')
print('Backend: Syntax OK ✅')
