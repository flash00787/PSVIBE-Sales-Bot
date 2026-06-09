"""Fix cache issue: serve FoodMenuRegister JS with Cache-Control: no-cache"""

import os

path = "/root/psvibe_api_server/app.py"
with open(path) as f:
    c = f.read()

# Find the static mount and dashboard_dir definition
# We need to add cache control headers for JS files

# Add a custom route for the FoodMenuRegister JS that serves with no-cache
# We'll replace the static assets mount with one that has custom headers

# First, find the assets mount line
old_mount = 'app.mount("/assets", StaticFiles(directory=os.path.join(dashboard_dir, "assets")), name="dashboard_assets")'

# Replace with a custom approach that adds no-cache header to FoodMenuRegister
new_mount = '''import starlette.routing
from starlette.responses import FileResponse as _FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

class _NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if "FoodMenuRegister" in str(request.url) or "FoodMenuRegister" in response.headers.get("Content-Type", ""):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.mount("/assets", StaticFiles(directory=os.path.join(dashboard_dir, "assets")), name="dashboard_assets")

# Add no-cache middleware for FoodMenuRegister JS to bust CDN/browser cache
app.add_middleware(_NoCacheMiddleware)'''

if old_mount in c:
    c = c.replace(old_mount, new_mount)
    with open(path, "w") as f:
        f.write(c)
    print("Added no-cache header for FoodMenuRegister JS")
else:
    print("ERROR: Mount pattern not found")
    # Try to find it
    idx = c.find("Mount")
    if idx < 0:
        idx = c.find("mount")
    print(f"  Found in file at offset {idx}")
    print(f"  Context: {repr(c[idx:idx+150])}")
