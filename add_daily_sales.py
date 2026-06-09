with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

new_route = """
@app.get("/daily_sales", tags=["Analytics"])
async def daily_sales(
    date: str = Query(None, description="Date in M/D/YYYY format, defaults to today"),
):
    \"\"\"Return today's (or specified date's) sales KPIs from Sales_Daily. No auth required.\"\"\"
    try:
        from analytics import get_daily_sales
        return ok(get_daily_sales(date))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

insert_marker = "# ═══════════════════════════════════════\n#  fetch_console_status"
content = content.replace(insert_marker, new_route + insert_marker)

with open("/root/psvibe_api_server/app.py", "w") as f:
    f.write(content)
print("DONE")
