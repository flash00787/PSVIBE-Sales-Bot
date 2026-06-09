"""Add no-cache header for FoodMenuRegister JS and update index.html with CDN bypass"""

path = "/root/psvibe_api_server/app.py"
with open(path) as f:
    c = f.read()

# Add a route specifically for FoodMenuRegister that serves with no-cache header
old = '''app.mount("/assets", StaticFiles(directory=os.path.join(dashboard_dir, "assets")), name="dashboard_assets")'''

new = '''@app.get("/assets/FoodMenuRegister-{rest:path}", include_in_schema=False)
async def serve_food_menu_js(rest: str):
    """Serve FoodMenuRegister JS with no-cache headers to bypass CDN/browser cache."""
    from starlette.responses import FileResponse
    import os
    fpath = os.path.join(dashboard_dir, "assets", f"FoodMenuRegister-{rest}")
    if os.path.isfile(fpath):
        resp = FileResponse(fpath, media_type="application/javascript")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    return Response(status_code=404)

app.mount("/assets", StaticFiles(directory=os.path.join(dashboard_dir, "assets")), name="dashboard_assets")'''

if old in c:
    c = c.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(c)
    print("Added dedicated FoodMenuRegister route with no-cache headers ✅")
else:
    # Try to find the exact mount
    idx = c.find("app.mount")
    ctx = c[max(0,idx-20):idx+200]
    print(f"Pattern at offset {idx}")
    print(f"Context: {repr(ctx)}")
