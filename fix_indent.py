"""Fix indentation of the FoodMenuRegister route in app.py"""

path = "/root/psvibe_api_server/app.py"
with open(path) as f:
    c = f.read()

# Find the broken section and replace it
old_broken = '''        @app.get("/assets/FoodMenuRegister-{rest:path}", include_in_schema=False)
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

new_fixed = '''        @app.get("/assets/FoodMenuRegister-{rest:path}", include_in_schema=False)
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

if old_broken in c:
    c = c.replace(old_broken, new_fixed)
    with open(path, "w") as f:
        f.write(c)
    print("Indentation fixed!")
else:
    print("Pattern not found - checking alternatives")
    idx = c.find("serve_food_menu_js")
    if idx >= 0:
        print(f"Found at offset {idx}")
        print(repr(c[idx-50:idx+300]))
