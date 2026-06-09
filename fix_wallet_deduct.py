import sys

with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

# Find the api_fetch_balance_mins function (around line 473)
marker = "#  fetch_balance_mins (alias live read)"
pos = content.find(marker)
if pos < 0:
    print("ERROR: marker for balance_mins not found")
    sys.exit(1)

# Find end of function (next @app route)
next_route = content.find("@app.", pos + 100)
if next_route < 0:
    print("ERROR: next route not found")
    sys.exit(1)

wallet_deduct_endpoint = '''
#  wallet_deduct (after sale)
@app.post("/api/wallet/deduct", response_model=GenericResponse, tags=["Members"], summary="Deduct wallet balance after sale [MySQL]")
async def api_wallet_deduct(data: dict, auth=Depends(verify_api_key)):
    """Deduct wallet balance_mins after a gaming session sale."""
    try:
        member_id = data.get("member_id", "")
        deduct_mins = int(data.get("deduct_mins", 0))
        total_mins = int(data.get("total_mins", 0))

        if not member_id or deduct_mins <= 0:
            return error_response(message="member_id and deduct_mins > 0 required")

        rows = _mysql_query(
            "SELECT balance_mins, total_spend, total_bought_mins FROM member_wallets WHERE member_id=%s",
            (member_id,))
        if not rows:
            return error_response(message=f"Member {member_id} not found in wallet")

        cur = rows[0]
        old_bal = cur.get("balance_mins", 0) or 0
        new_bal = max(0, old_bal - deduct_mins)
        new_spend = (cur.get("total_spend", 0) or 0) + int(total_mins)

        _mysql_exec(
            "UPDATE member_wallets SET balance_mins=%s, total_spend=%s, last_updated=NOW() WHERE member_id=%s",
            (new_bal, new_spend, member_id))

        return ok({
            "success": True,
            "member_id": member_id,
            "balance_before": old_bal,
            "balance_after": new_bal,
            "deducted": deduct_mins,
            "total_spend": new_spend
        })
    except Exception as e:
        return error_response(message=str(e))

'''

content = content[:next_route] + wallet_deduct_endpoint + content[next_route:]

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(content)

print('BUG 3a: wallet/deduct endpoint added to app.py')
