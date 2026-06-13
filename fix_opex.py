import sys

with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

old = '    mysql_execute("INSERT INTO opex (category,description,amount,payment_method,recorded_by,expense_date) VALUES (%s,%s,%s,%s,%s,%s)", (cat, desc, amt, pmt, by, dt))\n    return GenericResponse(success=True, data={"msg": f"{cat}: {amt:,} Ks recorded"})'

new = '''    mysql_execute("INSERT INTO opex (category,description,amount,payment_method,recorded_by,expense_date) VALUES (%s,%s,%s,%s,%s,%s)", (cat, desc, amt, pmt, by, dt))
    # Deduct from account balance if payment method matches an account name
    try:
        acc = mysql_query_one("SELECT id, balance FROM accounts WHERE account_name = %s", (pmt,))
        if acc:
            new_bal = float(acc["balance"]) - amt
            mysql_execute("UPDATE accounts SET balance = %s WHERE id = %s", (new_bal, acc["id"]))
            logger.info("OPEX: deducted %d from account '%s' (new balance: %.2f)", amt, pmt, new_bal)
    except Exception as ae:
        logger.warning("OPEX account deduction failed: %s", ae)
    return GenericResponse(success=True, data={"msg": f"{cat}: {amt:,} Ks recorded"})'''

if old not in content:
    print("ERROR: old code not found")
    sys.exit(1)

content = content.replace(old, new, 1)

with open("/root/psvibe_api_server/app.py", "w") as f:
    f.write(content)

print("OK: OPEX account deduction fix applied")
